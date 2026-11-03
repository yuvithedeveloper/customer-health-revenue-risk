from pathlib import Path
from datetime import datetime, date, timedelta
import calendar
import csv
import random


# =========================================================
# PROJECT SETTINGS
# =========================================================

SEED = 252

ANALYSIS_START = date(2025, 1, 1)
ANALYSIS_END = date(2026, 12, 31)

DUPLICATE_ROWS = 15

DIRTY_TYPE_ROWS = 12
DIRTY_ENGAGEMENT_ROWS = 12
DIRTY_FOLLOWUP_ROWS = 10
DIRTY_NOTES_ROWS = 10
INVALID_FOLLOWUP_DATE_ROWS = 7


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

PRODUCT_USAGE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "product_usage.csv"
)

SUPPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "support_tickets.csv"
)

INVOICES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "invoices.csv"
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
    / "customer_success_interactions_raw.csv"
)


# =========================================================
# VALID VALUES
# =========================================================

INTERACTION_TYPES = [
    "Email",
    "Call",
    "Meeting",
    "QBR",
    "Training",
]

ENGAGEMENT_STATUSES = [
    "Engaged",
    "Neutral",
    "Unresponsive",
]

NOTES_CATEGORIES = [
    "General Check-in",
    "Adoption",
    "Training Need",
    "Support Escalation",
    "Billing Follow-up",
    "Renewal",
    "Expansion",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def parse_date(value):

    cleaned_value = value.strip()

    if cleaned_value == "":
        return None

    return datetime.strptime(
        cleaned_value,
        "%Y-%m-%d",
    ).date()


def month_start(value):

    return date(
        value.year,
        value.month,
        1,
    )


def month_end(value):

    final_day = calendar.monthrange(
        value.year,
        value.month,
    )[1]

    return date(
        value.year,
        value.month,
        final_day,
    )


def next_month(value):

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


def random_date_between(
    start_date,
    end_date,
    rng,
):

    difference = (
        end_date
        - start_date
    ).days

    return (
        start_date
        + timedelta(
            days=rng.randint(
                0,
                difference,
            )
        )
    )


def interaction_count_from_rate(
    rate,
    rng,
):

    whole_interactions = int(
        rate
    )

    fractional_part = (
        rate
        - whole_interactions
    )

    interaction_count = (
        whole_interactions
    )

    if rng.random() < fractional_part:

        interaction_count += 1

    return interaction_count


def choose_interaction_type(
    segment,
    low_usage,
    support_pressure,
    payment_issue,
    rng,
):

    if low_usage:

        return rng.choices(
            INTERACTION_TYPES,
            weights=[
                25,
                28,
                15,
                7,
                25,
            ],
            k=1,
        )[0]


    if support_pressure:

        return rng.choices(
            INTERACTION_TYPES,
            weights=[
                25,
                35,
                25,
                5,
                10,
            ],
            k=1,
        )[0]


    if payment_issue:

        return rng.choices(
            INTERACTION_TYPES,
            weights=[
                45,
                35,
                15,
                2,
                3,
            ],
            k=1,
        )[0]


    if segment == "Enterprise":

        return rng.choices(
            INTERACTION_TYPES,
            weights=[
                20,
                20,
                25,
                25,
                10,
            ],
            k=1,
        )[0]


    if segment == "Mid-Market":

        return rng.choices(
            INTERACTION_TYPES,
            weights=[
                30,
                28,
                20,
                12,
                10,
            ],
            k=1,
        )[0]


    return rng.choices(
        INTERACTION_TYPES,
        weights=[
            45,
            30,
            12,
            3,
            10,
        ],
        k=1,
    )[0]


def choose_engagement_status(
    low_usage,
    near_churn,
    support_pressure,
    payment_issue,
    rng,
):

    if near_churn:

        weights = [
            28,
            32,
            40,
        ]

    elif low_usage:

        weights = [
            38,
            37,
            25,
        ]

    elif payment_issue:

        weights = [
            45,
            38,
            17,
        ]

    elif support_pressure:

        weights = [
            52,
            35,
            13,
        ]

    else:

        weights = [
            68,
            25,
            7,
        ]

    return rng.choices(
        ENGAGEMENT_STATUSES,
        weights=weights,
        k=1,
    )[0]


def choose_follow_up_required(
    engagement_status,
    support_pressure,
    payment_issue,
    rng,
):

    if engagement_status == "Unresponsive":

        probability = 0.78

    elif engagement_status == "Neutral":

        probability = 0.48

    else:

        probability = 0.25


    if support_pressure:

        probability += 0.10


    if payment_issue:

        probability += 0.12


    probability = min(
        probability,
        0.95,
    )


    return (
        rng.random()
        < probability
    )


def choose_notes_category(
    interaction_type,
    low_usage,
    support_pressure,
    payment_issue,
    near_churn,
    rng,
):

    if payment_issue:

        return "Billing Follow-up"


    if support_pressure:

        return "Support Escalation"


    if low_usage:

        if interaction_type == "Training":

            return "Training Need"

        return "Adoption"


    if near_churn:

        return "Renewal"


    if interaction_type == "QBR":

        return rng.choices(
            [
                "Renewal",
                "Expansion",
                "General Check-in",
            ],
            weights=[
                35,
                35,
                30,
            ],
            k=1,
        )[0]


    if interaction_type == "Training":

        return "Training Need"


    return rng.choices(
        [
            "General Check-in",
            "Adoption",
            "Expansion",
            "Renewal",
        ],
        weights=[
            50,
            25,
            15,
            10,
        ],
        k=1,
    )[0]


# =========================================================
# READ ACCOUNTS
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
# READ PRODUCT USAGE
# =========================================================

with PRODUCT_USAGE_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    usage_rows = list(
        reader
    )


# =========================================================
# READ SUPPORT TICKETS
# =========================================================

with SUPPORT_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    support_rows = list(
        reader
    )


# =========================================================
# READ INVOICES
# =========================================================

with INVOICES_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    invoice_rows = list(
        reader
    )


# =========================================================
# BUILD PRODUCT USAGE LOOKUP
# =========================================================

usage_lookup = {}


for row in usage_rows:

    account_id = int(
        row["account_id"]
    )

    licensed_users = int(
        row["licensed_users"]
    )

    active_users = int(
        row["active_users"]
    )


    if licensed_users == 0:

        active_ratio = 0

    else:

        active_ratio = (
            active_users
            / licensed_users
        )


    key = (
        account_id,
        row["usage_month"],
    )


    usage_lookup[
        key
    ] = active_ratio


# =========================================================
# BUILD MONTHLY SUPPORT LOOKUP
# =========================================================

support_lookup = {}


for row in support_rows:

    account_id = int(
        row["account_id"]
    )

    created_date = parse_date(
        row["created_date"]
    )

    support_month = month_start(
        created_date
    ).isoformat()


    key = (
        account_id,
        support_month,
    )


    support_lookup[
        key
    ] = (
        support_lookup.get(
            key,
            0,
        )
        + 1
    )


# =========================================================
# BUILD MONTHLY PAYMENT ISSUE LOOKUP
# =========================================================

payment_issue_lookup = {}


for row in invoice_rows:

    if row[
        "payment_status"
    ] not in {
        "Late",
        "Failed",
    }:

        continue


    account_id = int(
        row["account_id"]
    )


    invoice_date = parse_date(
        row["invoice_date"]
    )


    invoice_month = month_start(
        invoice_date
    ).isoformat()


    key = (
        account_id,
        invoice_month,
    )


    payment_issue_lookup[
        key
    ] = True


# =========================================================
# GENERATE CUSTOMER SUCCESS INTERACTIONS
# =========================================================

interaction_records = []

interaction_id = 1


for account in accounts:

    account_id = int(
        account[
            "account_id"
        ]
    )


    segment = account[
        "segment"
    ]


    assigned_csm = account[
        "assigned_csm"
    ].strip()


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


    account_rng = random.Random(
        SEED
        + (
            account_id
            * 197
        )
    )


    # -----------------------------------------------------
    # INTERACTION HISTORY RANGE
    # -----------------------------------------------------

    start_date = max(
        signup_date,
        ANALYSIS_START,
    )


    if churn_date is None:

        end_date = ANALYSIS_END

    else:

        end_date = min(
            churn_date,
            ANALYSIS_END,
        )


    if start_date > end_date:

        continue


    months = build_month_range(
        month_start(
            start_date
        ),
        month_start(
            end_date
        ),
    )


    # -----------------------------------------------------
    # BASE MONTHLY INTERACTION RATE
    # -----------------------------------------------------

    if segment == "SMB":

        base_rate = 0.20

    elif segment == "Mid-Market":

        base_rate = 0.36

    else:

        base_rate = 0.62


    # -----------------------------------------------------
    # MONTHLY INTERACTION GENERATION
    # -----------------------------------------------------

    for interaction_month in months:

        month_key = (
            account_id,
            interaction_month.isoformat(),
        )


        active_ratio = usage_lookup.get(
            month_key,
            0.60,
        )


        monthly_support_count = (
            support_lookup.get(
                month_key,
                0,
            )
        )


        payment_issue = (
            payment_issue_lookup.get(
                month_key,
                False,
            )
        )


        low_usage = (
            active_ratio < 0.45
        )


        support_pressure = (
            monthly_support_count >= 2
        )


        near_churn = False


        if churn_date is not None:

            days_to_churn = (
                churn_date
                - interaction_month
            ).days


            if (
                0
                <= days_to_churn
                <= 120
            ):

                near_churn = True


        monthly_rate = (
            base_rate
        )


        if low_usage:

            monthly_rate += 0.16


        if support_pressure:

            monthly_rate += 0.15


        if payment_issue:

            monthly_rate += 0.16


        if near_churn:

            monthly_rate += 0.20


        interaction_count = (
            interaction_count_from_rate(
                monthly_rate,
                account_rng,
            )
        )


        for _ in range(
            interaction_count
        ):

            valid_start = max(
                interaction_month,
                start_date,
            )


            valid_end = min(
                month_end(
                    interaction_month
                ),
                end_date,
            )


            if valid_start > valid_end:

                continue


            interaction_date = (
                random_date_between(
                    valid_start,
                    valid_end,
                    account_rng,
                )
            )


            interaction_type = (
                choose_interaction_type(
                    segment,
                    low_usage,
                    support_pressure,
                    payment_issue,
                    account_rng,
                )
            )


            engagement_status = (
                choose_engagement_status(
                    low_usage,
                    near_churn,
                    support_pressure,
                    payment_issue,
                    account_rng,
                )
            )


            follow_up_required = (
                choose_follow_up_required(
                    engagement_status,
                    support_pressure,
                    payment_issue,
                    account_rng,
                )
            )


            notes_category = (
                choose_notes_category(
                    interaction_type,
                    low_usage,
                    support_pressure,
                    payment_issue,
                    near_churn,
                    account_rng,
                )
            )


            if follow_up_required:

                next_follow_up_date = (
                    interaction_date
                    + timedelta(
                        days=account_rng.randint(
                            3,
                            30,
                        )
                    )
                )

            else:

                next_follow_up_date = None


            interaction_record = {
                "interaction_id":
                    interaction_id,

                "account_id":
                    account_id,

                "interaction_date":
                    interaction_date,

                "interaction_type":
                    interaction_type,

                "csm_name":
                    assigned_csm,

                "engagement_status":
                    engagement_status,

                "follow_up_required":
                    follow_up_required,

                "notes_category":
                    notes_category,

                "next_follow_up_date":
                    next_follow_up_date,
            }


            interaction_records.append(
                interaction_record
            )


            interaction_id += 1


# =========================================================
# BASE ROW COUNT
# =========================================================

base_row_count = len(
    interaction_records
)


# =========================================================
# INTENTIONAL RAW DATA QUALITY ISSUES
# =========================================================

# ---------------------------------------------------------
# DIRTY INTERACTION TYPES
# ---------------------------------------------------------

type_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_TYPE_ROWS,
        base_row_count,
    ),
)


type_variants = {
    "Email": "email",
    "Call": "CALL",
    "Meeting": "Meeting ",
    "QBR": "qbr",
    "Training": "training ",
}


for index in type_indexes:

    original_value = interaction_records[
        index
    ][
        "interaction_type"
    ]


    interaction_records[
        index
    ][
        "interaction_type"
    ] = type_variants[
        original_value
    ]


# ---------------------------------------------------------
# DIRTY ENGAGEMENT STATUSES
# ---------------------------------------------------------

engagement_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_ENGAGEMENT_ROWS,
        base_row_count,
    ),
)


engagement_variants = {
    "Engaged": "engaged",
    "Neutral": "Neutral ",
    "Unresponsive": "UNRESPONSIVE",
}


for index in engagement_indexes:

    original_value = interaction_records[
        index
    ][
        "engagement_status"
    ]


    interaction_records[
        index
    ][
        "engagement_status"
    ] = engagement_variants[
        original_value
    ]


# ---------------------------------------------------------
# DIRTY FOLLOW-UP BOOLEAN VALUES
# ---------------------------------------------------------

followup_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_FOLLOWUP_ROWS,
        base_row_count,
    ),
)


for index in followup_indexes:

    original_value = interaction_records[
        index
    ][
        "follow_up_required"
    ]


    if original_value:

        interaction_records[
            index
        ][
            "follow_up_required"
        ] = random.choice(
            [
                "TRUE ",
                "yes",
            ]
        )

    else:

        interaction_records[
            index
        ][
            "follow_up_required"
        ] = random.choice(
            [
                "FALSE ",
                "no",
            ]
        )


# ---------------------------------------------------------
# DIRTY NOTES CATEGORIES
# ---------------------------------------------------------

notes_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_NOTES_ROWS,
        base_row_count,
    ),
)


for index in notes_indexes:

    original_value = interaction_records[
        index
    ][
        "notes_category"
    ]


    if random.random() < 0.5:

        dirty_value = (
            original_value.lower()
        )

    else:

        dirty_value = (
            original_value
            + " "
        )


    interaction_records[
        index
    ][
        "notes_category"
    ] = dirty_value


# ---------------------------------------------------------
# INVALID FOLLOW-UP DATES
# ---------------------------------------------------------

followup_date_eligible = [
    index
    for index, row in enumerate(
        interaction_records
    )
    if row[
        "next_follow_up_date"
    ] is not None
]


invalid_followup_indexes = random.sample(
    followup_date_eligible,
    min(
        INVALID_FOLLOWUP_DATE_ROWS,
        len(
            followup_date_eligible
        ),
    ),
)


for index in invalid_followup_indexes:

    interaction_date = interaction_records[
        index
    ][
        "interaction_date"
    ]


    interaction_records[
        index
    ][
        "next_follow_up_date"
    ] = (
        interaction_date
        - timedelta(
            days=random.randint(
                1,
                10,
            )
        )
    )


# =========================================================
# ADD EXACT DUPLICATES
# =========================================================

duplicate_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DUPLICATE_ROWS,
        base_row_count,
    ),
)


duplicate_records = [
    dict(
        interaction_records[
            index
        ]
    )
    for index in duplicate_indexes
]


interactions_raw = (
    interaction_records
    + duplicate_records
)


# =========================================================
# SHUFFLE RAW DATA
# =========================================================

random.shuffle(
    interactions_raw
)


# =========================================================
# WRITE RAW CSV
# =========================================================

fieldnames = [
    "interaction_id",
    "account_id",
    "interaction_date",
    "interaction_type",
    "csm_name",
    "engagement_status",
    "follow_up_required",
    "notes_category",
    "next_follow_up_date",
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


    for record in interactions_raw:

        output_row = dict(
            record
        )


        output_row[
            "interaction_date"
        ] = record[
            "interaction_date"
        ].isoformat()


        if record[
            "next_follow_up_date"
        ] is None:

            output_row[
                "next_follow_up_date"
            ] = ""

        else:

            output_row[
                "next_follow_up_date"
            ] = record[
                "next_follow_up_date"
            ].isoformat()


        writer.writerow(
            output_row
        )


# =========================================================
# RAW DATA QUALITY COUNTS
# =========================================================

valid_types = set(
    INTERACTION_TYPES
)

valid_engagement = set(
    ENGAGEMENT_STATUSES
)

valid_notes = set(
    NOTES_CATEGORIES
)


dirty_type_count = sum(
    1
    for row in interactions_raw
    if row[
        "interaction_type"
    ] not in valid_types
)


dirty_engagement_count = sum(
    1
    for row in interactions_raw
    if row[
        "engagement_status"
    ] not in valid_engagement
)


dirty_followup_count = sum(
    1
    for row in interactions_raw
    if str(
        row[
            "follow_up_required"
        ]
    ).strip().lower()
    not in {
        "true",
        "false",
    }
)


dirty_notes_count = sum(
    1
    for row in interactions_raw
    if row[
        "notes_category"
    ] not in valid_notes
)


invalid_followup_date_count = sum(
    1
    for row in interactions_raw
    if (
        row[
            "next_follow_up_date"
        ] is not None
        and row[
            "next_follow_up_date"
        ] < row[
            "interaction_date"
        ]
    )
)


# =========================================================
# EXACT DUPLICATE COUNT
# =========================================================

seen_signatures = set()

exact_duplicate_count = 0


for row in interactions_raw:

    signature = tuple(
        str(
            row[
                field
            ]
        )
        for field in fieldnames
    )


    if signature in seen_signatures:

        exact_duplicate_count += 1

    else:

        seen_signatures.add(
            signature
        )


# =========================================================
# BASE ENGAGEMENT COUNTS
# =========================================================

engaged_count = sum(
    1
    for row in interaction_records
    if str(
        row[
            "engagement_status"
        ]
    ).strip().lower()
    == "engaged"
)


neutral_count = sum(
    1
    for row in interaction_records
    if str(
        row[
            "engagement_status"
        ]
    ).strip().lower()
    == "neutral"
)


unresponsive_count = sum(
    1
    for row in interaction_records
    if str(
        row[
            "engagement_status"
        ]
    ).strip().lower()
    == "unresponsive"
)


# =========================================================
# FOLLOW-UP COUNT
# =========================================================

follow_up_required_count = sum(
    1
    for row in interaction_records
    if (
        row[
            "follow_up_required"
        ] is True
    )
)


# =========================================================
# MISSING CSM COUNT
# =========================================================

missing_csm_count = sum(
    1
    for row in interaction_records
    if str(
        row[
            "csm_name"
        ]
    ).strip()
    == ""
)


# =========================================================
# PRINT SUMMARY
# =========================================================

print()

print(
    "=" * 65
)

print(
    "CLOUDPATH ANALYTICS - SYNTHETIC CUSTOMER SUCCESS INTERACTIONS"
)

print(
    "=" * 65
)

print(
    f"Customer accounts read: "
    f"{len(accounts)}"
)

print(
    f"Base interactions generated: "
    f"{base_row_count}"
)

print(
    f"Raw rows after duplicates: "
    f"{len(interactions_raw)}"
)

print(
    f"Exact duplicate rows: "
    f"{exact_duplicate_count}"
)

print()

print(
    f"Engaged interactions: "
    f"{engaged_count}"
)

print(
    f"Neutral interactions: "
    f"{neutral_count}"
)

print(
    f"Unresponsive interactions: "
    f"{unresponsive_count}"
)

print(
    f"Follow-up required interactions: "
    f"{follow_up_required_count}"
)

print(
    f"Interactions with missing CSM name: "
    f"{missing_csm_count}"
)

print()

print(
    f"Inconsistent interaction-type values: "
    f"{dirty_type_count}"
)

print(
    f"Inconsistent engagement-status values: "
    f"{dirty_engagement_count}"
)

print(
    f"Inconsistent follow-up boolean values: "
    f"{dirty_followup_count}"
)

print(
    f"Inconsistent notes-category values: "
    f"{dirty_notes_count}"
)

print(
    f"Follow-up dates before interaction dates: "
    f"{invalid_followup_date_count}"
)

print()

print(
    "Raw Customer Success interaction file created:"
)

print(
    OUTPUT_FILE
)

print(
    "=" * 65
)
