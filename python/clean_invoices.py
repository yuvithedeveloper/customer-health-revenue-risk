from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
import csv


# =========================================================
# PROJECT SETTINGS
# =========================================================

ANALYSIS_START = date(2025, 1, 1)
ANALYSIS_END = date(2026, 12, 31)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_INVOICE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "invoices_raw.csv"
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
    / "invoices.csv"
)

QUALITY_REPORT_FILE = (
    PROCESSED_DATA_DIR
    / "invoices_quality_report.txt"
)


# =========================================================
# EXPECTED SCHEMA
# =========================================================

EXPECTED_COLUMNS = [
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


VALID_STATUSES = {
    "Paid",
    "Late",
    "Pending",
    "Failed",
}


VALID_PAYMENT_METHODS = {
    "Credit Card",
    "ACH",
    "Wire Transfer",
}


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


def normalize_payment_status(value):

    cleaned_value = value.strip()

    mapping = {
        "paid": "Paid",
        "late": "Late",
        "pending": "Pending",
        "failed": "Failed",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_payment_method(value):

    cleaned_value = value.strip()

    if cleaned_value == "":
        return ""

    mapping = {
        "credit card": "Credit Card",
        "ach": "ACH",
        "wire transfer": "Wire Transfer",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
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
# READ RAW INVOICE DATA
# =========================================================

with RAW_INVOICE_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    if reader.fieldnames != EXPECTED_COLUMNS:

        raise ValueError(
            "Raw invoice columns do not "
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

raw_invalid_status = sum(
    1
    for row in raw_rows
    if row["payment_status"]
    not in VALID_STATUSES
)


raw_invalid_method = sum(
    1
    for row in raw_rows
    if (
        row["payment_method"].strip() != ""
        and row["payment_method"]
        not in VALID_PAYMENT_METHODS
    )
)


raw_missing_method = sum(
    1
    for row in raw_rows
    if row["payment_method"].strip() == ""
)


raw_negative_days_late = sum(
    1
    for row in raw_rows
    if int(
        row["days_late"]
    ) < 0
)


raw_invalid_payment_dates = sum(
    1
    for row in raw_rows
    if (
        row["payment_date"].strip() != ""
        and parse_date(
            row["payment_date"]
        )
        < parse_date(
            row["invoice_date"]
        )
    )
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
# CLEAN DATA
# =========================================================

cleaned_rows = []

corrected_statuses = 0
corrected_methods = 0
corrected_days_late = 0
corrected_payment_dates = 0


for row in deduplicated_rows:

    original_status = row[
        "payment_status"
    ]


    original_method = row[
        "payment_method"
    ]


    payment_status = (
        normalize_payment_status(
            original_status
        )
    )


    payment_method = (
        normalize_payment_method(
            original_method
        )
    )


    if payment_status != original_status:

        corrected_statuses += 1


    if (
        payment_method != original_method
        and original_method.strip() != ""
    ):

        corrected_methods += 1


    invoice_date = parse_date(
        row[
            "invoice_date"
        ]
    )


    due_date = parse_date(
        row[
            "due_date"
        ]
    )


    payment_date = parse_date(
        row[
            "payment_date"
        ]
    )


    days_late = int(
        row[
            "days_late"
        ]
    )


    # -----------------------------------------------------
    # FIX NEGATIVE DAYS LATE
    # -----------------------------------------------------

    if days_late < 0:

        days_late = abs(
            days_late
        )

        corrected_days_late += 1


    # -----------------------------------------------------
    # FIX PAYMENT DATES BEFORE INVOICE DATE
    # -----------------------------------------------------

    if (
        payment_date is not None
        and payment_date < invoice_date
    ):

        if payment_status == "Late":

            if days_late == 0:

                days_late = 1


            payment_date = (
                due_date
                + timedelta(
                    days=days_late
                )
            )


        else:

            payment_date = invoice_date

            if payment_status == "Paid":

                days_late = 0


        corrected_payment_dates += 1


    # -----------------------------------------------------
    # ALIGN LATE PAYMENT DAYS WITH PAYMENT DATE
    # -----------------------------------------------------

    if (
        payment_status == "Late"
        and payment_date is not None
    ):

        calculated_days_late = (
            payment_date
            - due_date
        ).days


        if calculated_days_late <= 0:

            calculated_days_late = max(
                1,
                days_late,
            )


            payment_date = (
                due_date
                + timedelta(
                    days=calculated_days_late
                )
            )


        days_late = (
            calculated_days_late
        )


    # -----------------------------------------------------
    # PAID INVOICES SHOULD HAVE ZERO DAYS LATE
    # -----------------------------------------------------

    if payment_status == "Paid":

        days_late = 0


    # -----------------------------------------------------
    # PENDING INVOICES SHOULD NOT HAVE PAYMENT DATE
    # -----------------------------------------------------

    if payment_status == "Pending":

        payment_date = None

        days_late = 0


    # -----------------------------------------------------
    # FAILED INVOICES HAVE NO SUCCESSFUL PAYMENT DATE
    # -----------------------------------------------------

    if payment_status == "Failed":

        payment_date = None

        days_late = max(
            1,
            days_late,
        )


    cleaned_row = {
        "invoice_id":
            row[
                "invoice_id"
            ].strip(),

        "account_id":
            row[
                "account_id"
            ].strip(),

        "invoice_date":
            invoice_date.isoformat(),

        "due_date":
            due_date.isoformat(),

        "payment_date":
            (
                ""
                if payment_date is None
                else payment_date.isoformat()
            ),

        "invoice_amount":
            row[
                "invoice_amount"
            ].strip(),

        "payment_status":
            payment_status,

        "days_late":
            str(
                days_late
            ),

        "payment_method":
            payment_method,
    }


    cleaned_rows.append(
        cleaned_row
    )


# =========================================================
# VALIDATION
# =========================================================

validation_errors = []

invoice_ids = set()


for row in cleaned_rows:

    invoice_id = row[
        "invoice_id"
    ]

    account_id = row[
        "account_id"
    ]


    # -----------------------------------------------------
    # UNIQUE INVOICE ID
    # -----------------------------------------------------

    if invoice_id in invoice_ids:

        validation_errors.append(
            f"Duplicate invoice_id: "
            f"{invoice_id}"
        )


    invoice_ids.add(
        invoice_id
    )


    # -----------------------------------------------------
    # ACCOUNT FOREIGN KEY
    # -----------------------------------------------------

    if account_id not in valid_account_ids:

        validation_errors.append(
            f"Invoice {invoice_id}: "
            f"account_id {account_id} "
            "does not exist"
        )

        continue


    # -----------------------------------------------------
    # STATUS VALIDATION
    # -----------------------------------------------------

    if (
        row["payment_status"]
        not in VALID_STATUSES
    ):

        validation_errors.append(
            f"Invoice {invoice_id}: "
            f"invalid payment status "
            f"{row['payment_status']}"
        )


    # -----------------------------------------------------
    # PAYMENT METHOD VALIDATION
    # Missing methods are allowed.
    # -----------------------------------------------------

    if (
        row["payment_method"] != ""
        and row["payment_method"]
        not in VALID_PAYMENT_METHODS
    ):

        validation_errors.append(
            f"Invoice {invoice_id}: "
            f"invalid payment method "
            f"{row['payment_method']}"
        )


    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    invoice_date = parse_date(
        row[
            "invoice_date"
        ]
    )


    due_date = parse_date(
        row[
            "due_date"
        ]
    )


    payment_date = parse_date(
        row[
            "payment_date"
        ]
    )


    if (
        invoice_date < ANALYSIS_START
        or invoice_date > ANALYSIS_END
    ):

        validation_errors.append(
            f"Invoice {invoice_id}: "
            "invoice date falls outside "
            "analysis period"
        )


    if due_date < invoice_date:

        validation_errors.append(
            f"Invoice {invoice_id}: "
            "due date occurs before "
            "invoice date"
        )


    if (
        payment_date is not None
        and payment_date < invoice_date
    ):

        validation_errors.append(
            f"Invoice {invoice_id}: "
            "payment date occurs before "
            "invoice date"
        )


    # -----------------------------------------------------
    # ACCOUNT LIFETIME VALIDATION
    # -----------------------------------------------------

    account = account_lookup[
        account_id
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


    if invoice_date < signup_date:

        validation_errors.append(
            f"Invoice {invoice_id}: "
            "invoice occurs before "
            "customer signup"
        )


    if (
        churn_date is not None
        and invoice_date > churn_date
    ):

        validation_errors.append(
            f"Invoice {invoice_id}: "
            "invoice occurs after churn"
        )


    # -----------------------------------------------------
    # INVOICE AMOUNT
    # -----------------------------------------------------

    try:

        invoice_amount = Decimal(
            row[
                "invoice_amount"
            ]
        )


        if invoice_amount <= 0:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "invoice amount must "
                "be greater than zero"
            )


    except InvalidOperation:

        validation_errors.append(
            f"Invoice {invoice_id}: "
            "invalid invoice amount"
        )


    # -----------------------------------------------------
    # DAYS LATE
    # -----------------------------------------------------

    days_late = int(
        row[
            "days_late"
        ]
    )


    if days_late < 0:

        validation_errors.append(
            f"Invoice {invoice_id}: "
            "days_late cannot be negative"
        )


    # -----------------------------------------------------
    # PAYMENT STATUS BUSINESS RULES
    # -----------------------------------------------------

    status = row[
        "payment_status"
    ]


    if status == "Paid":

        if payment_date is None:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Paid invoice is missing "
                "payment_date"
            )


        if days_late != 0:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Paid invoice should have "
                "days_late = 0"
            )


        if (
            payment_date is not None
            and payment_date > due_date
        ):

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Paid invoice has payment "
                "after due date"
            )


    elif status == "Late":

        if payment_date is None:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Late invoice is missing "
                "payment_date"
            )


        if days_late <= 0:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Late invoice must have "
                "days_late > 0"
            )


        if (
            payment_date is not None
            and payment_date <= due_date
        ):

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Late invoice must be paid "
                "after due date"
            )


        if (
            payment_date is not None
            and (
                payment_date
                - due_date
            ).days != days_late
        ):

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "days_late does not match "
                "payment date"
            )


    elif status == "Pending":

        if payment_date is not None:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Pending invoice should not "
                "have payment_date"
            )


        if days_late != 0:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Pending invoice should have "
                "days_late = 0"
            )


    elif status == "Failed":

        if payment_date is not None:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Failed invoice should not "
                "have successful payment_date"
            )


        if days_late <= 0:

            validation_errors.append(
                f"Invoice {invoice_id}: "
                "Failed invoice should have "
                "days_late > 0"
            )


# =========================================================
# STOP IF VALIDATION FAILS
# =========================================================

if validation_errors:

    print()

    print(
        "INVOICE VALIDATION ERRORS"
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
            "invoice_id"
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
# FINAL METRICS
# =========================================================

status_counts = {
    status: 0
    for status in VALID_STATUSES
}


for row in cleaned_rows:

    status_counts[
        row[
            "payment_status"
        ]
    ] += 1


accounts_with_invoices = {
    row["account_id"]
    for row in cleaned_rows
}


missing_payment_methods = sum(
    1
    for row in cleaned_rows
    if row[
        "payment_method"
    ] == ""
)


total_invoice_value = sum(
    Decimal(
        row[
            "invoice_amount"
        ]
    )
    for row in cleaned_rows
)


late_days = [
    int(
        row[
            "days_late"
        ]
    )
    for row in cleaned_rows
    if row[
        "payment_status"
    ] == "Late"
]


if late_days:

    average_days_late = (
        sum(
            late_days
        )
        / len(
            late_days
        )
    )

else:

    average_days_late = 0


# =========================================================
# FINAL QUALITY CHECK COUNTS
# =========================================================

clean_invalid_status = sum(
    1
    for row in cleaned_rows
    if row[
        "payment_status"
    ] not in VALID_STATUSES
)


clean_invalid_method = sum(
    1
    for row in cleaned_rows
    if (
        row[
            "payment_method"
        ] != ""
        and row[
            "payment_method"
        ] not in VALID_PAYMENT_METHODS
    )
)


clean_negative_days_late = sum(
    1
    for row in cleaned_rows
    if int(
        row[
            "days_late"
        ]
    ) < 0
)


clean_invalid_payment_dates = sum(
    1
    for row in cleaned_rows
    if (
        row[
            "payment_date"
        ] != ""
        and parse_date(
            row[
                "payment_date"
            ]
        )
        < parse_date(
            row[
                "invoice_date"
            ]
        )
    )
)


# =========================================================
# QUALITY REPORT
# =========================================================

report_lines = [
    "CLOUDPATH ANALYTICS - INVOICE DATA QUALITY REPORT",
    "=" * 65,
    "",
    "RAW DATA",
    f"Raw rows: {raw_row_count}",
    f"Exact duplicate rows: {exact_duplicate_count}",
    (
        "Inconsistent payment-status values: "
        f"{raw_invalid_status}"
    ),
    (
        "Inconsistent payment-method values: "
        f"{raw_invalid_method}"
    ),
    (
        "Missing payment-method values: "
        f"{raw_missing_method}"
    ),
    (
        "Negative days_late rows: "
        f"{raw_negative_days_late}"
    ),
    (
        "Payment dates before invoice dates: "
        f"{raw_invalid_payment_dates}"
    ),
    "",
    "CLEANED DATA",
    f"Clean rows: {len(cleaned_rows)}",
    f"Unique invoice IDs: {len(invoice_ids)}",
    (
        "Accounts with invoice records: "
        f"{len(accounts_with_invoices)}"
    ),
    f"Paid invoices: {status_counts['Paid']}",
    f"Late invoices: {status_counts['Late']}",
    f"Pending invoices: {status_counts['Pending']}",
    f"Failed invoices: {status_counts['Failed']}",
    (
        "Missing payment methods retained: "
        f"{missing_payment_methods}"
    ),
    (
        "Invalid payment statuses remaining: "
        f"{clean_invalid_status}"
    ),
    (
        "Invalid payment methods remaining: "
        f"{clean_invalid_method}"
    ),
    (
        "Negative days_late rows remaining: "
        f"{clean_negative_days_late}"
    ),
    (
        "Invalid payment dates remaining: "
        f"{clean_invalid_payment_dates}"
    ),
    (
        "Business rule violations: "
        f"{len(validation_errors)}"
    ),
    "",
    "PAYMENT METRICS",
    (
        "Total invoice value: "
        f"${total_invoice_value:,.2f}"
    ),
    (
        "Average days late for late invoices: "
        f"{average_days_late:.2f}"
    ),
    "",
    "CLEANING ACTIONS",
    "- Removed exact duplicate records",
    "- Standardized payment-status values",
    "- Standardized payment-method values",
    (
        "- Retained missing payment methods rather than "
        "inventing unavailable information"
    ),
    (
        "- Converted invalid negative days_late values "
        "to positive values"
    ),
    (
        "- Corrected payment dates that occurred before "
        "their invoice dates"
    ),
    (
        "- Recalculated days_late for late invoices "
        "from due and payment dates"
    ),
    "- Validated account foreign keys",
    "- Validated invoice and payment date logic",
    "- Validated invoice amounts",
    "- Validated payment-status business rules",
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
    "CLOUDPATH ANALYTICS - INVOICE DATA CLEANING"
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
    f"Unique invoice IDs: "
    f"{len(invoice_ids)}"
)

print(
    f"Accounts with invoices: "
    f"{len(accounts_with_invoices)}"
)

print()

print(
    f"Payment-status values corrected: "
    f"{corrected_statuses}"
)

print(
    f"Payment-method values corrected: "
    f"{corrected_methods}"
)

print(
    f"Negative days_late values corrected: "
    f"{corrected_days_late}"
)

print(
    f"Invalid payment dates corrected: "
    f"{corrected_payment_dates}"
)

print()

print(
    f"Paid invoices: "
    f"{status_counts['Paid']}"
)

print(
    f"Late invoices: "
    f"{status_counts['Late']}"
)

print(
    f"Pending invoices: "
    f"{status_counts['Pending']}"
)

print(
    f"Failed invoices: "
    f"{status_counts['Failed']}"
)

print()

print(
    f"Missing payment methods retained: "
    f"{missing_payment_methods}"
)

print(
    f"Total invoice value: "
    f"${total_invoice_value:,.2f}"
)

print(
    f"Average days late: "
    f"{average_days_late:.2f}"
)

print()

print(
    f"Invalid payment statuses remaining: "
    f"{clean_invalid_status}"
)

print(
    f"Invalid payment methods remaining: "
    f"{clean_invalid_method}"
)

print(
    f"Negative days_late rows remaining: "
    f"{clean_negative_days_late}"
)

print(
    f"Invalid payment dates remaining: "
    f"{clean_invalid_payment_dates}"
)

print(
    f"Business rule violations: "
    f"{len(validation_errors)}"
)

print()

print(
    "Processed invoice file:"
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
