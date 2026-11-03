from pathlib import Path
from datetime import datetime, date
import csv
import random


# =========================================================
# PROJECT SETTINGS
# =========================================================

SEED = 126

ANALYSIS_START_MONTH = date(2025, 1, 1)
ANALYSIS_END_MONTH = date(2026, 12, 1)

DUPLICATE_ROWS = 12

INVALID_ACTIVE_USER_ROWS = 10
INVALID_FEATURE_ROWS = 8
NEGATIVE_LOGIN_ROWS = 8


# =========================================================
# REPRODUCIBILITY
# =========================================================

random.seed(SEED)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ACCOUNTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "accounts.csv"
)

RAW_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
)

RAW_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE = (
    RAW_DATA_DIR
    / "product_usage_raw.csv"
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def parse_date(value):
    """
    Convert YYYY-MM-DD text into a Python date.
    Blank values return None.
    """

    cleaned_value = value.strip()

    if cleaned_value == "":
        return None

    return datetime.strptime(
        cleaned_value,
        "%Y-%m-%d",
    ).date()


def month_start(value):
    """
    Convert a date to the first day of its month.
    """

    return date(
        value.year,
        value.month,
        1,
    )


def next_month(value):
    """
    Return the first day of the next month.
    """

    if value.month == 12:

        return date(
            value.year + 1,
            1,
            1,
        )

    return date(
        value.year,
        value.month + 1,
        1,
    )


def build_month_range(
    start_month,
    end_month,
):
    """
    Build an inclusive list of monthly dates.
    """

    months = []

    current_month = start_month

    while current_month <= end_month:

        months.append(
            current_month
        )

        current_month = next_month(
            current_month
        )

    return months


def clamp(
    value,
    minimum,
    maximum,
):
    """
    Restrict a numeric value to a given range.
    """

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def generate_licensed_users(
    segment,
    account_rng,
):
    """
    Generate licensed-user capacity based on segment.
    """

    if segment == "SMB":

        return account_rng.randint(
            10,
            60,
        )

    if segment == "Mid-Market":

        return account_rng.randint(
            60,
            250,
        )

    return account_rng.randint(
        250,
        1000,
    )


def choose_usage_profile(
    customer_status,
    account_rng,
):
    """
    Assign an underlying synthetic engagement pattern.

    Churned accounts are more likely to show declining
    or low engagement.

    Active accounts contain a mix of stable, growing,
    declining, low-engagement, and volatile behavior.
    """

    if customer_status == "Churned":

        return account_rng.choices(
            [
                "Declining",
                "Low Engagement",
                "Stable",
            ],
            weights=[
                70,
                20,
                10,
            ],
            k=1,
        )[0]

    return account_rng.choices(
        [
            "Stable",
            "Growth",
            "Declining",
            "Low Engagement",
            "Volatile",
        ],
        weights=[
            50,
            20,
            15,
            10,
            5,
        ],
        k=1,
    )[0]


def calculate_active_ratio(
    profile,
    base_ratio,
    progress,
    customer_status,
    account_rng,
):
    """
    Calculate the share of licensed users active
    during a given month.
    """

    noise = account_rng.uniform(
        -0.04,
        0.04,
    )


    if profile == "Stable":

        ratio = (
            base_ratio
            + noise
        )


    elif profile == "Growth":

        growth_multiplier = (
            0.72
            + (
                0.38
                * progress
            )
        )

        ratio = (
            base_ratio
            * growth_multiplier
            + noise
        )


    elif profile == "Declining":

        if customer_status == "Churned":

            decline_progress = max(
                0,
                (
                    progress - 0.55
                )
                / 0.45,
            )

            ratio = (
                base_ratio
                * (
                    1
                    - (
                        0.68
                        * decline_progress
                    )
                )
                + noise
            )

        else:

            ratio = (
                base_ratio
                * (
                    1
                    - (
                        0.35
                        * progress
                    )
                )
                + noise
            )


    elif profile == "Low Engagement":

        ratio = (
            base_ratio
            * account_rng.uniform(
                0.30,
                0.50,
            )
            + noise
        )


    else:

        ratio = (
            base_ratio
            * account_rng.uniform(
                0.55,
                1.25,
            )
            + noise
        )


    return clamp(
        ratio,
        0.05,
        0.98,
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


# =========================================================
# GENERATE MONTHLY PRODUCT USAGE
# =========================================================

usage_records = []

usage_id = 1

profile_counts = {
    "Stable": 0,
    "Growth": 0,
    "Declining": 0,
    "Low Engagement": 0,
    "Volatile": 0,
}

temporary_spike_count = 0


for account in accounts:

    account_id = int(
        account[
            "account_id"
        ]
    )

    segment = account[
        "segment"
    ]

    customer_status = account[
        "customer_status"
    ]

    signup_date = parse_date(
        account[
            "signup_date"
        ]
    )

    churn_date = parse_date(
        account[
            "churn_date"
        ]
    )


    # -----------------------------------------------------
    # USE A DETERMINISTIC RANDOM GENERATOR PER ACCOUNT
    # -----------------------------------------------------

    account_rng = random.Random(
        SEED
        + (
            account_id
            * 101
        )
    )


    # -----------------------------------------------------
    # DETERMINE ACCOUNT USAGE PERIOD
    # -----------------------------------------------------

    start_month = max(
        month_start(
            signup_date
        ),
        ANALYSIS_START_MONTH,
    )


    if churn_date is not None:

        end_month = min(
            month_start(
                churn_date
            ),
            ANALYSIS_END_MONTH,
        )

    else:

        end_month = (
            ANALYSIS_END_MONTH
        )


    if start_month > end_month:

        continue


    months = build_month_range(
        start_month,
        end_month,
    )


    # -----------------------------------------------------
    # ACCOUNT CHARACTERISTICS
    # -----------------------------------------------------

    licensed_users = (
        generate_licensed_users(
            segment,
            account_rng,
        )
    )


    if segment == "SMB":

        base_active_ratio = (
            account_rng.uniform(
                0.55,
                0.82,
            )
        )

    elif segment == "Mid-Market":

        base_active_ratio = (
            account_rng.uniform(
                0.58,
                0.85,
            )
        )

    else:

        base_active_ratio = (
            account_rng.uniform(
                0.60,
                0.88,
            )
        )


    profile = choose_usage_profile(
        customer_status,
        account_rng,
    )

    profile_counts[
        profile
    ] += 1


    total_months = len(
        months
    )


    # -----------------------------------------------------
    # GENERATE EACH MONTH
    # -----------------------------------------------------

    for month_index, usage_month in enumerate(
        months
    ):

        if total_months == 1:

            progress = 1.0

        else:

            progress = (
                month_index
                / (
                    total_months - 1
                )
            )


        active_ratio = (
            calculate_active_ratio(
                profile,
                base_active_ratio,
                progress,
                customer_status,
                account_rng,
            )
        )


        active_users = round(
            licensed_users
            * active_ratio
        )


        active_users = int(
            clamp(
                active_users,
                0,
                licensed_users,
            )
        )


        # -------------------------------------------------
        # NORMAL MONTHLY ACTIVITY
        # -------------------------------------------------

        login_count = int(
            round(
                active_users
                * account_rng.uniform(
                    5,
                    14,
                )
            )
        )


        dashboards_viewed = int(
            round(
                active_users
                * account_rng.uniform(
                    2,
                    8,
                )
            )
        )


        reports_generated = int(
            round(
                active_users
                * account_rng.uniform(
                    0.3,
                    2.5,
                )
            )
        )


        alerts_created = int(
            round(
                active_users
                * account_rng.uniform(
                    0.05,
                    0.65,
                )
            )
        )


        core_features_used = int(
            round(
                2
                + (
                    active_ratio
                    * 6
                )
                + account_rng.uniform(
                    -0.6,
                    0.6,
                )
            )
        )


        core_features_used = int(
            clamp(
                core_features_used,
                0,
                8,
            )
        )


        # -------------------------------------------------
        # TEMPORARY VALID USAGE SPIKES
        # -------------------------------------------------

        if account_rng.random() < 0.025:

            spike_multiplier = (
                account_rng.uniform(
                    1.8,
                    3.2,
                )
            )

            login_count = int(
                round(
                    login_count
                    * spike_multiplier
                )
            )

            dashboards_viewed = int(
                round(
                    dashboards_viewed
                    * spike_multiplier
                )
            )

            reports_generated = int(
                round(
                    reports_generated
                    * spike_multiplier
                )
            )

            temporary_spike_count += 1


        usage_record = {
            "usage_id": (
                usage_id
            ),
            "account_id": (
                account_id
            ),
            "usage_month": (
                usage_month
            ),
            "licensed_users": (
                licensed_users
            ),
            "active_users": (
                active_users
            ),
            "login_count": (
                login_count
            ),
            "dashboards_viewed": (
                dashboards_viewed
            ),
            "reports_generated": (
                reports_generated
            ),
            "alerts_created": (
                alerts_created
            ),
            "core_features_used": (
                core_features_used
            ),
        }


        usage_records.append(
            usage_record
        )

        usage_id += 1


# =========================================================
# ADD INTENTIONAL RAW-DATA QUALITY ISSUES
# =========================================================

total_base_rows = len(
    usage_records
)


# ---------------------------------------------------------
# Active users greater than licensed users
# ---------------------------------------------------------

invalid_active_indexes = random.sample(
    range(
        total_base_rows
    ),
    INVALID_ACTIVE_USER_ROWS,
)


for index in invalid_active_indexes:

    usage_records[index][
        "active_users"
    ] = (
        usage_records[index][
            "licensed_users"
        ]
        + random.randint(
            1,
            15,
        )
    )


# ---------------------------------------------------------
# Core feature count above maximum of 8
# ---------------------------------------------------------

invalid_feature_indexes = random.sample(
    range(
        total_base_rows
    ),
    INVALID_FEATURE_ROWS,
)


for index in invalid_feature_indexes:

    usage_records[index][
        "core_features_used"
    ] = random.choice(
        [
            9,
            10,
        ]
    )


# ---------------------------------------------------------
# Negative login counts
# ---------------------------------------------------------

negative_login_indexes = random.sample(
    range(
        total_base_rows
    ),
    NEGATIVE_LOGIN_ROWS,
)


for index in negative_login_indexes:

    usage_records[index][
        "login_count"
    ] = -random.randint(
        1,
        30,
    )


# =========================================================
# ADD EXACT DUPLICATE ROWS
# =========================================================

duplicate_indexes = random.sample(
    range(
        total_base_rows
    ),
    DUPLICATE_ROWS,
)


duplicate_records = [
    dict(
        usage_records[
            index
        ]
    )
    for index in duplicate_indexes
]


product_usage_raw = (
    usage_records
    + duplicate_records
)


# =========================================================
# SHUFFLE RAW DATA
# =========================================================

random.shuffle(
    product_usage_raw
)


# =========================================================
# SAVE RAW CSV
# =========================================================

fieldnames = [
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


with OUTPUT_FILE.open(
    mode="w",
    encoding="utf-8",
    newline="",
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()


    for record in product_usage_raw:

        output_row = dict(
            record
        )

        output_row[
            "usage_month"
        ] = record[
            "usage_month"
        ].isoformat()

        writer.writerow(
            output_row
        )


# =========================================================
# RAW DATA QUALITY SUMMARY
# =========================================================

invalid_active_user_count = sum(
    1
    for row in product_usage_raw
    if row["active_users"]
    > row["licensed_users"]
)


invalid_feature_count = sum(
    1
    for row in product_usage_raw
    if row["core_features_used"] > 8
)


negative_login_count = sum(
    1
    for row in product_usage_raw
    if row["login_count"] < 0
)


# =========================================================
# COUNT EXACT DUPLICATES
# =========================================================

def record_signature(record):
    """
    Convert a usage record into a tuple
    for duplicate detection.
    """

    return tuple(
        str(
            record[field]
        )
        for field in fieldnames
    )


seen_records = set()

exact_duplicate_count = 0


for record in product_usage_raw:

    signature = record_signature(
        record
    )

    if signature in seen_records:

        exact_duplicate_count += 1

    else:

        seen_records.add(
            signature
        )


# =========================================================
# PRINT SUMMARY
# =========================================================

print()

print(
    "=" * 65
)

print(
    "CLOUDPATH ANALYTICS - SYNTHETIC PRODUCT USAGE DATA"
)

print(
    "=" * 65
)

print(
    f"Customer accounts read: "
    f"{len(accounts)}"
)

print(
    f"Base monthly usage rows: "
    f"{len(usage_records)}"
)

print(
    f"Raw rows after duplicates: "
    f"{len(product_usage_raw)}"
)

print(
    f"Exact duplicate rows: "
    f"{exact_duplicate_count}"
)

print(
    f"Rows with active_users > licensed_users: "
    f"{invalid_active_user_count}"
)

print(
    f"Rows with core_features_used > 8: "
    f"{invalid_feature_count}"
)

print(
    f"Rows with negative login_count: "
    f"{negative_login_count}"
)

print(
    f"Temporary usage spikes generated: "
    f"{temporary_spike_count}"
)

print()

print(
    "Synthetic usage profiles:"
)

for profile_name in [
    "Stable",
    "Growth",
    "Declining",
    "Low Engagement",
    "Volatile",
]:

    print(
        f"  {profile_name}: "
        f"{profile_counts[profile_name]}"
    )

print()

print(
    "Raw product usage file created:"
)

print(
    OUTPUT_FILE
)

print(
    "=" * 65
)
