from __future__ import annotations

from prometheus_client import Counter


PROVISION_REQUESTS = Counter("provision_requests_total", "Successful provision operations")
PROVISION_ERRORS = Counter("provision_errors_total", "Provision errors")
REVOCATION_REQUESTS = Counter("provision_revocations_total", "Revocation operations")
SWITCH_REQUESTS = Counter("provision_switch_total", "Switch node operations")
