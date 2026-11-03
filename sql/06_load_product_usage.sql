-- Customer Health & Revenue Risk Analytics
-- Load cleaned product usage data into PostgreSQL


-- =========================================================
-- STOP SCRIPT IF ANY COMMAND FAILS
-- =========================================================

\set ON_ERROR_STOP on


-- =========================================================
-- PRE-LOAD CHECK
-- Expected before first load: 0 rows
-- =========================================================

SELECT
    COUNT(*) AS existing_product_usage_rows
FROM product_usage;


-- =========================================================
-- LOAD PRODUCT USAGE
-- Source:
-- data/processed/product_usage.csv
-- =========================================================

BEGIN;

\copy product_usage (usage_id, account_id, usage_month, licensed_users, active_users, login_count, dashboards_viewed, reports_generated, alerts_created, core_features_used) FROM 'C:/Yuvraj/Stevens/Projects/customer-health-revenue-risk/data/processed/product_usage.csv' WITH (FORMAT csv, HEADER true, NULL '');


-- =========================================================
-- SYNCHRONIZE IDENTITY SEQUENCE
-- =========================================================

SELECT setval(
    pg_get_serial_sequence(
        'product_usage',
        'usage_id'
    ),
    (
        SELECT MAX(usage_id)
        FROM product_usage
    ),
    true
);


COMMIT;


-- =========================================================
-- VALIDATION 1
-- TOTAL ROW COUNT
-- Expected: 8184
-- =========================================================

SELECT
    COUNT(*) AS total_product_usage_rows
FROM product_usage;


-- =========================================================
-- VALIDATION 2
-- UNIQUE USAGE IDS
-- Expected: 8184
-- =========================================================

SELECT
    COUNT(DISTINCT usage_id)
        AS unique_usage_ids
FROM product_usage;


-- =========================================================
-- VALIDATION 3
-- ACCOUNT COVERAGE
-- Expected: 500
-- =========================================================

SELECT
    COUNT(DISTINCT account_id)
        AS accounts_with_usage
FROM product_usage;


-- =========================================================
-- VALIDATION 4
-- UNIQUE ACCOUNT-MONTH COMBINATIONS
-- Expected: 8184
-- =========================================================

SELECT
    COUNT(*) AS account_month_rows
FROM (
    SELECT
        account_id,
        usage_month
    FROM product_usage
    GROUP BY
        account_id,
        usage_month
) AS account_months;


-- =========================================================
-- VALIDATION 5
-- ORPHAN ACCOUNT CHECK
-- Expected: 0 rows
-- =========================================================

SELECT
    p.usage_id,
    p.account_id
FROM product_usage AS p
LEFT JOIN accounts AS a
    ON p.account_id = a.account_id
WHERE a.account_id IS NULL;


-- =========================================================
-- VALIDATION 6
-- ACTIVE USERS EXCEEDING LICENSED USERS
-- Expected: 0 rows
-- =========================================================

SELECT
    usage_id,
    account_id,
    licensed_users,
    active_users
FROM product_usage
WHERE active_users > licensed_users;


-- =========================================================
-- VALIDATION 7
-- INVALID FEATURE COUNTS
-- Expected: 0 rows
-- =========================================================

SELECT
    usage_id,
    account_id,
    core_features_used
FROM product_usage
WHERE core_features_used < 0
   OR core_features_used > 8;


-- =========================================================
-- VALIDATION 8
-- NEGATIVE ACTIVITY VALUES
-- Expected: 0 rows
-- =========================================================

SELECT
    usage_id,
    account_id,
    login_count,
    dashboards_viewed,
    reports_generated,
    alerts_created
FROM product_usage
WHERE login_count < 0
   OR dashboards_viewed < 0
   OR reports_generated < 0
   OR alerts_created < 0;


-- =========================================================
-- VALIDATION 9
-- USAGE DATE RANGE
-- =========================================================

SELECT
    MIN(usage_month) AS earliest_usage_month,
    MAX(usage_month) AS latest_usage_month
FROM product_usage;


-- =========================================================
-- VALIDATION 10
-- MONTHLY ROW COUNTS
-- =========================================================

SELECT
    usage_month,
    COUNT(*) AS account_count
FROM product_usage
GROUP BY usage_month
ORDER BY usage_month;


-- =========================================================
-- VALIDATION 11
-- BASIC USAGE SUMMARY
-- =========================================================

SELECT
    ROUND(
        AVG(
            active_users::NUMERIC
            / NULLIF(
                licensed_users,
                0
            )
        )
        * 100,
        2
    ) AS average_active_user_rate_pct,

    ROUND(
        AVG(
            core_features_used::NUMERIC
            / 8
        )
        * 100,
        2
    ) AS average_feature_adoption_pct

FROM product_usage;


-- =========================================================
-- VALIDATION 12
-- CURRENT MONTH USAGE BY SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(*) AS accounts,

    ROUND(
        AVG(
            p.active_users::NUMERIC
            / NULLIF(
                p.licensed_users,
                0
            )
        )
        * 100,
        2
    ) AS avg_active_user_rate_pct,

    ROUND(
        AVG(
            p.core_features_used::NUMERIC
            / 8
        )
        * 100,
        2
    ) AS avg_feature_adoption_pct

FROM product_usage AS p

INNER JOIN accounts AS a
    ON p.account_id = a.account_id

WHERE p.usage_month = (
    SELECT MAX(usage_month)
    FROM product_usage
)

GROUP BY a.segment

ORDER BY a.segment;


-- =========================================================
-- VALIDATION 13
-- SAMPLE RECORDS
-- =========================================================

SELECT
    usage_id,
    account_id,
    usage_month,
    licensed_users,
    active_users,
    login_count,
    dashboards_viewed,
    reports_generated,
    alerts_created,
    core_features_used
FROM product_usage
ORDER BY usage_id
LIMIT 10;
