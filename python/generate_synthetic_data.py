from pathlib import Path
from datetime import date, timedelta
import csv
import random

from faker import Faker


# =========================================================
# PROJECT SETTINGS
# =========================================================

SEED = 42
NUM_ACCOUNTS = 500
DUPLICATE_ROWS = 6

SIGNUP_START = date(2024, 1, 1)
SIGNUP_END = date(2026, 9, 30)
ANALYSIS_END = date(2026, 12, 31)


# =========================================================
# REPRODUCIBILITY
# =========================================================

random.seed(SEED)

Faker.seed(SEED)
fake = Faker("en_US")


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

RAW_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# REFERENCE VALUES
# =========================================================

SEGMENTS = [
    "SMB",
    "Mid-Market",
    "Enterprise",
]

SEGMENT_WEIGHTS = [
    52,
    33,
    15,
]


INDUSTRIES = [
    "Technology",
    "Financial Services",
    "Healthcare",
    "Retail",
    "Manufacturing",
    "Professional Services",
    "Logistics",
    "Media",
]

INDUSTRY_WEIGHTS = [
    20,
    14,
    13,
    13,
    12,
    12,
    9,
    7,
]


REGIONS = [
    "Northeast",
    "South",
    "Midwest",
    "West",
    "Canada",
]

REGION_WEIGHTS = [
    27,
    23,
    17,
    25,
    8,
]


CUSTOMER_SUCCESS_MANAGERS = [
    "Maya Chen",
    "Daniel Brooks",
    "Priya Shah",
    "Jordan Lee",
    "Sofia Martinez",
    "Ethan Walker",
    "Rachel Kim",
    "Marcus Johnson",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def random_date(start_date, end_date):
    """
    Return a random date between start_date and end_date.
    """

    day_range = (
        end_date - start_date
    ).days

    random_days = random.randint(
        0,
        day_range,
    )

    return (
        start_date
        + timedelta(days=random_days)
    )


def generate_unique_company_names(
    number_of_accounts,
):
    """
    Generate unique fictional company names.
    """

    company_names = []
    seen_names = set()

    while len(company_names) < number_of_accounts:

        company_name = fake.company()

        if company_name not in seen_names:

            seen_names.add(
                company_name
            )

            company_names.append(
                company_name
            )

    return company_names


def determine_churn(
    segment,
    signup_date,
):
    """
    Determine whether an account churned.

    Churn probabilities are synthetic project assumptions,
    not external SaaS industry benchmarks.
    """

    churn_probability = {
        "SMB": 0.18,
        "Mid-Market": 0.12,
        "Enterprise": 0.08,
    }

    minimum_lifetime_days = 90

    earliest_churn_date = max(
        signup_date
        + timedelta(
            days=minimum_lifetime_days
        ),
        date(2025, 1, 1),
    )

    if earliest_churn_date > ANALYSIS_END:

        return "Active", None

    if (
        random.random()
        >= churn_probability[segment]
    ):

        return "Active", None

    churn_date = random_date(
        earliest_churn_date,
        ANALYSIS_END,
    )

    return "Churned", churn_date


# =========================================================
# GENERATE COMPANY NAMES
# =========================================================

company_names = (
    generate_unique_company_names(
        NUM_ACCOUNTS
    )
)


# =========================================================
# GENERATE BASE ACCOUNT RECORDS
# =========================================================

accounts = []

for account_id in range(
    1,
    NUM_ACCOUNTS + 1,
):

    segment = random.choices(
        SEGMENTS,
        weights=SEGMENT_WEIGHTS,
        k=1,
    )[0]

    industry = random.choices(
        INDUSTRIES,
        weights=INDUSTRY_WEIGHTS,
        k=1,
    )[0]

    region = random.choices(
        REGIONS,
        weights=REGION_WEIGHTS,
        k=1,
    )[0]

    signup_date = random_date(
        SIGNUP_START,
        SIGNUP_END,
    )

    assigned_csm = random.choice(
        CUSTOMER_SUCCESS_MANAGERS
    )

    customer_status, churn_date = (
        determine_churn(
            segment,
            signup_date,
        )
    )

    account = {
        "account_id": account_id,
        "account_name": (
            company_names[
                account_id - 1
            ]
        ),
        "industry": industry,
        "segment": segment,
        "region": region,
        "signup_date": signup_date,
        "customer_status": (
            customer_status
        ),
        "churn_date": churn_date,
        "assigned_csm": assigned_csm,
    }

    accounts.append(
        account
    )


# =========================================================
# SAVE BASE CHURN COUNT BEFORE DIRTYING VALUES
# =========================================================

base_churned_accounts = sum(
    1
    for account in accounts
    if account["customer_status"]
    == "Churned"
)


# =========================================================
# ADD REALISTIC RAW-DATA QUALITY ISSUES
# =========================================================


# ---------------------------------------------------------
# Missing industry values
# Approximately 4%
# ---------------------------------------------------------

missing_industry_count = int(
    NUM_ACCOUNTS * 0.04
)

missing_industry_indexes = (
    random.sample(
        range(NUM_ACCOUNTS),
        missing_industry_count,
    )
)

for index in missing_industry_indexes:

    accounts[index]["industry"] = None


# ---------------------------------------------------------
# Missing CSM assignments
# Approximately 1.5%
# ---------------------------------------------------------

missing_csm_count = int(
    NUM_ACCOUNTS * 0.015
)

missing_csm_indexes = (
    random.sample(
        range(NUM_ACCOUNTS),
        missing_csm_count,
    )
)

for index in missing_csm_indexes:

    accounts[index]["assigned_csm"] = None


# ---------------------------------------------------------
# Inconsistent segment labels
# Approximately 2%
# ---------------------------------------------------------

dirty_segment_count = int(
    NUM_ACCOUNTS * 0.02
)

dirty_segment_indexes = (
    random.sample(
        range(NUM_ACCOUNTS),
        dirty_segment_count,
    )
)

segment_variations = {
    "SMB": "smb",
    "Mid-Market": "Mid Market",
    "Enterprise": "Enterprise ",
}

for index in dirty_segment_indexes:

    original_value = (
        accounts[index]["segment"]
    )

    accounts[index]["segment"] = (
        segment_variations[
            original_value
        ]
    )


# ---------------------------------------------------------
# Inconsistent region labels
# Approximately 2%
# ---------------------------------------------------------

dirty_region_count = int(
    NUM_ACCOUNTS * 0.02
)

dirty_region_indexes = (
    random.sample(
        range(NUM_ACCOUNTS),
        dirty_region_count,
    )
)

region_variations = {
    "Northeast": "north east",
    "South": "SOUTH",
    "Midwest": "Mid-west",
    "West": "West ",
    "Canada": "canada",
}

for index in dirty_region_indexes:

    original_value = (
        accounts[index]["region"]
    )

    accounts[index]["region"] = (
        region_variations[
            original_value
        ]
    )


# ---------------------------------------------------------
# Inconsistent customer-status labels
# Approximately 1%
# ---------------------------------------------------------

dirty_status_count = int(
    NUM_ACCOUNTS * 0.01
)

dirty_status_indexes = (
    random.sample(
        range(NUM_ACCOUNTS),
        dirty_status_count,
    )
)

status_variations = {
    "Active": "active",
    "Churned": "Churned ",
}

for index in dirty_status_indexes:

    original_value = (
        accounts[index][
            "customer_status"
        ]
    )

    accounts[index][
        "customer_status"
    ] = status_variations[
        original_value
    ]


# =========================================================
# ADD EXACT DUPLICATE RECORDS
# =========================================================

duplicate_indexes = random.sample(
    range(NUM_ACCOUNTS),
    DUPLICATE_ROWS,
)

duplicate_records = [
    dict(accounts[index])
    for index in duplicate_indexes
]


accounts_raw = (
    accounts
    + duplicate_records
)


# =========================================================
# SHUFFLE RAW ROWS
# =========================================================

random.shuffle(
    accounts_raw
)


# =========================================================
# SAVE RAW CSV
# =========================================================

output_file = (
    RAW_DATA_DIR
    / "accounts_raw.csv"
)

fieldnames = [
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


with output_file.open(
    mode="w",
    newline="",
    encoding="utf-8",
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    for account in accounts_raw:

        output_row = dict(
            account
        )

        output_row[
            "signup_date"
        ] = (
            account[
                "signup_date"
            ].isoformat()
        )

        if account["churn_date"]:

            output_row[
                "churn_date"
            ] = (
                account[
                    "churn_date"
                ].isoformat()
            )

        else:

            output_row[
                "churn_date"
            ] = ""

        writer.writerow(
            output_row
        )


# =========================================================
# DATA QUALITY SUMMARY
# =========================================================

missing_industry_rows = sum(
    1
    for account in accounts_raw
    if account["industry"] is None
)

missing_csm_rows = sum(
    1
    for account in accounts_raw
    if account["assigned_csm"] is None
)


def record_signature(record):
    """
    Convert a record into a tuple so exact duplicates
    can be counted.
    """

    return tuple(
        record[field]
        for field in fieldnames
    )


seen_records = set()
duplicate_count = 0

for account in accounts_raw:

    signature = record_signature(
        account
    )

    if signature in seen_records:

        duplicate_count += 1

    else:

        seen_records.add(
            signature
        )


# =========================================================
# PRINT SUMMARY
# =========================================================

print()

print(
    "=" * 60
)

print(
    "CLOUDPATH ANALYTICS - SYNTHETIC ACCOUNT DATA"
)

print(
    "=" * 60
)

print(
    f"Base customer accounts: "
    f"{NUM_ACCOUNTS}"
)

print(
    f"Raw rows after duplicates: "
    f"{len(accounts_raw)}"
)

print(
    f"Exact duplicate rows: "
    f"{duplicate_count}"
)

print(
    f"Missing industry values: "
    f"{missing_industry_rows}"
)

print(
    f"Missing CSM assignments: "
    f"{missing_csm_rows}"
)

print(
    f"Base churned accounts: "
    f"{base_churned_accounts}"
)

print()

print(
    "Raw accounts file created:"
)

print(
    output_file
)

print(
    "=" * 60
)
