from __future__ import annotations

import asyncio
import logging
import time

from dnslib import DNSRecord

from .metrics import MONITOR_STATUS

logger = logging.getLogger(__name__)


class DNSMonitor:
    def __init__(self, host: str, port: int, domain: str, interval: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.domain = domain
        self.interval = interval
        self.timeout = timeout

    async def run(self) -> None:
        while True:
            try:
                await asyncio.to_thread(self._probe)
                MONITOR_STATUS.set(1)
            except Exception as exc:
                MONITOR_STATUS.set(0)
                logger.warning("SmartDNS health probe failed: %s", exc)
            await asyncio.sleep(self.interval)

    def _probe(self) -> None:
        query = DNSRecord.question(self.domain)
        start = time.perf_counter()
        query.send(self.host, self.port, timeout=self.timeout)
        duration = time.perf_counter() - start
        logger.debug("Health probe resolved %s in %.3fs", self.domain, duration)
