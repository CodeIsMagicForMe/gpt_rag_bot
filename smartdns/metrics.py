from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

REQUEST_TOTAL = Counter(
    "smartdns_requests_total",
    "Total DNS queries handled by SmartDNS",
    labelnames=("result",),
)

RULE_MATCHES = Counter(
    "smartdns_rule_matches_total",
    "Number of queries served from SmartDNS rules",
    labelnames=("pattern",),
)

RULE_RELOADS = Counter(
    "smartdns_rule_reloads_total",
    "Rule reload attempts",
    labelnames=("status",),
)

RULES_ACTIVE = Gauge(
    "smartdns_rules_active",
    "Currently active rules in memory",
)

UPSTREAM_LATENCY = Histogram(
    "smartdns_upstream_request_seconds",
    "Latency of upstream DNS queries",
)

MONITOR_STATUS = Gauge(
    "smartdns_health_status",
    "1 if last health probe succeeded",
)
