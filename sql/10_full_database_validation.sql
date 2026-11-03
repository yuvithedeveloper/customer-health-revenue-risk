-- Customer Health & Revenue Risk Analytics
-- Full database-wide validation
--
-- Purpose:
-- Confirm that all six cleaned datasets were loaded correctly,
-- relationships are valid, business rules hold, and the database
-- is ready for analytical SQL.


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- 1. TABLE ROW COUNTS
-- =========================================================

SELECT
    'accounts' AS table_name,
    COUNT(*) AS row_count
FROM accounts

UNION ALL

SELECT
    'subscriptions',
    COUNT(*)
FROM subscriptions

UNION ALL

SELECT
    'product_usage',
    COUNT(*)
FROM product_usage

UNION ALL

SELECT
    'support_tickets',
    COUNT(*)
FROM support_tickets

UNION ALL

SELECT
    'invoices',
    COUNT(*)
FROM invoices

UNION ALL

SELECT
    'customer_success_interactions',
    COUNT(*)
FROM customer_success_interactions;


-- =========================================================
-- 2. EXPECTED ROW COUNTS
--
-- Expected:
-- accounts                         500
-- subscriptions                    980
-- product_usage                   8184
-- support_tickets                 3792
-- invoices                        4420
-- customer_success_interactions   3086
-- =========================================================

WITH actual_counts AS (

    SELECT
        'accounts' AS table_name,
        COUNT(*) AS actual_rows
    FROM accounts

    UNION ALL

    SELECT
        'subscriptions',
        COUNT(*)
    FROM subscriptions

    UNION ALL

    SELECT
        'product_usage',
        COUNT(*)
    FROM product_usage

    UNION ALL

    SELECT
        'support_tickets',
        COUNT(*)
    FROM support_tickets

    UNION ALL

    SELECT
        'invoices',
        COUNT(*)
    FROM invoices

    UNION ALL

    SELECT
        'customer_success_interactions',
        COUNT(*)
    FROM customer_success_interactions
),

expected_counts AS (

    SELECT
        'accounts' AS table_name,
        500::BIGINT AS expected_rows

    UNION ALL
    SELECT
        'subscriptions',
        980

    UNION ALL
    SELECT
        'product_usage',
        8184

    UNION ALL
    SELECT
        'support_tickets',
        3792

    UNION ALL
    SELECT
        'invoices',
        4420

    UNION ALL
    SELECT
        'customer_success_interactions',
        3086
)

SELECT
    e.table_name,
    e.expected_rows,
    a.actual_rows,

    CASE
        WHEN e.expected_rows = a.actual_rows
            THEN 'PASS'
        ELSE 'FAIL'
    END AS validation_status

FROM expected_counts AS e

INNER JOIN actual_counts AS a
    ON e.table_name = a.table_name

ORDER BY e.table_name;


-- =========================================================
-- 3. PRIMARY KEY UNIQUENESS
--
-- All duplicate counts should be 0.
-- =========================================================

SELECT
    'accounts' AS table_name,
    COUNT(*) - COUNT(DISTINCT account_id)
        AS duplicate_primary_keys
FROM accounts

UNION ALL

SELECT
    'subscriptions',
    COUNT(*) - COUNT(DISTINCT subscription_id)
FROM subscriptions

UNION ALL

SELECT
    'product_usage',
    COUNT(*) - COUNT(DISTINCT usage_id)
FROM product_usage

UNION ALL

SELECT
    'support_tickets',
    COUNT(*) - COUNT(DISTINCT ticket_id)
FROM support_tickets

UNION ALL

SELECT
    'invoices',
    COUNT(*) - COUNT(DISTINCT invoice_id)
FROM invoices

UNION ALL

SELECT
    'customer_success_interactions',
    COUNT(*) - COUNT(DISTINCT interaction_id)
FROM customer_success_interactions;


-- =========================================================
-- 4. FOREIGN KEY / ORPHAN VALIDATION
--
-- All orphan counts should be 0.
-- =========================================================

SELECT
    'subscriptions' AS child_table,
    COUNT(*) AS orphan_rows

FROM subscriptions AS s

LEFT JOIN accounts AS a
    ON s.account_id = a.account_id

WHERE a.account_id IS NULL

UNION ALL

SELECT
    'product_usage',
    COUNT(*)

FROM product_usage AS p

LEFT JOIN accounts AS a
    ON p.account_id = a.account_id

WHERE a.account_id IS NULL

UNION ALL

SELECT
    'support_tickets',
    COUNT(*)

FROM support_tickets AS st

LEFT JOIN accounts AS a
    ON st.account_id = a.account_id

WHERE a.account_id IS NULL

UNION ALL

SELECT
    'invoices',
    COUNT(*)

FROM invoices AS i

LEFT JOIN accounts AS a
    ON i.account_id = a.account_id

WHERE a.account_id IS NULL

UNION ALL

SELECT
    'customer_success_interactions',
    COUNT(*)

FROM customer_success_interactions AS c

LEFT JOIN accounts AS a
    ON c.account_id = a.account_id

WHERE a.account_id IS NULL;


-- =========================================================
-- 5. ACCOUNT STATUS SUMMARY
-- =========================================================

SELECT
    customer_status,
    COUNT(*) AS account_count
FROM accounts
GROUP BY customer_status
ORDER BY customer_status;


-- =========================================================
-- 6. CUSTOMER SEGMENT SUMMARY
-- =========================================================

SELECT
    segment,
    COUNT(*) AS account_count
FROM accounts
GROUP BY segment
ORDER BY account_count DESC;


-- =========================================================
-- 7. ACCOUNT DATA QUALITY
--
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
-- 8. ACCOUNT CHURN DATE RULES
--
-- Expected violations = 0
-- =========================================================

SELECT
    COUNT(*) AS account_status_date_violations

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
-- 9. SUBSCRIPTION STATUS SUMMARY
--
-- Expected:
-- Active 426
-- Churned 74
-- Renewed 480
-- =========================================================

SELECT
    subscription_status,
    COUNT(*) AS subscription_count
FROM subscriptions
GROUP BY subscription_status
ORDER BY subscription_status;


-- =========================================================
-- 10. ACTIVE CUSTOMER / SUBSCRIPTION CONSISTENCY
--
-- Expected:
-- active_accounts = 426
-- active_subscriptions = 426
-- =========================================================

SELECT
    (
        SELECT COUNT(*)
        FROM accounts
        WHERE customer_status = 'Active'
    ) AS active_accounts,

    (
        SELECT COUNT(*)
        FROM subscriptions
        WHERE subscription_status = 'Active'
    ) AS active_subscriptions;


-- =========================================================
-- 11. ACTIVE ACCOUNTS WITHOUT ACTIVE SUBSCRIPTION
--
-- Expected: 0
-- =========================================================

SELECT
    COUNT(*) AS active_accounts_without_subscription

FROM accounts AS a

LEFT JOIN subscriptions AS s
    ON a.account_id = s.account_id
    AND s.subscription_status = 'Active'

WHERE a.customer_status = 'Active'
  AND s.subscription_id IS NULL;


-- =========================================================
-- 12. ACTIVE ACCOUNTS WITH MULTIPLE ACTIVE SUBSCRIPTIONS
--
-- Expected: 0
-- =========================================================

SELECT
    COUNT(*) AS accounts_with_multiple_active_subscriptions

FROM (

    SELECT
        account_id

    FROM subscriptions

    WHERE subscription_status = 'Active'

    GROUP BY account_id

    HAVING COUNT(*) > 1

) AS duplicate_active_subscriptions;


-- =========================================================
-- 13. CURRENT RECURRING REVENUE
--
-- Expected:
-- MRR = 1,574,850
-- ARR = 18,898,200
-- =========================================================

SELECT
    SUM(mrr) AS current_mrr,
    SUM(mrr) * 12 AS current_arr

FROM subscriptions

WHERE subscription_status = 'Active';


-- =========================================================
-- 14. PRODUCT USAGE UNIQUENESS
--
-- Expected duplicate account-month combinations = 0
-- =========================================================

SELECT
    COUNT(*) AS duplicate_account_months

FROM (

    SELECT
        account_id,
        usage_month

    FROM product_usage

    GROUP BY
        account_id,
        usage_month

    HAVING COUNT(*) > 1

) AS duplicate_months;


-- =========================================================
-- 15. PRODUCT USAGE BUSINESS RULES
--
-- Expected violations = 0
-- =========================================================

SELECT
    COUNT(*) AS product_usage_rule_violations

FROM product_usage

WHERE
    licensed_users < 0
    OR active_users < 0
    OR active_users > licensed_users
    OR login_count < 0
    OR dashboards_viewed < 0
    OR reports_generated < 0
    OR alerts_created < 0
    OR core_features_used < 0
    OR core_features_used > 8;


-- =========================================================
-- 16. PRODUCT USAGE DATE RANGE
-- =========================================================

SELECT
    MIN(usage_month) AS earliest_usage_month,
    MAX(usage_month) AS latest_usage_month,
    COUNT(DISTINCT usage_month)
        AS months_of_usage_data

FROM product_usage;


-- =========================================================
-- 17. SUPPORT TICKET BUSINESS RULES
--
-- Expected violations = 0
-- =========================================================

SELECT
    COUNT(*) AS support_ticket_rule_violations

FROM support_tickets

WHERE
    resolution_hours < 0

    OR customer_satisfaction_score < 1

    OR customer_satisfaction_score > 5

    OR resolved_date < created_date

    OR (
        ticket_status = 'Resolved'
        AND (
            resolved_date IS NULL
            OR resolution_hours IS NULL
        )
    )

    OR (
        ticket_status <> 'Resolved'
        AND (
            resolved_date IS NOT NULL
            OR resolution_hours IS NOT NULL
            OR customer_satisfaction_score IS NOT NULL
        )
    );


-- =========================================================
-- 18. SUPPORT SUMMARY
-- =========================================================

SELECT
    COUNT(*) AS total_support_tickets,

    COUNT(DISTINCT account_id)
        AS accounts_with_support_tickets,

    ROUND(
        AVG(resolution_hours)
            FILTER (
                WHERE ticket_status = 'Resolved'
            ),
        2
    ) AS avg_resolution_hours,

    ROUND(
        AVG(customer_satisfaction_score)
            FILTER (
                WHERE customer_satisfaction_score
                IS NOT NULL
            ),
        2
    ) AS avg_csat

FROM support_tickets;


-- =========================================================
-- 19. INVOICE BUSINESS RULES
--
-- Expected violations = 0
-- =========================================================

SELECT
    COUNT(*) AS invoice_rule_violations

FROM invoices

WHERE
    invoice_amount <= 0

    OR days_late < 0

    OR due_date < invoice_date

    OR payment_date < invoice_date

    OR (
        payment_status = 'Paid'
        AND (
            payment_date IS NULL
            OR payment_date > due_date
            OR days_late <> 0
        )
    )

    OR (
        payment_status = 'Late'
        AND (
            payment_date IS NULL
            OR payment_date <= due_date
            OR days_late <= 0
            OR payment_date - due_date <> days_late
        )
    )

    OR (
        payment_status = 'Pending'
        AND (
            payment_date IS NOT NULL
            OR days_late <> 0
        )
    )

    OR (
        payment_status = 'Failed'
        AND (
            payment_date IS NOT NULL
            OR days_late <= 0
        )
    );


-- =========================================================
-- 20. INVOICE SUMMARY
--
-- Expected:
-- invoice total = 31,880,975
-- missing payment methods = 15
-- =========================================================

SELECT
    COUNT(*) AS total_invoices,

    COUNT(DISTINCT account_id)
        AS accounts_with_invoices,

    SUM(invoice_amount)
        AS total_invoice_value,

    COUNT(*) FILTER (
        WHERE payment_method IS NULL
    ) AS missing_payment_methods,

    ROUND(
        AVG(days_late)
            FILTER (
                WHERE payment_status = 'Late'
            ),
        2
    ) AS average_days_late

FROM invoices;


-- =========================================================
-- 21. CUSTOMER SUCCESS BUSINESS RULES
--
-- Expected violations = 0
-- =========================================================

SELECT
    COUNT(*) AS cs_interaction_rule_violations

FROM customer_success_interactions AS c

INNER JOIN accounts AS a
    ON c.account_id = a.account_id

WHERE
    c.interaction_date < a.signup_date

    OR (
        a.churn_date IS NOT NULL
        AND c.interaction_date > a.churn_date
    )

    OR (
        c.next_follow_up_date IS NOT NULL
        AND c.next_follow_up_date
            < c.interaction_date
    )

    OR (
        c.follow_up_required = FALSE
        AND c.next_follow_up_date IS NOT NULL
    )

    OR (
        a.assigned_csm IS NOT NULL
        AND c.csm_name IS NOT NULL
        AND a.assigned_csm <> c.csm_name
    );


-- =========================================================
-- 22. CUSTOMER SUCCESS SUMMARY
--
-- Expected:
-- total interactions = 3086
-- accounts = 487
-- missing CSM = 33
-- required follow-ups without date = 7
-- =========================================================

SELECT
    COUNT(*) AS total_interactions,

    COUNT(DISTINCT account_id)
        AS accounts_with_interactions,

    COUNT(*) FILTER (
        WHERE csm_name IS NULL
    ) AS missing_csm,

    COUNT(*) FILTER (
        WHERE follow_up_required = TRUE
        AND next_follow_up_date IS NULL
    ) AS required_followups_without_date

FROM customer_success_interactions;


-- =========================================================
-- 23. ACCOUNT COVERAGE ACROSS ALL DATASETS
-- =========================================================

SELECT
    'subscriptions' AS dataset,
    COUNT(DISTINCT account_id)
        AS accounts_represented
FROM subscriptions

UNION ALL

SELECT
    'product_usage',
    COUNT(DISTINCT account_id)
FROM product_usage

UNION ALL

SELECT
    'support_tickets',
    COUNT(DISTINCT account_id)
FROM support_tickets

UNION ALL

SELECT
    'invoices',
    COUNT(DISTINCT account_id)
FROM invoices

UNION ALL

SELECT
    'customer_success_interactions',
    COUNT(DISTINCT account_id)
FROM customer_success_interactions;


-- =========================================================
-- 24. ANALYSIS-PERIOD DATE COVERAGE
-- =========================================================

SELECT
    'product_usage' AS dataset,
    MIN(usage_month)::DATE AS earliest_date,
    MAX(usage_month)::DATE AS latest_date
FROM product_usage

UNION ALL

SELECT
    'support_tickets',
    MIN(created_date),
    MAX(created_date)
FROM support_tickets

UNION ALL

SELECT
    'invoices',
    MIN(invoice_date),
    MAX(invoice_date)
FROM invoices

UNION ALL

SELECT
    'customer_success_interactions',
    MIN(interaction_date),
    MAX(interaction_date)
FROM customer_success_interactions;


-- =========================================================
-- 25. CURRENT ACTIVE CUSTOMER SNAPSHOT
--
-- Combines accounts and subscriptions only.
-- More behavioral metrics will be added during analysis.
-- =========================================================

SELECT
    a.segment,

    COUNT(*) AS active_accounts,

    SUM(s.mrr) AS current_mrr,

    SUM(s.mrr) * 12 AS current_arr

FROM accounts AS a

INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id

WHERE a.customer_status = 'Active'
  AND s.subscription_status = 'Active'

GROUP BY a.segment

ORDER BY current_arr DESC;


-- =========================================================
-- 26. FINAL DATABASE READINESS SUMMARY
-- =========================================================

SELECT
    (
        SELECT COUNT(*)
        FROM accounts
    ) AS accounts,

    (
        SELECT COUNT(*)
        FROM subscriptions
    ) AS subscriptions,

    (
        SELECT COUNT(*)
        FROM product_usage
    ) AS product_usage_rows,

    (
        SELECT COUNT(*)
        FROM support_tickets
    ) AS support_tickets,

    (
        SELECT COUNT(*)
        FROM invoices
    ) AS invoices,

    (
        SELECT COUNT(*)
        FROM customer_success_interactions
    ) AS cs_interactions;
    