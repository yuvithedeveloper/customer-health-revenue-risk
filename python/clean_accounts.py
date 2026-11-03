from pathlib import Path
from datetime import datetime
import csv


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "accounts_raw.csv"
)

PROCESSED_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

PROCESSED_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE = (
    PROCESSED_DATA_DIR
    / "accounts.csv"
)

QUALITY_REPORT_FILE = (
    PROCESSED_DATA_DIR
    / "accounts_quality_report.txt"
)


# =========================================================
# EXPECTED SCHEMA
# =========================================================

EXPECTED_COLUMNS = [
    "account_id",
    "account_name",
    "industry",
    "segment",
    "region",
    "signup_date",
    "customer_status",
    "churn_date",
    "assigned_csm",
]


VALID_SEGMENTS = {
    "SMB",
    "Mid-Market",
    "Enterprise",
}


VALID_REGIONS = {
    "Northeast",
    "South",
    "Midwest",
    "West",
    "Canada",
}


VALID_STATUSES = {
    "Active",
    "Churned",
}


# =========================================================
# NORMALIZATION FUNCTIONS
# =========================================================

def normalize_segment(value):
    """
    Standardize known segment variations.
    """

    cleaned_value = value.strip()

    mapping = {
        "smb": "SMB",
        "mid market": "Mid-Market",
        "mid-market": "Mid-Market",
        "enterprise": "Enterprise",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_region(value):
    """
    Standardize known region variations.
    """

    cleaned_value = value.strip()

    mapping = {
        "northeast": "Northeast",
        "north east": "Northeast",
        "south": "South",
        "midwest": "Midwest",
        "mid-west": "Midwest",
        "west": "West",
        "canada": "Canada",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_status(value):
    """
    Standardize known customer status variations.
    """

    cleaned_value = value.strip()

    mapping = {
        "active": "Active",
        "churned": "Churned",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


# =========================================================
# DATE VALIDATION
# =========================================================

def parse_date(value):
    """
    Convert YYYY-MM-DD text into a date object.

    Blank values return None.
    """

    cleaned_value = value.strip()

    if cleaned_value == "":
        return None

    return datetime.strptime(
        cleaned_value,
        "%Y-%m-%d",
    ).date()


# =========================================================
# READ RAW DATA
# =========================================================

with RAW_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    if reader.fieldnames != EXPECTED_COLUMNS:

        raise ValueError(
            "Raw accounts file columns do not "
            "match the expected schema."
        )

    raw_rows = list(
        reader
    )


# =========================================================
# RAW DATA QUALITY CHECKS
# =========================================================

raw_row_count = len(
    raw_rows
)


raw_missing_industry = sum(
    1
    for row in raw_rows
    if row["industry"].strip() == ""
)


raw_missing_csm = sum(
    1
    for row in raw_rows
    if row["assigned_csm"].strip() == ""
)


raw_invalid_segments = sum(
    1
    for row in raw_rows
    if row["segment"] not in VALID_SEGMENTS
)


raw_invalid_regions = sum(
    1
    for row in raw_rows
    if row["region"] not in VALID_REGIONS
)


raw_invalid_statuses = sum(
    1
    for row in raw_rows
    if row["customer_status"] not in VALID_STATUSES
)


# =========================================================
# IDENTIFY EXACT DUPLICATES
# =========================================================

seen_signatures = set()

deduplicated_rows = []

exact_duplicate_count = 0


for row in raw_rows:

    signature = tuple(
        row[column]
        for column in EXPECTED_COLUMNS
    )

    if signature in seen_signatures:

        exact_duplicate_count += 1

        continue

    seen_signatures.add(
        signature
    )

    deduplicated_rows.append(
        dict(row)
    )


# =========================================================
# NORMALIZE VALUES
# =========================================================

cleaned_rows = []


for row in deduplicated_rows:

    cleaned_row = {
        "account_id": (
            row["account_id"].strip()
        ),
        "account_name": (
            row["account_name"].strip()
        ),
        "industry": (
            row["industry"].strip()
        ),
        "segment": normalize_segment(
            row["segment"]
        ),
        "region": normalize_region(
            row["region"]
        ),
        "signup_date": (
            row["signup_date"].strip()
        ),
        "customer_status": (
            normalize_status(
                row["customer_status"]
            )
        ),
        "churn_date": (
            row["churn_date"].strip()
        ),
        "assigned_csm": (
            row["assigned_csm"].strip()
        ),
    }

    cleaned_rows.append(
        cleaned_row
    )


# =========================================================
# CHECK DUPLICATE ACCOUNT IDS
# =========================================================

account_ids = set()

duplicate_account_ids = []


for row in cleaned_rows:

    account_id = row[
        "account_id"
    ]

    if account_id in account_ids:

        duplicate_account_ids.append(
            account_id
        )

    else:

        account_ids.add(
            account_id
        )


# =========================================================
# BUSINESS RULE VALIDATION
# =========================================================

validation_errors = []


for row in cleaned_rows:

    account_id = row[
        "account_id"
    ]


    # -----------------------------------------------------
    # Required values
    # -----------------------------------------------------

    if account_id == "":

        validation_errors.append(
            "Missing account_id"
        )


    if row["account_name"] == "":

        validation_errors.append(
            f"Account {account_id}: "
            "missing account_name"
        )


    if row["signup_date"] == "":

        validation_errors.append(
            f"Account {account_id}: "
            "missing signup_date"
        )


    # -----------------------------------------------------
    # Category validation
    # -----------------------------------------------------

    if (
        row["segment"]
        not in VALID_SEGMENTS
    ):

        validation_errors.append(
            f"Account {account_id}: "
            f"invalid segment "
            f"{row['segment']}"
        )


    if (
        row["region"]
        not in VALID_REGIONS
    ):

        validation_errors.append(
            f"Account {account_id}: "
            f"invalid region "
            f"{row['region']}"
        )


    if (
        row["customer_status"]
        not in VALID_STATUSES
    ):

        validation_errors.append(
            f"Account {account_id}: "
            f"invalid customer_status "
            f"{row['customer_status']}"
        )


    # -----------------------------------------------------
    # Date validation
    # -----------------------------------------------------

    signup_date = parse_date(
        row["signup_date"]
    )

    churn_date = parse_date(
        row["churn_date"]
    )


    if (
        signup_date
        and churn_date
        and churn_date < signup_date
    ):

        validation_errors.append(
            f"Account {account_id}: "
            "churn_date occurs before "
            "signup_date"
        )


    # -----------------------------------------------------
    # Customer status / churn relationship
    # -----------------------------------------------------

    if (
        row["customer_status"]
        == "Active"
        and churn_date is not None
    ):

        validation_errors.append(
            f"Account {account_id}: "
            "Active account has a churn_date"
        )


    if (
        row["customer_status"]
        == "Churned"
        and churn_date is None
    ):

        validation_errors.append(
            f"Account {account_id}: "
            "Churned account has no churn_date"
        )


# =========================================================
# STOP IF SERIOUS DATA ERRORS EXIST
# =========================================================

if duplicate_account_ids:

    raise ValueError(
        "Duplicate account IDs remain after "
        "exact duplicate removal: "
        + ", ".join(
            duplicate_account_ids
        )
    )


if validation_errors:

    print()

    print(
        "DATA VALIDATION ERRORS FOUND"
    )

    print(
        "=" * 60
    )

    for error in validation_errors:

        print(
            error
        )

    raise ValueError(
        f"{len(validation_errors)} "
        "validation error(s) found."
    )


# =========================================================
# SORT CLEAN DATA
# =========================================================

cleaned_rows.sort(
    key=lambda row: int(
        row["account_id"]
    )
)


# =========================================================
# WRITE PROCESSED CSV
# =========================================================

with OUTPUT_FILE.open(
    mode="w",
    encoding="utf-8",
    newline="",
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=EXPECTED_COLUMNS,
    )

    writer.writeheader()

    writer.writerows(
        cleaned_rows
    )


# =========================================================
# FINAL DATA QUALITY CHECKS
# =========================================================

clean_row_count = len(
    cleaned_rows
)


clean_missing_industry = sum(
    1
    for row in cleaned_rows
    if row["industry"] == ""
)


clean_missing_csm = sum(
    1
    for row in cleaned_rows
    if row["assigned_csm"] == ""
)


clean_invalid_segments = sum(
    1
    for row in cleaned_rows
    if row["segment"]
    not in VALID_SEGMENTS
)


clean_invalid_regions = sum(
    1
    for row in cleaned_rows
    if row["region"]
    not in VALID_REGIONS
)


clean_invalid_statuses = sum(
    1
    for row in cleaned_rows
    if row["customer_status"]
    not in VALID_STATUSES
)


# =========================================================
# CREATE QUALITY REPORT
# =========================================================

report_lines = [
    "CLOUDPATH ANALYTICS - ACCOUNTS DATA QUALITY REPORT",
    "=" * 60,
    "",
    "RAW DATA",
    f"Raw rows: {raw_row_count}",
    f"Exact duplicate rows: {exact_duplicate_count}",
    f"Missing industry values: {raw_missing_industry}",
    f"Missing CSM assignments: {raw_missing_csm}",
    f"Inconsistent segment values: {raw_invalid_segments}",
    f"Inconsistent region values: {raw_invalid_regions}",
    f"Inconsistent status values: {raw_invalid_statuses}",
    "",
    "CLEANED DATA",
    f"Clean rows: {clean_row_count}",
    f"Unique account IDs: {len(account_ids)}",
    f"Missing industry values retained: {clean_missing_industry}",
    f"Missing CSM assignments retained: {clean_missing_csm}",
    f"Invalid segment values: {clean_invalid_segments}",
    f"Invalid region values: {clean_invalid_regions}",
    f"Invalid status values: {clean_invalid_statuses}",
    f"Business rule violations: {len(validation_errors)}",
    "",
    "CLEANING ACTIONS",
    "- Removed exact duplicate records",
    "- Standardized segment labels",
    "- Standardized region labels",
    "- Standardized customer status labels",
    "- Trimmed unnecessary whitespace",
    "- Retained missing industry values for later analysis",
    "- Retained missing CSM assignments for later analysis",
    "- Validated signup and churn dates",
    "- Validated customer status and churn-date consistency",
]


QUALITY_REPORT_FILE.write_text(
    "\n".join(
        report_lines
    ),
    encoding="utf-8",
)


# =========================================================
# PRINT SUMMARY
# =========================================================

print()

print(
    "=" * 60
)

print(
    "CLOUDPATH ANALYTICS - ACCOUNT DATA CLEANING"
)

print(
    "=" * 60
)

print(
    f"Raw rows: {raw_row_count}"
)

print(
    f"Exact duplicates removed: "
    f"{exact_duplicate_count}"
)

print(
    f"Clean rows: {clean_row_count}"
)

print(
    f"Unique account IDs: "
    f"{len(account_ids)}"
)

print(
    f"Missing industries retained: "
    f"{clean_missing_industry}"
)

print(
    f"Missing CSM assignments retained: "
    f"{clean_missing_csm}"
)

print(
    f"Invalid segment values after cleaning: "
    f"{clean_invalid_segments}"
)

print(
    f"Invalid region values after cleaning: "
    f"{clean_invalid_regions}"
)

print(
    f"Invalid status values after cleaning: "
    f"{clean_invalid_statuses}"
)

print(
    f"Business rule violations: "
    f"{len(validation_errors)}"
)

print()

print(
    "Processed accounts file:"
)

print(
    OUTPUT_FILE
)

print()

print(
    "Data quality report:"
)

print(
    QUALITY_REPORT_FILE
)

print(
    "=" * 60
)
