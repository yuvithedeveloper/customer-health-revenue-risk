from pathlib import Path
from datetime import datetime, date, timedelta
import calendar
import csv
import random


# =========================================================
# PROJECT SETTINGS
# =========================================================

SEED = 168

ANALYSIS_START = date(2025, 1, 1)
ANALYSIS_END = date(2026, 12, 31)

DUPLICATE_ROWS = 15
INVALID_RESOLUTION_ROWS = 8
INVALID_CSAT_ROWS = 7
DIRTY_PRIORITY_ROWS = 12
DIRTY_STATUS_ROWS = 12
DIRTY_CATEGORY_ROWS = 10


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
    / "support_tickets_raw.csv"
)


# =========================================================
# VALID VALUES
# =========================================================

PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

CATEGORIES = [
    "Login/Access",
    "Data Integration",
    "Dashboard/Reporting",
    "Performance",
    "Billing",
    "Feature Question",
    "Bug",
]

STATUSES = [
    "Open",
    "In Progress",
    "Resolved",
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

    last_day = calendar.monthrange(
        value.year,
        value.month,
    )[1]

    return date(
        value.year,
        value.month,
        last_day,
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

    day_range = (
        end_date
        - start_date
    ).days

    return (
        start_date
        + timedelta(
            days=rng.randint(
                0,
                day_range,
            )
        )
    )


def ticket_count_from_rate(
    rate,
    rng,
):
    """
    Convert a monthly expected ticket rate
    into a small integer count.
    """

    whole_tickets = int(
        rate
    )

    fractional_part = (
        rate
        - whole_tickets
    )

    ticket_count = (
        whole_tickets
    )

    if rng.random() < fractional_part:

        ticket_count += 1

    return ticket_count


def choose_priority(
    low_usage,
    near_churn,
    rng,
):

    if near_churn:

        weights = [
            12,
            40,
            35,
            13,
        ]

    elif low_usage:

        weights = [
            18,
            48,
            28,
            6,
        ]

    else:

        weights = [
            30,
            50,
            17,
            3,
        ]

    return rng.choices(
        PRIORITIES,
        weights=weights,
        k=1,
    )[0]


def choose_category(
    rng,
):

    return rng.choices(
        CATEGORIES,
        weights=[
            14,
            20,
            20,
            14,
            8,
            12,
            12,
        ],
        k=1,
    )[0]


def base_resolution_hours(
    priority,
    rng,
):

    if priority == "Low":

        return rng.uniform(
            8,
            72,
        )

    if priority == "Medium":

        return rng.uniform(
            4,
            48,
        )

    if priority == "High":

        return rng.uniform(
            2,
            24,
        )

    return rng.uniform(
        1,
        12,
    )


def choose_csat(
    priority,
    resolution_hours,
    rng,
):

    if rng.random() < 0.15:

        return ""

    score = 5

    if resolution_hours > 48:

        score -= 2

    elif resolution_hours > 24:

        score -= 1

    if priority == "Critical":

        score -= 1

    score += rng.choice(
        [
            -1,
            0,
            0,
            0,
            1,
        ]
    )

    score = max(
        1,
        min(
            5,
            score,
        ),
    )

    return score


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
# BUILD USAGE LOOKUP
# =========================================================

usage_lookup = {}


for row in usage_rows:

    key = (
        int(
            row["account_id"]
        ),
        row["usage_month"],
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

    usage_lookup[
        key
    ] = active_ratio


# =========================================================
# GENERATE SUPPORT TICKETS
# =========================================================

support_records = []

ticket_id = 1

support_spike_months = 0


for account in accounts:

    account_id = int(
        account[
            "account_id"
        ]
    )

    segment = account[
        "segment"
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


    account_rng = random.Random(
        SEED
        + (
            account_id
            * 149
        )
    )


    # -----------------------------------------------------
    # SUPPORT HISTORY RANGE
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


    start_month_value = month_start(
        start_date
    )

    end_month_value = month_start(
        end_date
    )


    months = build_month_range(
        start_month_value,
        end_month_value,
    )


    # -----------------------------------------------------
    # BASE MONTHLY SUPPORT RATE BY SEGMENT
    # -----------------------------------------------------

    if segment == "SMB":

        base_rate = 0.24

    elif segment == "Mid-Market":

        base_rate = 0.42

    else:

        base_rate = 0.72


    # -----------------------------------------------------
    # MONTH-BY-MONTH TICKET GENERATION
    # -----------------------------------------------------

    for usage_month in months:

        usage_key = (
            account_id,
            usage_month.isoformat(),
        )


        active_ratio = usage_lookup.get(
            usage_key,
            0.60,
        )


        low_usage = (
            active_ratio < 0.45
        )


        near_churn = False


        if churn_date is not None:

            days_to_churn = (
                churn_date
                - usage_month
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

            monthly_rate *= 1.35


        if near_churn:

            monthly_rate *= 1.50


        # -------------------------------------------------
        # OCCASIONAL SUPPORT INCIDENT / SPIKE
        # -------------------------------------------------

        support_spike = (
            account_rng.random()
            < 0.025
        )


        if support_spike:

            monthly_rate += (
                account_rng.uniform(
                    1.5,
                    3.0,
                )
            )

            support_spike_months += 1


        ticket_count = ticket_count_from_rate(
            monthly_rate,
            account_rng,
        )


        # -------------------------------------------------
        # GENERATE INDIVIDUAL TICKETS
        # -------------------------------------------------

        for _ in range(
            ticket_count
        ):

            valid_start = max(
                usage_month,
                start_date,
            )


            valid_end = min(
                month_end(
                    usage_month
                ),
                end_date,
            )


            if valid_start > valid_end:

                continue


            created_date = random_date_between(
                valid_start,
                valid_end,
                account_rng,
            )


            priority = choose_priority(
                low_usage,
                near_churn,
                account_rng,
            )


            category = choose_category(
                account_rng
            )


            # ---------------------------------------------
            # MORE RECENT TICKETS CAN REMAIN UNRESOLVED
            # ---------------------------------------------

            days_from_analysis_end = (
                ANALYSIS_END
                - created_date
            ).days


            if days_from_analysis_end <= 30:

                status = account_rng.choices(
                    STATUSES,
                    weights=[
                        15,
                        20,
                        65,
                    ],
                    k=1,
                )[0]

            else:

                status = account_rng.choices(
                    STATUSES,
                    weights=[
                        3,
                        5,
                        92,
                    ],
                    k=1,
                )[0]


            if status == "Resolved":

                resolution_hours = (
                    base_resolution_hours(
                        priority,
                        account_rng,
                    )
                )


                if support_spike:

                    resolution_hours *= (
                        account_rng.uniform(
                            1.15,
                            1.60,
                        )
                    )


                resolution_hours = round(
                    resolution_hours,
                    2,
                )


                resolution_days = max(
                    1,
                    int(
                        resolution_hours
                        / 24
                    ),
                )


                resolved_date = (
                    created_date
                    + timedelta(
                        days=resolution_days
                    )
                )


                if resolved_date > ANALYSIS_END:

                    status = "In Progress"

                    resolved_date = None

                    resolution_hours = ""

                    csat = ""

                else:

                    csat = choose_csat(
                        priority,
                        resolution_hours,
                        account_rng,
                    )


            else:

                resolved_date = None

                resolution_hours = ""

                csat = ""


            support_record = {
                "ticket_id":
                    ticket_id,

                "account_id":
                    account_id,

                "created_date":
                    created_date,

                "resolved_date":
                    resolved_date,

                "priority":
                    priority,

                "category":
                    category,

                "ticket_status":
                    status,

                "resolution_hours":
                    resolution_hours,

                "customer_satisfaction_score":
                    csat,
            }


            support_records.append(
                support_record
            )


            ticket_id += 1


# =========================================================
# INTENTIONAL RAW-DATA QUALITY ISSUES
# =========================================================

base_row_count = len(
    support_records
)


# ---------------------------------------------------------
# NEGATIVE RESOLUTION HOURS
# ---------------------------------------------------------

resolved_indexes = [
    index
    for index, row in enumerate(
        support_records
    )
    if row["ticket_status"] == "Resolved"
]


negative_resolution_indexes = random.sample(
    resolved_indexes,
    min(
        INVALID_RESOLUTION_ROWS,
        len(
            resolved_indexes
        ),
    ),
)


for index in negative_resolution_indexes:

    support_records[index][
        "resolution_hours"
    ] = -round(
        random.uniform(
            1,
            24,
        ),
        2,
    )


# ---------------------------------------------------------
# INVALID CSAT VALUES
# ---------------------------------------------------------

csat_indexes = [
    index
    for index, row in enumerate(
        support_records
    )
    if row[
        "customer_satisfaction_score"
    ] != ""
]


invalid_csat_indexes = random.sample(
    csat_indexes,
    min(
        INVALID_CSAT_ROWS,
        len(
            csat_indexes
        ),
    ),
)


for index in invalid_csat_indexes:

    support_records[index][
        "customer_satisfaction_score"
    ] = random.choice(
        [
            0,
            6,
        ]
    )


# ---------------------------------------------------------
# DIRTY PRIORITY VALUES
# ---------------------------------------------------------

priority_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_PRIORITY_ROWS,
        base_row_count,
    ),
)


for index in priority_indexes:

    current_value = support_records[
        index
    ][
        "priority"
    ]


    variants = {
        "Low": "low",
        "Medium": "Medium ",
        "High": "HIGH",
        "Critical": "critical",
    }


    support_records[index][
        "priority"
    ] = variants[
        current_value
    ]


# ---------------------------------------------------------
# DIRTY STATUS VALUES
# ---------------------------------------------------------

status_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_STATUS_ROWS,
        base_row_count,
    ),
)


for index in status_indexes:

    current_value = support_records[
        index
    ][
        "ticket_status"
    ]


    variants = {
        "Open": "open",
        "In Progress": "In progress ",
        "Resolved": "RESOLVED",
    }


    support_records[index][
        "ticket_status"
    ] = variants[
        current_value
    ]


# ---------------------------------------------------------
# DIRTY CATEGORY VALUES
# ---------------------------------------------------------

category_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_CATEGORY_ROWS,
        base_row_count,
    ),
)


for index in category_indexes:

    current_value = support_records[
        index
    ][
        "category"
    ]


    support_records[index][
        "category"
    ] = (
        current_value.lower()
        if random.random() < 0.5
        else current_value + " "
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
        support_records[
            index
        ]
    )
    for index in duplicate_indexes
]


support_tickets_raw = (
    support_records
    + duplicate_records
)


# =========================================================
# SHUFFLE RAW DATA
# =========================================================

random.shuffle(
    support_tickets_raw
)


# =========================================================
# WRITE RAW CSV
# =========================================================

fieldnames = [
    "ticket_id",
    "account_id",
    "created_date",
    "resolved_date",
    "priority",
    "category",
    "ticket_status",
    "resolution_hours",
    "customer_satisfaction_score",
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


    for record in support_tickets_raw:

        output_row = dict(
            record
        )


        output_row[
            "created_date"
        ] = record[
            "created_date"
        ].isoformat()


        if record[
            "resolved_date"
        ] is None:

            output_row[
                "resolved_date"
            ] = ""

        else:

            output_row[
                "resolved_date"
            ] = record[
                "resolved_date"
            ].isoformat()


        writer.writerow(
            output_row
        )


# =========================================================
# RAW DATA QUALITY SUMMARY
# =========================================================

valid_priorities = set(
    PRIORITIES
)

valid_statuses = set(
    STATUSES
)

valid_categories = set(
    CATEGORIES
)


dirty_priority_count = sum(
    1
    for row in support_tickets_raw
    if row["priority"]
    not in valid_priorities
)


dirty_status_count = sum(
    1
    for row in support_tickets_raw
    if row["ticket_status"]
    not in valid_statuses
)


dirty_category_count = sum(
    1
    for row in support_tickets_raw
    if row["category"]
    not in valid_categories
)


negative_resolution_count = sum(
    1
    for row in support_tickets_raw
    if (
        row["resolution_hours"] != ""
        and float(
            row["resolution_hours"]
        ) < 0
    )
)


invalid_csat_count = sum(
    1
    for row in support_tickets_raw
    if (
        row[
            "customer_satisfaction_score"
        ] != ""
        and (
            int(
                row[
                    "customer_satisfaction_score"
                ]
            ) < 1
            or int(
                row[
                    "customer_satisfaction_score"
                ]
            ) > 5
        )
    )
)


seen_signatures = set()

exact_duplicate_count = 0


for row in support_tickets_raw:

    signature = tuple(
        str(
            row[field]
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
# STATUS COUNTS
# =========================================================

base_resolved = sum(
    1
    for row in support_records
    if str(
        row["ticket_status"]
    ).strip().lower()
    == "resolved"
)


base_open_or_progress = (
    base_row_count
    - base_resolved
)


# =========================================================
# PRINT SUMMARY
# =========================================================

print()

print(
    "=" * 65
)

print(
    "CLOUDPATH ANALYTICS - SYNTHETIC SUPPORT TICKET DATA"
)

print(
    "=" * 65
)

print(
    f"Customer accounts read: "
    f"{len(accounts)}"
)

print(
    f"Base support tickets: "
    f"{base_row_count}"
)

print(
    f"Raw rows after duplicates: "
    f"{len(support_tickets_raw)}"
)

print(
    f"Exact duplicate rows: "
    f"{exact_duplicate_count}"
)

print()

print(
    f"Resolved tickets: "
    f"{base_resolved}"
)

print(
    f"Open / In Progress tickets: "
    f"{base_open_or_progress}"
)

print(
    f"Support spike months generated: "
    f"{support_spike_months}"
)

print()

print(
    f"Inconsistent priority values: "
    f"{dirty_priority_count}"
)

print(
    f"Inconsistent status values: "
    f"{dirty_status_count}"
)

print(
    f"Inconsistent category values: "
    f"{dirty_category_count}"
)

print(
    f"Negative resolution-hour rows: "
    f"{negative_resolution_count}"
)

print(
    f"Invalid CSAT rows: "
    f"{invalid_csat_count}"
)

print()

print(
    "Raw support ticket file created:"
)

print(
    OUTPUT_FILE
)

print(
    "=" * 65
)
