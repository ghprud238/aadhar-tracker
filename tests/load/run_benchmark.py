"""
Native Async Load Benchmark for Suraksha Platform.
Executes 200 concurrent simulated requests using httpx to measure latency percentiles and outbox throughput.
"""
import asyncio
import time
import uuid
import statistics
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db


async def run_benchmark(concurrency: int = 50, total_requests: int = 200):
    await init_db()
    transport = ASGITransport(app=app)
    latencies: list[float] = []

    print(f"[*] Starting native benchmark: {total_requests} requests across {concurrency} workers...")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Pre-authenticate a benchmark subject
        res_auth = await client.get("/api/v1/auth/callback?email=benchmark@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        semaphore = asyncio.Semaphore(concurrency)

        async def worker(req_idx: int):
            async with semaphore:
                start = time.perf_counter()
                if req_idx % 3 == 0:
                    resp = await client.get("/api/v1/companion/glance", headers=headers)
                elif req_idx % 3 == 1:
                    resp = await client.get("/readyz")
                else:
                    resp = await client.get("/metrics")
                elapsed = (time.perf_counter() - start) * 1000  # ms
                assert resp.status_code == 200
                latencies.append(elapsed)

        start_time = time.perf_counter()
        tasks = [worker(i) for i in range(total_requests)]
        await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    rps = total_requests / total_time

    print("\n[+] Benchmark Results:")
    print(f"    Total Requests:     {total_requests}")
    print(f"    Elapsed Time:       {total_time:.2f}s")
    print(f"    Throughput:         {rps:.1f} requests/sec")
    print(f"    Latency p50:        {p50:.2f} ms")
    print(f"    Latency p95:        {p95:.2f} ms")
    print(f"    Latency p99:        {p99:.2f} ms")
    return {"rps": rps, "p50": p50, "p95": p95}


if __name__ == "__main__":
    asyncio.run(run_benchmark())
