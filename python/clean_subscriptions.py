from pathlib import Path
from datetime import datetime
import csv


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_SUBSCRIPTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "subscriptions_raw.csv"
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
    / "subscriptions.csv"
)

QUALITY_REPORT_FILE = (
    PROCESSED_DATA_DIR
    / "subscriptions_quality_report.txt"
)


# =========================================================
# EXPECTED SCHEMA
# =========================================================

EXPECTED_COLUMNS = [
    "subscription_id",
    "account_id",
    "plan_name",
    "subscription_start_date",
    "subscription_end_date",
    "billing_frequency",
    "mrr",
    "subscription_status",
    "renewal_date",
]


VALID_PLANS = {
    "Standard",
    "Professional",
    "Enterprise",
}

VALID_BILLING_FREQUENCIES = {
    "Monthly",
    "Annual",
}

VALID_STATUSES = {
    "Active",
    "Renewed",
    "Churned",
    "Expired",
}


# =========================================================
# NORMALIZATION FUNCTIONS
# =========================================================

def normalize_plan(value):
    cleaned_value = value.strip()

    mapping = {
        "standard": "Standard",
        "professional": "Professional",
        "enterprise": "Enterprise",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_billing_frequency(value):
    cleaned_value = value.strip()

    mapping = {
        "monthly": "Monthly",
        "annual": "Annual",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_status(value):
    cleaned_value = value.strip()

    mapping = {
        "active": "Active",
        "renewed": "Renewed",
        "churned": "Churned",
        "expired": "Expired",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


# =========================================================
# DATE PARSING
# =========================================================

def parse_date(value):
    cleaned_value = value.strip()

    if cleaned_value == "":
        return None

    return datetime.strptime(
        cleaned_value,
        "%Y-%m-%d",
    ).date()


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


account_status_lookup = {
    row["account_id"].strip():
    row["customer_status"].strip()
    for row in accounts
}


# =========================================================
# READ RAW SUBSCRIPTION DATA
# =========================================================

with RAW_SUBSCRIPTIONS_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    if reader.fieldnames != EXPECTED_COLUMNS:

        raise ValueError(
            "Raw subscriptions file columns do not "
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


raw_invalid_plans = sum(
    1
    for row in raw_rows
    if row["plan_name"]
    not in VALID_PLANS
)


raw_invalid_billing = sum(
    1
    for row in raw_rows
    if row["billing_frequency"]
    not in VALID_BILLING_FREQUENCIES
)


raw_invalid_status = sum(
    1
    for row in raw_rows
    if row["subscription_status"]
    not in VALID_STATUSES
)


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
# NORMALIZE VALUES
# =========================================================

cleaned_rows = []


for row in deduplicated_rows:

    cleaned_row = {
        "subscription_id":
            row["subscription_id"].strip(),

        "account_id":
            row["account_id"].strip(),

        "plan_name":
            normalize_plan(
                row["plan_name"]
            ),

        "subscription_start_date":
            row[
                "subscription_start_date"
            ].strip(),

        "subscription_end_date":
            row[
                "subscription_end_date"
            ].strip(),

        "billing_frequency":
            normalize_billing_frequency(
                row["billing_frequency"]
            ),

        "mrr":
            row["mrr"].strip(),

        "subscription_status":
            normalize_status(
                row["subscription_status"]
            ),

        "renewal_date":
            row["renewal_date"].strip(),
    }

    cleaned_rows.append(
        cleaned_row
    )


# =========================================================
# VALIDATION
# =========================================================

validation_errors = []

subscription_ids = set()


for row in cleaned_rows:

    subscription_id = row[
        "subscription_id"
    ]

    account_id = row[
        "account_id"
    ]


    # -----------------------------------------------------
    # UNIQUE SUBSCRIPTION ID
    # -----------------------------------------------------

    if subscription_id in subscription_ids:

        validation_errors.append(
            f"Duplicate subscription_id: "
            f"{subscription_id}"
        )

    subscription_ids.add(
        subscription_id
    )


    # -----------------------------------------------------
    # ACCOUNT FOREIGN KEY
    # -----------------------------------------------------

    if account_id not in valid_account_ids:

        validation_errors.append(
            f"Subscription {subscription_id}: "
            f"account_id {account_id} "
            "does not exist in accounts"
        )


    # -----------------------------------------------------
    # VALID CATEGORIES
    # -----------------------------------------------------

    if row["plan_name"] not in VALID_PLANS:

        validation_errors.append(
            f"Subscription {subscription_id}: "
            f"invalid plan "
            f"{row['plan_name']}"
        )


    if (
        row["billing_frequency"]
        not in VALID_BILLING_FREQUENCIES
    ):

        validation_errors.append(
            f"Subscription {subscription_id}: "
            "invalid billing frequency "
            f"{row['billing_frequency']}"
        )


    if (
        row["subscription_status"]
        not in VALID_STATUSES
    ):

        validation_errors.append(
            f"Subscription {subscription_id}: "
            f"invalid status "
            f"{row['subscription_status']}"
        )


    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    start_date = parse_date(
        row["subscription_start_date"]
    )

    end_date = parse_date(
        row["subscription_end_date"]
    )

    renewal_date = parse_date(
        row["renewal_date"]
    )


    if start_date is None:

        validation_errors.append(
            f"Subscription {subscription_id}: "
            "missing start date"
        )


    if end_date is None:

        validation_errors.append(
            f"Subscription {subscription_id}: "
            "missing end date"
        )


    if (
        start_date is not None
        and end_date is not None
        and end_date < start_date
    ):

        validation_errors.append(
            f"Subscription {subscription_id}: "
            "end date occurs before start date"
        )


    if (
        renewal_date is not None
        and end_date is not None
        and renewal_date <= end_date
    ):

        validation_errors.append(
            f"Subscription {subscription_id}: "
            "renewal date must occur after "
            "subscription end date"
        )


    # -----------------------------------------------------
    # MRR VALIDATION
    # -----------------------------------------------------

    try:

        mrr = float(
            row["mrr"]
        )

        if mrr < 0:

            validation_errors.append(
                f"Subscription {subscription_id}: "
                "MRR cannot be negative"
            )

    except ValueError:

        validation_errors.append(
            f"Subscription {subscription_id}: "
            f"invalid MRR {row['mrr']}"
        )


    # -----------------------------------------------------
    # CHURNED SUBSCRIPTIONS SHOULD NOT HAVE RENEWAL DATE
    # -----------------------------------------------------

    if (
        row["subscription_status"]
        == "Churned"
        and renewal_date is not None
    ):

        validation_errors.append(
            f"Subscription {subscription_id}: "
            "churned subscription has "
            "a renewal date"
        )


# =========================================================
# ACCOUNT-LEVEL SUBSCRIPTION VALIDATION
# =========================================================

subscriptions_by_account = {}


for row in cleaned_rows:

    account_id = row[
        "account_id"
    ]

    subscriptions_by_account.setdefault(
        account_id,
        [],
    ).append(
        row
    )


active_subscription_count = 0


for account_id, rows in subscriptions_by_account.items():

    rows.sort(
        key=lambda row:
        parse_date(
            row[
                "subscription_start_date"
            ]
        )
    )


    # -----------------------------------------------------
    # CHECK PERIOD CONTINUITY / OVERLAP
    # -----------------------------------------------------

    for index in range(
        1,
        len(rows),
    ):

        previous_row = rows[
            index - 1
        ]

        current_row = rows[
            index
        ]


        previous_end = parse_date(
            previous_row[
                "subscription_end_date"
            ]
        )

        current_start = parse_date(
            current_row[
                "subscription_start_date"
            ]
        )


        if (
            previous_end is not None
            and current_start is not None
            and current_start <= previous_end
        ):

            validation_errors.append(
                f"Account {account_id}: "
                "subscription periods overlap"
            )


    # -----------------------------------------------------
    # FINAL SUBSCRIPTION STATUS
    # -----------------------------------------------------

    final_subscription = rows[-1]

    final_status = final_subscription[
        "subscription_status"
    ]

    account_status = (
        account_status_lookup[
            account_id
        ]
    )


    if account_status == "Active":

        if final_status != "Active":

            validation_errors.append(
                f"Account {account_id}: "
                "active customer does not have "
                "an Active final subscription"
            )

        else:

            active_subscription_count += 1


    if account_status == "Churned":

        if final_status != "Churned":

            validation_errors.append(
                f"Account {account_id}: "
                "churned customer does not have "
                "a Churned final subscription"
            )


# =========================================================
# STOP IF VALIDATION FAILS
# =========================================================

if validation_errors:

    print()

    print(
        "SUBSCRIPTION VALIDATION ERRORS"
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
            "subscription_id"
        ]
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
# FINAL METRICS
# =========================================================

clean_invalid_plans = sum(
    1
    for row in cleaned_rows
    if row["plan_name"]
    not in VALID_PLANS
)


clean_invalid_billing = sum(
    1
    for row in cleaned_rows
    if row["billing_frequency"]
    not in VALID_BILLING_FREQUENCIES
)


clean_invalid_status = sum(
    1
    for row in cleaned_rows
    if row["subscription_status"]
    not in VALID_STATUSES
)


current_active_rows = [
    row
    for row in cleaned_rows
    if row["subscription_status"]
    == "Active"
]


current_mrr = sum(
    float(
        row["mrr"]
    )
    for row in current_active_rows
)


current_arr = (
    current_mrr * 12
)


# =========================================================
# QUALITY REPORT
# =========================================================

report_lines = [
    "CLOUDPATH ANALYTICS - SUBSCRIPTIONS DATA QUALITY REPORT",
    "=" * 65,
    "",
    "RAW DATA",
    f"Raw rows: {raw_row_count}",
    f"Exact duplicate rows: {exact_duplicate_count}",
    f"Inconsistent plan values: {raw_invalid_plans}",
    f"Inconsistent billing values: {raw_invalid_billing}",
    f"Inconsistent status values: {raw_invalid_status}",
    "",
    "CLEANED DATA",
    f"Clean rows: {len(cleaned_rows)}",
    f"Unique subscription IDs: {len(subscription_ids)}",
    f"Invalid plan values: {clean_invalid_plans}",
    f"Invalid billing values: {clean_invalid_billing}",
    f"Invalid status values: {clean_invalid_status}",
    f"Business rule violations: {len(validation_errors)}",
    "",
    "CURRENT RECURRING REVENUE",
    f"Active subscriptions: {len(current_active_rows)}",
    f"Current MRR: ${current_mrr:,.2f}",
    f"Current ARR: ${current_arr:,.2f}",
    "",
    "CLEANING ACTIONS",
    "- Removed exact duplicate records",
    "- Standardized plan names",
    "- Standardized billing-frequency values",
    "- Standardized subscription-status values",
    "- Validated account foreign keys",
    "- Validated subscription dates",
    "- Validated MRR values",
    "- Checked subscription periods for overlap",
    "- Validated final subscription status against customer status",
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
    "CLOUDPATH ANALYTICS - SUBSCRIPTION DATA CLEANING"
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
    f"Unique subscription IDs: "
    f"{len(subscription_ids)}"
)

print(
    f"Invalid plan values after cleaning: "
    f"{clean_invalid_plans}"
)

print(
    f"Invalid billing values after cleaning: "
    f"{clean_invalid_billing}"
)

print(
    f"Invalid status values after cleaning: "
    f"{clean_invalid_status}"
)

print(
    f"Business rule violations: "
    f"{len(validation_errors)}"
)

print()

print(
    f"Current active subscriptions: "
    f"{len(current_active_rows)}"
)

print(
    f"Current MRR: "
    f"${current_mrr:,.2f}"
)

print(
    f"Current ARR: "
    f"${current_arr:,.2f}"
)

print()

print(
    "Processed subscriptions file:"
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
