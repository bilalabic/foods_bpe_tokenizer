"""Collect registered food names from TÜRKPATENT into foods_raw.txt.

Queries two product groups across every province, one page at a time, with a delay
between requests. Read the portal's current terms before running:
https://ci.turkpatent.gov.tr/sayfa/kullanım-koşulları

Usage:
    python scrape_foods.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENDPOINT = "https://ci.turkpatent.gov.tr/Data/GetList"
PAGE_SIZE = 150
TARGET = 500

# 51 = "Yemekler ve çorbalar", 54 = pastry and desserts, used when 51 falls short.
PRODUCT_GROUPS = ("51", "54")


def fetch_page(group_id: str, start: int) -> dict:
    body = urlencode(
        {
            "draw": "1",
            "start": str(start),
            "length": str(PAGE_SIZE),
            "Name": "",
            "FileNumber": "",
            "ApplicationDate": "",
            "ApplicationDateEnd": "",
            "RegistrationNumber": "",
            "RegistrationDate": "",
            "RegistrationDateEnd": "",
            "TypeId": "",
            "ProductGroupId": group_id,
            "CityId": "",
            "StatusId": "545",  # Tescilli
        }
    ).encode("utf-8")

    request = Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "single-letter-transformers-educational-dataset/0.1",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def strip_alternatives(value: str) -> str:
    """Keep the primary name, dropping the slash and parenthesised variants."""
    name = value.split("/", 1)[0]
    name = re.sub(r"\s*\([^)]*\)", "", name)
    return " ".join(name.split()).strip(" -")


def scrape_names(target: int, delay: float) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()

    for group_id in PRODUCT_GROUPS:
        start = 0
        while True:
            payload = fetch_page(group_id, start)
            rows = payload.get("data", [])
            total = int(payload.get("recordsFiltered", 0))

            for row in rows:
                name = strip_alternatives(row.get("Name") or "")
                key = name.casefold()
                if name and key not in seen:
                    seen.add(key)
                    names.append(name)
            start += len(rows)
            if not rows or start >= total:
                break
            time.sleep(delay)

        if len(names) >= target:
            break

    # Fixed seed: the same query returns the same sample.
    random.Random(42).shuffle(names)
    return names[:target]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download registered food names as TXT.")
    parser.add_argument("--target", type=int, default=TARGET)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("foods_raw.txt"),
    )
    args = parser.parse_args()

    if not 1 <= args.target <= TARGET:
        parser.error(f"--target must be between 1 and {TARGET}")
    if args.delay < 1.0:
        parser.error("--delay must be at least 1.0 seconds")

    names = scrape_names(args.target, args.delay)
    args.output.write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"wrote {len(names)} names: {args.output}")


if __name__ == "__main__":
    main()
