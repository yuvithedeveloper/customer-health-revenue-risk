-- Customer Health & Revenue Risk Analytics
-- Retention and Recurring Revenue Analysis
--
-- Purpose:
-- Analyze annual customer retention and recurring-revenue
-- movement using beginning-of-year customer cohorts.
--
-- Metrics:
-- Logo Retention
-- Logo Churn
-- Gross Revenue Retention (GRR)
-- Net Revenue Retention (NRR)
-- Expansion MRR
-- Contraction MRR
-- Churned MRR
--
-- Years analyzed:
-- 2025
-- 2026
--
-- IMPORTANT:
-- GRR and NRR use customers that existed at the START
-- of each year. New customers acquired during the year
-- are excluded from these retention calculations.


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- DROP VIEW IF IT ALREADY EXISTS
-- =========================================================

DROP VIEW IF EXISTS vw_retention_revenue_cohort;


-- =========================================================
-- CREATE ACCOUNT-YEAR RETENTION VIEW
-- =========================================================

CREATE VIEW vw_retention_revenue_cohort AS


WITH analysis_periods AS (

    SELECT
        2025 AS analysis_year,
        DATE '2025-01-01' AS period_start,
        DATE '2025-12-31' AS period_end

    UNION ALL

    SELECT
        2026,
        DATE '2026-01-01',
        DATE '2026-12-31'
),


-- =========================================================
-- FIND ACCOUNT MRR AT START AND END OF EACH YEAR
-- =========================================================

account_snapshots AS (

    SELECT
        y.analysis_year,
        y.period_start,
        y.period_end,

        a.account_id,
        a.account_name,
        a.segment,
        a.industry,
        a.region,

        start_sub.plan_name
            AS start_plan_name,

        start_sub.mrr
            AS start_mrr,

        end_sub.plan_name
            AS end_plan_name,

        COALESCE(
            end_sub.mrr,
            0
        ) AS end_mrr

    FROM analysis_periods AS y

    CROSS JOIN accounts AS a


    -- -----------------------------------------------------
    -- SUBSCRIPTION ACTIVE AT START OF YEAR
    -- -----------------------------------------------------

    LEFT JOIN LATERAL (

        SELECT
            s.plan_name,
            s.mrr

        FROM subscriptions AS s

        WHERE s.account_id = a.account_id

          AND s.subscription_start_date
                <= y.period_start

          AND s.subscription_end_date
                >= y.period_start

        ORDER BY
            s.subscription_start_date DESC

        LIMIT 1

    ) AS start_sub
        ON TRUE


    -- -----------------------------------------------------
    -- SUBSCRIPTION ACTIVE AT END OF YEAR
    -- -----------------------------------------------------

    LEFT JOIN LATERAL (

        SELECT
            s.plan_name,
            s.mrr

        FROM subscriptions AS s

        WHERE s.account_id = a.account_id

          AND s.subscription_start_date
                <= y.period_end

          AND s.subscription_end_date
                >= y.period_end

        ORDER BY
            s.subscription_start_date DESC

        LIMIT 1

    ) AS end_sub
        ON TRUE


    -- -----------------------------------------------------
    -- RETENTION COHORT:
    -- CUSTOMER MUST EXIST AT START OF YEAR
    -- -----------------------------------------------------

    WHERE start_sub.mrr IS NOT NULL
)


-- =========================================================
-- CLASSIFY ANNUAL REVENUE MOVEMENT
-- =========================================================

SELECT
    analysis_year,
    period_start,
    period_end,

    account_id,
    account_name,
    segment,
    industry,
    region,

    start_plan_name,
    end_plan_name,

    start_mrr,
    end_mrr,

    start_mrr * 12
        AS start_arr,

    end_mrr * 12
        AS end_arr,


    -- -----------------------------------------------------
    -- MRR CHANGE
    -- -----------------------------------------------------

    end_mrr - start_mrr
        AS net_mrr_change,


    -- -----------------------------------------------------
    -- RETENTION OUTCOME
    -- -----------------------------------------------------

    CASE

        WHEN end_mrr = 0
            THEN 'Churned'

        WHEN end_mrr > start_mrr
            THEN 'Expanded'

        WHEN end_mrr < start_mrr
            THEN 'Contracted'

        ELSE 'Retained - Flat'

    END AS retention_outcome,


    -- -----------------------------------------------------
    -- CHURNED MRR
    -- -----------------------------------------------------

    CASE

        WHEN end_mrr = 0
            THEN start_mrr

        ELSE 0

    END AS churned_mrr,


    -- -----------------------------------------------------
    -- CONTRACTION MRR
    -- -----------------------------------------------------

    CASE

        WHEN end_mrr > 0
         AND end_mrr < start_mrr

            THEN start_mrr - end_mrr

        ELSE 0

    END AS contraction_mrr,


    -- -----------------------------------------------------
    -- EXPANSION MRR
    -- -----------------------------------------------------

    CASE

        WHEN end_mrr > start_mrr
            THEN end_mrr - start_mrr

        ELSE 0

    END AS expansion_mrr


FROM account_snapshots;


-- =========================================================
-- 1. VIEW VALIDATION
--
-- Each account should appear at most once in each year.
-- Expected duplicate combinations = 0
-- =========================================================

SELECT
    COUNT(*) AS duplicate_account_years

FROM (

    SELECT
        analysis_year,
        account_id

    FROM vw_retention_revenue_cohort

    GROUP BY
        analysis_year,
        account_id

    HAVING COUNT(*) > 1

) AS duplicates;


-- =========================================================
-- 2. COHORT SIZE BY YEAR
-- =========================================================

SELECT
    analysis_year,

    COUNT(*) AS beginning_accounts,

    SUM(start_mrr)
        AS beginning_mrr,

    SUM(start_arr)
        AS beginning_arr

FROM vw_retention_revenue_cohort

GROUP BY analysis_year

ORDER BY analysis_year;


-- =========================================================
-- 3. ANNUAL RETENTION METRICS
--
-- Logo Retention:
-- retained accounts / beginning accounts
--
-- GRR:
-- excludes expansion
--
-- NRR:
-- includes expansion
-- =========================================================

SELECT
    analysis_year,

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
        AS ending_mrr_from_starting_cohort,


    SUM(churned_mrr)
        AS churned_mrr,


    SUM(contraction_mrr)
        AS contraction_mrr,


    SUM(expansion_mrr)
        AS expansion_mrr,


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

GROUP BY analysis_year

ORDER BY analysis_year;


-- =========================================================
-- 4. RETENTION OUTCOME MIX BY YEAR
-- =========================================================

SELECT
    analysis_year,
    retention_outcome,

    COUNT(*) AS accounts,

    SUM(start_mrr)
        AS beginning_mrr,

    SUM(end_mrr)
        AS ending_mrr,

    SUM(net_mrr_change)
        AS net_mrr_change

FROM vw_retention_revenue_cohort

GROUP BY
    analysis_year,
    retention_outcome

ORDER BY
    analysis_year,

    CASE retention_outcome

        WHEN 'Churned'
            THEN 1

        WHEN 'Contracted'
            THEN 2

        WHEN 'Retained - Flat'
            THEN 3

        WHEN 'Expanded'
            THEN 4

    END;


-- =========================================================
-- 5. 2026 RETENTION BY SEGMENT
--
-- Segment differences are especially useful for the
-- eventual Power BI retention page.
-- =========================================================

SELECT
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


    SUM(start_mrr)
        AS beginning_mrr,


    SUM(churned_mrr)
        AS churned_mrr,


    SUM(contraction_mrr)
        AS contraction_mrr,


    SUM(expansion_mrr)
        AS expansion_mrr,


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

WHERE analysis_year = 2026

GROUP BY segment

ORDER BY beginning_mrr DESC;


-- =========================================================
-- 6. 2025 RETENTION BY SEGMENT
-- =========================================================

SELECT
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


    SUM(start_mrr)
        AS beginning_mrr,


    SUM(churned_mrr)
        AS churned_mrr,


    SUM(contraction_mrr)
        AS contraction_mrr,


    SUM(expansion_mrr)
        AS expansion_mrr,


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

WHERE analysis_year = 2025

GROUP BY segment

ORDER BY beginning_mrr DESC;


-- =========================================================
-- 7. REVENUE MOVEMENT BRIDGE
--
-- Starting MRR
-- + Expansion
-- - Contraction
-- - Churn
-- = Ending MRR from starting customer cohort
-- =========================================================

SELECT
    analysis_year,

    SUM(start_mrr)
        AS starting_mrr,

    SUM(expansion_mrr)
        AS expansion_mrr,

    SUM(contraction_mrr)
        AS contraction_mrr,

    SUM(churned_mrr)
        AS churned_mrr,

    SUM(start_mrr)
        + SUM(expansion_mrr)
        - SUM(contraction_mrr)
        - SUM(churned_mrr)
            AS calculated_ending_mrr,

    SUM(end_mrr)
        AS actual_ending_mrr

FROM vw_retention_revenue_cohort

GROUP BY analysis_year

ORDER BY analysis_year;


-- =========================================================
-- 8. REVENUE BRIDGE VALIDATION
--
-- Expected difference = 0 for each year
-- =========================================================

SELECT
    analysis_year,

    (
        SUM(start_mrr)
        + SUM(expansion_mrr)
        - SUM(contraction_mrr)
        - SUM(churned_mrr)
    )
    - SUM(end_mrr)
        AS bridge_difference

FROM vw_retention_revenue_cohort

GROUP BY analysis_year

ORDER BY analysis_year;


-- =========================================================
-- 9. NEW CUSTOMER MRR DURING EACH YEAR
--
-- These customers are excluded from NRR/GRR because
-- they were not present at the beginning of the year.
-- =========================================================

WITH analysis_periods AS (

    SELECT
        2025 AS analysis_year,
        DATE '2025-01-01' AS period_start,
        DATE '2025-12-31' AS period_end

    UNION ALL

    SELECT
        2026,
        DATE '2026-01-01',
        DATE '2026-12-31'
),

snapshots AS (

    SELECT
        y.analysis_year,
        a.account_id,

        start_sub.mrr
            AS start_mrr,

        end_sub.mrr
            AS end_mrr

    FROM analysis_periods AS y

    CROSS JOIN accounts AS a


    LEFT JOIN LATERAL (

        SELECT
            s.mrr

        FROM subscriptions AS s

        WHERE s.account_id = a.account_id

          AND s.subscription_start_date
                <= y.period_start

          AND s.subscription_end_date
                >= y.period_start

        ORDER BY
            s.subscription_start_date DESC

        LIMIT 1

    ) AS start_sub
        ON TRUE


    LEFT JOIN LATERAL (

        SELECT
            s.mrr

        FROM subscriptions AS s

        WHERE s.account_id = a.account_id

          AND s.subscription_start_date
                <= y.period_end

          AND s.subscription_end_date
                >= y.period_end

        ORDER BY
            s.subscription_start_date DESC

        LIMIT 1

    ) AS end_sub
        ON TRUE
)

SELECT
    analysis_year,

    COUNT(*) FILTER (
        WHERE start_mrr IS NULL
          AND end_mrr IS NOT NULL
    ) AS new_customers,

    SUM(end_mrr) FILTER (
        WHERE start_mrr IS NULL
          AND end_mrr IS NOT NULL
    ) AS new_customer_mrr,

    SUM(end_mrr) FILTER (
        WHERE start_mrr IS NULL
          AND end_mrr IS NOT NULL
    ) * 12 AS new_customer_arr

FROM snapshots

GROUP BY analysis_year

ORDER BY analysis_year;


-- =========================================================
-- 10. TOTAL PORTFOLIO MRR GROWTH
--
-- Unlike NRR, this DOES include new customers.
-- =========================================================

WITH analysis_periods AS (

    SELECT
        2025 AS analysis_year,
        DATE '2025-01-01' AS period_start,
        DATE '2025-12-31' AS period_end

    UNION ALL

    SELECT
        2026,
        DATE '2026-01-01',
        DATE '2026-12-31'
)

SELECT
    y.analysis_year,


    (
        SELECT SUM(s.mrr)

        FROM subscriptions AS s

        WHERE s.subscription_start_date
                <= y.period_start

          AND s.subscription_end_date
                >= y.period_start

    ) AS beginning_portfolio_mrr,


    (
        SELECT SUM(s.mrr)

        FROM subscriptions AS s

        WHERE s.subscription_start_date
                <= y.period_end

          AND s.subscription_end_date
                >= y.period_end

    ) AS ending_portfolio_mrr,


    ROUND(
        (
            (
                SELECT SUM(s.mrr)

                FROM subscriptions AS s

                WHERE s.subscription_start_date
                        <= y.period_end

                  AND s.subscription_end_date
                        >= y.period_end
            )

            -

            (
                SELECT SUM(s.mrr)

                FROM subscriptions AS s

                WHERE s.subscription_start_date
                        <= y.period_start

                  AND s.subscription_end_date
                        >= y.period_start
            )
        )::NUMERIC

        /

        NULLIF(
            (
                SELECT SUM(s.mrr)

                FROM subscriptions AS s

                WHERE s.subscription_start_date
                        <= y.period_start

                  AND s.subscription_end_date
                        >= y.period_start
            ),
            0
        )

        * 100,
        2
    ) AS total_mrr_growth_pct


FROM analysis_periods AS y

ORDER BY y.analysis_year;


-- =========================================================
-- 11. TOP EXPANSION ACCOUNTS
-- =========================================================

SELECT
    analysis_year,
    account_id,
    account_name,
    segment,

    start_mrr,
    end_mrr,
    expansion_mrr,

    expansion_mrr * 12
        AS expansion_arr

FROM vw_retention_revenue_cohort

WHERE retention_outcome = 'Expanded'

ORDER BY
    expansion_mrr DESC

LIMIT 20;


-- =========================================================
-- 12. TOP CONTRACTION ACCOUNTS
-- =========================================================

SELECT
    analysis_year,
    account_id,
    account_name,
    segment,

    start_mrr,
    end_mrr,
    contraction_mrr,

    contraction_mrr * 12
        AS contraction_arr

FROM vw_retention_revenue_cohort

WHERE retention_outcome = 'Contracted'

ORDER BY
    contraction_mrr DESC

LIMIT 20;


-- =========================================================
-- 13. HIGHEST-VALUE CHURNED ACCOUNTS
-- =========================================================

SELECT
    analysis_year,
    account_id,
    account_name,
    segment,

    start_mrr,

    start_mrr * 12
        AS churned_arr

FROM vw_retention_revenue_cohort

WHERE retention_outcome = 'Churned'

ORDER BY
    start_mrr DESC

LIMIT 20;


-- =========================================================
-- 14. RETENTION OUTCOME BY SEGMENT ACROSS BOTH YEARS
-- =========================================================

SELECT
    analysis_year,
    segment,
    retention_outcome,

    COUNT(*) AS accounts,

    SUM(start_mrr)
        AS starting_mrr,

    SUM(net_mrr_change)
        AS net_mrr_change

FROM vw_retention_revenue_cohort

GROUP BY
    analysis_year,
    segment,
    retention_outcome

ORDER BY
    analysis_year,
    segment,
    retention_outcome;


-- =========================================================
-- 15. RETENTION METRIC VALIDATION
--
-- GRR should not exceed 100%.
-- Logo retention should remain within 0-100%.
-- NRR can exceed 100% because of expansion.
--
-- Expected: 0 rows
-- =========================================================

WITH retention_metrics AS (

    SELECT
        analysis_year,

        (
            COUNT(*) FILTER (
                WHERE end_mrr > 0
            )
        )::NUMERIC
        / NULLIF(
            COUNT(*),
            0
        )
        * 100 AS logo_retention_pct,


        (
            SUM(start_mrr)
            - SUM(churned_mrr)
            - SUM(contraction_mrr)
        )
        / NULLIF(
            SUM(start_mrr),
            0
        )
        * 100 AS grr_pct,


        SUM(end_mrr)
        / NULLIF(
            SUM(start_mrr),
            0
        )
        * 100 AS nrr_pct

    FROM vw_retention_revenue_cohort

    GROUP BY analysis_year
)

SELECT
    analysis_year,
    logo_retention_pct,
    grr_pct,
    nrr_pct

FROM retention_metrics

WHERE logo_retention_pct < 0
   OR logo_retention_pct > 100

   OR grr_pct < 0
   OR grr_pct > 100

   OR nrr_pct < 0;


-- =========================================================
-- 16. FINAL RETENTION SUMMARY
-- =========================================================

SELECT
    analysis_year,

    COUNT(*) AS beginning_accounts,

    COUNT(*) FILTER (
        WHERE end_mrr = 0
    ) AS churned_accounts,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE end_mrr > 0
            )
        )::NUMERIC
        / COUNT(*)
        * 100,
        2
    ) AS logo_retention_pct,


    ROUND(
        (
            SUM(start_mrr)
            - SUM(churned_mrr)
            - SUM(contraction_mrr)
        )
        / SUM(start_mrr)
        * 100,
        2
    ) AS grr_pct,


    ROUND(
        SUM(end_mrr)
        / SUM(start_mrr)
        * 100,
        2
    ) AS nrr_pct,


    SUM(expansion_mrr)
        AS expansion_mrr,

    SUM(contraction_mrr)
        AS contraction_mrr,

    SUM(churned_mrr)
        AS churned_mrr

FROM vw_retention_revenue_cohort

GROUP BY analysis_year

ORDER BY analysis_year;
