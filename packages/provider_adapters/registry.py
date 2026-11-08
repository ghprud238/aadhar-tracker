"""
Dynamic Capability Registry for Intelligence Providers.
Supports operator kill-switches, capability checks, and health introspection.
"""
from typing import Dict, List, Optional
from packages.provider_adapters.base import IntelligenceProvider, ProviderCapabilities, ProviderHealth
from packages.provider_adapters.hibp import HibpProvider
from packages.provider_adapters.flare import FlareProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, IntelligenceProvider] = {}
        # Register standard default providers
        self.register_provider("hibp", HibpProvider())
        self.register_provider("flare", FlareProvider())

    def register_provider(self, name: str, provider: IntelligenceProvider):
        self._providers[name] = provider

    def get_provider(self, name: str) -> Optional[IntelligenceProvider]:
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    async def get_all_capabilities(self) -> List[ProviderCapabilities]:
        caps = []
        for p in self._providers.values():
            caps.append(await p.capabilities())
        return caps

    async def get_all_health(self) -> List[ProviderHealth]:
        healths = []
        for p in self._providers.values():
            healths.append(await p.healthcheck())
        return healths

    def disable_provider(self, name: str) -> bool:
        p = self.get_provider(name)
        if p and hasattr(p, "is_enabled"):
            p.is_enabled = False
            return True
        return False

    def enable_provider(self, name: str) -> bool:
        p = self.get_provider(name)
        if p and hasattr(p, "is_enabled"):
            p.is_enabled = True
            return True
        return False


provider_registry = ProviderRegistry()
