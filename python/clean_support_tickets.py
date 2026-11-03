from pathlib import Path
from datetime import datetime, date
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

RAW_SUPPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "support_tickets_raw.csv"
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
    / "support_tickets.csv"
)

QUALITY_REPORT_FILE = (
    PROCESSED_DATA_DIR
    / "support_tickets_quality_report.txt"
)


# =========================================================
# EXPECTED SCHEMA
# =========================================================

EXPECTED_COLUMNS = [
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


VALID_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Critical",
}


VALID_CATEGORIES = {
    "Login/Access",
    "Data Integration",
    "Dashboard/Reporting",
    "Performance",
    "Billing",
    "Feature Question",
    "Bug",
}


VALID_STATUSES = {
    "Open",
    "In Progress",
    "Resolved",
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


def normalize_priority(value):

    cleaned_value = value.strip()

    mapping = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_status(value):

    cleaned_value = value.strip()

    mapping = {
        "open": "Open",
        "in progress": "In Progress",
        "resolved": "Resolved",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_category(value):

    cleaned_value = value.strip()

    mapping = {
        "login/access":
            "Login/Access",

        "data integration":
            "Data Integration",

        "dashboard/reporting":
            "Dashboard/Reporting",

        "performance":
            "Performance",

        "billing":
            "Billing",

        "feature question":
            "Feature Question",

        "bug":
            "Bug",
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
# READ RAW SUPPORT DATA
# =========================================================

with RAW_SUPPORT_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    if reader.fieldnames != EXPECTED_COLUMNS:

        raise ValueError(
            "Raw support ticket columns do not "
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

raw_invalid_priority = sum(
    1
    for row in raw_rows
    if row["priority"]
    not in VALID_PRIORITIES
)


raw_invalid_category = sum(
    1
    for row in raw_rows
    if row["category"]
    not in VALID_CATEGORIES
)


raw_invalid_status = sum(
    1
    for row in raw_rows
    if row["ticket_status"]
    not in VALID_STATUSES
)


raw_negative_resolution = sum(
    1
    for row in raw_rows
    if (
        row["resolution_hours"].strip()
        != ""
        and float(
            row["resolution_hours"]
        ) < 0
    )
)


raw_invalid_csat = sum(
    1
    for row in raw_rows
    if (
        row[
            "customer_satisfaction_score"
        ].strip()
        != ""
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

corrected_priorities = 0
corrected_categories = 0
corrected_statuses = 0
corrected_resolution_hours = 0
corrected_csat = 0


for row in deduplicated_rows:

    original_priority = (
        row["priority"]
    )

    original_category = (
        row["category"]
    )

    original_status = (
        row["ticket_status"]
    )


    priority = normalize_priority(
        original_priority
    )


    category = normalize_category(
        original_category
    )


    ticket_status = normalize_status(
        original_status
    )


    if priority != original_priority:

        corrected_priorities += 1


    if category != original_category:

        corrected_categories += 1


    if ticket_status != original_status:

        corrected_statuses += 1


    resolution_value = (
        row[
            "resolution_hours"
        ].strip()
    )


    if resolution_value == "":

        resolution_hours = ""

    else:

        resolution_hours = float(
            resolution_value
        )


        if resolution_hours < 0:

            resolution_hours = abs(
                resolution_hours
            )

            corrected_resolution_hours += 1


        resolution_hours = round(
            resolution_hours,
            2,
        )


    csat_value = (
        row[
            "customer_satisfaction_score"
        ].strip()
    )


    if csat_value == "":

        csat = ""

    else:

        csat = int(
            csat_value
        )


        if csat < 1:

            csat = 1

            corrected_csat += 1


        elif csat > 5:

            csat = 5

            corrected_csat += 1


    cleaned_row = {
        "ticket_id":
            row[
                "ticket_id"
            ].strip(),

        "account_id":
            row[
                "account_id"
            ].strip(),

        "created_date":
            row[
                "created_date"
            ].strip(),

        "resolved_date":
            row[
                "resolved_date"
            ].strip(),

        "priority":
            priority,

        "category":
            category,

        "ticket_status":
            ticket_status,

        "resolution_hours":
            (
                ""
                if resolution_hours == ""
                else f"{resolution_hours:.2f}"
            ),

        "customer_satisfaction_score":
            (
                ""
                if csat == ""
                else str(csat)
            ),
    }


    cleaned_rows.append(
        cleaned_row
    )


# =========================================================
# VALIDATION
# =========================================================

validation_errors = []

ticket_ids = set()


for row in cleaned_rows:

    ticket_id = row[
        "ticket_id"
    ]

    account_id = row[
        "account_id"
    ]


    # -----------------------------------------------------
    # UNIQUE TICKET ID
    # -----------------------------------------------------

    if ticket_id in ticket_ids:

        validation_errors.append(
            f"Duplicate ticket_id: "
            f"{ticket_id}"
        )


    ticket_ids.add(
        ticket_id
    )


    # -----------------------------------------------------
    # ACCOUNT FOREIGN KEY
    # -----------------------------------------------------

    if account_id not in valid_account_ids:

        validation_errors.append(
            f"Ticket {ticket_id}: "
            f"account_id {account_id} "
            "does not exist"
        )

        continue


    # -----------------------------------------------------
    # VALID CATEGORY VALUES
    # -----------------------------------------------------

    if row["priority"] not in VALID_PRIORITIES:

        validation_errors.append(
            f"Ticket {ticket_id}: "
            f"invalid priority "
            f"{row['priority']}"
        )


    if row["category"] not in VALID_CATEGORIES:

        validation_errors.append(
            f"Ticket {ticket_id}: "
            f"invalid category "
            f"{row['category']}"
        )


    if row["ticket_status"] not in VALID_STATUSES:

        validation_errors.append(
            f"Ticket {ticket_id}: "
            f"invalid status "
            f"{row['ticket_status']}"
        )


    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    created_date = parse_date(
        row["created_date"]
    )


    resolved_date = parse_date(
        row["resolved_date"]
    )


    if created_date is None:

        validation_errors.append(
            f"Ticket {ticket_id}: "
            "missing created_date"
        )

        continue


    if (
        created_date < ANALYSIS_START
        or created_date > ANALYSIS_END
    ):

        validation_errors.append(
            f"Ticket {ticket_id}: "
            "created_date falls outside "
            "analysis period"
        )


    if (
        resolved_date is not None
        and resolved_date < created_date
    ):

        validation_errors.append(
            f"Ticket {ticket_id}: "
            "resolved_date occurs before "
            "created_date"
        )


    if (
        resolved_date is not None
        and resolved_date > ANALYSIS_END
    ):

        validation_errors.append(
            f"Ticket {ticket_id}: "
            "resolved_date occurs after "
            "analysis period"
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


    earliest_ticket_date = max(
        signup_date,
        ANALYSIS_START,
    )


    if created_date < earliest_ticket_date:

        validation_errors.append(
            f"Ticket {ticket_id}: "
            "ticket created before "
            "customer signup"
        )


    if (
        churn_date is not None
        and created_date > churn_date
    ):

        validation_errors.append(
            f"Ticket {ticket_id}: "
            "ticket created after churn"
        )


    # -----------------------------------------------------
    # RESOLUTION LOGIC
    # -----------------------------------------------------

    status = row[
        "ticket_status"
    ]


    resolution_value = row[
        "resolution_hours"
    ]


    csat_value = row[
        "customer_satisfaction_score"
    ]


    if status == "Resolved":

        if resolved_date is None:

            validation_errors.append(
                f"Ticket {ticket_id}: "
                "resolved ticket is missing "
                "resolved_date"
            )


        if resolution_value == "":

            validation_errors.append(
                f"Ticket {ticket_id}: "
                "resolved ticket is missing "
                "resolution_hours"
            )

        else:

            resolution_hours = float(
                resolution_value
            )


            if resolution_hours < 0:

                validation_errors.append(
                    f"Ticket {ticket_id}: "
                    "negative resolution_hours"
                )


    else:

        if resolved_date is not None:

            validation_errors.append(
                f"Ticket {ticket_id}: "
                "unresolved ticket has "
                "resolved_date"
            )


        if resolution_value != "":

            validation_errors.append(
                f"Ticket {ticket_id}: "
                "unresolved ticket has "
                "resolution_hours"
            )


        if csat_value != "":

            validation_errors.append(
                f"Ticket {ticket_id}: "
                "unresolved ticket has CSAT"
            )


    # -----------------------------------------------------
    # CSAT VALIDATION
    # -----------------------------------------------------

    if csat_value != "":

        csat = int(
            csat_value
        )


        if (
            csat < 1
            or csat > 5
        ):

            validation_errors.append(
                f"Ticket {ticket_id}: "
                "CSAT must be between "
                "1 and 5"
            )


# =========================================================
# STOP IF VALIDATION FAILS
# =========================================================

if validation_errors:

    print()

    print(
        "SUPPORT TICKET VALIDATION ERRORS"
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
            "ticket_id"
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

clean_invalid_priority = sum(
    1
    for row in cleaned_rows
    if row["priority"]
    not in VALID_PRIORITIES
)


clean_invalid_category = sum(
    1
    for row in cleaned_rows
    if row["category"]
    not in VALID_CATEGORIES
)


clean_invalid_status = sum(
    1
    for row in cleaned_rows
    if row["ticket_status"]
    not in VALID_STATUSES
)


clean_negative_resolution = sum(
    1
    for row in cleaned_rows
    if (
        row[
            "resolution_hours"
        ] != ""
        and float(
            row[
                "resolution_hours"
            ]
        ) < 0
    )
)


clean_invalid_csat = sum(
    1
    for row in cleaned_rows
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


resolved_rows = [
    row
    for row in cleaned_rows
    if row[
        "ticket_status"
    ] == "Resolved"
]


open_rows = [
    row
    for row in cleaned_rows
    if row[
        "ticket_status"
    ] == "Open"
]


in_progress_rows = [
    row
    for row in cleaned_rows
    if row[
        "ticket_status"
    ] == "In Progress"
]


resolution_values = [
    float(
        row[
            "resolution_hours"
        ]
    )
    for row in resolved_rows
    if row[
        "resolution_hours"
    ] != ""
]


csat_values = [
    int(
        row[
            "customer_satisfaction_score"
        ]
    )
    for row in resolved_rows
    if row[
        "customer_satisfaction_score"
    ] != ""
]


if resolution_values:

    average_resolution_hours = (
        sum(
            resolution_values
        )
        / len(
            resolution_values
        )
    )

else:

    average_resolution_hours = 0


if csat_values:

    average_csat = (
        sum(
            csat_values
        )
        / len(
            csat_values
        )
    )

else:

    average_csat = 0


accounts_with_tickets = {
    row["account_id"]
    for row in cleaned_rows
}


# =========================================================
# QUALITY REPORT
# =========================================================

report_lines = [
    "CLOUDPATH ANALYTICS - SUPPORT TICKET DATA QUALITY REPORT",
    "=" * 65,
    "",
    "RAW DATA",
    f"Raw rows: {raw_row_count}",
    f"Exact duplicate rows: {exact_duplicate_count}",
    f"Inconsistent priority values: {raw_invalid_priority}",
    f"Inconsistent category values: {raw_invalid_category}",
    f"Inconsistent status values: {raw_invalid_status}",
    (
        "Negative resolution-hour rows: "
        f"{raw_negative_resolution}"
    ),
    f"Invalid CSAT rows: {raw_invalid_csat}",
    "",
    "CLEANED DATA",
    f"Clean rows: {len(cleaned_rows)}",
    f"Unique ticket IDs: {len(ticket_ids)}",
    (
        "Accounts with at least one support ticket: "
        f"{len(accounts_with_tickets)}"
    ),
    f"Resolved tickets: {len(resolved_rows)}",
    f"Open tickets: {len(open_rows)}",
    (
        "In Progress tickets: "
        f"{len(in_progress_rows)}"
    ),
    (
        "Invalid priority values remaining: "
        f"{clean_invalid_priority}"
    ),
    (
        "Invalid category values remaining: "
        f"{clean_invalid_category}"
    ),
    (
        "Invalid status values remaining: "
        f"{clean_invalid_status}"
    ),
    (
        "Negative resolution-hour rows remaining: "
        f"{clean_negative_resolution}"
    ),
    (
        "Invalid CSAT rows remaining: "
        f"{clean_invalid_csat}"
    ),
    (
        "Business rule violations: "
        f"{len(validation_errors)}"
    ),
    "",
    "SUPPORT METRICS",
    (
        "Average resolution hours: "
        f"{average_resolution_hours:.2f}"
    ),
    (
        "Average CSAT for scored resolved tickets: "
        f"{average_csat:.2f}"
    ),
    "",
    "CLEANING ACTIONS",
    "- Removed exact duplicate records",
    "- Standardized priority values",
    "- Standardized support categories",
    "- Standardized ticket-status values",
    (
        "- Converted invalid negative resolution-hour "
        "values to positive durations"
    ),
    (
        "- Capped invalid CSAT values to the valid "
        "1-5 range"
    ),
    "- Validated account foreign keys",
    (
        "- Validated created dates against customer "
        "signup and churn dates"
    ),
    (
        "- Validated resolved-ticket and unresolved-ticket "
        "business rules"
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
    "CLOUDPATH ANALYTICS - SUPPORT TICKET DATA CLEANING"
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
    f"Unique ticket IDs: "
    f"{len(ticket_ids)}"
)

print(
    f"Accounts with support tickets: "
    f"{len(accounts_with_tickets)}"
)

print()

print(
    f"Priority values corrected: "
    f"{corrected_priorities}"
)

print(
    f"Category values corrected: "
    f"{corrected_categories}"
)

print(
    f"Status values corrected: "
    f"{corrected_statuses}"
)

print(
    f"Resolution-hour values corrected: "
    f"{corrected_resolution_hours}"
)

print(
    f"CSAT values corrected: "
    f"{corrected_csat}"
)

print()

print(
    f"Resolved tickets: "
    f"{len(resolved_rows)}"
)

print(
    f"Open tickets: "
    f"{len(open_rows)}"
)

print(
    f"In Progress tickets: "
    f"{len(in_progress_rows)}"
)

print()

print(
    f"Average resolution hours: "
    f"{average_resolution_hours:.2f}"
)

print(
    f"Average CSAT: "
    f"{average_csat:.2f}"
)

print()

print(
    f"Invalid priority values remaining: "
    f"{clean_invalid_priority}"
)

print(
    f"Invalid category values remaining: "
    f"{clean_invalid_category}"
)

print(
    f"Invalid status values remaining: "
    f"{clean_invalid_status}"
)

print(
    f"Negative resolution-hour rows remaining: "
    f"{clean_negative_resolution}"
)

print(
    f"Invalid CSAT rows remaining: "
    f"{clean_invalid_csat}"
)

print(
    f"Business rule violations: "
    f"{len(validation_errors)}"
)

print()

print(
    "Processed support ticket file:"
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
