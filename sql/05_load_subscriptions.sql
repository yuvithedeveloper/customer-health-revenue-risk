-- Customer Health & Revenue Risk Analytics
-- Load cleaned subscription data into PostgreSQL


-- =========================================================
-- STOP SCRIPT IF ANY COMMAND FAILS
-- =========================================================

\set ON_ERROR_STOP on


-- =========================================================
-- PRE-LOAD CHECK
-- Expected before first load: 0 rows
-- =========================================================

SELECT
    COUNT(*) AS existing_subscription_rows
FROM subscriptions;


-- =========================================================
-- LOAD SUBSCRIPTIONS
-- Source:
-- data/processed/subscriptions.csv
-- =========================================================

BEGIN;

\copy subscriptions (subscription_id, account_id, plan_name, subscription_start_date, subscription_end_date, billing_frequency, mrr, subscription_status, renewal_date) FROM 'C:/Yuvraj/Stevens/Projects/customer-health-revenue-risk/data/processed/subscriptions.csv' WITH (FORMAT csv, HEADER true, NULL '');


-- =========================================================
-- SYNCHRONIZE IDENTITY SEQUENCE
-- =========================================================

SELECT setval(
    pg_get_serial_sequence(
        'subscriptions',
        'subscription_id'
    ),
    (
        SELECT MAX(subscription_id)
        FROM subscriptions
    ),
    true
);


COMMIT;


-- =========================================================
-- VALIDATION 1
-- TOTAL SUBSCRIPTION ROWS
-- Expected: 980
-- =========================================================

SELECT
    COUNT(*) AS total_subscriptions
FROM subscriptions;


-- =========================================================
-- VALIDATION 2
-- UNIQUE SUBSCRIPTION IDS
-- Expected: 980
-- =========================================================

SELECT
    COUNT(DISTINCT subscription_id)
        AS unique_subscription_ids
FROM subscriptions;


-- =========================================================
-- VALIDATION 3
-- SUBSCRIPTION ID RANGE
-- Expected:
-- Minimum = 1
-- Maximum = 980
-- =========================================================

SELECT
    MIN(subscription_id)
        AS minimum_subscription_id,

    MAX(subscription_id)
        AS maximum_subscription_id

FROM subscriptions;


-- =========================================================
-- VALIDATION 4
-- ACCOUNT COVERAGE
-- Expected: 500 accounts
-- =========================================================

SELECT
    COUNT(DISTINCT account_id)
        AS accounts_with_subscriptions
FROM subscriptions;


-- =========================================================
-- VALIDATION 5
-- FOREIGN KEY / ORPHAN CHECK
-- Expected: 0 rows
-- =========================================================

SELECT
    s.subscription_id,
    s.account_id
FROM subscriptions AS s
LEFT JOIN accounts AS a
    ON s.account_id = a.account_id
WHERE a.account_id IS NULL;


-- =========================================================
-- VALIDATION 6
-- SUBSCRIPTION STATUS COUNTS
--
-- Expected:
-- Active  = 426
-- Churned = 74
-- Renewed = 480
-- =========================================================

SELECT
    subscription_status,
    COUNT(*) AS subscription_count
FROM subscriptions
GROUP BY subscription_status
ORDER BY subscription_status;


-- =========================================================
-- VALIDATION 7
-- PLAN DISTRIBUTION
-- =========================================================

SELECT
    plan_name,
    COUNT(*) AS subscription_count
FROM subscriptions
GROUP BY plan_name
ORDER BY subscription_count DESC;


-- =========================================================
-- VALIDATION 8
-- BILLING FREQUENCY DISTRIBUTION
-- =========================================================

SELECT
    billing_frequency,
    COUNT(*) AS subscription_count
FROM subscriptions
GROUP BY billing_frequency
ORDER BY subscription_count DESC;


-- =========================================================
-- VALIDATION 9
-- CURRENT ACTIVE SUBSCRIPTIONS
-- Expected: 426
-- =========================================================

SELECT
    COUNT(*) AS active_subscriptions
FROM subscriptions
WHERE subscription_status = 'Active';


-- =========================================================
-- VALIDATION 10
-- CURRENT MRR AND ARR
--
-- Expected:
-- MRR = 1,574,850.00
-- ARR = 18,898,200.00
-- =========================================================

SELECT
    SUM(mrr) AS current_mrr,
    SUM(mrr) * 12 AS current_arr
FROM subscriptions
WHERE subscription_status = 'Active';


-- =========================================================
-- VALIDATION 11
-- CURRENT REVENUE BY CUSTOMER SEGMENT
-- =========================================================

SELECT
    a.segment,
    COUNT(*) AS active_subscriptions,
    SUM(s.mrr) AS current_mrr,
    SUM(s.mrr) * 12 AS current_arr
FROM subscriptions AS s
INNER JOIN accounts AS a
    ON s.account_id = a.account_id
WHERE s.subscription_status = 'Active'
GROUP BY a.segment
ORDER BY current_arr DESC;


-- =========================================================
-- VALIDATION 12
-- INVALID MRR
-- Expected: 0 rows
-- =========================================================

SELECT
    subscription_id,
    account_id,
    mrr
FROM subscriptions
WHERE mrr < 0;


-- =========================================================
-- VALIDATION 13
-- INVALID SUBSCRIPTION DATES
-- Expected: 0 rows
-- =========================================================

SELECT
    subscription_id,
    account_id,
    subscription_start_date,
    subscription_end_date
FROM subscriptions
WHERE subscription_end_date
      < subscription_start_date;


-- =========================================================
-- VALIDATION 14
-- CHURNED SUBSCRIPTIONS WITH RENEWAL DATE
-- Expected: 0 rows
-- =========================================================

SELECT
    subscription_id,
    account_id,
    subscription_status,
    renewal_date
FROM subscriptions
WHERE subscription_status = 'Churned'
  AND renewal_date IS NOT NULL;


-- =========================================================
-- VALIDATION 15
-- ACTIVE CUSTOMER / ACTIVE SUBSCRIPTION MATCH
-- Expected: 426
-- =========================================================

SELECT
    COUNT(DISTINCT a.account_id)
        AS active_accounts_with_active_subscription
FROM accounts AS a
INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id
WHERE a.customer_status = 'Active'
  AND s.subscription_status = 'Active';


-- =========================================================
-- VALIDATION 16
-- ACTIVE ACCOUNTS WITHOUT ACTIVE SUBSCRIPTION
-- Expected: 0 rows
-- =========================================================

SELECT
    a.account_id,
    a.account_name
FROM accounts AS a
LEFT JOIN subscriptions AS s
    ON a.account_id = s.account_id
    AND s.subscription_status = 'Active'
WHERE a.customer_status = 'Active'
  AND s.subscription_id IS NULL;


-- =========================================================
-- VALIDATION 17
-- SAMPLE SUBSCRIPTION RECORDS
-- =========================================================

SELECT
    subscription_id,
    account_id,
    plan_name,
    subscription_start_date,
    subscription_end_date,
    billing_frequency,
    mrr,
    subscription_status,
    renewal_date
FROM subscriptions
ORDER BY subscription_id
LIMIT 10;
