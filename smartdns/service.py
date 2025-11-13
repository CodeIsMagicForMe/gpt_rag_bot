from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress

from prometheus_client import start_http_server

from .config import SmartDNSSettings, get_settings
from .dns_server import create_dns_server, parse_upstreams
from .metrics import RULE_RELOADS, RULES_ACTIVE
from .monitor import DNSMonitor
from .rules import RuleStore, build_rule_source

logger = logging.getLogger(__name__)


class RuleReloader:
    def __init__(self, store: RuleStore, interval: int) -> None:
        self.store = store
        self.interval = interval

    async def run(self) -> None:
        while True:
            try:
                changed = await asyncio.to_thread(self.store.reload)
                status = "updated" if changed else "skipped"
                RULE_RELOADS.labels(status=status).inc()
                if changed:
                    RULES_ACTIVE.set(len(self.store))
            except Exception as exc:
                RULE_RELOADS.labels(status="error").inc()
                logger.exception("Failed to reload SmartDNS rules: %s", exc)
            await asyncio.sleep(self.interval)


async def run_service(settings: SmartDNSSettings) -> None:
    os.environ.setdefault("DATABASE_URL", settings.database_url)
    rule_source = build_rule_source(settings.rules_backend, settings.rules_file)
    store = RuleStore(rule_source)
    await asyncio.to_thread(store.reload)
    upstreams = parse_upstreams(settings.upstream_servers)
    dns_server = create_dns_server(
        store=store,
        upstreams=upstreams,
        timeout=settings.upstream_timeout,
        host=settings.host,
        port=settings.port,
        enable_tcp=settings.enable_tcp,
    )
    dns_server.start_thread()
    logger.info("SmartDNS listening on %s:%s (TCP=%s)", settings.host, settings.port, settings.enable_tcp)
    start_http_server(settings.metrics_port, addr=settings.metrics_host)
    logger.info("Prometheus metrics exposed on %s:%s", settings.metrics_host, settings.metrics_port)

    tasks = []
    if settings.reload_interval > 0:
        tasks.append(asyncio.create_task(RuleReloader(store, settings.reload_interval).run()))
    if settings.monitor_domain:
        monitor = DNSMonitor(
            host=settings.monitor_host,
            port=settings.monitor_port,
            domain=settings.monitor_domain,
            interval=settings.monitor_interval,
            timeout=settings.monitor_timeout,
        )
        tasks.append(asyncio.create_task(monitor.run()))

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        for task in tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        dns_server.stop()
        logger.info("SmartDNS server stopped")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    try:
        asyncio.run(run_service(settings))
    except KeyboardInterrupt:
        logger.info("SmartDNS interrupted, shutting down")


if __name__ == "__main__":
    main()
