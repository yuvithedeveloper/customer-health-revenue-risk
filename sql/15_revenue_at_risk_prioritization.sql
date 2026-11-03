-- Customer Health & Revenue Risk Analytics
-- Revenue at Risk and Customer Success Prioritization
--
-- Purpose:
-- Translate Customer Health Scores into:
--
-- 1. Estimated Revenue at Risk
-- 2. Renewal urgency
-- 3. Account value
-- 4. Customer Success priority ranking
-- 5. Primary risk driver
--
-- IMPORTANT:
-- Revenue at Risk is a rules-based management estimate.
-- It is NOT a statistically predicted churn loss.
--
-- Analysis snapshot date:
-- 2026-12-31


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- DROP VIEW IF IT ALREADY EXISTS
-- =========================================================

DROP VIEW IF EXISTS vw_revenue_at_risk_priority;


-- =========================================================
-- CREATE VIEW
-- =========================================================

CREATE VIEW vw_revenue_at_risk_priority AS


WITH risk_inputs AS (

    SELECT
        h.*,


        -- =================================================
        -- 1. REVENUE EXPOSURE FACTOR
        --
        -- Converts Health Score severity into an
        -- explainable percentage of ARR considered exposed.
        --
        -- This is a management assumption, NOT a churn
        -- probability.
        --
        -- Health Score:
        -- <45      = 75% exposure
        -- 45-54.99 = 60%
        -- 55-64.99 = 40%
        -- 65-74.99 = 25%
        -- 75+      = 0%
        -- =================================================

        CASE

            WHEN health_score < 45
                THEN 0.75::NUMERIC

            WHEN health_score < 55
                THEN 0.60::NUMERIC

            WHEN health_score < 65
                THEN 0.40::NUMERIC

            WHEN health_score < 75
                THEN 0.25::NUMERIC

            ELSE 0.00::NUMERIC

        END AS revenue_exposure_factor,


        -- =================================================
        -- 2. HEALTH RISK SEVERITY SCORE
        --
        -- Used only for prioritization.
        -- =================================================

        CASE

            WHEN health_score < 45
                THEN 100

            WHEN health_score < 55
                THEN 85

            WHEN health_score < 65
                THEN 65

            WHEN health_score < 75
                THEN 45

            ELSE 0

        END AS health_risk_severity_score,


        -- =================================================
        -- 3. RENEWAL URGENCY SCORE
        --
        -- Accounts closer to renewal deserve faster action.
        -- =================================================

        CASE

            WHEN days_to_renewal <= 30
                THEN 100

            WHEN days_to_renewal <= 60
                THEN 85

            WHEN days_to_renewal <= 90
                THEN 70

            WHEN days_to_renewal <= 180
                THEN 50

            WHEN days_to_renewal <= 270
                THEN 30

            ELSE 15

        END AS renewal_urgency_score,


        -- =================================================
        -- 4. RENEWAL WINDOW
        -- =================================================

        CASE

            WHEN days_to_renewal <= 30
                THEN '0-30 days'

            WHEN days_to_renewal <= 60
                THEN '31-60 days'

            WHEN days_to_renewal <= 90
                THEN '61-90 days'

            WHEN days_to_renewal <= 180
                THEN '91-180 days'

            WHEN days_to_renewal <= 270
                THEN '181-270 days'

            ELSE '271+ days'

        END AS renewal_window,


        -- =================================================
        -- 5. ARR VALUE PERCENTILE
        --
        -- Gives high-value accounts more priority without
        -- manually selecting arbitrary dollar thresholds.
        -- =================================================

        ROUND(
            (
                PERCENT_RANK() OVER (
                    ORDER BY arr
                )
                * 100
            )::NUMERIC,
            2
        ) AS arr_value_percentile


    FROM vw_customer_health_score AS h
),


priority_inputs AS (

    SELECT
        r.*,


        -- =================================================
        -- 6. ARR VALUE SCORE
        --
        -- Convert percentile into a simple 0-100 score.
        -- =================================================

        CASE

            WHEN arr_value_percentile >= 80
                THEN 100

            WHEN arr_value_percentile >= 60
                THEN 80

            WHEN arr_value_percentile >= 40
                THEN 60

            WHEN arr_value_percentile >= 20
                THEN 40

            ELSE 20

        END AS arr_value_score,


        -- =================================================
        -- 7. ESTIMATED REVENUE AT RISK
        --
        -- ARR × exposure factor
        --
        -- Example:
        -- $100,000 ARR × 60%
        -- = $60,000 estimated revenue at risk
        -- =================================================

        ROUND(
            arr
            * revenue_exposure_factor,
            2
        ) AS estimated_revenue_at_risk,


        -- =================================================
        -- 8. PRIMARY RISK DRIVER
        --
        -- Identify the weakest health dimension.
        --
        -- In case of a tie, the first matching component
        -- below is selected.
        -- =================================================

        CASE

            WHEN product_usage_score = LEAST(
                product_usage_score,
                usage_trend_score,
                feature_adoption_score,
                support_health_score,
                payment_health_score,
                engagement_score
            )
                THEN 'Product Usage'


            WHEN usage_trend_score = LEAST(
                product_usage_score,
                usage_trend_score,
                feature_adoption_score,
                support_health_score,
                payment_health_score,
                engagement_score
            )
                THEN 'Usage Trend'


            WHEN feature_adoption_score = LEAST(
                product_usage_score,
                usage_trend_score,
                feature_adoption_score,
                support_health_score,
                payment_health_score,
                engagement_score
            )
                THEN 'Feature Adoption'


            WHEN support_health_score = LEAST(
                product_usage_score,
                usage_trend_score,
                feature_adoption_score,
                support_health_score,
                payment_health_score,
                engagement_score
            )
                THEN 'Support Health'


            WHEN payment_health_score = LEAST(
                product_usage_score,
                usage_trend_score,
                feature_adoption_score,
                support_health_score,
                payment_health_score,
                engagement_score
            )
                THEN 'Payment Health'


            ELSE 'Customer Engagement'

        END AS primary_risk_driver


    FROM risk_inputs AS r
),


priority_scores AS (

    SELECT
        p.*,


        -- =================================================
        -- 9. CUSTOMER SUCCESS PRIORITY SCORE
        --
        -- Health Risk Severity = 50%
        -- Renewal Urgency      = 30%
        -- ARR Value            = 20%
        --
        -- This answers:
        -- "Which customer should the CS team work on first?"
        -- =================================================

        ROUND(
              health_risk_severity_score
                * 0.50

            + renewal_urgency_score
                * 0.30

            + arr_value_score
                * 0.20,

            2
        ) AS priority_score


    FROM priority_inputs AS p
)


SELECT
    p.*,


    -- =====================================================
    -- 10. PRIORITY TIER
    --
    -- Healthy customers remain Routine even if they are
    -- large or close to renewal because this particular
    -- queue is designed for risk intervention.
    -- =====================================================

    CASE

        WHEN health_status = 'Healthy'
            THEN 'Routine'

        WHEN priority_score >= 75
            THEN 'Critical'

        WHEN priority_score >= 60
            THEN 'High'

        WHEN priority_score >= 45
            THEN 'Medium'

        ELSE 'Low'

    END AS priority_tier,


    -- =====================================================
    -- 11. ACTION FLAG
    -- =====================================================

    CASE

        WHEN health_status IN (
            'At Risk',
            'Monitor'
        )
            THEN TRUE

        ELSE FALSE

    END AS cs_action_required


FROM priority_scores AS p;


-- =========================================================
-- VALIDATION 1
-- ONE ROW PER ACTIVE ACCOUNT
--
-- Expected:
-- 426 rows
-- 426 unique accounts
-- =========================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT(DISTINCT account_id)
        AS unique_accounts

FROM vw_revenue_at_risk_priority;


-- =========================================================
-- VALIDATION 2
-- ARR RECONCILIATION
--
-- Expected:
-- 18,898,200 ARR
-- =========================================================

SELECT
    SUM(arr) AS total_arr
FROM vw_revenue_at_risk_priority;


-- =========================================================
-- VALIDATION 3
-- HEALTH STATUS SHOULD MATCH PRIOR VIEW
--
-- Expected:
-- At Risk = 24
-- Monitor = 129
-- Healthy = 273
-- =========================================================

SELECT
    health_status,
    COUNT(*) AS accounts,
    SUM(arr) AS arr

FROM vw_revenue_at_risk_priority

GROUP BY health_status

ORDER BY
    CASE health_status
        WHEN 'At Risk' THEN 1
        WHEN 'Monitor' THEN 2
        WHEN 'Healthy' THEN 3
    END;


-- =========================================================
-- 12. OVERALL REVENUE AT RISK
-- =========================================================

SELECT
    COUNT(*) FILTER (
        WHERE cs_action_required = TRUE
    ) AS accounts_requiring_action,

    SUM(arr) FILTER (
        WHERE cs_action_required = TRUE
    ) AS gross_arr_exposed,

    ROUND(
        SUM(estimated_revenue_at_risk),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority;


-- =========================================================
-- 13. REVENUE AT RISK BY HEALTH STATUS
-- =========================================================

SELECT
    health_status,

    COUNT(*) AS accounts,

    SUM(arr) AS total_arr,

    ROUND(
        SUM(estimated_revenue_at_risk),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority

GROUP BY health_status

ORDER BY
    CASE health_status
        WHEN 'At Risk' THEN 1
        WHEN 'Monitor' THEN 2
        WHEN 'Healthy' THEN 3
    END;


-- =========================================================
-- 14. PRIORITY TIER DISTRIBUTION
-- =========================================================

SELECT
    priority_tier,

    COUNT(*) AS accounts,

    SUM(arr) AS arr,

    ROUND(
        SUM(estimated_revenue_at_risk),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority

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
-- 15. REVENUE AT RISK BY SEGMENT
-- =========================================================

SELECT
    segment,

    COUNT(*) FILTER (
        WHERE cs_action_required = TRUE
    ) AS accounts_requiring_action,

    SUM(arr) FILTER (
        WHERE cs_action_required = TRUE
    ) AS gross_arr_exposed,

    ROUND(
        SUM(estimated_revenue_at_risk),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority

GROUP BY segment

ORDER BY estimated_revenue_at_risk DESC;


-- =========================================================
-- 16. RISK BY RENEWAL WINDOW
--
-- This helps identify how much exposure is approaching
-- renewal soon.
-- =========================================================

SELECT
    renewal_window,

    COUNT(*) FILTER (
        WHERE cs_action_required = TRUE
    ) AS accounts_requiring_action,

    SUM(arr) FILTER (
        WHERE cs_action_required = TRUE
    ) AS gross_arr_exposed,

    ROUND(
        SUM(estimated_revenue_at_risk)
            FILTER (
                WHERE cs_action_required = TRUE
            ),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority

GROUP BY renewal_window

ORDER BY
    CASE renewal_window

        WHEN '0-30 days' THEN 1
        WHEN '31-60 days' THEN 2
        WHEN '61-90 days' THEN 3
        WHEN '91-180 days' THEN 4
        WHEN '181-270 days' THEN 5
        WHEN '271+ days' THEN 6

    END;


-- =========================================================
-- 17. PRIMARY RISK DRIVER DISTRIBUTION
--
-- Only accounts requiring intervention.
-- =========================================================

SELECT
    primary_risk_driver,

    COUNT(*) AS accounts,

    SUM(arr) AS gross_arr,

    ROUND(
        SUM(estimated_revenue_at_risk),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority

WHERE cs_action_required = TRUE

GROUP BY primary_risk_driver

ORDER BY estimated_revenue_at_risk DESC;


-- =========================================================
-- 18. TOP CUSTOMER SUCCESS PRIORITIES
--
-- This becomes the basis for the eventual Power BI
-- intervention table.
-- =========================================================

SELECT
    account_id,
    account_name,
    segment,
    assigned_csm,

    health_score,
    health_status,
    risk_flag_count,

    arr,
    estimated_revenue_at_risk,

    days_to_renewal,
    renewal_window,

    priority_score,
    priority_tier,

    primary_risk_driver,

    latest_active_user_rate_pct,
    usage_trend_percentage_points,
    latest_feature_adoption_pct,

    high_critical_tickets_90d,
    unresolved_tickets_90d,

    late_invoices_6m,
    failed_invoices_6m,

    unresponsive_interactions_90d,
    days_since_last_cs_interaction

FROM vw_revenue_at_risk_priority

WHERE cs_action_required = TRUE

ORDER BY
    priority_score DESC,
    estimated_revenue_at_risk DESC

LIMIT 30;


-- =========================================================
-- 19. AT-RISK ACCOUNTS ONLY
-- =========================================================

SELECT
    account_id,
    account_name,
    segment,
    assigned_csm,

    health_score,
    arr,
    estimated_revenue_at_risk,

    days_to_renewal,
    renewal_window,

    priority_score,
    priority_tier,

    primary_risk_driver

FROM vw_revenue_at_risk_priority

WHERE health_status = 'At Risk'

ORDER BY
    priority_score DESC,
    estimated_revenue_at_risk DESC;


-- =========================================================
-- 20. NEAR-TERM RISK
--
-- Monitor / At Risk accounts renewing within 90 days.
-- =========================================================

SELECT
    account_id,
    account_name,
    segment,
    assigned_csm,

    health_status,
    health_score,

    arr,
    estimated_revenue_at_risk,

    days_to_renewal,

    priority_score,
    priority_tier,

    primary_risk_driver

FROM vw_revenue_at_risk_priority

WHERE cs_action_required = TRUE
  AND days_to_renewal <= 90

ORDER BY
    priority_score DESC,
    days_to_renewal ASC,
    arr DESC;


-- =========================================================
-- 21. CUSTOMER SUCCESS WORKLOAD
--
-- How many Monitor / At Risk accounts sit with each CSM?
-- =========================================================

SELECT
    COALESCE(
        assigned_csm,
        'Unassigned'
    ) AS assigned_csm,

    COUNT(*) FILTER (
        WHERE health_status = 'At Risk'
    ) AS at_risk_accounts,

    COUNT(*) FILTER (
        WHERE health_status = 'Monitor'
    ) AS monitor_accounts,

    COUNT(*) FILTER (
        WHERE priority_tier = 'Critical'
    ) AS critical_priority_accounts,

    COUNT(*) FILTER (
        WHERE priority_tier = 'High'
    ) AS high_priority_accounts,

    SUM(arr) FILTER (
        WHERE cs_action_required = TRUE
    ) AS gross_arr_exposed,

    ROUND(
        SUM(estimated_revenue_at_risk),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority

GROUP BY
    COALESCE(
        assigned_csm,
        'Unassigned'
    )

ORDER BY estimated_revenue_at_risk DESC;


-- =========================================================
-- 22. PRIORITY SCORE VALIDATION
--
-- Expected:
-- No score outside 0-100.
-- =========================================================

SELECT
    account_id,
    account_name,
    priority_score

FROM vw_revenue_at_risk_priority

WHERE priority_score < 0
   OR priority_score > 100;


-- =========================================================
-- 23. FINAL MANAGEMENT SUMMARY
-- =========================================================

SELECT
    COUNT(*) AS active_accounts,

    SUM(arr) AS total_arr,

    COUNT(*) FILTER (
        WHERE health_status = 'At Risk'
    ) AS at_risk_accounts,

    COUNT(*) FILTER (
        WHERE health_status = 'Monitor'
    ) AS monitor_accounts,

    COUNT(*) FILTER (
        WHERE priority_tier IN (
            'Critical',
            'High'
        )
    ) AS urgent_priority_accounts,

    SUM(arr) FILTER (
        WHERE cs_action_required = TRUE
    ) AS gross_arr_exposed,

    ROUND(
        SUM(estimated_revenue_at_risk),
        2
    ) AS estimated_revenue_at_risk

FROM vw_revenue_at_risk_priority;
