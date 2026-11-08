"""
Connector Worker.
Executes the full 18-step monitoring workflow from PRD Page 20:
Loads scheduled identifier -> re-checks authorization -> decrypts in vault boundary ->
queries provider -> parses untrusted input -> normalizes -> matches exact email ->
re-checks authorization -> upserts findings/incidents -> writes alert intents to outbox.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from packages.domain.models import (
    Identifier,
    Subject,
    ConsentGrant,
    MonitoringJob,
    SourceObservation,
    Finding,
    FindingObservation,
    Incident,
    IncidentFinding,
    RemediationAction,
    OutboxEvent,
    ProviderConnection,
)
from packages.domain.enums import IdentifierState, IncidentState, ScanState
from packages.provider_adapters.registry import provider_registry
from packages.provider_adapters.base import AuthorizedIdentifier
from packages.security.crypto import vault
from packages.domain.scoring import calculate_severity_and_confidence, calculate_priority_score
from packages.observability.logging import logger
from packages.observability.metrics import metrics


class ConnectorWorker:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_job(self, job_id: str) -> bool:
        """Execute one monitoring job adhering to the 18-step monitoring workflow."""
        res_job = await self.db.execute(select(MonitoringJob).where(MonitoringJob.id == job_id))
        job = res_job.scalars().first()
        if not job or job.state == ScanState.CANCELLED.value or job.state == ScanState.AUTHORIZATION_REVOKED.value:
            return False

        # Step 1 & 2: Re-check account and authorization state
        res_sub = await self.db.execute(select(Subject).where(Subject.id == job.subject_id))
        subject = res_sub.scalars().first()
        if not subject or subject.monitoring_state != "active":
            job.state = ScanState.AUTHORIZATION_REVOKED.value
            await self.db.commit()
            return False

        # Step 3: Check consent
        res_consent = await self.db.execute(
            select(ConsentGrant).where(
                ConsentGrant.tenant_id == job.tenant_id,
                ConsentGrant.subject_id == job.subject_id,
                ConsentGrant.status == "granted"
            )
        )
        if not res_consent.scalars().first():
            job.state = ScanState.AUTHORIZATION_REVOKED.value
            await self.db.commit()
            return False

        # Step 4: Check provider contract and capability
        provider = provider_registry.get_provider(job.provider_name)
        if not provider or not getattr(provider, "is_enabled", True):
            job.state = ScanState.PARTIALLY_COMPLETED.value
            job.outcome = "contract_disabled"
            await self.db.commit()
            return False

        # Step 5: Short-lived lease token
        lease_token = str(uuid.uuid4())
        job.state = ScanState.RUNNING.value
        job.lease_token = lease_token
        job.lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await self.db.commit()

        # Step 6: Resolve encrypted identifier through vault boundary
        res_ident = await self.db.execute(select(Identifier).where(Identifier.id == job.identifier_id))
        ident = res_ident.scalars().first()
        if not ident or ident.state != IdentifierState.ACTIVE.value:
            job.state = ScanState.FAILED.value
            await self.db.commit()
            return False

        decrypted_email = vault.decrypt(ident.encrypted_value, associated_data=job.tenant_id)
        auth_target = AuthorizedIdentifier(
            id=ident.id,
            tenant_id=job.tenant_id,
            subject_id=job.subject_id,
            type=ident.type,
            decrypted_value=decrypted_email,
            authorization_version=subject.authorization_version
        )

        # Step 7 & 8: Submit approved provider query
        try:
            page = await provider.search(auth_target)
        except Exception as e:
            logger.error(f"Provider query error for {job.provider_name}: {str(e)}")
            job.state = ScanState.FAILED.value
            job.outcome = "unavailable"
            await self.db.commit()
            return False

        # Step 9, 10, 11: Normalize allowed observations
        observations = await provider.normalize(page, auth_target)

        # Step 12: Match against exact authorized identifier
        matched_observations = [
            obs for obs in observations
            if obs.match_type == "exact_email"
        ]

        # Step 13: Re-check authorization before persistence
        res_sub_check = await self.db.execute(select(Subject).where(Subject.id == job.subject_id))
        fresh_sub = res_sub_check.scalars().first()
        if not fresh_sub or fresh_sub.monitoring_state != "active" or fresh_sub.authorization_version != auth_target.authorization_version:
            job.state = ScanState.AUTHORIZATION_REVOKED.value
            await self.db.commit()
            return False

        # Step 14: Upsert findings and incident relationships
        if not matched_observations:
            job.state = ScanState.COMPLETED.value
            job.outcome = "no_match"
            job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            return True

        # Process each observation into observations, findings, and incidents
        for obs in matched_observations:
            # Find or create provider connection
            res_conn = await self.db.execute(
                select(ProviderConnection).where(ProviderConnection.provider_name == job.provider_name)
            )
            conn = res_conn.scalars().first()
            if not conn:
                conn = ProviderConnection(
                    provider_name=job.provider_name,
                    account_reference="default_contract_account"
                )
                self.db.add(conn)
                await self.db.flush()

            # Check if source observation already exists for this provider connection and record
            res_obs = await self.db.execute(
                select(SourceObservation).where(
                    SourceObservation.provider_connection_id == conn.id,
                    SourceObservation.provider_record_id == obs.provider_record_id
                )
            )
            source_obs = res_obs.scalars().first()
            if not source_obs:
                source_obs = SourceObservation(
                    tenant_id=job.tenant_id,
                    provider_connection_id=conn.id,
                    provider_record_id=obs.provider_record_id,
                    source_class=obs.source_class,
                    source_name=obs.source_name,
                    event_occurred_at=obs.event_occurred_at,
                    source_published_at=obs.source_published_at,
                    provider_first_seen_at=obs.provider_first_seen_at,
                    exposure_categories=obs.exposure_categories,
                    credential_material_present=obs.credential_material_present,
                    redacted_excerpt=obs.redacted_excerpt,
                    provenance_json=obs.provenance
                )
                self.db.add(source_obs)
                await self.db.flush()

            # Compute severity, confidence, priority
            sev, conf, exp = calculate_severity_and_confidence(
                exposure_categories=obs.exposure_categories,
                credential_material_present=obs.credential_material_present,
                is_stealer_log=obs.source_class == "stealer_log",
                is_spam_list=obs.is_spam_list,
                is_unverified=obs.is_unverified,
                is_fabricated=obs.is_fabricated,
                exact_match=True
            )
            p_score, breakdown = calculate_priority_score(sev, obs.event_occurred_at)

            # Deduplicate finding
            res_f = await self.db.execute(
                select(Finding).where(
                    Finding.tenant_id == job.tenant_id,
                    Finding.subject_id == job.subject_id,
                    Finding.identifier_id == ident.id,
                    Finding.exposure_category == obs.source_class
                )
            )
            finding = res_f.scalars().first()
            if not finding:
                finding = Finding(
                    tenant_id=job.tenant_id,
                    subject_id=job.subject_id,
                    identifier_id=ident.id,
                    exposure_category=obs.source_class,
                    confidence=conf.value,
                    severity=sev.value,
                    state="active"
                )
                self.db.add(finding)
                await self.db.flush()

            # Deduplicate finding observation link
            res_fo = await self.db.execute(
                select(FindingObservation).where(
                    FindingObservation.finding_id == finding.id,
                    FindingObservation.observation_id == source_obs.id
                )
            )
            if not res_fo.scalars().first():
                fo = FindingObservation(
                    finding_id=finding.id,
                    observation_id=source_obs.id
                )
                self.db.add(fo)

            # Grouping key for incident
            grouping_key = f"{obs.source_name}_{ident.masked_value}"
            res_inc = await self.db.execute(
                select(Incident).where(
                    Incident.tenant_id == job.tenant_id,
                    Incident.subject_id == job.subject_id,
                    Incident.incident_grouping_key == grouping_key
                )
            )
            incident = res_inc.scalars().first()

            is_new_incident = False
            if not incident:
                is_new_incident = True
                incident = Incident(
                    tenant_id=job.tenant_id,
                    subject_id=job.subject_id,
                    incident_grouping_key=grouping_key,
                    title=f"Exposure detected in {obs.source_name}",
                    severity=sev.value,
                    confidence=conf.value,
                    state=IncidentState.NEW.value,
                    identifier_id=ident.id,
                    exposure_categories=obs.exposure_categories,
                    priority_score=p_score,
                    event_occurred_at=obs.event_occurred_at,
                    first_detected_at=datetime.now(timezone.utc)
                )
                self.db.add(incident)
                await self.db.flush()

                # Add recommended remediation actions
                actions = [
                    RemediationAction(
                        tenant_id=job.tenant_id,
                        incident_id=incident.id,
                        action_type="change_affected_password",
                        title="Change password on affected service",
                        description=f"Update your login password on {obs.source_name} and any account where the same password was used."
                    ),
                    RemediationAction(
                        tenant_id=job.tenant_id,
                        incident_id=incident.id,
                        action_type="enable_mfa",
                        title="Enable Multi-Factor Authentication (MFA)",
                        description="Activate an authenticator app (TOTP) or hardware key for your primary email and related accounts."
                    )
                ]
                self.db.add_all(actions)

            inc_finding = IncidentFinding(
                incident_id=incident.id,
                finding_id=finding.id
            )
            self.db.add(inc_finding)

            # Step 15: Write alert intent to transactional outbox
            if is_new_incident and sev.value in ["medium", "high", "critical"]:
                outbox_alert = OutboxEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="alert.notification.requested",
                    tenant_id=job.tenant_id,
                    subject_id=job.subject_id,
                    resource_id=incident.id,
                    authorization_version=subject.authorization_version,
                    payload={
                        "incident_id": incident.id,
                        "title": incident.title,
                        "severity": incident.severity,
                        "masked_identifier": ident.masked_value
                    }
                )
                self.db.add(outbox_alert)

        # Step 16, 17, 18: Commit checkpoint and release lease
        job.state = ScanState.COMPLETED.value
        job.outcome = "matched"
        job.completed_at = datetime.now(timezone.utc)
        job.lease_token = None
        await self.db.commit()

        metrics.increment("incidents_created_total", len(matched_observations))
        return True
