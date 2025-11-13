from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Dict, Iterable, List, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rule:
    pattern: str
    ip_address: str
    ttl: int = 60


class RuleSource(Protocol):
    def load(self) -> List[Rule]:
        ...


class DatabaseRuleSource:
    def load(self) -> List[Rule]:
        from db import session_scope
        from db.models import SmartDNSRule

        with session_scope() as session:
            rows = (
                session.query(SmartDNSRule)
                .filter(SmartDNSRule.is_active.is_(True))
                .order_by(SmartDNSRule.id.asc())
                .all()
            )
            logger.debug("Loaded %s rules from database", len(rows))
            return [Rule(pattern=row.pattern.lower(), ip_address=row.ip_address, ttl=row.ttl) for row in rows]


class FileRuleSource:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> List[Rule]:
        if not self.path.exists():
            logger.warning("Rules file %s does not exist", self.path)
            return []
        rules: List[Rule] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts = stripped.split()
                if len(parts) < 2:
                    continue
                pattern, ip = parts[0].lower(), parts[1]
                try:
                    ttl = int(parts[2]) if len(parts) > 2 else 60
                except ValueError:
                    logger.warning("Invalid TTL for rule %s", stripped)
                    continue
                rules.append(Rule(pattern=pattern, ip_address=ip, ttl=ttl))
        logger.debug("Loaded %s rules from file %s", len(rules), self.path)
        return rules


class CompositeRuleSource:
    def __init__(self, sources: Iterable[RuleSource]) -> None:
        self.sources = list(sources)

    def load(self) -> List[Rule]:
        merged: Dict[str, Rule] = {}
        for source in self.sources:
            for rule in source.load():
                merged[rule.pattern] = rule
        return list(merged.values())


class RuleStore:
    def __init__(self, source: RuleSource) -> None:
        self._source = source
        self._lock = RLock()
        self._rules: Dict[str, Rule] = {}

    def reload(self) -> bool:
        rules = self._source.load()
        normalized = {rule.pattern.rstrip("."): rule for rule in rules}
        with self._lock:
            if normalized == self._rules:
                return False
            self._rules = normalized
        logger.info("Loaded %s SmartDNS rules", len(normalized))
        return True

    def lookup(self, domain: str) -> Rule | None:
        domain = domain.rstrip(".").lower()
        with self._lock:
            if domain in self._rules:
                return self._rules[domain]
            parts = domain.split(".")
            for idx in range(1, len(parts)):
                candidate = "*." + ".".join(parts[idx:])
                if candidate in self._rules:
                    return self._rules[candidate]
        return None

    def __len__(self) -> int:
        with self._lock:
            return len(self._rules)


def build_rule_source(backend: str, rules_file: str | None) -> RuleSource:
    sources: List[RuleSource] = []
    backend = backend.lower()
    if backend in {"auto", "db", "both"}:
        sources.append(DatabaseRuleSource())
    if backend in {"auto", "file", "both"} and rules_file:
        sources.append(FileRuleSource(rules_file))
    if not sources:
        raise RuntimeError("No rule sources configured")
    if len(sources) == 1:
        return sources[0]
    return CompositeRuleSource(sources)
