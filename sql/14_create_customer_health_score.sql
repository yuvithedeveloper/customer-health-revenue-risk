-- Customer Health & Revenue Risk Analytics
-- Customer Health Score
--
-- Purpose:
-- Convert the six account health dimensions into
-- transparent component scores and calculate one
-- weighted Customer Health Score for each active account.
--
-- This is a rules-based analytical score.
-- It is not a machine-learning churn probability.
--
-- Analysis snapshot date:
-- 2026-12-31


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- DROP VIEW IF IT ALREADY EXISTS
-- =========================================================

DROP VIEW IF EXISTS vw_customer_health_score;


-- =========================================================
-- CREATE CUSTOMER HEALTH SCORE VIEW
-- =========================================================

CREATE VIEW vw_customer_health_score AS


WITH component_scores AS (

    SELECT
        b.*,


        -- =================================================
        -- 1. PRODUCT USAGE SCORE
        --
        -- Distribution reference:
        -- p10    ~ 36%
        -- p25    ~ 53%
        -- median ~ 67%
        -- p75    ~ 77%
        --
        -- Weight in final score: 25%
        -- =================================================

        CASE

            WHEN latest_active_user_rate_pct >= 80
                THEN 100

            WHEN latest_active_user_rate_pct >= 65
                THEN 80

            WHEN latest_active_user_rate_pct >= 50
                THEN 60

            WHEN latest_active_user_rate_pct >= 35
                THEN 40

            ELSE 20

        END AS product_usage_score,


        -- =================================================
        -- 2. USAGE TREND SCORE
        --
        -- Percentage-point change:
        -- latest 3 months vs previous 3 months
        --
        -- Most customers are relatively stable.
        -- Strong negative movement receives a larger
        -- penalty.
        --
        -- Weight: 20%
        -- =================================================

        CASE

            WHEN usage_trend_percentage_points >= 5
                THEN 100

            WHEN usage_trend_percentage_points >= 0
                THEN 85

            WHEN usage_trend_percentage_points >= -5
                THEN 70

            WHEN usage_trend_percentage_points >= -10
                THEN 40

            ELSE 20

        END AS usage_trend_score,


        -- =================================================
        -- 3. FEATURE ADOPTION SCORE
        --
        -- Eight core features create discrete adoption
        -- levels:
        --
        -- 37.5
        -- 50.0
        -- 62.5
        -- 75.0
        -- 87.5
        -- 100.0
        --
        -- Weight: 15%
        -- =================================================

        CASE

            WHEN latest_feature_adoption_pct >= 87.50
                THEN 100

            WHEN latest_feature_adoption_pct >= 75.00
                THEN 85

            WHEN latest_feature_adoption_pct >= 62.50
                THEN 70

            WHEN latest_feature_adoption_pct >= 50.00
                THEN 45

            ELSE 20

        END AS feature_adoption_score,


        -- =================================================
        -- 4. SUPPORT HEALTH SCORE
        --
        -- Uses the final 90 days.
        --
        -- Recent severe/unresolved issues receive more
        -- weight than ticket volume alone.
        --
        -- Weight: 15%
        -- =================================================

        CASE

            WHEN
                high_critical_tickets_90d >= 2
                AND unresolved_tickets_90d >= 1

                THEN 20


            WHEN
                high_critical_tickets_90d >= 2
                OR unresolved_tickets_90d >= 2
                OR tickets_90d >= 4

                THEN 40


            WHEN
                high_critical_tickets_90d = 1
                OR unresolved_tickets_90d = 1
                OR tickets_90d = 3

                THEN 65


            WHEN tickets_90d = 2
                THEN 80


            ELSE 100

        END AS support_health_score,


        -- =================================================
        -- 5. PAYMENT HEALTH SCORE
        --
        -- Uses the final six months.
        --
        -- Failed payments are treated as more serious than
        -- late payments.
        --
        -- Weight: 10%
        -- =================================================

        CASE

            WHEN failed_invoices_6m >= 2
                THEN 20


            WHEN failed_invoices_6m = 1
                THEN 40


            WHEN
                late_invoices_6m >= 2
                OR max_days_late_6m > 30

                THEN 60


            WHEN late_invoices_6m = 1
                THEN 80


            ELSE 100

        END AS payment_health_score,


        -- =================================================
        -- 6. CUSTOMER ENGAGEMENT SCORE
        --
        -- Uses:
        -- - unresponsive interactions
        -- - days since last CS interaction
        --
        -- Weight: 15%
        -- =================================================

        CASE

            WHEN most_recent_interaction_date IS NULL
                THEN 30


            WHEN unresponsive_interactions_90d >= 2
                THEN 20


            WHEN unresponsive_interactions_90d = 1
                THEN 45


            WHEN days_since_last_cs_interaction > 90
                THEN 55


            WHEN days_since_last_cs_interaction > 60
                THEN 70


            WHEN days_since_last_cs_interaction > 30
                THEN 85


            ELSE 100

        END AS engagement_score,


        -- =================================================
        -- EXPLAINABLE RISK FLAGS
        --
        -- These do not directly determine the score.
        -- They make the final output easier for business
        -- users to interpret.
        -- =================================================

        CASE
            WHEN latest_active_user_rate_pct < 50
                THEN 1
            ELSE 0
        END AS low_usage_flag,


        CASE
            WHEN usage_trend_percentage_points <= -5
                THEN 1
            ELSE 0
        END AS declining_usage_flag,


        CASE
            WHEN latest_feature_adoption_pct < 62.50
                THEN 1
            ELSE 0
        END AS low_feature_adoption_flag,


        CASE
            WHEN
                high_critical_tickets_90d >= 2
                OR unresolved_tickets_90d > 0
                THEN 1
            ELSE 0
        END AS support_risk_flag,


        CASE
            WHEN
                failed_invoices_6m > 0
                OR late_invoices_6m >= 2
                THEN 1
            ELSE 0
        END AS payment_risk_flag,


        CASE
            WHEN
                most_recent_interaction_date IS NULL
                OR days_since_last_cs_interaction > 90
                OR unresponsive_interactions_90d > 0
                THEN 1
            ELSE 0
        END AS engagement_risk_flag


    FROM vw_account_health_base AS b
),


weighted_scores AS (

    SELECT
        c.*,


        -- =================================================
        -- TOTAL CUSTOMER HEALTH SCORE
        --
        -- Product Usage        25%
        -- Usage Trend          20%
        -- Feature Adoption     15%
        -- Support Health       15%
        -- Payment Health       10%
        -- Engagement           15%
        -- =================================================

        ROUND(
              product_usage_score
                * 0.25

            + usage_trend_score
                * 0.20

            + feature_adoption_score
                * 0.15

            + support_health_score
                * 0.15

            + payment_health_score
                * 0.10

            + engagement_score
                * 0.15,

            2
        ) AS health_score,


        (
              low_usage_flag
            + declining_usage_flag
            + low_feature_adoption_flag
            + support_risk_flag
            + payment_risk_flag
            + engagement_risk_flag
        ) AS risk_flag_count


    FROM component_scores AS c
)


SELECT
    w.*,


    -- =====================================================
    -- HEALTH CATEGORY
    --
    -- Initial business interpretation:
    --
    -- Healthy : 75-100
    -- Monitor : 55-74.99
    -- At Risk : below 55
    -- =====================================================

    CASE

        WHEN health_score >= 75
            THEN 'Healthy'

        WHEN health_score >= 55
            THEN 'Monitor'

        ELSE 'At Risk'

    END AS health_status


FROM weighted_scores AS w;


-- =========================================================
-- VALIDATION 1
-- ONE ROW PER ACTIVE CUSTOMER
--
-- Expected:
-- 426 rows
-- 426 unique accounts
-- =========================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT(DISTINCT account_id)
        AS unique_accounts

FROM vw_customer_health_score;


-- =========================================================
-- VALIDATION 2
-- SCORE COMPLETENESS
--
-- All values should be 0.
-- =========================================================

SELECT
    COUNT(*) FILTER (
        WHERE product_usage_score IS NULL
    ) AS missing_product_usage_score,

    COUNT(*) FILTER (
        WHERE usage_trend_score IS NULL
    ) AS missing_usage_trend_score,

    COUNT(*) FILTER (
        WHERE feature_adoption_score IS NULL
    ) AS missing_feature_adoption_score,

    COUNT(*) FILTER (
        WHERE support_health_score IS NULL
    ) AS missing_support_health_score,

    COUNT(*) FILTER (
        WHERE payment_health_score IS NULL
    ) AS missing_payment_health_score,

    COUNT(*) FILTER (
        WHERE engagement_score IS NULL
    ) AS missing_engagement_score,

    COUNT(*) FILTER (
        WHERE health_score IS NULL
    ) AS missing_health_score

FROM vw_customer_health_score;


-- =========================================================
-- VALIDATION 3
-- SCORE RANGE
--
-- Expected: 0 rows
-- =========================================================

SELECT
    account_id,
    account_name,
    health_score
FROM vw_customer_health_score
WHERE health_score < 0
   OR health_score > 100;


-- =========================================================
-- 4. OVERALL HEALTH SCORE DISTRIBUTION
-- =========================================================

SELECT
    ROUND(
        MIN(health_score),
        2
    ) AS minimum_health_score,

    ROUND(
        PERCENTILE_CONT(0.10)
        WITHIN GROUP (
            ORDER BY health_score
        )::NUMERIC,
        2
    ) AS p10_health_score,

    ROUND(
        PERCENTILE_CONT(0.25)
        WITHIN GROUP (
            ORDER BY health_score
        )::NUMERIC,
        2
    ) AS p25_health_score,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY health_score
        )::NUMERIC,
        2
    ) AS median_health_score,

    ROUND(
        AVG(health_score),
        2
    ) AS average_health_score,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY health_score
        )::NUMERIC,
        2
    ) AS p75_health_score,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY health_score
        )::NUMERIC,
        2
    ) AS p90_health_score,

    ROUND(
        MAX(health_score),
        2
    ) AS maximum_health_score

FROM vw_customer_health_score;


-- =========================================================
-- 5. HEALTH STATUS DISTRIBUTION
-- =========================================================

SELECT
    health_status,

    COUNT(*) AS accounts,

    SUM(arr) AS arr,

    ROUND(
        COUNT(*)::NUMERIC
        / (
            SELECT COUNT(*)
            FROM vw_customer_health_score
        )
        * 100,
        2
    ) AS percentage_of_accounts,

    ROUND(
        SUM(arr)::NUMERIC
        / (
            SELECT SUM(arr)
            FROM vw_customer_health_score
        )
        * 100,
        2
    ) AS percentage_of_arr

FROM vw_customer_health_score

GROUP BY health_status

ORDER BY
    CASE health_status

        WHEN 'At Risk'
            THEN 1

        WHEN 'Monitor'
            THEN 2

        WHEN 'Healthy'
            THEN 3

    END;


-- =========================================================
-- 6. HEALTH STATUS BY CUSTOMER SEGMENT
-- =========================================================

SELECT
    segment,

    COUNT(*) FILTER (
        WHERE health_status = 'Healthy'
    ) AS healthy_accounts,

    COUNT(*) FILTER (
        WHERE health_status = 'Monitor'
    ) AS monitor_accounts,

    COUNT(*) FILTER (
        WHERE health_status = 'At Risk'
    ) AS at_risk_accounts,

    ROUND(
        AVG(health_score),
        2
    ) AS average_health_score

FROM vw_customer_health_score

GROUP BY segment

ORDER BY segment;


-- =========================================================
-- 7. AVERAGE COMPONENT SCORES
--
-- This helps determine whether one dimension is
-- disproportionately harsh or lenient.
-- =========================================================

SELECT
    ROUND(
        AVG(product_usage_score),
        2
    ) AS avg_product_usage_score,

    ROUND(
        AVG(usage_trend_score),
        2
    ) AS avg_usage_trend_score,

    ROUND(
        AVG(feature_adoption_score),
        2
    ) AS avg_feature_adoption_score,

    ROUND(
        AVG(support_health_score),
        2
    ) AS avg_support_health_score,

    ROUND(
        AVG(payment_health_score),
        2
    ) AS avg_payment_health_score,

    ROUND(
        AVG(engagement_score),
        2
    ) AS avg_engagement_score,

    ROUND(
        AVG(health_score),
        2
    ) AS avg_total_health_score

FROM vw_customer_health_score;


-- =========================================================
-- 8. RISK FLAG DISTRIBUTION
-- =========================================================

SELECT
    risk_flag_count,

    COUNT(*) AS accounts,

    SUM(arr) AS arr

FROM vw_customer_health_score

GROUP BY risk_flag_count

ORDER BY risk_flag_count;


-- =========================================================
-- 9. HIGH-VALUE AT-RISK ACCOUNTS
--
-- These are likely candidates for eventual Revenue at Risk
-- and Customer Success prioritization.
-- =========================================================

SELECT
    account_id,
    account_name,
    segment,
    assigned_csm,

    mrr,
    arr,
    days_to_renewal,

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
    usage_trend_percentage_points,
    latest_feature_adoption_pct,

    high_critical_tickets_90d,
    unresolved_tickets_90d,

    late_invoices_6m,
    failed_invoices_6m,

    unresponsive_interactions_90d,
    days_since_last_cs_interaction

FROM vw_customer_health_score

WHERE health_status = 'At Risk'

ORDER BY
    arr DESC,
    health_score ASC

LIMIT 25;


-- =========================================================
-- 10. MONITOR ACCOUNTS WITH HIGH ARR
-- =========================================================

SELECT
    account_id,
    account_name,
    segment,
    mrr,
    arr,
    days_to_renewal,
    health_score,
    risk_flag_count

FROM vw_customer_health_score

WHERE health_status = 'Monitor'

ORDER BY arr DESC

LIMIT 20;


-- =========================================================
-- 11. HEALTH SCORE BY SEGMENT AND REVENUE
-- =========================================================

SELECT
    segment,

    COUNT(*) AS active_accounts,

    SUM(arr) AS total_arr,

    ROUND(
        AVG(health_score),
        2
    ) AS average_health_score,

    SUM(arr) FILTER (
        WHERE health_status = 'At Risk'
    ) AS at_risk_arr,

    SUM(arr) FILTER (
        WHERE health_status = 'Monitor'
    ) AS monitor_arr,

    SUM(arr) FILTER (
        WHERE health_status = 'Healthy'
    ) AS healthy_arr

FROM vw_customer_health_score

GROUP BY segment

ORDER BY total_arr DESC;


-- =========================================================
-- 12. SCORE VS RISK FLAGS
--
-- The expected pattern is that more observed risk signals
-- should generally correspond to lower average health.
-- =========================================================

SELECT
    risk_flag_count,

    COUNT(*) AS accounts,

    ROUND(
        AVG(health_score),
        2
    ) AS average_health_score,

    MIN(health_score)
        AS minimum_health_score,

    MAX(health_score)
        AS maximum_health_score

FROM vw_customer_health_score

GROUP BY risk_flag_count

ORDER BY risk_flag_count;
