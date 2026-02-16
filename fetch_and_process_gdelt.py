#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import logging
import time
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

LAST_UPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
ARCHIVE_DIR = Path("data/archive")
OUTPUT_FILE = Path("latest_risks.json")
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 5

COLUMNS = [
    "GLOBALEVENTID",
    "SQLDATE",
    "MonthYear",
    "Year",
    "FractionDate",
    "Actor1Code",
    "Actor1Name",
    "Actor1CountryCode",
    "Actor1KnownGroupCode",
    "Actor1EthnicCode",
    "Actor1Religion1Code",
    "Actor1Religion2Code",
    "Actor1Type1Code",
    "Actor1Type2Code",
    "Actor1Type3Code",
    "Actor2Code",
    "Actor2Name",
    "Actor2CountryCode",
    "Actor2KnownGroupCode",
    "Actor2EthnicCode",
    "Actor2Religion1Code",
    "Actor2Religion2Code",
    "Actor2Type1Code",
    "Actor2Type2Code",
    "Actor2Type3Code",
    "IsRootEvent",
    "EventCode",
    "EventBaseCode",
    "EventRootCode",
    "QuadClass",
    "GoldsteinScale",
    "NumMentions",
    "NumSources",
    "NumArticles",
    "AvgTone",
    "Actor1Geo_Type",
    "Actor1Geo_FullName",
    "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code",
    "Actor1Geo_Lat",
    "Actor1Geo_Long",
    "Actor1Geo_FeatureID",
    "Actor2Geo_Type",
    "Actor2Geo_FullName",
    "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code",
    "Actor2Geo_Lat",
    "Actor2Geo_Long",
    "Actor2Geo_FeatureID",
    "ActionGeo_Type",
    "ActionGeo_FullName",
    "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code",
    "ActionGeo_Lat",
    "ActionGeo_Long",
    "ActionGeo_FeatureID",
    "DATEADDED",
    "SOURCEURL",
]

# FIPS 10-4 country code -> ISO 3166-1 alpha-3 (mainly high-frequency/modern codes)
FIPS_TO_ISO3 = {
    "AF": "AFG",
    "AL": "ALB",
    "AG": "DZA",
    "AR": "ARG",
    "AM": "ARM",
    "AS": "AUS",
    "AU": "AUT",
    "AZ": "AZE",
    "BA": "BHR",
    "BG": "BGD",
    "BB": "BRB",
    "BO": "BLR",
    "BE": "BEL",
    "BH": "BLZ",
    "BN": "BEN",
    "BT": "BTN",
    "BL": "BOL",
    "BK": "BIH",
    "BC": "BWA",
    "BR": "BRA",
    "BU": "BGR",
    "BM": "MMR",
    "BY": "BDI",
    "CM": "KHM",
    "CA": "CAN",
    "CV": "CPV",
    "CF": "CAF",
    "CD": "TCD",
    "CI": "CHL",
    "CH": "CHN",
    "CO": "COL",
    "CN": "COM",
    "CG": "COD",
    "CS": "CRI",
    "IV": "CIV",
    "HR": "HRV",
    "CU": "CUB",
    "CY": "CYP",
    "EZ": "CZE",
    "DA": "DNK",
    "DJ": "DJI",
    "DO": "DMA",
    "DR": "DOM",
    "EC": "ECU",
    "EG": "EGY",
    "ES": "SLV",
    "EN": "EST",
    "ET": "ETH",
    "FI": "FIN",
    "FR": "FRA",
    "GA": "GAB",
    "GM": "DEU",
    "GH": "GHA",
    "GR": "GRC",
    "GT": "GTM",
    "GV": "GIN",
    "GY": "GUY",
    "HA": "HTI",
    "HO": "HND",
    "HU": "HUN",
    "IC": "ISL",
    "IN": "IND",
    "ID": "IDN",
    "IR": "IRN",
    "IZ": "IRQ",
    "EI": "IRL",
    "IS": "ISR",
    "IT": "ITA",
    "JM": "JAM",
    "JA": "JPN",
    "JO": "JOR",
    "KZ": "KAZ",
    "KE": "KEN",
    "KN": "PRK",
    "KS": "KOR",
    "KV": "XKX",
    "KU": "KWT",
    "KG": "KGZ",
    "LA": "LAO",
    "LG": "LVA",
    "LE": "LBN",
    "LT": "LSO",
    "LI": "LBR",
    "LY": "LBY",
    "LH": "LTU",
    "LU": "LUX",
    "MA": "MDG",
    "MI": "MWI",
    "MY": "MYS",
    "MV": "MDV",
    "ML": "MLI",
    "MT": "MLT",
    "MR": "MRT",
    "MX": "MEX",
    "MD": "MDA",
    "MG": "MNG",
    "MJ": "MNE",
    "MO": "MAR",
    "MZ": "MOZ",
    "WA": "NAM",
    "NP": "NPL",
    "NL": "NLD",
    "NZ": "NZL",
    "NU": "NIC",
    "NG": "NER",
    "NI": "NGA",
    "MK": "MKD",
    "NO": "NOR",
    "MU": "OMN",
    "PK": "PAK",
    "PM": "PAN",
    "PP": "PNG",
    "PA": "PRY",
    "PE": "PER",
    "RP": "PHL",
    "PL": "POL",
    "PO": "PRT",
    "QA": "QAT",
    "RO": "ROU",
    "RS": "RUS",
    "RW": "RWA",
    "SA": "SAU",
    "SG": "SEN",
    "RI": "SRB",
    "SE": "SYC",
    "SL": "SLE",
    "SN": "SGP",
    "LO": "SVK",
    "SI": "SVN",
    "SF": "ZAF",
    "SP": "ESP",
    "CE": "LKA",
    "SU": "SDN",
    "SW": "SWE",
    "SZ": "CHE",
    "SY": "SYR",
    "TW": "TWN",
    "TI": "TJK",
    "TZ": "TZA",
    "TH": "THA",
    "TO": "TON",
    "TD": "TTO",
    "TS": "TUN",
    "TU": "TUR",
    "TX": "TKM",
    "UG": "UGA",
    "UP": "UKR",
    "AE": "ARE",
    "UK": "GBR",
    "US": "USA",
    "UY": "URY",
    "UZ": "UZB",
    "VE": "VEN",
    "VM": "VNM",
    "YM": "YEM",
    "ZA": "ZMB",
    "ZI": "ZWE",
}


def fetch_bytes(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            logging.warning("Fetch failed (%s/%s) for %s: %s", attempt, MAX_RETRIES, url, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS * attempt)
    raise RuntimeError(f"Failed to fetch {url}") from last_error


def get_latest_export_url() -> str:
    content = fetch_bytes(LAST_UPDATE_URL).decode("utf-8", errors="ignore")
    for line in content.splitlines():
        parts = line.split(" ")
        if len(parts) >= 3 and parts[2].endswith(".export.CSV.zip"):
            return parts[2]
    raise RuntimeError("Could not find latest GDELT export URL")


def download_latest_rows() -> list[list[str]]:
    export_url = get_latest_export_url()
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            payload = fetch_bytes(export_url)
            with zipfile.ZipFile(BytesIO(payload)) as zf:
                names = zf.namelist()
                if not names:
                    raise RuntimeError("GDELT ZIP archive is empty")
                first_name = names[0]
                with zf.open(first_name) as csv_file:
                    decoded = (line.decode("utf-8", errors="replace") for line in csv_file)
                    return [row for row in csv.reader(decoded, delimiter="\t") if row]
        except (zipfile.BadZipFile, IndexError, KeyError, RuntimeError) as exc:
            last_error = exc
            logging.warning("GDELT ZIP processing failed (%s/%s): %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS * attempt)
    raise RuntimeError("Could not load latest GDELT export") from last_error


def append_archive(rows: list[list[str]]) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_file = ARCHIVE_DIR / f"{datetime.now(UTC).date().isoformat()}.csv"
    write_header = not archive_file.exists() or archive_file.stat().st_size == 0

    with archive_file.open("a", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        if write_header:
            writer.writerow(COLUMNS)
        writer.writerows(rows)


def parse_dateadded(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    except ValueError:
        return None


def fips_to_iso3(code: str) -> str | None:
    if not code:
        return None
    code = code.strip().upper()
    if len(code) == 3 and code.isalpha():
        return code
    return FIPS_TO_ISO3.get(code)


def iter_recent_archive_rows(hours: int = 24):
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    for day_delta in (0, 1):
        day = (datetime.now(UTC) - timedelta(days=day_delta)).date().isoformat()
        path = ARCHIVE_DIR / f"{day}.csv"
        if not path.exists():
            continue
        with path.open("r", newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                timestamp = parse_dateadded(row.get("DATEADDED", ""))
                if timestamp and timestamp >= cutoff:
                    yield row


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def distill_latest_risks() -> list[dict[str, object]]:
    aggregate: dict[str, dict[str, object]] = defaultdict(
        lambda: {"conflict_score": 0.0, "event_count": 0, "sample_url": "", "max_mentions": 0.0}
    )

    for row in iter_recent_archive_rows(hours=24):
        iso3 = fips_to_iso3(row.get("ActionGeo_CountryCode", ""))
        if not iso3:
            continue

        goldstein = to_float(row.get("GoldsteinScale", "0"))
        mentions = to_float(row.get("NumMentions", "1"))
        if mentions <= 0:
            mentions = 1.0
        conflict_impact = max(0.0, -goldstein) * mentions

        country = aggregate[iso3]
        country["conflict_score"] = float(country["conflict_score"]) + conflict_impact
        country["event_count"] = int(country["event_count"]) + 1

        if mentions > float(country["max_mentions"]):
            country["max_mentions"] = mentions
            country["sample_url"] = row.get("SOURCEURL", "")

    risks = [
        {
            "country_iso3": country,
            "conflict_score": round(float(values["conflict_score"]), 2),
            "event_count": int(values["event_count"]),
            "sample_url": values["sample_url"],
        }
        for country, values in aggregate.items()
    ]
    risks.sort(key=lambda x: (x["conflict_score"], x["event_count"]), reverse=True)
    return risks


def export_risks_json() -> None:
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_hours": 24,
        "risks": distill_latest_risks(),
    }
    with OUTPUT_FILE.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = download_latest_rows()
    append_archive(rows)
    export_risks_json()
    logging.info("Processed %s latest rows", len(rows))


if __name__ == "__main__":
    main()
