-- Customer Health & Revenue Risk Analytics
-- Load cleaned account data into PostgreSQL


-- =========================================================
-- STOP SCRIPT IF ANY COMMAND FAILS
-- =========================================================

\set ON_ERROR_STOP on


-- =========================================================
-- LOAD ACCOUNTS
-- Source:
-- data/processed/accounts.csv
-- =========================================================

BEGIN;

\copy accounts (account_id, account_name, industry, segment, region, signup_date, customer_status, churn_date, assigned_csm) FROM 'C:/Yuvraj/Stevens/Projects/customer-health-revenue-risk/data/processed/accounts.csv' WITH (FORMAT csv, HEADER true, NULL '');


-- =========================================================
-- SYNCHRONIZE IDENTITY SEQUENCE
-- =========================================================

SELECT setval(
    pg_get_serial_sequence(
        'accounts',
        'account_id'
    ),
    (
        SELECT MAX(account_id)
        FROM accounts
    ),
    true
);


COMMIT;


-- =========================================================
-- VALIDATION 1
-- TOTAL ROW COUNT
-- Expected: 500
-- =========================================================

SELECT
    COUNT(*) AS total_accounts
FROM accounts;


-- =========================================================
-- VALIDATION 2
-- UNIQUE ACCOUNT IDS
-- Expected: 500
-- =========================================================

SELECT
    COUNT(DISTINCT account_id) AS unique_account_ids
FROM accounts;


-- =========================================================
-- VALIDATION 3
-- ACCOUNT ID RANGE
-- Expected:
-- Minimum = 1
-- Maximum = 500
-- =========================================================

SELECT
    MIN(account_id) AS minimum_account_id,
    MAX(account_id) AS maximum_account_id
FROM accounts;


-- =========================================================
-- VALIDATION 4
-- MISSING VALUES RETAINED
-- Expected:
-- Missing industry = 20
-- Missing assigned CSM = 7
-- =========================================================

SELECT
    COUNT(*) FILTER (
        WHERE industry IS NULL
    ) AS missing_industry,

    COUNT(*) FILTER (
        WHERE assigned_csm IS NULL
    ) AS missing_assigned_csm

FROM accounts;


-- =========================================================
-- VALIDATION 5
-- CUSTOMER STATUS
-- Expected total = 500
-- Expected churned = 74
-- =========================================================

SELECT
    customer_status,
    COUNT(*) AS account_count
FROM accounts
GROUP BY customer_status
ORDER BY customer_status;


-- =========================================================
-- VALIDATION 6
-- CUSTOMER SEGMENTS
-- =========================================================

SELECT
    segment,
    COUNT(*) AS account_count
FROM accounts
GROUP BY segment
ORDER BY account_count DESC;


-- =========================================================
-- VALIDATION 7
-- CHECK FOR INVALID CATEGORIES
-- Expected result: 0 rows
-- =========================================================

SELECT
    account_id,
    segment,
    region,
    customer_status
FROM accounts
WHERE segment NOT IN (
        'SMB',
        'Mid-Market',
        'Enterprise'
    )
   OR region NOT IN (
        'Northeast',
        'South',
        'Midwest',
        'West',
        'Canada'
    )
   OR customer_status NOT IN (
        'Active',
        'Churned'
    );


-- =========================================================
-- VALIDATION 8
-- CHECK CHURN BUSINESS RULES
-- Expected result: 0 rows
-- =========================================================

SELECT
    account_id,
    signup_date,
    customer_status,
    churn_date
FROM accounts
WHERE
    (
        customer_status = 'Active'
        AND churn_date IS NOT NULL
    )
    OR
    (
        customer_status = 'Churned'
        AND churn_date IS NULL
    )
    OR
    (
        churn_date IS NOT NULL
        AND churn_date < signup_date
    );


-- =========================================================
-- VALIDATION 9
-- SAMPLE RECORDS
-- =========================================================

SELECT *
FROM accounts
ORDER BY account_id
LIMIT 10;
