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

RAW_INTERACTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "customer_success_interactions_raw.csv"
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
    / "customer_success_interactions.csv"
)

QUALITY_REPORT_FILE = (
    PROCESSED_DATA_DIR
    / "customer_success_interactions_quality_report.txt"
)


# =========================================================
# EXPECTED SCHEMA
# =========================================================

EXPECTED_COLUMNS = [
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


VALID_INTERACTION_TYPES = {
    "Email",
    "Call",
    "Meeting",
    "QBR",
    "Training",
}


VALID_ENGAGEMENT_STATUSES = {
    "Engaged",
    "Neutral",
    "Unresponsive",
}


VALID_NOTES_CATEGORIES = {
    "General Check-in",
    "Adoption",
    "Training Need",
    "Support Escalation",
    "Billing Follow-up",
    "Renewal",
    "Expansion",
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


def normalize_interaction_type(value):

    cleaned_value = value.strip()

    mapping = {
        "email": "Email",
        "call": "Call",
        "meeting": "Meeting",
        "qbr": "QBR",
        "training": "Training",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_engagement_status(value):

    cleaned_value = value.strip()

    mapping = {
        "engaged": "Engaged",
        "neutral": "Neutral",
        "unresponsive": "Unresponsive",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_notes_category(value):

    cleaned_value = value.strip()

    mapping = {
        "general check-in":
            "General Check-in",

        "adoption":
            "Adoption",

        "training need":
            "Training Need",

        "support escalation":
            "Support Escalation",

        "billing follow-up":
            "Billing Follow-up",

        "renewal":
            "Renewal",

        "expansion":
            "Expansion",
    }

    return mapping.get(
        cleaned_value.lower(),
        cleaned_value,
    )


def normalize_boolean(value):

    cleaned_value = (
        str(value)
        .strip()
        .lower()
    )

    true_values = {
        "true",
        "yes",
        "1",
    }

    false_values = {
        "false",
        "no",
        "0",
    }

    if cleaned_value in true_values:

        return True

    if cleaned_value in false_values:

        return False

    raise ValueError(
        f"Invalid boolean value: {value}"
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
# READ RAW INTERACTION DATA
# =========================================================

with RAW_INTERACTIONS_FILE.open(
    mode="r",
    encoding="utf-8",
    newline="",
) as csv_file:

    reader = csv.DictReader(
        csv_file
    )

    if reader.fieldnames != EXPECTED_COLUMNS:

        raise ValueError(
            "Raw Customer Success interaction "
            "columns do not match the expected schema."
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

raw_invalid_type = sum(
    1
    for row in raw_rows
    if row[
        "interaction_type"
    ] not in VALID_INTERACTION_TYPES
)


raw_invalid_engagement = sum(
    1
    for row in raw_rows
    if row[
        "engagement_status"
    ] not in VALID_ENGAGEMENT_STATUSES
)


raw_invalid_notes = sum(
    1
    for row in raw_rows
    if row[
        "notes_category"
    ] not in VALID_NOTES_CATEGORIES
)


raw_noncanonical_boolean = sum(
    1
    for row in raw_rows
    if row[
        "follow_up_required"
    ].strip()
    not in {
        "True",
        "False",
    }
)


raw_invalid_followup_dates = sum(
    1
    for row in raw_rows
    if (
        row[
            "next_follow_up_date"
        ].strip()
        != ""
        and parse_date(
            row[
                "next_follow_up_date"
            ]
        )
        < parse_date(
            row[
                "interaction_date"
            ]
        )
    )
)


raw_missing_csm = sum(
    1
    for row in raw_rows
    if row[
        "csm_name"
    ].strip()
    == ""
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

corrected_types = 0
corrected_engagement = 0
corrected_booleans = 0
corrected_notes = 0
corrected_followup_dates = 0


for row in deduplicated_rows:

    original_type = row[
        "interaction_type"
    ]


    original_engagement = row[
        "engagement_status"
    ]


    original_boolean = row[
        "follow_up_required"
    ]


    original_notes = row[
        "notes_category"
    ]


    interaction_type = (
        normalize_interaction_type(
            original_type
        )
    )


    engagement_status = (
        normalize_engagement_status(
            original_engagement
        )
    )


    follow_up_required = (
        normalize_boolean(
            original_boolean
        )
    )


    notes_category = (
        normalize_notes_category(
            original_notes
        )
    )


    if interaction_type != original_type:

        corrected_types += 1


    if engagement_status != original_engagement:

        corrected_engagement += 1


    if (
        original_boolean.strip()
        not in {
            "True",
            "False",
        }
    ):

        corrected_booleans += 1


    if notes_category != original_notes:

        corrected_notes += 1


    interaction_date = parse_date(
        row[
            "interaction_date"
        ]
    )


    next_follow_up_date = parse_date(
        row[
            "next_follow_up_date"
        ]
    )


    # -----------------------------------------------------
    # INVALID FOLLOW-UP DATE
    #
    # Do not invent a replacement date.
    # Keep follow_up_required = True but remove the
    # unreliable date.
    # -----------------------------------------------------

    if (
        next_follow_up_date is not None
        and next_follow_up_date
        < interaction_date
    ):

        next_follow_up_date = None

        corrected_followup_dates += 1


    # -----------------------------------------------------
    # NO FOLLOW-UP REQUIRED = NO FOLLOW-UP DATE
    # -----------------------------------------------------

    if not follow_up_required:

        next_follow_up_date = None


    cleaned_row = {
        "interaction_id":
            row[
                "interaction_id"
            ].strip(),

        "account_id":
            row[
                "account_id"
            ].strip(),

        "interaction_date":
            interaction_date.isoformat(),

        "interaction_type":
            interaction_type,

        "csm_name":
            row[
                "csm_name"
            ].strip(),

        "engagement_status":
            engagement_status,

        "follow_up_required":
            (
                "true"
                if follow_up_required
                else "false"
            ),

        "notes_category":
            notes_category,

        "next_follow_up_date":
            (
                ""
                if next_follow_up_date is None
                else next_follow_up_date.isoformat()
            ),
    }


    cleaned_rows.append(
        cleaned_row
    )


# =========================================================
# VALIDATION
# =========================================================

validation_errors = []

interaction_ids = set()


for row in cleaned_rows:

    interaction_id = row[
        "interaction_id"
    ]


    account_id = row[
        "account_id"
    ]


    # -----------------------------------------------------
    # UNIQUE INTERACTION ID
    # -----------------------------------------------------

    if interaction_id in interaction_ids:

        validation_errors.append(
            f"Duplicate interaction_id: "
            f"{interaction_id}"
        )


    interaction_ids.add(
        interaction_id
    )


    # -----------------------------------------------------
    # ACCOUNT FOREIGN KEY
    # -----------------------------------------------------

    if account_id not in valid_account_ids:

        validation_errors.append(
            f"Interaction {interaction_id}: "
            f"account_id {account_id} "
            "does not exist"
        )

        continue


    # -----------------------------------------------------
    # CATEGORY VALIDATION
    # -----------------------------------------------------

    if (
        row[
            "interaction_type"
        ]
        not in VALID_INTERACTION_TYPES
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "invalid interaction type "
            f"{row['interaction_type']}"
        )


    if (
        row[
            "engagement_status"
        ]
        not in VALID_ENGAGEMENT_STATUSES
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "invalid engagement status "
            f"{row['engagement_status']}"
        )


    if (
        row[
            "notes_category"
        ]
        not in VALID_NOTES_CATEGORIES
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "invalid notes category "
            f"{row['notes_category']}"
        )


    # -----------------------------------------------------
    # BOOLEAN VALIDATION
    # -----------------------------------------------------

    if (
        row[
            "follow_up_required"
        ]
        not in {
            "true",
            "false",
        }
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "invalid follow_up_required value"
        )


    follow_up_required = (
        row[
            "follow_up_required"
        ]
        == "true"
    )


    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    interaction_date = parse_date(
        row[
            "interaction_date"
        ]
    )


    next_follow_up_date = parse_date(
        row[
            "next_follow_up_date"
        ]
    )


    if (
        interaction_date < ANALYSIS_START
        or interaction_date > ANALYSIS_END
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "interaction date falls outside "
            "analysis period"
        )


    if (
        next_follow_up_date is not None
        and next_follow_up_date
        < interaction_date
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "follow-up date occurs before "
            "interaction date"
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


    if interaction_date < signup_date:

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "interaction occurs before signup"
        )


    if (
        churn_date is not None
        and interaction_date > churn_date
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "interaction occurs after churn"
        )


    # -----------------------------------------------------
    # FOLLOW-UP BUSINESS RULE
    # -----------------------------------------------------

    if (
        not follow_up_required
        and next_follow_up_date is not None
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "follow-up date exists when "
            "follow_up_required is false"
        )


    # -----------------------------------------------------
    # CSM VALIDATION
    #
    # Missing assigned CSM values are permitted.
    # If both values exist, they should agree.
    # -----------------------------------------------------

    account_csm = account[
        "assigned_csm"
    ].strip()


    interaction_csm = row[
        "csm_name"
    ].strip()


    if (
        account_csm != ""
        and interaction_csm != ""
        and account_csm
        != interaction_csm
    ):

        validation_errors.append(
            f"Interaction {interaction_id}: "
            "CSM does not match account "
            "assignment"
        )


# =========================================================
# STOP IF VALIDATION FAILS
# =========================================================

if validation_errors:

    print()

    print(
        "CUSTOMER SUCCESS INTERACTION "
        "VALIDATION ERRORS"
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
            "interaction_id"
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

accounts_with_interactions = {
    row[
        "account_id"
    ]
    for row in cleaned_rows
}


engaged_count = sum(
    1
    for row in cleaned_rows
    if row[
        "engagement_status"
    ] == "Engaged"
)


neutral_count = sum(
    1
    for row in cleaned_rows
    if row[
        "engagement_status"
    ] == "Neutral"
)


unresponsive_count = sum(
    1
    for row in cleaned_rows
    if row[
        "engagement_status"
    ] == "Unresponsive"
)


follow_up_required_count = sum(
    1
    for row in cleaned_rows
    if row[
        "follow_up_required"
    ] == "true"
)


missing_csm_count = sum(
    1
    for row in cleaned_rows
    if row[
        "csm_name"
    ] == ""
)


missing_followup_date_when_required = sum(
    1
    for row in cleaned_rows
    if (
        row[
            "follow_up_required"
        ]
        == "true"
        and row[
            "next_follow_up_date"
        ]
        == ""
    )
)


# =========================================================
# FINAL QUALITY CHECK COUNTS
# =========================================================

clean_invalid_type = sum(
    1
    for row in cleaned_rows
    if row[
        "interaction_type"
    ] not in VALID_INTERACTION_TYPES
)


clean_invalid_engagement = sum(
    1
    for row in cleaned_rows
    if row[
        "engagement_status"
    ] not in VALID_ENGAGEMENT_STATUSES
)


clean_invalid_notes = sum(
    1
    for row in cleaned_rows
    if row[
        "notes_category"
    ] not in VALID_NOTES_CATEGORIES
)


clean_invalid_boolean = sum(
    1
    for row in cleaned_rows
    if row[
        "follow_up_required"
    ] not in {
        "true",
        "false",
    }
)


clean_invalid_followup_dates = sum(
    1
    for row in cleaned_rows
    if (
        row[
            "next_follow_up_date"
        ] != ""
        and parse_date(
            row[
                "next_follow_up_date"
            ]
        )
        < parse_date(
            row[
                "interaction_date"
            ]
        )
    )
)


# =========================================================
# QUALITY REPORT
# =========================================================

report_lines = [
    (
        "CLOUDPATH ANALYTICS - CUSTOMER SUCCESS "
        "INTERACTION DATA QUALITY REPORT"
    ),
    "=" * 65,
    "",
    "RAW DATA",
    f"Raw rows: {raw_row_count}",
    f"Exact duplicate rows: {exact_duplicate_count}",
    (
        "Inconsistent interaction-type values: "
        f"{raw_invalid_type}"
    ),
    (
        "Inconsistent engagement-status values: "
        f"{raw_invalid_engagement}"
    ),
    (
        "Noncanonical follow-up boolean values: "
        f"{raw_noncanonical_boolean}"
    ),
    (
        "Inconsistent notes-category values: "
        f"{raw_invalid_notes}"
    ),
    (
        "Follow-up dates before interaction dates: "
        f"{raw_invalid_followup_dates}"
    ),
    (
        "Interactions with missing CSM: "
        f"{raw_missing_csm}"
    ),
    "",
    "CLEANED DATA",
    f"Clean rows: {len(cleaned_rows)}",
    (
        "Unique interaction IDs: "
        f"{len(interaction_ids)}"
    ),
    (
        "Accounts with interactions: "
        f"{len(accounts_with_interactions)}"
    ),
    f"Engaged interactions: {engaged_count}",
    f"Neutral interactions: {neutral_count}",
    (
        "Unresponsive interactions: "
        f"{unresponsive_count}"
    ),
    (
        "Follow-up required interactions: "
        f"{follow_up_required_count}"
    ),
    (
        "Missing CSM values retained: "
        f"{missing_csm_count}"
    ),
    (
        "Required follow-ups with unknown date: "
        f"{missing_followup_date_when_required}"
    ),
    (
        "Invalid interaction types remaining: "
        f"{clean_invalid_type}"
    ),
    (
        "Invalid engagement statuses remaining: "
        f"{clean_invalid_engagement}"
    ),
    (
        "Invalid notes categories remaining: "
        f"{clean_invalid_notes}"
    ),
    (
        "Invalid boolean values remaining: "
        f"{clean_invalid_boolean}"
    ),
    (
        "Invalid follow-up dates remaining: "
        f"{clean_invalid_followup_dates}"
    ),
    (
        "Business rule violations: "
        f"{len(validation_errors)}"
    ),
    "",
    "CLEANING ACTIONS",
    "- Removed exact duplicate records",
    "- Standardized interaction-type values",
    "- Standardized engagement-status values",
    "- Standardized follow-up boolean values",
    "- Standardized notes-category values",
    (
        "- Removed invalid follow-up dates rather than "
        "inventing replacement dates"
    ),
    (
        "- Retained missing CSM values where the "
        "account itself has no assigned CSM"
    ),
    "- Validated account foreign keys",
    (
        "- Validated interaction dates against customer "
        "signup and churn dates"
    ),
    (
        "- Validated follow-up dates against "
        "interaction dates"
    ),
    (
        "- Validated CSM names against account "
        "assignments where available"
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
    "CLOUDPATH ANALYTICS - "
    "CUSTOMER SUCCESS INTERACTION DATA CLEANING"
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
    f"Unique interaction IDs: "
    f"{len(interaction_ids)}"
)

print(
    f"Accounts with interactions: "
    f"{len(accounts_with_interactions)}"
)

print()

print(
    f"Interaction-type values corrected: "
    f"{corrected_types}"
)

print(
    f"Engagement-status values corrected: "
    f"{corrected_engagement}"
)

print(
    f"Boolean values corrected: "
    f"{corrected_booleans}"
)

print(
    f"Notes-category values corrected: "
    f"{corrected_notes}"
)

print(
    f"Invalid follow-up dates removed: "
    f"{corrected_followup_dates}"
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
    f"Missing CSM values retained: "
    f"{missing_csm_count}"
)

print(
    f"Required follow-ups with unknown date: "
    f"{missing_followup_date_when_required}"
)

print()

print(
    f"Invalid interaction types remaining: "
    f"{clean_invalid_type}"
)

print(
    f"Invalid engagement statuses remaining: "
    f"{clean_invalid_engagement}"
)

print(
    f"Invalid notes categories remaining: "
    f"{clean_invalid_notes}"
)

print(
    f"Invalid boolean values remaining: "
    f"{clean_invalid_boolean}"
)

print(
    f"Invalid follow-up dates remaining: "
    f"{clean_invalid_followup_dates}"
)

print(
    f"Business rule violations: "
    f"{len(validation_errors)}"
)

print()

print(
    "Processed Customer Success interaction file:"
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
