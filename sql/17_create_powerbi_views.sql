-- Customer Health & Revenue Risk Analytics
-- Power BI Ready Views
--
-- Purpose:
-- Create clean analytical views that Power BI can connect
-- to directly without rebuilding complex SQL logic.
--
-- Views created:
--
-- 1. vw_pbi_account_health
-- 2. vw_pbi_retention_summary
-- 3. vw_pbi_monthly_revenue
-- 4. vw_pbi_monthly_usage
-- 5. vw_pbi_monthly_support
--
-- Analysis snapshot date:
-- 2026-12-31


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- DROP EXISTING POWER BI VIEWS
-- =========================================================

DROP VIEW IF EXISTS vw_pbi_monthly_support;
DROP VIEW IF EXISTS vw_pbi_monthly_usage;
DROP VIEW IF EXISTS vw_pbi_monthly_revenue;
DROP VIEW IF EXISTS vw_pbi_retention_summary;
DROP VIEW IF EXISTS vw_pbi_account_health;


-- =========================================================
-- 1. ACCOUNT HEALTH / REVENUE AT RISK VIEW
--
-- Grain:
-- One row per currently active customer
--
-- Main use in Power BI:
-- Executive summary
-- Health distribution
-- Revenue at Risk
-- Priority accounts
-- Risk drivers
-- CSM workload
-- =========================================================

CREATE VIEW vw_pbi_account_health AS

SELECT
    account_id,
    account_name,
    industry,
    segment,
    region,
    signup_date,
    assigned_csm,

    plan_name,
    billing_frequency,
    renewal_date,
    days_to_renewal,
    renewal_window,

    mrr,
    arr,

    health_score,
    health_status,
    risk_flag_count,

    product_usage_score,
    usage_trend_score,
    feature_adoption_score,
    support_health_score,
    payment_health_score,
    engagement_score,

    latest_active_user_rate_pct,
    latest_feature_adoption_pct,
    latest_3_month_active_rate_pct,
    previous_3_month_active_rate_pct,
    usage_trend_percentage_points,

    tickets_90d,
    high_critical_tickets_90d,
    unresolved_tickets_90d,
    avg_resolution_hours_90d,
    avg_csat_90d,

    invoices_6m,
    late_invoices_6m,
    failed_invoices_6m,
    pending_invoices_6m,
    max_days_late_6m,
    payment_issue_rate_6m_pct,

    most_recent_interaction_date,
    days_since_last_cs_interaction,
    cs_interactions_90d,
    engaged_interactions_90d,
    neutral_interactions_90d,
    unresponsive_interactions_90d,
    followups_required_90d,

    revenue_exposure_factor,
    estimated_revenue_at_risk,

    health_risk_severity_score,
    renewal_urgency_score,
    arr_value_score,

    priority_score,
    priority_tier,

    primary_risk_driver,
    cs_action_required

FROM vw_revenue_at_risk_priority;


-- =========================================================
-- 2. RETENTION SUMMARY VIEW
--
-- Grain:
-- One row per year per customer segment
--
-- Main use:
-- Logo retention
-- GRR
-- NRR
-- Expansion
-- Contraction
-- Churn
-- =========================================================

CREATE VIEW vw_pbi_retention_summary AS

SELECT
    analysis_year,
    segment,

    COUNT(*) AS beginning_accounts,

    COUNT(*) FILTER (
        WHERE end_mrr > 0
    ) AS retained_accounts,

    COUNT(*) FILTER (
        WHERE end_mrr = 0
    ) AS churned_accounts,


    ROUND(
        (
            COUNT(*) FILTER (
                WHERE end_mrr > 0
            )
        )::NUMERIC
        / NULLIF(
            COUNT(*),
            0
        )
        * 100,
        2
    ) AS logo_retention_pct,


    ROUND(
        (
            COUNT(*) FILTER (
                WHERE end_mrr = 0
            )
        )::NUMERIC
        / NULLIF(
            COUNT(*),
            0
        )
        * 100,
        2
    ) AS logo_churn_pct,


    SUM(start_mrr)
        AS beginning_mrr,

    SUM(end_mrr)
        AS ending_mrr,

    SUM(start_mrr) * 12
        AS beginning_arr,

    SUM(end_mrr) * 12
        AS ending_arr,

    SUM(expansion_mrr)
        AS expansion_mrr,

    SUM(contraction_mrr)
        AS contraction_mrr,

    SUM(churned_mrr)
        AS churned_mrr,


    ROUND(
        (
            SUM(start_mrr)
            - SUM(churned_mrr)
            - SUM(contraction_mrr)
        )
        / NULLIF(
            SUM(start_mrr),
            0
        )
        * 100,
        2
    ) AS grr_pct,


    ROUND(
        SUM(end_mrr)
        / NULLIF(
            SUM(start_mrr),
            0
        )
        * 100,
        2
    ) AS nrr_pct


FROM vw_retention_revenue_cohort

GROUP BY
    analysis_year,
    segment;


-- =========================================================
-- 3. MONTHLY RECURRING REVENUE VIEW
--
-- Grain:
-- Month + segment
--
-- Main use:
-- MRR trend
-- ARR trend
-- Active customer trend
-- Segment revenue trend
-- =========================================================

CREATE VIEW vw_pbi_monthly_revenue AS


WITH months AS (

    SELECT
        month_start::DATE AS month_start,

        (
            month_start
            + INTERVAL '1 month'
            - INTERVAL '1 day'
        )::DATE AS month_end

    FROM GENERATE_SERIES(
        DATE '2025-01-01',
        DATE '2026-12-01',
        INTERVAL '1 month'
    ) AS month_start
),


monthly_accounts AS (

    SELECT
        m.month_start,
        m.month_end,

        a.account_id,
        a.segment,

        s.mrr

    FROM months AS m

    INNER JOIN subscriptions AS s

        ON s.subscription_start_date
            <= m.month_end

        AND s.subscription_end_date
            >= m.month_end

    INNER JOIN accounts AS a
        ON s.account_id = a.account_id
)


SELECT
    month_start,
    month_end,
    segment,

    COUNT(DISTINCT account_id)
        AS active_accounts,

    SUM(mrr)
        AS mrr,

    SUM(mrr) * 12
        AS arr,

    ROUND(
        AVG(mrr),
        2
    ) AS average_mrr_per_account

FROM monthly_accounts

GROUP BY
    month_start,
    month_end,
    segment;


-- =========================================================
-- 4. MONTHLY PRODUCT USAGE VIEW
--
-- Grain:
-- Usage month + customer segment
--
-- Main use:
-- Usage trend
-- Adoption trend
-- Active users
-- Feature adoption
-- =========================================================

CREATE VIEW vw_pbi_monthly_usage AS

SELECT
    p.usage_month,
    a.segment,

    COUNT(DISTINCT p.account_id)
        AS accounts_with_usage,

    SUM(p.licensed_users)
        AS licensed_users,

    SUM(p.active_users)
        AS active_users,


    ROUND(
        SUM(p.active_users)::NUMERIC
        / NULLIF(
            SUM(p.licensed_users),
            0
        )
        * 100,
        2
    ) AS weighted_active_user_rate_pct,


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
    ) AS average_account_active_user_rate_pct,


    ROUND(
        AVG(
            p.core_features_used::NUMERIC
            / 8
        )
        * 100,
        2
    ) AS average_feature_adoption_pct,


    SUM(p.login_count)
        AS login_count,

    SUM(p.dashboards_viewed)
        AS dashboards_viewed,

    SUM(p.reports_generated)
        AS reports_generated,

    SUM(p.alerts_created)
        AS alerts_created

FROM product_usage AS p

INNER JOIN accounts AS a
    ON p.account_id = a.account_id

GROUP BY
    p.usage_month,
    a.segment;


-- =========================================================
-- 5. MONTHLY SUPPORT VIEW
--
-- Grain:
-- Ticket month + customer segment
--
-- Main use:
-- Ticket trend
-- Severe issue trend
-- Resolution time
-- CSAT
-- =========================================================

CREATE VIEW vw_pbi_monthly_support AS

SELECT
    DATE_TRUNC(
        'month',
        st.created_date
    )::DATE AS ticket_month,

    a.segment,

    COUNT(st.ticket_id)
        AS total_tickets,


    COUNT(*) FILTER (
        WHERE st.priority = 'Critical'
    ) AS critical_tickets,


    COUNT(*) FILTER (
        WHERE st.priority = 'High'
    ) AS high_tickets,


    COUNT(*) FILTER (
        WHERE st.priority IN (
            'High',
            'Critical'
        )
    ) AS high_critical_tickets,


    COUNT(*) FILTER (
        WHERE st.ticket_status <> 'Resolved'
    ) AS unresolved_tickets,


    ROUND(
        AVG(st.resolution_hours)
            FILTER (
                WHERE st.ticket_status = 'Resolved'
            ),
        2
    ) AS average_resolution_hours,


    ROUND(
        AVG(st.customer_satisfaction_score)
            FILTER (
                WHERE st.customer_satisfaction_score
                IS NOT NULL
            ),
        2
    ) AS average_csat

FROM support_tickets AS st

INNER JOIN accounts AS a
    ON st.account_id = a.account_id

GROUP BY
    DATE_TRUNC(
        'month',
        st.created_date
    )::DATE,
    a.segment;


-- =========================================================
-- VALIDATION 1
-- ACCOUNT HEALTH VIEW
--
-- Expected:
-- 426 rows
-- 426 unique accounts
-- =========================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT(DISTINCT account_id)
        AS unique_accounts

FROM vw_pbi_account_health;


-- =========================================================
-- VALIDATION 2
-- ACCOUNT HEALTH ARR
--
-- Expected:
-- 18,898,200
-- =========================================================

SELECT
    SUM(arr) AS total_arr
FROM vw_pbi_account_health;


-- =========================================================
-- VALIDATION 3
-- HEALTH STATUS COUNTS
--
-- Expected:
-- Healthy = 273
-- Monitor = 129
-- At Risk = 24
-- =========================================================

SELECT
    health_status,

    COUNT(*) AS accounts,

    SUM(arr) AS arr,

    SUM(estimated_revenue_at_risk)
        AS estimated_revenue_at_risk

FROM vw_pbi_account_health

GROUP BY health_status

ORDER BY
    CASE health_status
        WHEN 'At Risk' THEN 1
        WHEN 'Monitor' THEN 2
        WHEN 'Healthy' THEN 3
    END;


-- =========================================================
-- VALIDATION 4
-- PRIORITY DISTRIBUTION
-- =========================================================

SELECT
    priority_tier,

    COUNT(*) AS accounts,

    SUM(arr) AS arr

FROM vw_pbi_account_health

GROUP BY priority_tier

ORDER BY
    CASE priority_tier
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
        WHEN 'Routine' THEN 5
    END;


-- =========================================================
-- VALIDATION 5
-- RETENTION SUMMARY
--
-- Expected:
-- 2 years x 3 segments = 6 rows
-- =========================================================

SELECT
    COUNT(*) AS retention_summary_rows
FROM vw_pbi_retention_summary;


-- =========================================================
-- VALIDATION 6
-- RETENTION VIEW PREVIEW
-- =========================================================

SELECT
    analysis_year,
    segment,
    beginning_accounts,
    retained_accounts,
    churned_accounts,
    logo_retention_pct,
    grr_pct,
    nrr_pct,
    expansion_mrr,
    contraction_mrr,
    churned_mrr

FROM vw_pbi_retention_summary

ORDER BY
    analysis_year,
    segment;


-- =========================================================
-- VALIDATION 7
-- MONTHLY REVENUE DATE COVERAGE
-- =========================================================

SELECT
    MIN(month_start)
        AS earliest_month,

    MAX(month_start)
        AS latest_month,

    COUNT(DISTINCT month_start)
        AS months

FROM vw_pbi_monthly_revenue;


-- =========================================================
-- VALIDATION 8
-- DECEMBER 2026 REVENUE RECONCILIATION
--
-- Expected:
-- MRR = 1,574,850
-- ARR = 18,898,200
-- =========================================================

SELECT
    SUM(mrr) AS december_2026_mrr,

    SUM(arr) AS december_2026_arr,

    SUM(active_accounts)
        AS december_2026_active_accounts

FROM vw_pbi_monthly_revenue

WHERE month_start = DATE '2026-12-01';


-- =========================================================
-- VALIDATION 9
-- MONTHLY USAGE COVERAGE
--
-- Expected:
-- 24 distinct months
-- =========================================================

SELECT
    MIN(usage_month)
        AS earliest_usage_month,

    MAX(usage_month)
        AS latest_usage_month,

    COUNT(DISTINCT usage_month)
        AS months

FROM vw_pbi_monthly_usage;


-- =========================================================
-- VALIDATION 10
-- MONTHLY SUPPORT COVERAGE
-- =========================================================

SELECT
    MIN(ticket_month)
        AS earliest_ticket_month,

    MAX(ticket_month)
        AS latest_ticket_month,

    COUNT(DISTINCT ticket_month)
        AS months

FROM vw_pbi_monthly_support;


-- =========================================================
-- FINAL POWER BI READINESS SUMMARY
-- =========================================================

SELECT
    (
        SELECT COUNT(*)
        FROM vw_pbi_account_health
    ) AS account_health_rows,

    (
        SELECT COUNT(*)
        FROM vw_pbi_retention_summary
    ) AS retention_rows,

    (
        SELECT COUNT(*)
        FROM vw_pbi_monthly_revenue
    ) AS monthly_revenue_rows,

    (
        SELECT COUNT(*)
        FROM vw_pbi_monthly_usage
    ) AS monthly_usage_rows,

    (
        SELECT COUNT(*)
        FROM vw_pbi_monthly_support
    ) AS monthly_support_rows;
    