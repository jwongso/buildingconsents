"""Scrape NZ building-related Acts from legislation.govt.nz.

Same HTML parsing pattern as nz-legal-rag: each div.prov becomes one section.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

_CURL_CMD = [
    "curl", "-s", "-L", "--compressed",
    "-A", "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "--max-time", "30",
]

ACTS: dict[str, dict] = {
    "BA2004": {
        "title": "Building Act 2004",
        "year": 2004,
        "url": "https://www.legislation.govt.nz/act/public/2004/0072/latest/whole.html",
    },
    "EBWO2020": {
        "title": "Building (Exempt Building Work) Order 2020",
        "year": 2020,
        "url": "https://www.legislation.govt.nz/regulation/public/2020/0171/latest/whole.html",
    },
    "RMA1991": {
        "title": "Resource Management Act 1991",
        "year": 1991,
        "url": "https://www.legislation.govt.nz/act/public/1991/0069/latest/whole.html",
    },
}


@dataclass
class LegSection:
    act_code: str
    act_title: str
    act_year: int
    section_num: str
    section_title: str
    dlm_id: str
    url: str
    text: str


async def _curl_get(url: str) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            *_CURL_CMD, url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=35)
        if proc.returncode == 0 and stdout:
            return stdout.decode("utf-8", errors="replace")
        return None
    except Exception:
        return None


def _parse_act(html: str, act_code: str) -> list[LegSection]:
    meta = ACTS[act_code]
    base_url = meta["url"]
    soup = BeautifulSoup(html, "html.parser")

    sections: list[LegSection] = []
    for prov in soup.find_all("div", class_="prov"):
        dlm_id = prov.get("id", "")
        if "js-discontinued-info" in prov.get("class", []):
            continue

        heading = prov.find("h5", class_="prov")
        if not heading:
            continue

        label = heading.find("span", class_="label")
        section_num = label.get_text(strip=True) if label else ""
        if label:
            label.extract()
        section_title = heading.get_text(strip=True)

        body = prov.find("div", class_="prov-body")
        if not body:
            continue
        for tag in body.find_all("div", class_="history"):
            tag.decompose()

        text = re.sub(r"\s+", " ", body.get_text(separator=" ", strip=True)).strip()
        if len(text) < 30:
            continue

        sections.append(LegSection(
            act_code=act_code,
            act_title=meta["title"],
            act_year=meta["year"],
            section_num=section_num,
            section_title=section_title,
            dlm_id=dlm_id,
            url=f"{base_url}#{dlm_id}" if dlm_id else base_url,
            text=text,
        ))

    return sections


async def scrape_act(act_code: str, cache_dir: Path) -> list[LegSection]:
    if act_code not in ACTS:
        raise ValueError(f"Unknown act: {act_code}. Available: {list(ACTS)}")

    meta = ACTS[act_code]
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{act_code}.html"

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8", errors="replace")
        print(f"  [{act_code}] loaded from cache ({len(html):,} bytes)")
    else:
        print(f"  [{act_code}] fetching {meta['url']} ...")
        html = await _curl_get(meta["url"])
        if not html:
            print(f"  [{act_code}] fetch failed")
            return []
        cache_file.write_text(html, encoding="utf-8")
        print(f"  [{act_code}] fetched ({len(html):,} bytes)")

    sections = _parse_act(html, act_code)
    print(f"  [{act_code}] {len(sections)} sections parsed")
    return sections
