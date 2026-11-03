-- Customer Health & Revenue Risk Analytics
-- Exploratory SQL Analysis
--
-- Purpose:
-- Understand the current customer portfolio and identify
-- behavioral patterns that may later contribute to the
-- Customer Health Score and revenue-at-risk analysis.


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- 1. CUSTOMER PORTFOLIO SUMMARY
-- =========================================================

SELECT
    COUNT(*) AS total_accounts,

    COUNT(*) FILTER (
        WHERE customer_status = 'Active'
    ) AS active_accounts,

    COUNT(*) FILTER (
        WHERE customer_status = 'Churned'
    ) AS churned_accounts,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE customer_status = 'Churned'
            )
        )::NUMERIC
        / COUNT(*)
        * 100,
        2
    ) AS historical_churn_pct

FROM accounts;


-- =========================================================
-- 2. CURRENT RECURRING REVENUE
-- =========================================================

SELECT
    COUNT(*) AS active_subscriptions,

    SUM(mrr) AS current_mrr,

    SUM(mrr) * 12 AS current_arr,

    ROUND(
        AVG(mrr),
        2
    ) AS average_mrr_per_active_account

FROM subscriptions

WHERE subscription_status = 'Active';


-- =========================================================
-- 3. ACTIVE CUSTOMER AND REVENUE MIX BY SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(*) AS active_accounts,

    SUM(s.mrr) AS current_mrr,

    SUM(s.mrr) * 12 AS current_arr,

    ROUND(
        AVG(s.mrr),
        2
    ) AS average_mrr,

    ROUND(
        SUM(s.mrr)::NUMERIC
        / (
            SELECT SUM(mrr)
            FROM subscriptions
            WHERE subscription_status = 'Active'
        )
        * 100,
        2
    ) AS percentage_of_current_mrr

FROM accounts AS a

INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id

WHERE a.customer_status = 'Active'
  AND s.subscription_status = 'Active'

GROUP BY a.segment

ORDER BY current_arr DESC;


-- =========================================================
-- 4. HISTORICAL CHURN RATE BY SEGMENT
--
-- This is descriptive only.
-- It is not yet a predictive churn model.
-- =========================================================

SELECT
    segment,

    COUNT(*) AS total_accounts,

    COUNT(*) FILTER (
        WHERE customer_status = 'Churned'
    ) AS churned_accounts,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE customer_status = 'Churned'
            )
        )::NUMERIC
        / COUNT(*)
        * 100,
        2
    ) AS historical_churn_pct

FROM accounts

GROUP BY segment

ORDER BY historical_churn_pct DESC;


-- =========================================================
-- 5. CURRENT ACTIVE PLAN MIX
-- =========================================================

SELECT
    plan_name,

    COUNT(*) AS active_accounts,

    SUM(mrr) AS current_mrr,

    SUM(mrr) * 12 AS current_arr,

    ROUND(
        AVG(mrr),
        2
    ) AS average_mrr

FROM subscriptions

WHERE subscription_status = 'Active'

GROUP BY plan_name

ORDER BY current_arr DESC;


-- =========================================================
-- 6. LATEST PRODUCT USAGE FOR ACTIVE CUSTOMERS
--
-- Take the most recent usage row available for each
-- currently active account.
-- =========================================================

WITH latest_usage_ranked AS (

    SELECT
        p.account_id,
        p.usage_month,
        p.licensed_users,
        p.active_users,
        p.login_count,
        p.dashboards_viewed,
        p.reports_generated,
        p.alerts_created,
        p.core_features_used,

        ROW_NUMBER() OVER (
            PARTITION BY p.account_id
            ORDER BY p.usage_month DESC
        ) AS row_num

    FROM product_usage AS p

    INNER JOIN accounts AS a
        ON p.account_id = a.account_id

    WHERE a.customer_status = 'Active'
),

latest_usage AS (

    SELECT *
    FROM latest_usage_ranked
    WHERE row_num = 1
)

SELECT
    a.segment,

    COUNT(*) AS active_accounts,

    ROUND(
        AVG(
            l.active_users::NUMERIC
            / NULLIF(
                l.licensed_users,
                0
            )
        )
        * 100,
        2
    ) AS avg_active_user_rate_pct,

    ROUND(
        AVG(
            l.core_features_used::NUMERIC
            / 8
        )
        * 100,
        2
    ) AS avg_feature_adoption_pct,

    ROUND(
        AVG(l.login_count),
        2
    ) AS avg_monthly_logins

FROM latest_usage AS l

INNER JOIN accounts AS a
    ON l.account_id = a.account_id

GROUP BY a.segment

ORDER BY a.segment;


-- =========================================================
-- 7. ACTIVE ACCOUNTS WITH LOW CURRENT USAGE
--
-- Initial exploratory threshold:
-- active-user rate below 40%.
--
-- This is not yet a final Health Score threshold.
-- =========================================================

WITH latest_usage_ranked AS (

    SELECT
        p.*,

        ROW_NUMBER() OVER (
            PARTITION BY p.account_id
            ORDER BY p.usage_month DESC
        ) AS row_num

    FROM product_usage AS p
),

latest_usage AS (

    SELECT *
    FROM latest_usage_ranked
    WHERE row_num = 1
)

SELECT
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr,
    l.usage_month,
    l.licensed_users,
    l.active_users,

    ROUND(
        l.active_users::NUMERIC
        / NULLIF(
            l.licensed_users,
            0
        )
        * 100,
        2
    ) AS active_user_rate_pct,

    l.core_features_used

FROM accounts AS a

INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id
    AND s.subscription_status = 'Active'

INNER JOIN latest_usage AS l
    ON a.account_id = l.account_id

WHERE a.customer_status = 'Active'

  AND (
        l.active_users::NUMERIC
        / NULLIF(
            l.licensed_users,
            0
        )
      ) < 0.40

ORDER BY
    s.mrr DESC,
    active_user_rate_pct ASC

LIMIT 20;


-- =========================================================
-- 8. PRODUCT USAGE TREND
--
-- Compare average active-user rate during the latest
-- 3 months with the previous 3 months for each active
-- account.
-- =========================================================

WITH active_usage AS (

    SELECT
        p.account_id,
        p.usage_month,

        p.active_users::NUMERIC
        / NULLIF(
            p.licensed_users,
            0
        ) AS active_user_rate,

        ROW_NUMBER() OVER (
            PARTITION BY p.account_id
            ORDER BY p.usage_month DESC
        ) AS month_rank

    FROM product_usage AS p

    INNER JOIN accounts AS a
        ON p.account_id = a.account_id

    WHERE a.customer_status = 'Active'
),

usage_windows AS (

    SELECT
        account_id,

        AVG(active_user_rate) FILTER (
            WHERE month_rank BETWEEN 1 AND 3
        ) AS latest_3_month_rate,

        AVG(active_user_rate) FILTER (
            WHERE month_rank BETWEEN 4 AND 6
        ) AS previous_3_month_rate

    FROM active_usage

    GROUP BY account_id
),

usage_trends AS (

    SELECT
        account_id,
        latest_3_month_rate,
        previous_3_month_rate,

        latest_3_month_rate
        - previous_3_month_rate
            AS usage_rate_change

    FROM usage_windows

    WHERE latest_3_month_rate IS NOT NULL
      AND previous_3_month_rate IS NOT NULL
)

SELECT
    a.segment,

    COUNT(*) AS accounts_with_six_months_history,

    ROUND(
        AVG(
            latest_3_month_rate
        ) * 100,
        2
    ) AS latest_3_month_active_rate_pct,

    ROUND(
        AVG(
            previous_3_month_rate
        ) * 100,
        2
    ) AS previous_3_month_active_rate_pct,

    ROUND(
        AVG(
            usage_rate_change
        ) * 100,
        2
    ) AS avg_percentage_point_change

FROM usage_trends AS u

INNER JOIN accounts AS a
    ON u.account_id = a.account_id

GROUP BY a.segment

ORDER BY a.segment;


-- =========================================================
-- 9. ACCOUNTS WITH LARGEST USAGE DECLINES
-- =========================================================

WITH active_usage AS (

    SELECT
        p.account_id,
        p.usage_month,

        p.active_users::NUMERIC
        / NULLIF(
            p.licensed_users,
            0
        ) AS active_user_rate,

        ROW_NUMBER() OVER (
            PARTITION BY p.account_id
            ORDER BY p.usage_month DESC
        ) AS month_rank

    FROM product_usage AS p

    INNER JOIN accounts AS a
        ON p.account_id = a.account_id

    WHERE a.customer_status = 'Active'
),

usage_windows AS (

    SELECT
        account_id,

        AVG(active_user_rate) FILTER (
            WHERE month_rank BETWEEN 1 AND 3
        ) AS latest_3_month_rate,

        AVG(active_user_rate) FILTER (
            WHERE month_rank BETWEEN 4 AND 6
        ) AS previous_3_month_rate

    FROM active_usage

    GROUP BY account_id
),

usage_trends AS (

    SELECT
        account_id,
        latest_3_month_rate,
        previous_3_month_rate,

        latest_3_month_rate
        - previous_3_month_rate
            AS usage_rate_change

    FROM usage_windows

    WHERE latest_3_month_rate IS NOT NULL
      AND previous_3_month_rate IS NOT NULL
)

SELECT
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr,

    ROUND(
        u.previous_3_month_rate
        * 100,
        2
    ) AS previous_3_month_rate_pct,

    ROUND(
        u.latest_3_month_rate
        * 100,
        2
    ) AS latest_3_month_rate_pct,

    ROUND(
        u.usage_rate_change
        * 100,
        2
    ) AS percentage_point_change

FROM usage_trends AS u

INNER JOIN accounts AS a
    ON u.account_id = a.account_id

INNER JOIN subscriptions AS s
    ON u.account_id = s.account_id
    AND s.subscription_status = 'Active'

ORDER BY
    u.usage_rate_change ASC,
    s.mrr DESC

LIMIT 20;


-- =========================================================
-- 10. SUPPORT TICKET PROFILE BY SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(st.ticket_id)
        AS total_tickets,

    COUNT(*) FILTER (
        WHERE st.priority IN (
            'High',
            'Critical'
        )
    ) AS high_critical_tickets,

    ROUND(
        AVG(st.resolution_hours)
            FILTER (
                WHERE st.ticket_status = 'Resolved'
            ),
        2
    ) AS avg_resolution_hours,

    ROUND(
        AVG(st.customer_satisfaction_score)
            FILTER (
                WHERE st.customer_satisfaction_score
                IS NOT NULL
            ),
        2
    ) AS avg_csat

FROM support_tickets AS st

INNER JOIN accounts AS a
    ON st.account_id = a.account_id

GROUP BY a.segment

ORDER BY total_tickets DESC;


-- =========================================================
-- 11. RECENT SUPPORT PRESSURE
--
-- Use the final 90 days of the analysis period.
-- =========================================================

SELECT
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr,

    COUNT(st.ticket_id)
        AS tickets_last_90_days,

    COUNT(*) FILTER (
        WHERE st.priority IN (
            'High',
            'Critical'
        )
    ) AS high_critical_tickets_last_90_days,

    COUNT(*) FILTER (
        WHERE st.ticket_status <> 'Resolved'
    ) AS unresolved_tickets

FROM accounts AS a

INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id
    AND s.subscription_status = 'Active'

LEFT JOIN support_tickets AS st
    ON a.account_id = st.account_id
    AND st.created_date
        BETWEEN DATE '2026-10-03'
        AND DATE '2026-12-31'

WHERE a.customer_status = 'Active'

GROUP BY
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr

HAVING COUNT(st.ticket_id) > 0

ORDER BY
    high_critical_tickets_last_90_days DESC,
    tickets_last_90_days DESC,
    s.mrr DESC

LIMIT 20;


-- =========================================================
-- 12. PAYMENT PERFORMANCE BY SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(i.invoice_id)
        AS total_invoices,

    COUNT(*) FILTER (
        WHERE i.payment_status = 'Paid'
    ) AS paid_invoices,

    COUNT(*) FILTER (
        WHERE i.payment_status = 'Late'
    ) AS late_invoices,

    COUNT(*) FILTER (
        WHERE i.payment_status = 'Failed'
    ) AS failed_invoices,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE i.payment_status
                IN (
                    'Late',
                    'Failed'
                )
            )
        )::NUMERIC
        / NULLIF(
            COUNT(i.invoice_id),
            0
        )
        * 100,
        2
    ) AS payment_issue_rate_pct

FROM invoices AS i

INNER JOIN accounts AS a
    ON i.account_id = a.account_id

GROUP BY a.segment

ORDER BY payment_issue_rate_pct DESC;


-- =========================================================
-- 13. ACTIVE ACCOUNTS WITH PAYMENT ISSUES
--
-- Look at the last 6 months of the analysis period.
-- =========================================================

SELECT
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr,

    COUNT(i.invoice_id)
        AS invoices_last_6_months,

    COUNT(*) FILTER (
        WHERE i.payment_status = 'Late'
    ) AS late_invoices,

    COUNT(*) FILTER (
        WHERE i.payment_status = 'Failed'
    ) AS failed_invoices,

    MAX(i.days_late)
        AS maximum_days_late

FROM accounts AS a

INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id
    AND s.subscription_status = 'Active'

LEFT JOIN invoices AS i
    ON a.account_id = i.account_id
    AND i.invoice_date
        BETWEEN DATE '2026-07-01'
        AND DATE '2026-12-31'

WHERE a.customer_status = 'Active'

GROUP BY
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr

HAVING
    COUNT(*) FILTER (
        WHERE i.payment_status
        IN (
            'Late',
            'Failed'
        )
    ) > 0

ORDER BY
    failed_invoices DESC,
    late_invoices DESC,
    s.mrr DESC

LIMIT 20;


-- =========================================================
-- 14. CUSTOMER SUCCESS ENGAGEMENT BY SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(c.interaction_id)
        AS total_interactions,

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
            COUNT(c.interaction_id),
            0
        )
        * 100,
        2
    ) AS unresponsive_rate_pct

FROM customer_success_interactions AS c

INNER JOIN accounts AS a
    ON c.account_id = a.account_id

GROUP BY a.segment

ORDER BY unresponsive_rate_pct DESC;


-- =========================================================
-- 15. RECENT CUSTOMER SUCCESS ENGAGEMENT
--
-- Final 90 days of the analysis period.
-- =========================================================

SELECT
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr,

    COUNT(c.interaction_id)
        AS interactions_last_90_days,

    COUNT(*) FILTER (
        WHERE c.engagement_status = 'Unresponsive'
    ) AS unresponsive_interactions,

    COUNT(*) FILTER (
        WHERE c.follow_up_required = TRUE
    ) AS followups_required,

    MAX(c.interaction_date)
        AS most_recent_interaction

FROM accounts AS a

INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id
    AND s.subscription_status = 'Active'

LEFT JOIN customer_success_interactions AS c
    ON a.account_id = c.account_id
    AND c.interaction_date
        BETWEEN DATE '2026-10-03'
        AND DATE '2026-12-31'

WHERE a.customer_status = 'Active'

GROUP BY
    a.account_id,
    a.account_name,
    a.segment,
    s.mrr

HAVING COUNT(c.interaction_id) > 0

ORDER BY
    unresponsive_interactions DESC,
    followups_required DESC,
    s.mrr DESC

LIMIT 20;


-- =========================================================
-- 16. CURRENT ACTIVE CUSTOMER BASE FOR NEXT PHASE
--
-- This confirms the population that will eventually
-- receive a current Customer Health Score.
-- =========================================================

SELECT
    COUNT(*) AS health_score_population,

    SUM(s.mrr) AS health_score_population_mrr,

    SUM(s.mrr) * 12
        AS health_score_population_arr

FROM accounts AS a

INNER JOIN subscriptions AS s
    ON a.account_id = s.account_id

WHERE a.customer_status = 'Active'
  AND s.subscription_status = 'Active';
  