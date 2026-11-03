from pathlib import Path
from datetime import datetime, date, timedelta
import csv
import random


# =========================================================
# PROJECT SETTINGS
# =========================================================

SEED = 84

ANALYSIS_END = date(2026, 12, 31)

DUPLICATE_ROWS = 8


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
    / "subscriptions_raw.csv"
)


# =========================================================
# VALID VALUES
# =========================================================

VALID_PLANS = {
    "Standard",
    "Professional",
    "Enterprise",
}

VALID_BILLING_FREQUENCIES = {
    "Monthly",
    "Annual",
}

VALID_SUBSCRIPTION_STATUSES = {
    "Active",
    "Renewed",
    "Churned",
    "Expired",
}


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


def round_to_nearest_25(value):
    """
    Round monetary values to the nearest $25.
    """

    return round(
        value / 25
    ) * 25


def choose_initial_plan(segment):
    """
    Choose a realistic starting plan based on
    customer segment.
    """

    if segment == "SMB":

        return random.choices(
            [
                "Standard",
                "Professional",
            ],
            weights=[
                75,
                25,
            ],
            k=1,
        )[0]

    if segment == "Mid-Market":

        return random.choices(
            [
                "Professional",
                "Enterprise",
            ],
            weights=[
                80,
                20,
            ],
            k=1,
        )[0]

    return "Enterprise"


def choose_billing_frequency(segment):
    """
    Larger customers are more likely to use
    annual billing.
    """

    if segment == "SMB":

        return random.choices(
            [
                "Monthly",
                "Annual",
            ],
            weights=[
                65,
                35,
            ],
            k=1,
        )[0]

    if segment == "Mid-Market":

        return random.choices(
            [
                "Monthly",
                "Annual",
            ],
            weights=[
                45,
                55,
            ],
            k=1,
        )[0]

    return random.choices(
        [
            "Monthly",
            "Annual",
        ],
        weights=[
            20,
            80,
        ],
        k=1,
    )[0]


def generate_initial_mrr(segment):
    """
    Generate MRR based on customer segment.

    These values are synthetic project assumptions,
    not external SaaS industry benchmarks.
    """

    if segment == "SMB":

        value = random.randint(
            800,
            1800,
        )

    elif segment == "Mid-Market":

        value = random.randint(
            2500,
            5000,
        )

    else:

        value = random.randint(
            6500,
            12000,
        )

    return float(
        round_to_nearest_25(
            value
        )
    )


def update_subscription_for_renewal(
    plan_name,
    current_mrr,
):
    """
    Simulate revenue movement at renewal.

    Most customers receive a small price increase.

    Some accounts expand.

    Some accounts contract.
    """

    renewal_event = random.random()

    # -----------------------------------------------------
    # Expansion
    # -----------------------------------------------------

    if renewal_event < 0.12:

        upgrade_map = {
            "Standard": "Professional",
            "Professional": "Enterprise",
            "Enterprise": "Enterprise",
        }

        new_plan = upgrade_map[
            plan_name
        ]

        multiplier = random.uniform(
            1.12,
            1.25,
        )

    # -----------------------------------------------------
    # Contraction
    # -----------------------------------------------------

    elif renewal_event < 0.18:

        new_plan = plan_name

        multiplier = random.uniform(
            0.88,
            0.97,
        )

    # -----------------------------------------------------
    # Normal renewal / price increase
    # -----------------------------------------------------

    else:

        new_plan = plan_name

        multiplier = random.uniform(
            1.02,
            1.06,
        )

    new_mrr = round_to_nearest_25(
        current_mrr
        * multiplier
    )

    return (
        new_plan,
        float(new_mrr),
    )


# =========================================================
# READ CLEANED ACCOUNTS
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
# GENERATE SUBSCRIPTION PERIODS
# =========================================================

subscriptions = []

subscription_id = 1


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

    plan_name = choose_initial_plan(
        segment
    )

    billing_frequency = (
        choose_billing_frequency(
            segment
        )
    )

    current_mrr = (
        generate_initial_mrr(
            segment
        )
    )

    subscription_start_date = (
        signup_date
    )


    while True:

        natural_end_date = (
            subscription_start_date
            + timedelta(days=364)
        )


        # -------------------------------------------------
        # Customer churns during this subscription period
        # -------------------------------------------------

        if (
            customer_status == "Churned"
            and churn_date is not None
            and churn_date
            <= natural_end_date
        ):

            subscription_end_date = (
                churn_date
            )

            subscription_status = (
                "Churned"
            )

            renewal_date = None

            final_period = True


        # -------------------------------------------------
        # Subscription completed and customer renewed
        # -------------------------------------------------

        elif (
            natural_end_date
            < ANALYSIS_END
            and (
                churn_date is None
                or natural_end_date
                < churn_date
            )
        ):

            subscription_end_date = (
                natural_end_date
            )

            subscription_status = (
                "Renewed"
            )

            renewal_date = (
                subscription_end_date
                + timedelta(days=1)
            )

            final_period = False


        # -------------------------------------------------
        # Current active subscription period
        # -------------------------------------------------

        else:

            subscription_end_date = (
                natural_end_date
            )

            subscription_status = (
                "Active"
            )

            renewal_date = (
                subscription_end_date
                + timedelta(days=1)
            )

            final_period = True


        subscription_record = {
            "subscription_id": (
                subscription_id
            ),
            "account_id": (
                account_id
            ),
            "plan_name": (
                plan_name
            ),
            "subscription_start_date": (
                subscription_start_date
            ),
            "subscription_end_date": (
                subscription_end_date
            ),
            "billing_frequency": (
                billing_frequency
            ),
            "mrr": (
                f"{current_mrr:.2f}"
            ),
            "subscription_status": (
                subscription_status
            ),
            "renewal_date": (
                renewal_date
            ),
        }


        subscriptions.append(
            subscription_record
        )

        subscription_id += 1


        if final_period:

            break


        subscription_start_date = (
            subscription_end_date
            + timedelta(days=1)
        )


        # -------------------------------------------------
        # Simulate renewal revenue movement
        # -------------------------------------------------

        (
            plan_name,
            current_mrr,
        ) = update_subscription_for_renewal(
            plan_name,
            current_mrr,
        )


        # -------------------------------------------------
        # Some monthly customers switch to annual billing
        # after renewal.
        # -------------------------------------------------

        if (
            billing_frequency
            == "Monthly"
            and random.random()
            < 0.08
        ):

            billing_frequency = (
                "Annual"
            )


# =========================================================
# CURRENT RECURRING REVENUE BEFORE DIRTYING DATA
# =========================================================

current_active_subscriptions = [
    subscription
    for subscription in subscriptions
    if subscription[
        "subscription_status"
    ] == "Active"
]


current_mrr = sum(
    float(
        subscription[
            "mrr"
        ]
    )
    for subscription
    in current_active_subscriptions
)


current_arr = (
    current_mrr * 12
)


# =========================================================
# ADD REALISTIC RAW-DATA QUALITY ISSUES
# =========================================================


# ---------------------------------------------------------
# Inconsistent billing frequency labels
# Approximately 2%
# ---------------------------------------------------------

dirty_billing_count = max(
    1,
    int(
        len(subscriptions)
        * 0.02
    ),
)

dirty_billing_indexes = (
    random.sample(
        range(
            len(subscriptions)
        ),
        dirty_billing_count,
    )
)

billing_variations = {
    "Monthly": "monthly",
    "Annual": "Annual ",
}

for index in dirty_billing_indexes:

    original_value = (
        subscriptions[index][
            "billing_frequency"
        ]
    )

    subscriptions[index][
        "billing_frequency"
    ] = billing_variations[
        original_value
    ]


# ---------------------------------------------------------
# Inconsistent subscription status labels
# Approximately 1.5%
# ---------------------------------------------------------

dirty_status_count = max(
    1,
    int(
        len(subscriptions)
        * 0.015
    ),
)

dirty_status_indexes = (
    random.sample(
        range(
            len(subscriptions)
        ),
        dirty_status_count,
    )
)

status_variations = {
    "Active": "active",
    "Renewed": "Renewed ",
    "Churned": "CHURNED",
    "Expired": "expired",
}

for index in dirty_status_indexes:

    original_value = (
        subscriptions[index][
            "subscription_status"
        ]
    )

    subscriptions[index][
        "subscription_status"
    ] = status_variations[
        original_value
    ]


# ---------------------------------------------------------
# Inconsistent plan labels
# Approximately 1%
# ---------------------------------------------------------

dirty_plan_count = max(
    1,
    int(
        len(subscriptions)
        * 0.01
    ),
)

dirty_plan_indexes = (
    random.sample(
        range(
            len(subscriptions)
        ),
        dirty_plan_count,
    )
)

plan_variations = {
    "Standard": "STANDARD",
    "Professional": "professional",
    "Enterprise": "Enterprise ",
}

for index in dirty_plan_indexes:

    original_value = (
        subscriptions[index][
            "plan_name"
        ]
    )

    subscriptions[index][
        "plan_name"
    ] = plan_variations[
        original_value
    ]


# =========================================================
# ADD EXACT DUPLICATE RECORDS
# =========================================================

duplicate_indexes = random.sample(
    range(
        len(subscriptions)
    ),
    DUPLICATE_ROWS,
)

duplicate_records = [
    dict(
        subscriptions[index]
    )
    for index in duplicate_indexes
]


subscriptions_raw = (
    subscriptions
    + duplicate_records
)


# =========================================================
# SHUFFLE RAW DATA
# =========================================================

random.shuffle(
    subscriptions_raw
)


# =========================================================
# SAVE RAW CSV
# =========================================================

fieldnames = [
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


with OUTPUT_FILE.open(
    mode="w",
    newline="",
    encoding="utf-8",
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()


    for subscription in subscriptions_raw:

        output_row = dict(
            subscription
        )


        output_row[
            "subscription_start_date"
        ] = subscription[
            "subscription_start_date"
        ].isoformat()


        output_row[
            "subscription_end_date"
        ] = subscription[
            "subscription_end_date"
        ].isoformat()


        renewal_date = (
            subscription[
                "renewal_date"
            ]
        )


        if renewal_date is None:

            output_row[
                "renewal_date"
            ] = ""

        else:

            output_row[
                "renewal_date"
            ] = renewal_date.isoformat()


        writer.writerow(
            output_row
        )


# =========================================================
# DATA QUALITY SUMMARY
# =========================================================

raw_invalid_billing = sum(
    1
    for subscription
    in subscriptions_raw
    if subscription[
        "billing_frequency"
    ]
    not in VALID_BILLING_FREQUENCIES
)


raw_invalid_status = sum(
    1
    for subscription
    in subscriptions_raw
    if subscription[
        "subscription_status"
    ]
    not in VALID_SUBSCRIPTION_STATUSES
)


raw_invalid_plan = sum(
    1
    for subscription
    in subscriptions_raw
    if subscription[
        "plan_name"
    ]
    not in VALID_PLANS
)


# =========================================================
# COUNT EXACT DUPLICATES
# =========================================================

def record_signature(record):
    """
    Convert subscription record into a tuple
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


for subscription in subscriptions_raw:

    signature = record_signature(
        subscription
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
    "CLOUDPATH ANALYTICS - SYNTHETIC SUBSCRIPTION DATA"
)

print(
    "=" * 65
)

print(
    f"Customer accounts read: "
    f"{len(accounts)}"
)

print(
    f"Base subscription periods: "
    f"{len(subscriptions)}"
)

print(
    f"Raw rows after duplicates: "
    f"{len(subscriptions_raw)}"
)

print(
    f"Exact duplicate rows: "
    f"{exact_duplicate_count}"
)

print(
    f"Inconsistent billing values: "
    f"{raw_invalid_billing}"
)

print(
    f"Inconsistent status values: "
    f"{raw_invalid_status}"
)

print(
    f"Inconsistent plan values: "
    f"{raw_invalid_plan}"
)

print(
    f"Current active subscriptions: "
    f"{len(current_active_subscriptions)}"
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
    "Raw subscriptions file created:"
)

print(
    OUTPUT_FILE
)

print(
    "=" * 65
)
