#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
Automated web scraper for the top 20 startup incubators.

Input:
    critic_top20_all_features.csv

Required columns:
    Incubator_Name
    More Info (Website Link)

For each incubator:
    1. Download current homepage HTML.
    2. Discover and download the About Us page.
    3. Find the earliest successful HTML archive capture per month.
    4. Save archived HTML files in separate folders.

Archive period:
    January 2022 - September 2026

Output:
    scraped_html_top20/
        incubator_01_name/
            current/
            archived/
        incubator_02_name/
            current/
            archived/
        master_scraping_report.csv
"""

# ============================================================
# 1. IMPORT LIBRARIES
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import calendar
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from wayback import WaybackClient, Mode


# ============================================================
# 2. CONFIGURATION
# ============================================================

INPUT_CSV = "critic_top20_all_features.csv"

NAME_COL = "Incubator_Name"
URL_COL = "More Info (Website Link)"

START_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)

END_DATE = datetime(
    2026, 9, 30, 23, 59, 59,
    tzinfo=timezone.utc
)

OUTPUT_ROOT = Path("scraped_html_top20")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

REQUEST_DELAY = 1

session = requests.Session()
session.headers.update({
    "User-Agent": "AcademicResearchScraper/1.0"
})


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def safe_folder_name(name, max_length=70):
    """Convert an incubator name into a safe folder name."""
    name = str(name).strip().lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s-]+", "_", name)

    return name[:max_length].strip("_") or "unnamed_incubator"


def normalize_url(url):
    """Clean and validate a website URL."""
    if pd.isna(url):
        return None

    url = str(url).strip().strip("'\"")

    if not url or url.lower() in {
        "nan", "none", "null", "n/a", "na", "-"
    }:
        return None

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.netloc or "." not in parsed.netloc:
        return None

    return url


def build_expected_months():
    """Generate all months from January 2022 to September 2026."""
    months = []
    year, month = 2022, 1

    while (year, month) <= (2026, 9):
        months.append(f"{year}-{month:02d}")

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return months


EXPECTED_MONTHS = build_expected_months()


# ============================================================
# 4. DOWNLOAD CURRENT HTML
# ============================================================

def download_current_html(url, output_path, log):
    """Download and save the current HTML page."""

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "html" not in content_type:
            log.append({
                "Status": "FAILED CURRENT",
                "URL": url,
                "Details": f"Response was not HTML: {content_type}"
            })
            return False

        output_path.parent.mkdir(
            parents=True, exist_ok=True
        )

        output_path.write_bytes(response.content)

        log.append({
            "Status": "SUCCESS CURRENT",
            "URL": url,
            "Details": f"HTTP {response.status_code}; {output_path}"
        })

        print(f"      Saved current HTML: {output_path}")
        return True

    except requests.RequestException as error:
        log.append({
            "Status": "FAILED CURRENT",
            "URL": url,
            "Details": str(error)
        })

        print(f"      Failed current page: {url}")
        return False


# ============================================================
# 5. DISCOVER THE ABOUT US PAGE
# ============================================================

def find_about_page(homepage_url, log):
    """Find a likely About Us page on the same website."""

    keywords = [
        "about us",
        "about",
        "who we are",
        "our story",
        "about-us",
        "about_us"
    ]

    try:
        response = session.get(
            homepage_url, timeout=30
        )
        response.raise_for_status()

        soup = BeautifulSoup(
            response.content, "html.parser"
        )

        homepage_host = urlparse(
            response.url
        ).netloc.lower()

        candidates = []

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()

            text = link.get_text(
                " ", strip=True
            ).lower()

            combined = f"{text} {href.lower()}"

            if any(word in combined for word in keywords):
                candidate = urljoin(response.url, href)

                if (
                    urlparse(candidate).netloc.lower()
                    == homepage_host
                ):
                    candidates.append(candidate)

        candidates = list(dict.fromkeys(candidates))

        if candidates:
            log.append({
                "Status": "ABOUT DISCOVERED",
                "URL": candidates[0],
                "Details": "Discovered automatically; verify if necessary"
            })

            print(f"      About page: {candidates[0]}")
            return candidates[0]

        log.append({
            "Status": "ABOUT NOT FOUND",
            "URL": homepage_url,
            "Details": "No matching internal link found"
        })

        return None

    except requests.RequestException as error:
        log.append({
            "Status": "ABOUT DISCOVERY FAILED",
            "URL": homepage_url,
            "Details": str(error)
        })

        return None


# ============================================================
# 6. FIND EARLIEST ARCHIVED CAPTURE FOR EACH MONTH
# ============================================================

def get_earliest_monthly_captures(url, log):
    """
    Find the earliest successful HTML capture in each month.
    """

    monthly_captures = {}

    try:
        with WaybackClient() as client:

            captures = client.search(
                url,
                from_date=START_DATE,
                to_date=END_DATE,
                match_type="exact",
                filter_field=[
                    "statuscode:200",
                    "mimetype:text/html"
                ],
                limit=1000
            )

            for record in captures:
                timestamp = record.timestamp

                if not (START_DATE <= timestamp <= END_DATE):
                    continue

                if record.statuscode != 200:
                    continue

                if record.mimetype != "text/html":
                    continue

                month_key = timestamp.strftime("%Y-%m")

                if (
                    month_key not in monthly_captures
                    or timestamp
                    < monthly_captures[month_key].timestamp
                ):
                    monthly_captures[month_key] = record

        log.append({
            "Status": "ARCHIVE SEARCH COMPLETED",
            "URL": url,
            "Details": (
                f"Captures found for {len(monthly_captures)} months"
            )
        })

    except Exception as error:
        log.append({
            "Status": "ARCHIVE SEARCH FAILED",
            "URL": url,
            "Details": str(error)
        })

        print(f"      Archive search failed: {error}")

    return monthly_captures


# ============================================================
# 7. DOWNLOAD ARCHIVED HTML
# ============================================================

def download_archived_html(client, record, output_path, log):
    """Download and save an archived HTML response."""

    try:
        response = client.get_memento(
            record,
            mode=Mode.original
        )

        content = response.content

        if not content:
            log.append({
                "Status": "FAILED ARCHIVE",
                "URL": record.original,
                "Details": f"{record.timestamp}; empty response"
            })
            return False

        output_path.parent.mkdir(
            parents=True, exist_ok=True
        )

        output_path.write_bytes(content)

        log.append({
            "Status": "SUCCESS ARCHIVE",
            "URL": record.original,
            "Details": (
                f"Capture: {record.timestamp.isoformat()}; "
                f"Archived URL: {record.raw_url}; "
                f"File: {output_path}"
            )
        })

        print(
            f"      Saved archive {record.timestamp:%Y-%m}: "
            f"{output_path}"
        )

        return True

    except Exception as error:
        log.append({
            "Status": "FAILED ARCHIVE",
            "URL": record.original,
            "Details": f"{record.timestamp}; {error}"
        })

        print(
            f"      Failed archive for {record.timestamp:%Y-%m}"
        )

        return False


# ============================================================
# 8. SCRAPE ONE PAGE
# ============================================================

def scrape_page(
    page_label,
    url,
    current_dir,
    archive_dir,
    log
):
    """Download the current page and its monthly archived versions."""

    safe_label = page_label.lower().replace(" ", "_")

    print(f"\n    Processing {page_label}: {url}")

    # Download current HTML.
    current_path = current_dir / f"{safe_label}.html"

    download_current_html(
        url, current_path, log
    )

    # Search archived captures.
    captures = get_earliest_monthly_captures(
        url, log
    )

    print(
        f"    Monthly captures available: {len(captures)}"
    )

    # Download each available monthly capture.
    with WaybackClient() as client:

        for month_key in EXPECTED_MONTHS:

            if month_key not in captures:
                log.append({
                    "Status": "MISSING ARCHIVE",
                    "URL": url,
                    "Details": (
                        f"{month_key}: no matching HTML capture"
                    )
                })
                continue

            record = captures[month_key]

            year_str, month_str = month_key.split("-")
            month_name = calendar.month_name[int(month_str)]

            output_path = (
                archive_dir
                / safe_label
                / year_str
                / f"{month_str}_{month_name}.html"
            )

            download_archived_html(
                client,
                record,
                output_path,
                log
            )

            time.sleep(REQUEST_DELAY)


# ============================================================
# 9. SCRAPE ONE INCUBATOR
# ============================================================

def scrape_incubator(
    incubator_name,
    website_url,
    folder_number
):
    """Run the scraping process for one incubator."""

    folder_name = (
        f"incubator_{folder_number:02d}_"
        f"{safe_folder_name(incubator_name)}"
    )

    incubator_dir = OUTPUT_ROOT / folder_name

    current_dir = incubator_dir / "current"
    archive_dir = incubator_dir / "archived"

    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    log = []

    print("\n" + "=" * 75)
    print(f"Incubator {folder_number}: {incubator_name}")
    print(f"Website: {website_url}")
    print("=" * 75)

    # Scrape the homepage.
    scrape_page(
        "Homepage",
        website_url,
        current_dir,
        archive_dir,
        log
    )

    # Discover the About Us page.
    about_url = find_about_page(
        website_url,
        log
    )

    # Scrape About Us if discovered.
    if about_url:
        scrape_page(
            "About_Us",
            about_url,
            current_dir,
            archive_dir,
            log
        )
    else:
        log.append({
            "Status": "ABOUT PAGE NOT SCRAPED",
            "URL": website_url,
            "Details": (
                "No About Us URL discovered; verify manually if needed"
            )
        })

    # Count results for the master report.
    result = {
        "Incubator_Name": incubator_name,
        "Website": website_url,
        "About_Us_URL": about_url or "",
        "Output_Folder": str(incubator_dir),
        "Successful_Current_Pages": sum(
            item["Status"] == "SUCCESS CURRENT"
            for item in log
        ),
        "Successful_Archive_Pages": sum(
            item["Status"] == "SUCCESS ARCHIVE"
            for item in log
        ),
        "Missing_Archives": sum(
            item["Status"] == "MISSING ARCHIVE"
            for item in log
        ),
        "Failed_Operations": sum(
            "FAILED" in item["Status"]
            for item in log
        ),
        "About_Page_Found": bool(about_url)
    }

    return result, log


# ============================================================
# 10. READ THE TOP 20 INCUBATORS
# ============================================================

df = pd.read_csv(INPUT_CSV)

# Clean column names.
df.columns = df.columns.str.strip()

required_columns = [NAME_COL, URL_COL]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}\n"
        f"Available columns: {df.columns.tolist()}"
    )

# Retain required fields.
df = df[[NAME_COL, URL_COL]].copy()

# Remove rows without names.
df = df.dropna(subset=[NAME_COL])

df[NAME_COL] = df[NAME_COL].astype(str).str.strip()

# Remove duplicate names.
df = df.drop_duplicates(
    subset=[NAME_COL],
    keep="first"
)

# Clean website URLs.
df[URL_COL] = df[URL_COL].apply(normalize_url)

# Take the top 20 rows from the input file.
df = df.head(20).reset_index(drop=True)

print("Incubators selected:", len(df))
print(
    "Valid website URLs:",
    int(df[URL_COL].notna().sum())
)
print(
    "Missing or invalid website URLs:",
    int(df[URL_COL].isna().sum())
)


# ============================================================
# 11. AUTOMATE SCRAPING FOR ALL INCUBATORS
# ============================================================

master_report = []
detailed_report = []

for index, row in df.iterrows():

    incubator_name = row[NAME_COL]
    website_url = row[URL_COL]
    folder_number = index + 1

    # Skip records without a valid URL.
    if pd.isna(website_url) or not website_url:
        print(
            f"\nSkipping {incubator_name}: "
            "website URL missing or invalid."
        )

        master_report.append({
            "Incubator_Name": incubator_name,
            "Website": "",
            "About_Us_URL": "",
            "Output_Folder": "",
            "Successful_Current_Pages": 0,
            "Successful_Archive_Pages": 0,
            "Missing_Archives": 0,
            "Failed_Operations": 1,
            "About_Page_Found": False,
            "Overall_Status": "SKIPPED: INVALID WEBSITE"
        })

        continue

    try:
        result, log = scrape_incubator(
            incubator_name,
            website_url,
            folder_number
        )

        # Classify the overall outcome.
        if result["Failed_Operations"] > 0:
            result["Overall_Status"] = "COMPLETED WITH FAILURES"
        else:
            result["Overall_Status"] = "COMPLETED"

        master_report.append(result)

        # Preserve detailed outcomes in memory for a single CSV.
        for item in log:
            detailed_report.append({
                "Incubator_Name": incubator_name,
                "Website": website_url,
                "Status": item["Status"],
                "URL": item["URL"],
                "Details": item["Details"]
            })

    except Exception as error:
        # Continue with the remaining incubators if one fails.
        print(
            f"\nUnexpected error for {incubator_name}: {error}"
        )

        master_report.append({
            "Incubator_Name": incubator_name,
            "Website": website_url,
            "About_Us_URL": "",
            "Output_Folder": "",
            "Successful_Current_Pages": 0,
            "Successful_Archive_Pages": 0,
            "Missing_Archives": 0,
            "Failed_Operations": 1,
            "About_Page_Found": False,
            "Overall_Status": f"FAILED: {error}"
        })


# ============================================================
# 12. SAVE SCRAPING REPORTS
# ============================================================

# Summary report: one row per incubator.
master_df = pd.DataFrame(master_report)

master_path = OUTPUT_ROOT / "master_scraping_report.csv"

master_df.to_csv(
    master_path,
    index=False,
    encoding="utf-8-sig"
)

# Detailed report: individual page and archive outcomes.
details_df = pd.DataFrame(detailed_report)

details_path = OUTPUT_ROOT / "detailed_scraping_report.csv"

details_df.to_csv(
    details_path,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 13. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("SCRAPING PROCESS FINISHED")
print("=" * 75)

print("Incubators selected:", len(df))
print("Incubators processed:", len(master_report))

print("\nOutput directory:")
print(OUTPUT_ROOT.resolve())

print("\nMaster report:")
print(master_path.resolve())

print("\nDetailed report:")
print(details_path.resolve())

print("\nSummary of results:")

if not master_df.empty:
    columns_to_show = [
        "Incubator_Name",
        "Successful_Current_Pages",
        "Successful_Archive_Pages",
        "Missing_Archives",
        "Failed_Operations",
        "Overall_Status"
    ]

    print(
        master_df[columns_to_show].to_string(index=False)
    )



# In[ ]:




