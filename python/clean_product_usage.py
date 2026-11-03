from pathlib import Path
from datetime import datetime, date
import csv


# =========================================================
# PROJECT SETTINGS
# =========================================================

ANALYSIS_START_MONTH = date(2025, 1, 1)
ANALYSIS_END_MONTH = date(2026, 12, 1)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_USAGE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "product_usage_raw.csv"
)

ACCOUNTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "accounts.csv"
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
    / "product_usage.csv"
)

QUALITY_REPORT_FILE = (
    PROCESSED_DATA_DIR
    / "product_usage_quality_report.txt"
)


# =========================================================
# EXPECTED SCHEMA
# =========================================================

EXPECTED_COLUMNS = [
    "usage_id",
    "account_id",
    "usage_month",
    "licensed_users",
    "active_users",
    "login_count",
    "dashboards_viewed",
    "reports_generated",
    "alerts_created",
    "core_features_used",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def parse_date(value):
    """
    Convert YYYY-MM-DD text into a Python date.
    """

    return datetime.strptime(
        value.strip(),
        "%Y-%m-%d",
    ).date()


def month_start(value):
    """
    Convert any date to the first day of its month.
    """

    return date(
        value.year,
        value.month,
        1,
    )


def safe_integer(
    value,
    field_name,
    usage_id,
):
    """
    Convert a value to an integer.
    Raise a clear error if conversion fails.
    """

    try:

        return int(
            value.strip()
        )

    except ValueError:

        raise ValueError(
            f"Usage {usage_id}: "
            f"invalid integer in {field_name}: "
            f"{value}"
        )


# =========================================================
# READ CLEAN ACCOUNT DATA
# =========================================================

with ACCOUNTS_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    accounts = list(
        reader
    )


valid_account_ids = {
    row["account_id"].strip()
    for row in accounts
}


account_lookup = {
    row["account_id"].strip(): row
    for row in accounts
}


# =========================================================
# READ RAW PRODUCT USAGE
# =========================================================

with RAW_USAGE_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    if reader.fieldnames != EXPECTED_COLUMNS:

        raise ValueError(
            "Raw product usage columns do not "
            "match the expected schema."
        )

    raw_rows = list(
        reader
    )


raw_row_count = len(
    raw_rows
)


# =========================================================
# RAW DATA QUALITY COUNTS
# =========================================================

raw_invalid_active_users = 0
raw_invalid_features = 0
raw_negative_logins = 0


for row in raw_rows:

    licensed_users = int(
        row["licensed_users"]
    )

    active_users = int(
        row["active_users"]
    )

    core_features_used = int(
        row["core_features_used"]
    )

    login_count = int(
        row["login_count"]
    )


    if active_users > licensed_users:

        raw_invalid_active_users += 1


    if core_features_used > 8:

        raw_invalid_features += 1


    if login_count < 0:

        raw_negative_logins += 1


# =========================================================
# REMOVE EXACT DUPLICATES
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
# CLEAN INVALID VALUES
# =========================================================

cleaned_rows = []

corrected_active_users = 0
corrected_feature_counts = 0
corrected_negative_logins = 0


for row in deduplicated_rows:

    usage_id = row[
        "usage_id"
    ].strip()


    licensed_users = safe_integer(
        row["licensed_users"],
        "licensed_users",
        usage_id,
    )


    active_users = safe_integer(
        row["active_users"],
        "active_users",
        usage_id,
    )


    login_count = safe_integer(
        row["login_count"],
        "login_count",
        usage_id,
    )


    dashboards_viewed = safe_integer(
        row["dashboards_viewed"],
        "dashboards_viewed",
        usage_id,
    )


    reports_generated = safe_integer(
        row["reports_generated"],
        "reports_generated",
        usage_id,
    )


    alerts_created = safe_integer(
        row["alerts_created"],
        "alerts_created",
        usage_id,
    )


    core_features_used = safe_integer(
        row["core_features_used"],
        "core_features_used",
        usage_id,
    )


    # -----------------------------------------------------
    # ACTIVE USERS CANNOT EXCEED LICENSED USERS
    # -----------------------------------------------------

    if active_users > licensed_users:

        active_users = licensed_users

        corrected_active_users += 1


    # -----------------------------------------------------
    # FEATURE COUNT CANNOT EXCEED 8
    # -----------------------------------------------------

    if core_features_used > 8:

        core_features_used = 8

        corrected_feature_counts += 1


    # -----------------------------------------------------
    # LOGIN COUNT CANNOT BE NEGATIVE
    # -----------------------------------------------------

    if login_count < 0:

        login_count = 0

        corrected_negative_logins += 1


    cleaned_row = {
        "usage_id":
            usage_id,

        "account_id":
            row["account_id"].strip(),

        "usage_month":
            row["usage_month"].strip(),

        "licensed_users":
            str(licensed_users),

        "active_users":
            str(active_users),

        "login_count":
            str(login_count),

        "dashboards_viewed":
            str(dashboards_viewed),

        "reports_generated":
            str(reports_generated),

        "alerts_created":
            str(alerts_created),

        "core_features_used":
            str(core_features_used),
    }


    cleaned_rows.append(
        cleaned_row
    )


# =========================================================
# VALIDATION
# =========================================================

validation_errors = []

usage_ids = set()

account_month_pairs = set()


for row in cleaned_rows:

    usage_id = row[
        "usage_id"
    ]

    account_id = row[
        "account_id"
    ]


    # -----------------------------------------------------
    # UNIQUE USAGE ID
    # -----------------------------------------------------

    if usage_id in usage_ids:

        validation_errors.append(
            f"Duplicate usage_id: "
            f"{usage_id}"
        )


    usage_ids.add(
        usage_id
    )


    # -----------------------------------------------------
    # ACCOUNT FOREIGN KEY
    # -----------------------------------------------------

    if account_id not in valid_account_ids:

        validation_errors.append(
            f"Usage {usage_id}: "
            f"account_id {account_id} "
            "does not exist"
        )

        continue


    # -----------------------------------------------------
    # USAGE MONTH
    # -----------------------------------------------------

    usage_month = parse_date(
        row["usage_month"]
    )


    if usage_month.day != 1:

        validation_errors.append(
            f"Usage {usage_id}: "
            "usage_month is not the first "
            "day of the month"
        )


    if (
        usage_month < ANALYSIS_START_MONTH
        or usage_month > ANALYSIS_END_MONTH
    ):

        validation_errors.append(
            f"Usage {usage_id}: "
            "usage month falls outside "
            "the analysis period"
        )


    # -----------------------------------------------------
    # ONE RECORD PER ACCOUNT PER MONTH
    # -----------------------------------------------------

    account_month_key = (
        account_id,
        row["usage_month"],
    )


    if account_month_key in account_month_pairs:

        validation_errors.append(
            f"Account {account_id}: "
            f"duplicate usage month "
            f"{row['usage_month']}"
        )


    account_month_pairs.add(
        account_month_key
    )


    # -----------------------------------------------------
    # ACCOUNT DATE RANGE
    # -----------------------------------------------------

    account = account_lookup[
        account_id
    ]


    signup_date = parse_date(
        account[
            "signup_date"
        ]
    )


    earliest_usage_month = max(
        month_start(
            signup_date
        ),
        ANALYSIS_START_MONTH,
    )


    if usage_month < earliest_usage_month:

        validation_errors.append(
            f"Usage {usage_id}: "
            "usage occurs before "
            "customer signup"
        )


    churn_value = account[
        "churn_date"
    ].strip()


    if churn_value != "":

        churn_date = parse_date(
            churn_value
        )


        latest_usage_month = min(
            month_start(
                churn_date
            ),
            ANALYSIS_END_MONTH,
        )


        if usage_month > latest_usage_month:

            validation_errors.append(
                f"Usage {usage_id}: "
                "usage occurs after churn"
            )


    # -----------------------------------------------------
    # NUMERIC BUSINESS RULES
    # -----------------------------------------------------

    licensed_users = int(
        row["licensed_users"]
    )

    active_users = int(
        row["active_users"]
    )

    login_count = int(
        row["login_count"]
    )

    dashboards_viewed = int(
        row["dashboards_viewed"]
    )

    reports_generated = int(
        row["reports_generated"]
    )

    alerts_created = int(
        row["alerts_created"]
    )

    core_features_used = int(
        row["core_features_used"]
    )


    if licensed_users < 0:

        validation_errors.append(
            f"Usage {usage_id}: "
            "licensed_users is negative"
        )


    if active_users < 0:

        validation_errors.append(
            f"Usage {usage_id}: "
            "active_users is negative"
        )


    if active_users > licensed_users:

        validation_errors.append(
            f"Usage {usage_id}: "
            "active_users exceeds "
            "licensed_users"
        )


    if login_count < 0:

        validation_errors.append(
            f"Usage {usage_id}: "
            "login_count is negative"
        )


    if dashboards_viewed < 0:

        validation_errors.append(
            f"Usage {usage_id}: "
            "dashboards_viewed is negative"
        )


    if reports_generated < 0:

        validation_errors.append(
            f"Usage {usage_id}: "
            "reports_generated is negative"
        )


    if alerts_created < 0:

        validation_errors.append(
            f"Usage {usage_id}: "
            "alerts_created is negative"
        )


    if (
        core_features_used < 0
        or core_features_used > 8
    ):

        validation_errors.append(
            f"Usage {usage_id}: "
            "core_features_used must "
            "be between 0 and 8"
        )


# =========================================================
# CHECK ACCOUNT COVERAGE
# =========================================================

accounts_with_usage = {
    row["account_id"]
    for row in cleaned_rows
}


missing_accounts = (
    valid_account_ids
    - accounts_with_usage
)


if missing_accounts:

    validation_errors.append(
        f"{len(missing_accounts)} "
        "account(s) have no usage records"
    )


# =========================================================
# STOP IF VALIDATION FAILS
# =========================================================

if validation_errors:

    print()

    print(
        "PRODUCT USAGE VALIDATION ERRORS"
    )

    print(
        "=" * 65
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
    key=lambda row:
    int(
        row[
            "usage_id"
        ]
    )
)


# =========================================================
# WRITE CLEAN DATA
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
# FINAL QUALITY CHECKS
# =========================================================

clean_invalid_active_users = sum(
    1
    for row in cleaned_rows
    if int(
        row["active_users"]
    )
    > int(
        row["licensed_users"]
    )
)


clean_invalid_features = sum(
    1
    for row in cleaned_rows
    if int(
        row[
            "core_features_used"
        ]
    ) > 8
)


clean_negative_logins = sum(
    1
    for row in cleaned_rows
    if int(
        row["login_count"]
    ) < 0
)


# =========================================================
# QUALITY REPORT
# =========================================================

report_lines = [
    "CLOUDPATH ANALYTICS - PRODUCT USAGE DATA QUALITY REPORT",
    "=" * 65,
    "",
    "RAW DATA",
    f"Raw rows: {raw_row_count}",
    f"Exact duplicate rows: {exact_duplicate_count}",
    (
        "Rows with active_users > licensed_users: "
        f"{raw_invalid_active_users}"
    ),
    (
        "Rows with core_features_used > 8: "
        f"{raw_invalid_features}"
    ),
    (
        "Rows with negative login_count: "
        f"{raw_negative_logins}"
    ),
    "",
    "CLEANED DATA",
    f"Clean rows: {len(cleaned_rows)}",
    f"Unique usage IDs: {len(usage_ids)}",
    (
        "Unique account-month combinations: "
        f"{len(account_month_pairs)}"
    ),
    (
        "Accounts with usage records: "
        f"{len(accounts_with_usage)}"
    ),
    (
        "Invalid active-user rows remaining: "
        f"{clean_invalid_active_users}"
    ),
    (
        "Invalid feature-count rows remaining: "
        f"{clean_invalid_features}"
    ),
    (
        "Negative login rows remaining: "
        f"{clean_negative_logins}"
    ),
    (
        "Business rule violations: "
        f"{len(validation_errors)}"
    ),
    "",
    "CLEANING ACTIONS",
    "- Removed exact duplicate records",
    (
        "- Capped active_users at licensed_users "
        "when raw values exceeded the licensed limit"
    ),
    (
        "- Capped core_features_used at 8 "
        "when raw values exceeded the valid maximum"
    ),
    (
        "- Replaced negative login_count values with 0"
    ),
    "- Validated account foreign keys",
    "- Validated account-month uniqueness",
    "- Validated usage dates against signup and churn dates",
    "- Validated non-negative activity metrics",
    (
        "- Retained valid temporary usage spikes "
        "because they represent legitimate behavioral variation"
    ),
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
    "=" * 65
)

print(
    "CLOUDPATH ANALYTICS - PRODUCT USAGE DATA CLEANING"
)

print(
    "=" * 65
)

print(
    f"Raw rows: "
    f"{raw_row_count}"
)

print(
    f"Exact duplicates removed: "
    f"{exact_duplicate_count}"
)

print(
    f"Clean rows: "
    f"{len(cleaned_rows)}"
)

print(
    f"Unique usage IDs: "
    f"{len(usage_ids)}"
)

print(
    f"Unique account-month combinations: "
    f"{len(account_month_pairs)}"
)

print(
    f"Accounts with usage records: "
    f"{len(accounts_with_usage)}"
)

print()

print(
    f"Active-user values corrected: "
    f"{corrected_active_users}"
)

print(
    f"Feature-count values corrected: "
    f"{corrected_feature_counts}"
)

print(
    f"Negative login values corrected: "
    f"{corrected_negative_logins}"
)

print()

print(
    f"Invalid active-user rows remaining: "
    f"{clean_invalid_active_users}"
)

print(
    f"Invalid feature rows remaining: "
    f"{clean_invalid_features}"
)

print(
    f"Negative login rows remaining: "
    f"{clean_negative_logins}"
)

print(
    f"Business rule violations: "
    f"{len(validation_errors)}"
)

print()

print(
    "Processed product usage file:"
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
    "=" * 65
)
