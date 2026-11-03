from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import calendar
import csv
import random


# =========================================================
# PROJECT SETTINGS
# =========================================================

SEED = 210

ANALYSIS_START = date(2025, 1, 1)
ANALYSIS_END = date(2026, 12, 31)

DUPLICATE_ROWS = 20

DIRTY_STATUS_ROWS = 15
DIRTY_PAYMENT_METHOD_ROWS = 12
NEGATIVE_DAYS_LATE_ROWS = 8
INVALID_PAYMENT_DATE_ROWS = 6
MISSING_PAYMENT_METHOD_ROWS = 15


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

SUBSCRIPTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "subscriptions.csv"
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
    / "invoices_raw.csv"
)


# =========================================================
# VALID VALUES
# =========================================================

PAYMENT_STATUSES = [
    "Paid",
    "Late",
    "Pending",
    "Failed",
]

PAYMENT_METHODS = [
    "Credit Card",
    "ACH",
    "Wire Transfer",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def parse_date(value):
    """
    Convert YYYY-MM-DD text into a Python date.
    """

    cleaned_value = value.strip()

    if cleaned_value == "":
        return None

    return datetime.strptime(
        cleaned_value,
        "%Y-%m-%d",
    ).date()


def add_months(
    original_date,
    months,
):
    """
    Add months while preserving the day where possible.
    """

    month_index = (
        original_date.month
        - 1
        + months
    )

    year = (
        original_date.year
        + month_index // 12
    )

    month = (
        month_index % 12
        + 1
    )

    last_day = calendar.monthrange(
        year,
        month,
    )[1]

    day = min(
        original_date.day,
        last_day,
    )

    return date(
        year,
        month,
        day,
    )


def build_monthly_invoice_dates(
    subscription_start,
    subscription_end,
):
    """
    Create monthly billing dates during a
    subscription period.
    """

    invoice_dates = []

    month_offset = 0

    while True:

        invoice_date = add_months(
            subscription_start,
            month_offset,
        )

        if invoice_date > subscription_end:

            break

        invoice_dates.append(
            invoice_date
        )

        month_offset += 1

    return invoice_dates


def choose_payment_method(
    segment,
    rng,
):
    """
    Payment method varies somewhat by customer segment.
    """

    if segment == "SMB":

        return rng.choices(
            PAYMENT_METHODS,
            weights=[
                70,
                25,
                5,
            ],
            k=1,
        )[0]

    if segment == "Mid-Market":

        return rng.choices(
            PAYMENT_METHODS,
            weights=[
                40,
                50,
                10,
            ],
            k=1,
        )[0]

    return rng.choices(
        PAYMENT_METHODS,
        weights=[
            15,
            55,
            30,
        ],
        k=1,
    )[0]


def calculate_due_date(
    invoice_date,
    segment,
):
    """
    Use realistic synthetic payment terms.
    """

    if segment == "SMB":

        payment_terms_days = 15

    else:

        payment_terms_days = 30

    return (
        invoice_date
        + timedelta(
            days=payment_terms_days
        )
    )


def determine_payment(
    invoice_date,
    due_date,
    segment,
    churn_date,
    rng,
):
    """
    Generate payment behavior.

    Payment problems are somewhat more common
    near churn, but the relationship is intentionally
    imperfect.
    """

    near_churn = False

    if churn_date is not None:

        days_to_churn = (
            churn_date
            - invoice_date
        ).days

        if (
            0
            <= days_to_churn
            <= 120
        ):

            near_churn = True


    # -----------------------------------------------------
    # FUTURE-DUE INVOICES REMAIN PENDING
    # -----------------------------------------------------

    if due_date > ANALYSIS_END:

        return (
            "Pending",
            None,
            0,
        )


    # -----------------------------------------------------
    # BASE FAILURE / LATE PROBABILITIES
    # -----------------------------------------------------

    if segment == "SMB":

        failed_probability = 0.030
        late_probability = 0.150

    elif segment == "Mid-Market":

        failed_probability = 0.022
        late_probability = 0.120

    else:

        failed_probability = 0.015
        late_probability = 0.090


    # -----------------------------------------------------
    # PAYMENT RISK INCREASES SOMEWHAT NEAR CHURN
    # -----------------------------------------------------

    if near_churn:

        failed_probability *= 2.50
        late_probability *= 1.80


    random_value = rng.random()


    # -----------------------------------------------------
    # FAILED PAYMENT
    # -----------------------------------------------------

    if random_value < failed_probability:

        days_late = rng.randint(
            5,
            60,
        )

        return (
            "Failed",
            None,
            days_late,
        )


    # -----------------------------------------------------
    # LATE PAYMENT
    # -----------------------------------------------------

    if (
        random_value
        < failed_probability
        + late_probability
    ):

        if near_churn:

            delay_days = rng.randint(
                5,
                45,
            )

        else:

            delay_days = rng.randint(
                1,
                25,
            )


        payment_date = (
            due_date
            + timedelta(
                days=delay_days
            )
        )


        # Payment cannot be observed after the analysis date.
        if payment_date > ANALYSIS_END:

            days_past_due = max(
                1,
                (
                    ANALYSIS_END
                    - due_date
                ).days,
            )

            return (
                "Failed",
                None,
                days_past_due,
            )


        return (
            "Late",
            payment_date,
            delay_days,
        )


    # -----------------------------------------------------
    # ON-TIME PAYMENT
    # -----------------------------------------------------

    available_days = max(
        0,
        (
            due_date
            - invoice_date
        ).days,
    )


    payment_date = (
        invoice_date
        + timedelta(
            days=rng.randint(
                0,
                available_days,
            )
        )
    )


    return (
        "Paid",
        payment_date,
        0,
    )


def format_money(value):
    """
    Format Decimal values to two decimal places.
    """

    return str(
        value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )


# =========================================================
# READ CLEAN ACCOUNTS
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


account_lookup = {
    row["account_id"].strip(): row
    for row in accounts
}


# =========================================================
# READ CLEAN SUBSCRIPTIONS
# =========================================================

with SUBSCRIPTIONS_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    subscriptions = list(
        reader
    )


# =========================================================
# GENERATE INVOICES
# =========================================================

invoice_records = []

invoice_id = 1


for subscription in subscriptions:

    account_id = subscription[
        "account_id"
    ].strip()


    account = account_lookup[
        account_id
    ]


    segment = account[
        "segment"
    ]


    churn_date = parse_date(
        account[
            "churn_date"
        ]
    )


    subscription_start = parse_date(
        subscription[
            "subscription_start_date"
        ]
    )


    subscription_end = parse_date(
        subscription[
            "subscription_end_date"
        ]
    )


    billing_frequency = subscription[
        "billing_frequency"
    ]


    mrr = Decimal(
        subscription[
            "mrr"
        ]
    )


    account_rng = random.Random(
        SEED
        + (
            int(
                account_id
            )
            * 173
        )
        + (
            int(
                subscription[
                    "subscription_id"
                ]
            )
            * 19
        )
    )


    # -----------------------------------------------------
    # BUILD INVOICE DATES
    # -----------------------------------------------------

    if billing_frequency == "Monthly":

        invoice_dates = (
            build_monthly_invoice_dates(
                subscription_start,
                subscription_end,
            )
        )

        invoice_amount = mrr


    else:

        invoice_dates = [
            subscription_start
        ]

        invoice_amount = (
            mrr
            * Decimal("12")
        )


    # -----------------------------------------------------
    # CREATE EACH INVOICE
    # -----------------------------------------------------

    for invoice_date in invoice_dates:

        if invoice_date < ANALYSIS_START:

            continue


        if invoice_date > ANALYSIS_END:

            continue


        due_date = calculate_due_date(
            invoice_date,
            segment,
        )


        payment_status, payment_date, days_late = (
            determine_payment(
                invoice_date,
                due_date,
                segment,
                churn_date,
                account_rng,
            )
        )


        payment_method = choose_payment_method(
            segment,
            account_rng,
        )


        invoice_record = {
            "invoice_id":
                invoice_id,

            "account_id":
                int(
                    account_id
                ),

            "invoice_date":
                invoice_date,

            "due_date":
                due_date,

            "payment_date":
                payment_date,

            "invoice_amount":
                format_money(
                    invoice_amount
                ),

            "payment_status":
                payment_status,

            "days_late":
                days_late,

            "payment_method":
                payment_method,
        }


        invoice_records.append(
            invoice_record
        )


        invoice_id += 1


# =========================================================
# BASE COUNTS
# =========================================================

base_row_count = len(
    invoice_records
)


# =========================================================
# INTENTIONAL RAW DATA QUALITY ISSUES
# =========================================================

# ---------------------------------------------------------
# DIRTY PAYMENT STATUS
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


status_variants = {
    "Paid": "paid",
    "Late": "Late ",
    "Pending": "PENDING",
    "Failed": "failed",
}


for index in status_indexes:

    current_status = invoice_records[
        index
    ][
        "payment_status"
    ]


    invoice_records[index][
        "payment_status"
    ] = status_variants[
        current_status
    ]


# ---------------------------------------------------------
# DIRTY PAYMENT METHODS
# ---------------------------------------------------------

method_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        DIRTY_PAYMENT_METHOD_ROWS,
        base_row_count,
    ),
)


method_variants = {
    "Credit Card": "credit card",
    "ACH": "ACH ",
    "Wire Transfer": "wire transfer",
}


for index in method_indexes:

    current_method = invoice_records[
        index
    ][
        "payment_method"
    ]


    invoice_records[index][
        "payment_method"
    ] = method_variants[
        current_method
    ]


# ---------------------------------------------------------
# MISSING PAYMENT METHODS
# ---------------------------------------------------------

missing_method_indexes = random.sample(
    range(
        base_row_count
    ),
    min(
        MISSING_PAYMENT_METHOD_ROWS,
        base_row_count,
    ),
)


for index in missing_method_indexes:

    invoice_records[index][
        "payment_method"
    ] = ""


# ---------------------------------------------------------
# NEGATIVE DAYS LATE
# ---------------------------------------------------------

late_eligible_indexes = [
    index
    for index, row in enumerate(
        invoice_records
    )
    if int(
        row[
            "days_late"
        ]
    ) > 0
]


negative_days_indexes = random.sample(
    late_eligible_indexes,
    min(
        NEGATIVE_DAYS_LATE_ROWS,
        len(
            late_eligible_indexes
        ),
    ),
)


for index in negative_days_indexes:

    invoice_records[index][
        "days_late"
    ] = -abs(
        int(
            invoice_records[index][
                "days_late"
            ]
        )
    )


# ---------------------------------------------------------
# INVALID PAYMENT DATES BEFORE INVOICE DATE
# ---------------------------------------------------------

payment_date_eligible_indexes = [
    index
    for index, row in enumerate(
        invoice_records
    )
    if row[
        "payment_date"
    ] is not None
]


invalid_payment_date_indexes = random.sample(
    payment_date_eligible_indexes,
    min(
        INVALID_PAYMENT_DATE_ROWS,
        len(
            payment_date_eligible_indexes
        ),
    ),
)


for index in invalid_payment_date_indexes:

    invoice_date = invoice_records[
        index
    ][
        "invoice_date"
    ]


    invoice_records[index][
        "payment_date"
    ] = (
        invoice_date
        - timedelta(
            days=random.randint(
                1,
                5,
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
        invoice_records[
            index
        ]
    )
    for index in duplicate_indexes
]


invoices_raw = (
    invoice_records
    + duplicate_records
)


# =========================================================
# SHUFFLE RAW DATA
# =========================================================

random.shuffle(
    invoices_raw
)


# =========================================================
# WRITE RAW CSV
# =========================================================

fieldnames = [
    "invoice_id",
    "account_id",
    "invoice_date",
    "due_date",
    "payment_date",
    "invoice_amount",
    "payment_status",
    "days_late",
    "payment_method",
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


    for record in invoices_raw:

        output_row = dict(
            record
        )


        output_row[
            "invoice_date"
        ] = record[
            "invoice_date"
        ].isoformat()


        output_row[
            "due_date"
        ] = record[
            "due_date"
        ].isoformat()


        if record[
            "payment_date"
        ] is None:

            output_row[
                "payment_date"
            ] = ""

        else:

            output_row[
                "payment_date"
            ] = record[
                "payment_date"
            ].isoformat()


        writer.writerow(
            output_row
        )


# =========================================================
# RAW DATA QUALITY COUNTS
# =========================================================

valid_statuses = set(
    PAYMENT_STATUSES
)


dirty_status_count = sum(
    1
    for row in invoices_raw
    if row[
        "payment_status"
    ] not in valid_statuses
)


valid_methods = set(
    PAYMENT_METHODS
)


dirty_method_count = sum(
    1
    for row in invoices_raw
    if (
        row[
            "payment_method"
        ] != ""
        and row[
            "payment_method"
        ] not in valid_methods
    )
)


missing_method_count = sum(
    1
    for row in invoices_raw
    if row[
        "payment_method"
    ] == ""
)


negative_days_late_count = sum(
    1
    for row in invoices_raw
    if int(
        row[
            "days_late"
        ]
    ) < 0
)


invalid_payment_date_count = sum(
    1
    for row in invoices_raw
    if (
        row[
            "payment_date"
        ] is not None
        and row[
            "payment_date"
        ] < row[
            "invoice_date"
        ]
    )
)


# =========================================================
# EXACT DUPLICATE COUNT
# =========================================================

seen_signatures = set()

exact_duplicate_count = 0


for row in invoices_raw:

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
# BASE PAYMENT STATUS COUNTS
# =========================================================

paid_count = sum(
    1
    for row in invoice_records
    if str(
        row[
            "payment_status"
        ]
    ).strip().lower()
    == "paid"
)


late_count = sum(
    1
    for row in invoice_records
    if str(
        row[
            "payment_status"
        ]
    ).strip().lower()
    == "late"
)


pending_count = sum(
    1
    for row in invoice_records
    if str(
        row[
            "payment_status"
        ]
    ).strip().lower()
    == "pending"
)


failed_count = sum(
    1
    for row in invoice_records
    if str(
        row[
            "payment_status"
        ]
    ).strip().lower()
    == "failed"
)


# =========================================================
# BASE INVOICE VALUE
# =========================================================

total_invoice_value = sum(
    Decimal(
        row[
            "invoice_amount"
        ]
    )
    for row in invoice_records
)


# =========================================================
# PRINT SUMMARY
# =========================================================

print()

print(
    "=" * 65
)

print(
    "CLOUDPATH ANALYTICS - SYNTHETIC INVOICE DATA"
)

print(
    "=" * 65
)

print(
    f"Customer accounts read: "
    f"{len(accounts)}"
)

print(
    f"Subscription periods read: "
    f"{len(subscriptions)}"
)

print(
    f"Base invoices generated: "
    f"{base_row_count}"
)

print(
    f"Raw rows after duplicates: "
    f"{len(invoices_raw)}"
)

print(
    f"Exact duplicate rows: "
    f"{exact_duplicate_count}"
)

print()

print(
    f"Paid invoices: "
    f"{paid_count}"
)

print(
    f"Late invoices: "
    f"{late_count}"
)

print(
    f"Pending invoices: "
    f"{pending_count}"
)

print(
    f"Failed invoices: "
    f"{failed_count}"
)

print()

print(
    f"Total base invoice value: "
    f"${total_invoice_value:,.2f}"
)

print()

print(
    f"Inconsistent payment-status values: "
    f"{dirty_status_count}"
)

print(
    f"Inconsistent payment-method values: "
    f"{dirty_method_count}"
)

print(
    f"Missing payment-method values: "
    f"{missing_method_count}"
)

print(
    f"Negative days_late rows: "
    f"{negative_days_late_count}"
)

print(
    f"Payment dates before invoice dates: "
    f"{invalid_payment_date_count}"
)

print()

print(
    "Raw invoice file created:"
)

print(
    OUTPUT_FILE
)

print(
    "=" * 65
)
