"""Reguli sursă+gazdă → browser. Prima potrivire câștigă."""

from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "shunt" / "rules.json"


GLOB = set("*?[")


def host_matches(pattern: str, host: str) -> bool:
    """Un domeniu scris simplu acoperă și subdomeniile lui.

    Altfel `github.com` n-ar prinde `gist.github.com`, iar regula ar părea
    stricată exact în cazul pentru care ai scris-o. Cine vrea altceva scrie un
    glob: `*.github.com` prinde doar subdomeniile.
    """
    pattern = (pattern or "*").strip().lower().lstrip(".")
    if not pattern or pattern == "*":
        return True
    host = (host or "").lower()
    if GLOB & set(pattern):
        return fnmatch.fnmatch(host, pattern)
    return host == pattern or host.endswith("." + pattern)


@dataclass
class Rule:
    source: str = "*"  # resourceClass al ferestrei-sursă
    host: str = "*"
    browser: str = ""  # desktop-id, ex. "com.brave.Browser.desktop"

    def matches(self, source: str, host: str) -> bool:
        return fnmatch.fnmatch(source or "", self.source) and host_matches(
            self.host, host
        )

    @property
    def rank(self) -> tuple[bool, bool, int]:
        """Cât de îngustă e regula. Mai mare înseamnă mai specifică.

        Gazda contează înaintea aplicației: „GitHub se deschide în Brave" e o
        intenție mai fermă decât „din Slack deschid cu Chrome", și ar suna a
        defect dacă a doua ar înghiți-o. Ierarhia iese gazdă+aplicație, apoi
        gazdă, apoi aplicație, apoi regula generală.
        """
        return (self.host != "*", self.source != "*", len(self.host.replace("*", "")))


def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def load() -> list[Rule]:
    path = config_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        # Fișier stricat: mai bine fără reguli decât cu jumătate din ele.
        print(f"shunt: cannot read {path}: {exc}")
        return []
    return [
        Rule(
            source=item.get("source", "*"),
            host=item.get("host", "*"),
            browser=item["browser"],
        )
        for item in raw
        if isinstance(item, dict) and item.get("browser")
    ]


def save(rules: list[Rule]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(r) for r in rules], indent=2) + "\n", encoding="utf-8"
    )


def match(rules: list[Rule], source: str, url: str) -> str | None:
    """Desktop-id-ul browserului pentru (sursă, url), sau None."""
    host = host_of(url)
    for rule in rules:
        if rule.matches(source, host):
            return rule.browser
    return None


def insert(rules: list[Rule], new: Rule) -> list[Rule]:
    """Pune regula deasupra primeia mai largi decât ea.

    Prima potrivire câștigă, deci o excepție adăugată la coadă n-ar apuca
    niciodată să se aplice: „Slack → Chrome" ar înghiți „GitHub din Slack →
    Brave". Ordinea rămâne a ta, butoanele de mutat sunt tot acolo.
    """
    rules = list(rules)
    for index, existing in enumerate(rules):
        if new.rank > existing.rank:
            rules.insert(index, new)
            return rules
    rules.append(new)
    return rules


def remember(source: str, browser_desktop_id: str) -> None:
    """Regula generală pentru o aplicație-sursă, înlocuind-o pe cea existentă.

    Excepțiile pe gazdă rămân neatinse: se șterge doar regula cu host `*`.
    """
    rules = [r for r in load() if not (r.source == source and r.host == "*")]
    save(insert(rules, Rule(source=source, host="*", browser=browser_desktop_id)))
