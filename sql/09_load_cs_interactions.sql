-- Customer Health & Revenue Risk Analytics
-- Load cleaned Customer Success interaction data into PostgreSQL


-- =========================================================
-- STOP SCRIPT IF ANY COMMAND FAILS
-- =========================================================

\set ON_ERROR_STOP on


-- =========================================================
-- SCHEMA ADJUSTMENT
--
-- Missing CSM assignments are intentionally retained in
-- the cleaned dataset when the account itself has no
-- assigned CSM. Therefore csm_name must allow NULL.
-- =========================================================

ALTER TABLE customer_success_interactions
ALTER COLUMN csm_name DROP NOT NULL;


-- =========================================================
-- PRE-LOAD CHECK
-- Expected before first successful load: 0
-- =========================================================

SELECT
    COUNT(*) AS existing_cs_interaction_rows
FROM customer_success_interactions;


-- =========================================================
-- LOAD CUSTOMER SUCCESS INTERACTIONS
-- =========================================================

BEGIN;

\copy customer_success_interactions (interaction_id, account_id, interaction_date, interaction_type, csm_name, engagement_status, follow_up_required, notes_category, next_follow_up_date) FROM 'C:/Yuvraj/Stevens/Projects/customer-health-revenue-risk/data/processed/customer_success_interactions.csv' WITH (FORMAT csv, HEADER true, NULL '');


-- =========================================================
-- SYNCHRONIZE IDENTITY SEQUENCE
-- =========================================================

SELECT setval(
    pg_get_serial_sequence(
        'customer_success_interactions',
        'interaction_id'
    ),
    (
        SELECT MAX(interaction_id)
        FROM customer_success_interactions
    ),
    true
);


COMMIT;


-- =========================================================
-- VALIDATION 1
-- TOTAL ROW COUNT
-- Expected: 3086
-- =========================================================

SELECT
    COUNT(*) AS total_cs_interactions
FROM customer_success_interactions;


-- =========================================================
-- VALIDATION 2
-- UNIQUE INTERACTION IDS
-- Expected: 3086
-- =========================================================

SELECT
    COUNT(DISTINCT interaction_id)
        AS unique_interaction_ids
FROM customer_success_interactions;


-- =========================================================
-- VALIDATION 3
-- ID RANGE
-- Expected: 1 to 3086
-- =========================================================

SELECT
    MIN(interaction_id)
        AS minimum_interaction_id,
    MAX(interaction_id)
        AS maximum_interaction_id
FROM customer_success_interactions;


-- =========================================================
-- VALIDATION 4
-- ACCOUNT COVERAGE
-- Expected: 487
-- =========================================================

SELECT
    COUNT(DISTINCT account_id)
        AS accounts_with_interactions
FROM customer_success_interactions;


-- =========================================================
-- VALIDATION 5
-- ORPHAN ACCOUNT CHECK
-- Expected: 0 rows
-- =========================================================

SELECT
    c.interaction_id,
    c.account_id
FROM customer_success_interactions AS c
LEFT JOIN accounts AS a
    ON c.account_id = a.account_id
WHERE a.account_id IS NULL;


-- =========================================================
-- VALIDATION 6
-- ENGAGEMENT STATUS COUNTS
-- =========================================================

SELECT
    engagement_status,
    COUNT(*) AS interaction_count
FROM customer_success_interactions
GROUP BY engagement_status
ORDER BY engagement_status;


-- =========================================================
-- VALIDATION 7
-- INTERACTION TYPE DISTRIBUTION
-- =========================================================

SELECT
    interaction_type,
    COUNT(*) AS interaction_count
FROM customer_success_interactions
GROUP BY interaction_type
ORDER BY interaction_count DESC;


-- =========================================================
-- VALIDATION 8
-- NOTES CATEGORY DISTRIBUTION
-- =========================================================

SELECT
    notes_category,
    COUNT(*) AS interaction_count
FROM customer_success_interactions
GROUP BY notes_category
ORDER BY interaction_count DESC;


-- =========================================================
-- VALIDATION 9
-- FOLLOW-UP REQUIRED COUNT
-- Expected: 1211
-- =========================================================

SELECT
    COUNT(*) AS follow_up_required_interactions
FROM customer_success_interactions
WHERE follow_up_required = TRUE;


-- =========================================================
-- VALIDATION 10
-- MISSING CSM VALUES
-- Expected: 33
-- =========================================================

SELECT
    COUNT(*) AS missing_csm_values
FROM customer_success_interactions
WHERE csm_name IS NULL;


-- =========================================================
-- VALIDATION 11
-- REQUIRED FOLLOW-UPS WITH UNKNOWN DATE
-- Expected: 7
-- =========================================================

SELECT
    COUNT(*) AS required_followups_without_date
FROM customer_success_interactions
WHERE follow_up_required = TRUE
  AND next_follow_up_date IS NULL;


-- =========================================================
-- VALIDATION 12
-- INVALID FOLLOW-UP DATE
-- Expected: 0 rows
-- =========================================================

SELECT
    interaction_id,
    account_id,
    interaction_date,
    next_follow_up_date
FROM customer_success_interactions
WHERE next_follow_up_date < interaction_date;


-- =========================================================
-- VALIDATION 13
-- FOLLOW-UP DATE WHEN FOLLOW-UP NOT REQUIRED
-- Expected: 0 rows
-- =========================================================

SELECT
    interaction_id,
    account_id,
    follow_up_required,
    next_follow_up_date
FROM customer_success_interactions
WHERE follow_up_required = FALSE
  AND next_follow_up_date IS NOT NULL;


-- =========================================================
-- VALIDATION 14
-- INTERACTION BEFORE SIGNUP
-- Expected: 0 rows
-- =========================================================

SELECT
    c.interaction_id,
    c.account_id,
    a.signup_date,
    c.interaction_date
FROM customer_success_interactions AS c
INNER JOIN accounts AS a
    ON c.account_id = a.account_id
WHERE c.interaction_date < a.signup_date;


-- =========================================================
-- VALIDATION 15
-- INTERACTION AFTER CHURN
-- Expected: 0 rows
-- =========================================================

SELECT
    c.interaction_id,
    c.account_id,
    a.churn_date,
    c.interaction_date
FROM customer_success_interactions AS c
INNER JOIN accounts AS a
    ON c.account_id = a.account_id
WHERE a.churn_date IS NOT NULL
  AND c.interaction_date > a.churn_date;


-- =========================================================
-- VALIDATION 16
-- CSM ASSIGNMENT MISMATCH
-- Expected: 0 rows
-- =========================================================

SELECT
    c.interaction_id,
    c.account_id,
    a.assigned_csm,
    c.csm_name
FROM customer_success_interactions AS c
INNER JOIN accounts AS a
    ON c.account_id = a.account_id
WHERE a.assigned_csm IS NOT NULL
  AND c.csm_name IS NOT NULL
  AND a.assigned_csm <> c.csm_name;


-- =========================================================
-- VALIDATION 17
-- INTERACTION DATE RANGE
-- =========================================================

SELECT
    MIN(interaction_date)
        AS earliest_interaction_date,
    MAX(interaction_date)
        AS latest_interaction_date
FROM customer_success_interactions;


-- =========================================================
-- VALIDATION 18
-- ENGAGEMENT MIX
-- =========================================================

SELECT
    engagement_status,
    COUNT(*) AS interaction_count,
    ROUND(
        COUNT(*)::NUMERIC
        / (
            SELECT COUNT(*)
            FROM customer_success_interactions
        )
        * 100,
        2
    ) AS percentage_of_interactions
FROM customer_success_interactions
GROUP BY engagement_status
ORDER BY interaction_count DESC;


-- =========================================================
-- VALIDATION 19
-- CUSTOMER SUCCESS ACTIVITY BY SEGMENT
-- =========================================================

SELECT
    a.segment,
    COUNT(c.interaction_id)
        AS total_interactions,
    COUNT(DISTINCT c.account_id)
        AS accounts_with_interactions,
    ROUND(
        COUNT(c.interaction_id)::NUMERIC
        / NULLIF(
            COUNT(DISTINCT c.account_id),
            0
        ),
        2
    ) AS avg_interactions_per_account
FROM customer_success_interactions AS c
INNER JOIN accounts AS a
    ON c.account_id = a.account_id
GROUP BY a.segment
ORDER BY total_interactions DESC;


-- =========================================================
-- VALIDATION 20
-- ENGAGEMENT BY SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(*) FILTER (
        WHERE c.engagement_status = 'Engaged'
    ) AS engaged,

    COUNT(*) FILTER (
        WHERE c.engagement_status = 'Neutral'
    ) AS neutral,

    COUNT(*) FILTER (
        WHERE c.engagement_status = 'Unresponsive'
    ) AS unresponsive,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE c.engagement_status = 'Unresponsive'
            )
        )::NUMERIC
        / NULLIF(
            COUNT(*),
            0
        )
        * 100,
        2
    ) AS unresponsive_rate_pct

FROM customer_success_interactions AS c
INNER JOIN accounts AS a
    ON c.account_id = a.account_id
GROUP BY a.segment
ORDER BY a.segment;


-- =========================================================
-- VALIDATION 21
-- FOLLOW-UP REQUIREMENT BY ENGAGEMENT STATUS
-- =========================================================

SELECT
    engagement_status,
    COUNT(*) AS interactions,

    COUNT(*) FILTER (
        WHERE follow_up_required = TRUE
    ) AS follow_up_required,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE follow_up_required = TRUE
            )
        )::NUMERIC
        / NULLIF(
            COUNT(*),
            0
        )
        * 100,
        2
    ) AS follow_up_rate_pct

FROM customer_success_interactions
GROUP BY engagement_status
ORDER BY engagement_status;


-- =========================================================
-- VALIDATION 22
-- SAMPLE RECORDS
-- =========================================================

SELECT
    interaction_id,
    account_id,
    interaction_date,
    interaction_type,
    csm_name,
    engagement_status,
    follow_up_required,
    notes_category,
    next_follow_up_date
FROM customer_success_interactions
ORDER BY interaction_id
LIMIT 10;
