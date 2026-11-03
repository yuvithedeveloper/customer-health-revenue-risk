-- Customer Health & Revenue Risk Analytics
-- Account-Level Analytical Base
--
-- Purpose:
-- Create one reusable row per currently active customer
-- containing the revenue, usage, support, payment,
-- renewal, and Customer Success metrics required for
-- later Customer Health Score development.
--
-- Analysis snapshot date:
-- 2026-12-31


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- DROP VIEW IF IT ALREADY EXISTS
-- =========================================================

DROP VIEW IF EXISTS vw_account_health_base;


-- =========================================================
-- CREATE ACCOUNT HEALTH BASE VIEW
-- =========================================================

CREATE VIEW vw_account_health_base AS


WITH


-- =========================================================
-- 1. CURRENT ACTIVE SUBSCRIPTION
-- =========================================================

current_subscription AS (

    SELECT
        subscription_id,
        account_id,
        plan_name,
        billing_frequency,
        subscription_start_date,
        subscription_end_date,
        renewal_date,
        mrr,

        mrr * 12 AS arr,

        renewal_date
        - DATE '2026-12-31'
            AS days_to_renewal

    FROM subscriptions

    WHERE subscription_status = 'Active'
),


-- =========================================================
-- 2. RANK PRODUCT-USAGE MONTHS
--
-- month_rank = 1 means the most recent month available
-- for that account.
-- =========================================================

usage_ranked AS (

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
        ) AS month_rank

    FROM product_usage AS p

    INNER JOIN accounts AS a
        ON p.account_id = a.account_id

    WHERE a.customer_status = 'Active'
),


-- =========================================================
-- 3. PRODUCT-USAGE SUMMARY
--
-- Includes:
-- latest usage
-- latest feature adoption
-- latest 3 months
-- previous 3 months
-- 3-month usage trend
-- =========================================================

usage_summary AS (

    SELECT
        account_id,

        MAX(usage_month) FILTER (
            WHERE month_rank = 1
        ) AS latest_usage_month,


        MAX(licensed_users) FILTER (
            WHERE month_rank = 1
        ) AS latest_licensed_users,


        MAX(active_users) FILTER (
            WHERE month_rank = 1
        ) AS latest_active_users,


        MAX(login_count) FILTER (
            WHERE month_rank = 1
        ) AS latest_login_count,


        MAX(dashboards_viewed) FILTER (
            WHERE month_rank = 1
        ) AS latest_dashboards_viewed,


        MAX(reports_generated) FILTER (
            WHERE month_rank = 1
        ) AS latest_reports_generated,


        MAX(alerts_created) FILTER (
            WHERE month_rank = 1
        ) AS latest_alerts_created,


        MAX(core_features_used) FILTER (
            WHERE month_rank = 1
        ) AS latest_core_features_used,


        MAX(
            active_users::NUMERIC
            / NULLIF(
                licensed_users,
                0
            )
        ) FILTER (
            WHERE month_rank = 1
        ) AS latest_active_user_rate,


        MAX(
            core_features_used::NUMERIC
            / 8
        ) FILTER (
            WHERE month_rank = 1
        ) AS latest_feature_adoption_rate,


        AVG(
            active_users::NUMERIC
            / NULLIF(
                licensed_users,
                0
            )
        ) FILTER (
            WHERE month_rank BETWEEN 1 AND 3
        ) AS latest_3_month_active_rate,


        AVG(
            active_users::NUMERIC
            / NULLIF(
                licensed_users,
                0
            )
        ) FILTER (
            WHERE month_rank BETWEEN 4 AND 6
        ) AS previous_3_month_active_rate

    FROM usage_ranked

    GROUP BY account_id
),


-- =========================================================
-- 4. RECENT SUPPORT ACTIVITY
--
-- Final 90 days of analysis period:
-- 2026-10-03 through 2026-12-31
-- =========================================================

support_90d AS (

    SELECT
        account_id,

        COUNT(*) AS tickets_90d,


        COUNT(*) FILTER (
            WHERE priority IN (
                'High',
                'Critical'
            )
        ) AS high_critical_tickets_90d,


        COUNT(*) FILTER (
            WHERE ticket_status <> 'Resolved'
        ) AS unresolved_tickets_90d,


        ROUND(
            AVG(resolution_hours)
                FILTER (
                    WHERE ticket_status = 'Resolved'
                ),
            2
        ) AS avg_resolution_hours_90d,


        ROUND(
            AVG(customer_satisfaction_score)
                FILTER (
                    WHERE customer_satisfaction_score
                    IS NOT NULL
                ),
            2
        ) AS avg_csat_90d

    FROM support_tickets

    WHERE created_date
        BETWEEN DATE '2026-10-03'
        AND DATE '2026-12-31'

    GROUP BY account_id
),


-- =========================================================
-- 5. RECENT PAYMENT ACTIVITY
--
-- Final six months:
-- 2026-07-01 through 2026-12-31
-- =========================================================

payment_6m AS (

    SELECT
        account_id,

        COUNT(*) AS invoices_6m,


        COUNT(*) FILTER (
            WHERE payment_status = 'Paid'
        ) AS paid_invoices_6m,


        COUNT(*) FILTER (
            WHERE payment_status = 'Late'
        ) AS late_invoices_6m,


        COUNT(*) FILTER (
            WHERE payment_status = 'Failed'
        ) AS failed_invoices_6m,


        COUNT(*) FILTER (
            WHERE payment_status = 'Pending'
        ) AS pending_invoices_6m,


        MAX(days_late)
            AS max_days_late_6m,


        ROUND(
            (
                COUNT(*) FILTER (
                    WHERE payment_status IN (
                        'Late',
                        'Failed'
                    )
                )
            )::NUMERIC
            / NULLIF(
                COUNT(*),
                0
            )
            * 100,
            2
        ) AS payment_issue_rate_6m_pct

    FROM invoices

    WHERE invoice_date
        BETWEEN DATE '2026-07-01'
        AND DATE '2026-12-31'

    GROUP BY account_id
),


-- =========================================================
-- 6. CUSTOMER SUCCESS ACTIVITY
--
-- Use all history for most recent interaction date,
-- plus the final 90 days for recent engagement.
-- =========================================================

cs_summary AS (

    SELECT
        account_id,

        MAX(interaction_date)
            AS most_recent_interaction_date,


        COUNT(*) FILTER (
            WHERE interaction_date
                BETWEEN DATE '2026-10-03'
                AND DATE '2026-12-31'
        ) AS interactions_90d,


        COUNT(*) FILTER (
            WHERE interaction_date
                BETWEEN DATE '2026-10-03'
                AND DATE '2026-12-31'
              AND engagement_status = 'Engaged'
        ) AS engaged_interactions_90d,


        COUNT(*) FILTER (
            WHERE interaction_date
                BETWEEN DATE '2026-10-03'
                AND DATE '2026-12-31'
              AND engagement_status = 'Neutral'
        ) AS neutral_interactions_90d,


        COUNT(*) FILTER (
            WHERE interaction_date
                BETWEEN DATE '2026-10-03'
                AND DATE '2026-12-31'
              AND engagement_status = 'Unresponsive'
        ) AS unresponsive_interactions_90d,


        COUNT(*) FILTER (
            WHERE interaction_date
                BETWEEN DATE '2026-10-03'
                AND DATE '2026-12-31'
              AND follow_up_required = TRUE
        ) AS followups_required_90d,


        COUNT(*) FILTER (
            WHERE follow_up_required = TRUE
              AND next_follow_up_date IS NULL
        ) AS followups_without_date_all_time

    FROM customer_success_interactions

    GROUP BY account_id
)


-- =========================================================
-- 7. FINAL ONE-ROW-PER-ACTIVE-ACCOUNT VIEW
-- =========================================================

SELECT
    a.account_id,
    a.account_name,
    a.industry,
    a.segment,
    a.region,
    a.signup_date,
    a.assigned_csm,


    -- -----------------------------------------------------
    -- SUBSCRIPTION / REVENUE
    -- -----------------------------------------------------

    s.plan_name,
    s.billing_frequency,
    s.subscription_start_date,
    s.subscription_end_date,
    s.renewal_date,
    s.days_to_renewal,
    s.mrr,
    s.arr,


    -- -----------------------------------------------------
    -- PRODUCT USAGE
    -- -----------------------------------------------------

    u.latest_usage_month,
    u.latest_licensed_users,
    u.latest_active_users,
    u.latest_login_count,
    u.latest_dashboards_viewed,
    u.latest_reports_generated,
    u.latest_alerts_created,
    u.latest_core_features_used,


    ROUND(
        u.latest_active_user_rate
        * 100,
        2
    ) AS latest_active_user_rate_pct,


    ROUND(
        u.latest_feature_adoption_rate
        * 100,
        2
    ) AS latest_feature_adoption_pct,


    ROUND(
        u.latest_3_month_active_rate
        * 100,
        2
    ) AS latest_3_month_active_rate_pct,


    ROUND(
        u.previous_3_month_active_rate
        * 100,
        2
    ) AS previous_3_month_active_rate_pct,


    ROUND(
        (
            u.latest_3_month_active_rate
            - u.previous_3_month_active_rate
        )
        * 100,
        2
    ) AS usage_trend_percentage_points,


    -- -----------------------------------------------------
    -- SUPPORT
    -- -----------------------------------------------------

    COALESCE(
        st.tickets_90d,
        0
    ) AS tickets_90d,


    COALESCE(
        st.high_critical_tickets_90d,
        0
    ) AS high_critical_tickets_90d,


    COALESCE(
        st.unresolved_tickets_90d,
        0
    ) AS unresolved_tickets_90d,


    st.avg_resolution_hours_90d,
    st.avg_csat_90d,


    -- -----------------------------------------------------
    -- PAYMENT
    -- -----------------------------------------------------

    COALESCE(
        p.invoices_6m,
        0
    ) AS invoices_6m,


    COALESCE(
        p.paid_invoices_6m,
        0
    ) AS paid_invoices_6m,


    COALESCE(
        p.late_invoices_6m,
        0
    ) AS late_invoices_6m,


    COALESCE(
        p.failed_invoices_6m,
        0
    ) AS failed_invoices_6m,


    COALESCE(
        p.pending_invoices_6m,
        0
    ) AS pending_invoices_6m,


    COALESCE(
        p.max_days_late_6m,
        0
    ) AS max_days_late_6m,


    COALESCE(
        p.payment_issue_rate_6m_pct,
        0
    ) AS payment_issue_rate_6m_pct,


    -- -----------------------------------------------------
    -- CUSTOMER SUCCESS / ENGAGEMENT
    -- -----------------------------------------------------

    cs.most_recent_interaction_date,


    CASE

        WHEN cs.most_recent_interaction_date
            IS NULL
            THEN NULL

        ELSE
            DATE '2026-12-31'
            - cs.most_recent_interaction_date

    END AS days_since_last_cs_interaction,


    COALESCE(
        cs.interactions_90d,
        0
    ) AS cs_interactions_90d,


    COALESCE(
        cs.engaged_interactions_90d,
        0
    ) AS engaged_interactions_90d,


    COALESCE(
        cs.neutral_interactions_90d,
        0
    ) AS neutral_interactions_90d,


    COALESCE(
        cs.unresponsive_interactions_90d,
        0
    ) AS unresponsive_interactions_90d,


    COALESCE(
        cs.followups_required_90d,
        0
    ) AS followups_required_90d,


    COALESCE(
        cs.followups_without_date_all_time,
        0
    ) AS followups_without_date_all_time


FROM accounts AS a


INNER JOIN current_subscription AS s
    ON a.account_id = s.account_id


LEFT JOIN usage_summary AS u
    ON a.account_id = u.account_id


LEFT JOIN support_90d AS st
    ON a.account_id = st.account_id


LEFT JOIN payment_6m AS p
    ON a.account_id = p.account_id


LEFT JOIN cs_summary AS cs
    ON a.account_id = cs.account_id


WHERE a.customer_status = 'Active';


-- =========================================================
-- 8. VALIDATION
--
-- Expected:
-- rows = 426
-- unique accounts = 426
-- =========================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT(DISTINCT account_id)
        AS unique_accounts

FROM vw_account_health_base;


-- =========================================================
-- 9. REVENUE RECONCILIATION
--
-- Expected:
-- MRR = 1,574,850
-- ARR = 18,898,200
-- =========================================================

SELECT
    SUM(mrr) AS total_mrr,
    SUM(arr) AS total_arr
FROM vw_account_health_base;


-- =========================================================
-- 10. ESSENTIAL METRIC COMPLETENESS
--
-- Expected:
-- missing current subscription = impossible because INNER JOIN
-- missing latest usage = 0
-- missing 3-month usage = 0
-- missing previous 3-month usage = 0
-- =========================================================

SELECT
    COUNT(*) FILTER (
        WHERE latest_usage_month IS NULL
    ) AS missing_latest_usage,

    COUNT(*) FILTER (
        WHERE latest_active_user_rate_pct
            IS NULL
    ) AS missing_current_usage_rate,

    COUNT(*) FILTER (
        WHERE latest_3_month_active_rate_pct
            IS NULL
    ) AS missing_latest_3_month_rate,

    COUNT(*) FILTER (
        WHERE previous_3_month_active_rate_pct
            IS NULL
    ) AS missing_previous_3_month_rate

FROM vw_account_health_base;


-- =========================================================
-- 11. CURRENT PORTFOLIO SUMMARY BY SEGMENT
-- =========================================================

SELECT
    segment,

    COUNT(*) AS active_accounts,

    SUM(mrr) AS current_mrr,

    SUM(arr) AS current_arr,

    ROUND(
        AVG(
            latest_active_user_rate_pct
        ),
        2
    ) AS avg_current_usage_pct,

    ROUND(
        AVG(
            usage_trend_percentage_points
        ),
        2
    ) AS avg_usage_trend_pp,

    ROUND(
        AVG(
            tickets_90d
        ),
        2
    ) AS avg_tickets_90d,

    ROUND(
        AVG(
            payment_issue_rate_6m_pct
        ),
        2
    ) AS avg_payment_issue_rate_pct,

    ROUND(
        AVG(
            unresponsive_interactions_90d
        ),
        2
    ) AS avg_unresponsive_interactions_90d

FROM vw_account_health_base

GROUP BY segment

ORDER BY current_arr DESC;


-- =========================================================
-- 12. PREVIEW HIGH-VALUE ACCOUNTS
--
-- No Health Score is being applied yet.
-- =========================================================

SELECT
    account_id,
    account_name,
    segment,
    plan_name,
    mrr,
    arr,
    days_to_renewal,

    latest_active_user_rate_pct,
    latest_feature_adoption_pct,
    usage_trend_percentage_points,

    tickets_90d,
    high_critical_tickets_90d,
    unresolved_tickets_90d,

    late_invoices_6m,
    failed_invoices_6m,
    payment_issue_rate_6m_pct,

    cs_interactions_90d,
    unresponsive_interactions_90d,
    followups_required_90d,
    days_since_last_cs_interaction

FROM vw_account_health_base

ORDER BY mrr DESC

LIMIT 20;
