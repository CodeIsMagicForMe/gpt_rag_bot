from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable, List

from dnslib import A, DNSRecord, QTYPE, RR
from dnslib.server import BaseResolver, DNSServer

from .metrics import REQUEST_TOTAL, RULE_MATCHES, RULES_ACTIVE, UPSTREAM_LATENCY
from .rules import RuleStore

logger = logging.getLogger(__name__)


@dataclass
class Upstream:
    host: str
    port: int


def parse_upstreams(values: Iterable[str]) -> List[Upstream]:
    upstreams: List[Upstream] = []
    for value in values:
        if ":" in value:
            host, port_str = value.split(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                logger.warning("Invalid port in upstream %s, skipping", value)
                continue
        else:
            host, port = value, 53
        upstreams.append(Upstream(host=host, port=port))
    if not upstreams:
        raise ValueError("At least one upstream DNS server is required")
    return upstreams


class SmartDNSResolver(BaseResolver):
    def __init__(self, store: RuleStore, upstreams: List[Upstream], timeout: float) -> None:
        self.store = store
        self.upstreams = upstreams
        self.timeout = timeout

    def resolve(self, request: DNSRecord, handler) -> DNSRecord:  # type: ignore[override]
        qname = str(request.q.qname).rstrip(".").lower()
        qtype = QTYPE[request.q.qtype]
        logger.debug("Received query %s %s", qname, qtype)
        if qtype in {"A", "ANY"}:
            rule = self.store.lookup(qname)
            if rule:
                reply = request.reply()
                reply.add_answer(RR(rname=request.q.qname, rtype=QTYPE.A, rclass=1, ttl=rule.ttl, rdata=A(rule.ip_address)))
                REQUEST_TOTAL.labels(result="rule").inc()
                RULE_MATCHES.labels(pattern=rule.pattern).inc()
                return reply
        try:
            response = self._forward(request)
            REQUEST_TOTAL.labels(result="upstream").inc()
            return response
        except Exception:
            REQUEST_TOTAL.labels(result="failed").inc()
            raise

    def _forward(self, request: DNSRecord) -> DNSRecord:
        last_error: Exception | None = None
        for upstream in self.upstreams:
            try:
                start = time.perf_counter()
                raw = request.send(upstream.host, upstream.port, timeout=self.timeout)
                duration = time.perf_counter() - start
                UPSTREAM_LATENCY.observe(duration)
                return DNSRecord.parse(raw)
            except Exception as exc:
                last_error = exc
                logger.warning("Upstream %s:%s failed: %s", upstream.host, upstream.port, exc)
                continue
        if last_error:
            raise last_error
        raise RuntimeError("No upstream servers configured")


def create_dns_server(
    store: RuleStore,
    upstreams: List[Upstream],
    timeout: float,
    host: str,
    port: int,
    enable_tcp: bool,
) -> DNSServer:
    resolver = SmartDNSResolver(store=store, upstreams=upstreams, timeout=timeout)
    server = DNSServer(resolver, address=host, port=port, tcp=enable_tcp, udp=True)
    RULES_ACTIVE.set(len(store))
    return server
