-- Customer Health & Revenue Risk Analytics
-- Health Signal Distribution Analysis
--
-- Purpose:
-- Examine the actual distribution of the six intended
-- Customer Health dimensions before defining scoring rules.
--
-- Health dimensions:
-- 1. Product Usage
-- 2. Usage Trend
-- 3. Feature Adoption
-- 4. Support Health
-- 5. Payment Health
-- 6. Customer Engagement
--
-- Analysis snapshot date:
-- 2026-12-31


\set ON_ERROR_STOP on
\pset pager off


-- =========================================================
-- 1. CONFIRM ANALYTICAL POPULATION
-- Expected: 426 active accounts
-- =========================================================

SELECT
    COUNT(*) AS active_accounts,
    SUM(mrr) AS total_mrr,
    SUM(arr) AS total_arr
FROM vw_account_health_base;


-- =========================================================
-- 2. PRODUCT USAGE DISTRIBUTION
--
-- Metric:
-- latest_active_user_rate_pct
-- =========================================================

SELECT
    ROUND(
        MIN(latest_active_user_rate_pct),
        2
    ) AS minimum_usage_pct,

    ROUND(
        PERCENTILE_CONT(0.10)
        WITHIN GROUP (
            ORDER BY latest_active_user_rate_pct
        )::NUMERIC,
        2
    ) AS p10_usage_pct,

    ROUND(
        PERCENTILE_CONT(0.25)
        WITHIN GROUP (
            ORDER BY latest_active_user_rate_pct
        )::NUMERIC,
        2
    ) AS p25_usage_pct,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY latest_active_user_rate_pct
        )::NUMERIC,
        2
    ) AS median_usage_pct,

    ROUND(
        AVG(latest_active_user_rate_pct),
        2
    ) AS average_usage_pct,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY latest_active_user_rate_pct
        )::NUMERIC,
        2
    ) AS p75_usage_pct,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY latest_active_user_rate_pct
        )::NUMERIC,
        2
    ) AS p90_usage_pct,

    ROUND(
        MAX(latest_active_user_rate_pct),
        2
    ) AS maximum_usage_pct

FROM vw_account_health_base;


-- =========================================================
-- 3. PRODUCT USAGE BANDS
--
-- These are exploratory bands only.
-- They are NOT final scoring thresholds.
-- =========================================================

SELECT
    CASE

        WHEN latest_active_user_rate_pct < 40
            THEN '< 40%'

        WHEN latest_active_user_rate_pct < 55
            THEN '40% - 54.99%'

        WHEN latest_active_user_rate_pct < 70
            THEN '55% - 69.99%'

        WHEN latest_active_user_rate_pct < 85
            THEN '70% - 84.99%'

        ELSE '85%+'

    END AS usage_band,

    COUNT(*) AS accounts,

    SUM(arr) AS arr,

    ROUND(
        SUM(arr)::NUMERIC
        / (
            SELECT SUM(arr)
            FROM vw_account_health_base
        )
        * 100,
        2
    ) AS percentage_of_arr

FROM vw_account_health_base

GROUP BY
    CASE

        WHEN latest_active_user_rate_pct < 40
            THEN '< 40%'

        WHEN latest_active_user_rate_pct < 55
            THEN '40% - 54.99%'

        WHEN latest_active_user_rate_pct < 70
            THEN '55% - 69.99%'

        WHEN latest_active_user_rate_pct < 85
            THEN '70% - 84.99%'

        ELSE '85%+'

    END

ORDER BY
    MIN(latest_active_user_rate_pct);


-- =========================================================
-- 4. USAGE TREND DISTRIBUTION
--
-- Metric:
-- latest 3-month active-user rate
-- minus previous 3-month active-user rate
--
-- Unit:
-- percentage points
-- =========================================================

SELECT
    ROUND(
        MIN(usage_trend_percentage_points),
        2
    ) AS minimum_trend_pp,

    ROUND(
        PERCENTILE_CONT(0.10)
        WITHIN GROUP (
            ORDER BY usage_trend_percentage_points
        )::NUMERIC,
        2
    ) AS p10_trend_pp,

    ROUND(
        PERCENTILE_CONT(0.25)
        WITHIN GROUP (
            ORDER BY usage_trend_percentage_points
        )::NUMERIC,
        2
    ) AS p25_trend_pp,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY usage_trend_percentage_points
        )::NUMERIC,
        2
    ) AS median_trend_pp,

    ROUND(
        AVG(usage_trend_percentage_points),
        2
    ) AS average_trend_pp,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY usage_trend_percentage_points
        )::NUMERIC,
        2
    ) AS p75_trend_pp,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY usage_trend_percentage_points
        )::NUMERIC,
        2
    ) AS p90_trend_pp,

    ROUND(
        MAX(usage_trend_percentage_points),
        2
    ) AS maximum_trend_pp

FROM vw_account_health_base;


-- =========================================================
-- 5. USAGE TREND BANDS
--
-- Exploratory only.
-- =========================================================

SELECT
    CASE

        WHEN usage_trend_percentage_points <= -10
            THEN 'Decline <= -10 pp'

        WHEN usage_trend_percentage_points <= -5
            THEN 'Decline -5 to -9.99 pp'

        WHEN usage_trend_percentage_points < 5
            THEN 'Stable (-5 to +4.99 pp)'

        WHEN usage_trend_percentage_points < 10
            THEN 'Growth +5 to +9.99 pp'

        ELSE 'Growth >= +10 pp'

    END AS usage_trend_band,

    COUNT(*) AS accounts,

    SUM(arr) AS arr

FROM vw_account_health_base

GROUP BY
    CASE

        WHEN usage_trend_percentage_points <= -10
            THEN 'Decline <= -10 pp'

        WHEN usage_trend_percentage_points <= -5
            THEN 'Decline -5 to -9.99 pp'

        WHEN usage_trend_percentage_points < 5
            THEN 'Stable (-5 to +4.99 pp)'

        WHEN usage_trend_percentage_points < 10
            THEN 'Growth +5 to +9.99 pp'

        ELSE 'Growth >= +10 pp'

    END

ORDER BY
    MIN(usage_trend_percentage_points);


-- =========================================================
-- 6. FEATURE ADOPTION DISTRIBUTION
--
-- There are 8 core features, so this metric naturally
-- appears in 12.5 percentage-point increments.
-- =========================================================

SELECT
    latest_feature_adoption_pct,
    COUNT(*) AS accounts,
    SUM(arr) AS arr

FROM vw_account_health_base

GROUP BY latest_feature_adoption_pct

ORDER BY latest_feature_adoption_pct;


-- =========================================================
-- 7. FEATURE ADOPTION SUMMARY
-- =========================================================

SELECT
    ROUND(
        MIN(latest_feature_adoption_pct),
        2
    ) AS minimum_feature_adoption_pct,

    ROUND(
        PERCENTILE_CONT(0.25)
        WITHIN GROUP (
            ORDER BY latest_feature_adoption_pct
        )::NUMERIC,
        2
    ) AS p25_feature_adoption_pct,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY latest_feature_adoption_pct
        )::NUMERIC,
        2
    ) AS median_feature_adoption_pct,

    ROUND(
        AVG(latest_feature_adoption_pct),
        2
    ) AS average_feature_adoption_pct,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY latest_feature_adoption_pct
        )::NUMERIC,
        2
    ) AS p75_feature_adoption_pct,

    ROUND(
        MAX(latest_feature_adoption_pct),
        2
    ) AS maximum_feature_adoption_pct

FROM vw_account_health_base;


-- =========================================================
-- 8. SUPPORT HEALTH DISTRIBUTION
--
-- Recent period = final 90 days
-- =========================================================

SELECT
    ROUND(
        AVG(tickets_90d),
        2
    ) AS avg_tickets_90d,

    PERCENTILE_CONT(0.50)
    WITHIN GROUP (
        ORDER BY tickets_90d
    ) AS median_tickets_90d,

    PERCENTILE_CONT(0.75)
    WITHIN GROUP (
        ORDER BY tickets_90d
    ) AS p75_tickets_90d,

    PERCENTILE_CONT(0.90)
    WITHIN GROUP (
        ORDER BY tickets_90d
    ) AS p90_tickets_90d,

    MAX(tickets_90d)
        AS maximum_tickets_90d,

    ROUND(
        AVG(high_critical_tickets_90d),
        2
    ) AS avg_high_critical_tickets_90d,

    MAX(high_critical_tickets_90d)
        AS maximum_high_critical_tickets_90d,

    ROUND(
        AVG(unresolved_tickets_90d),
        2
    ) AS avg_unresolved_tickets_90d,

    MAX(unresolved_tickets_90d)
        AS maximum_unresolved_tickets_90d

FROM vw_account_health_base;


-- =========================================================
-- 9. SUPPORT TICKET COUNT DISTRIBUTION
-- =========================================================

SELECT
    CASE

        WHEN tickets_90d = 0
            THEN '0 tickets'

        WHEN tickets_90d = 1
            THEN '1 ticket'

        WHEN tickets_90d = 2
            THEN '2 tickets'

        WHEN tickets_90d = 3
            THEN '3 tickets'

        ELSE '4+ tickets'

    END AS ticket_band,

    COUNT(*) AS accounts,

    SUM(arr) AS arr

FROM vw_account_health_base

GROUP BY
    CASE

        WHEN tickets_90d = 0
            THEN '0 tickets'

        WHEN tickets_90d = 1
            THEN '1 ticket'

        WHEN tickets_90d = 2
            THEN '2 tickets'

        WHEN tickets_90d = 3
            THEN '3 tickets'

        ELSE '4+ tickets'

    END

ORDER BY
    MIN(tickets_90d);


-- =========================================================
-- 10. SUPPORT SEVERITY COUNTS
-- =========================================================

SELECT
    COUNT(*) FILTER (
        WHERE high_critical_tickets_90d = 0
    ) AS accounts_no_high_critical,

    COUNT(*) FILTER (
        WHERE high_critical_tickets_90d = 1
    ) AS accounts_one_high_critical,

    COUNT(*) FILTER (
        WHERE high_critical_tickets_90d >= 2
    ) AS accounts_multiple_high_critical,

    COUNT(*) FILTER (
        WHERE unresolved_tickets_90d > 0
    ) AS accounts_with_unresolved_tickets

FROM vw_account_health_base;


-- =========================================================
-- 11. PAYMENT HEALTH DISTRIBUTION
--
-- Recent period = final 6 months
-- =========================================================

SELECT
    ROUND(
        AVG(payment_issue_rate_6m_pct),
        2
    ) AS average_payment_issue_rate_pct,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY payment_issue_rate_6m_pct
        )::NUMERIC,
        2
    ) AS median_payment_issue_rate_pct,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY payment_issue_rate_6m_pct
        )::NUMERIC,
        2
    ) AS p75_payment_issue_rate_pct,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY payment_issue_rate_6m_pct
        )::NUMERIC,
        2
    ) AS p90_payment_issue_rate_pct,

    MAX(payment_issue_rate_6m_pct)
        AS maximum_payment_issue_rate_pct,

    COUNT(*) FILTER (
        WHERE late_invoices_6m > 0
    ) AS accounts_with_late_invoices,

    COUNT(*) FILTER (
        WHERE failed_invoices_6m > 0
    ) AS accounts_with_failed_invoices

FROM vw_account_health_base;


-- =========================================================
-- 12. PAYMENT BEHAVIOR GROUPS
--
-- These categories describe actual observed behavior.
-- They are not Health Score categories yet.
-- =========================================================

SELECT
    CASE

        WHEN failed_invoices_6m > 0
            THEN 'At least one failed invoice'

        WHEN late_invoices_6m > 0
            THEN 'Late invoice(s), no failures'

        ELSE 'No late or failed invoices'

    END AS payment_behavior,

    COUNT(*) AS accounts,

    SUM(arr) AS arr

FROM vw_account_health_base

GROUP BY
    CASE

        WHEN failed_invoices_6m > 0
            THEN 'At least one failed invoice'

        WHEN late_invoices_6m > 0
            THEN 'Late invoice(s), no failures'

        ELSE 'No late or failed invoices'

    END

ORDER BY
    CASE
        WHEN
            CASE

                WHEN failed_invoices_6m > 0
                    THEN 'At least one failed invoice'

                WHEN late_invoices_6m > 0
                    THEN 'Late invoice(s), no failures'

                ELSE 'No late or failed invoices'

            END = 'No late or failed invoices'
            THEN 1

        WHEN
            CASE

                WHEN failed_invoices_6m > 0
                    THEN 'At least one failed invoice'

                WHEN late_invoices_6m > 0
                    THEN 'Late invoice(s), no failures'

                ELSE 'No late or failed invoices'

            END = 'Late invoice(s), no failures'
            THEN 2

        ELSE 3
    END;


-- =========================================================
-- 13. CUSTOMER ENGAGEMENT DISTRIBUTION
-- =========================================================

SELECT
    COUNT(*) FILTER (
        WHERE most_recent_interaction_date IS NULL
    ) AS accounts_with_no_cs_history,

    ROUND(
        AVG(days_since_last_cs_interaction)
            FILTER (
                WHERE days_since_last_cs_interaction
                IS NOT NULL
            ),
        2
    ) AS avg_days_since_last_interaction,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY days_since_last_cs_interaction
        ) FILTER (
            WHERE days_since_last_cs_interaction
            IS NOT NULL
        )::NUMERIC,
        2
    ) AS median_days_since_last_interaction,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY days_since_last_cs_interaction
        ) FILTER (
            WHERE days_since_last_cs_interaction
            IS NOT NULL
        )::NUMERIC,
        2
    ) AS p75_days_since_last_interaction,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY days_since_last_cs_interaction
        ) FILTER (
            WHERE days_since_last_cs_interaction
            IS NOT NULL
        )::NUMERIC,
        2
    ) AS p90_days_since_last_interaction

FROM vw_account_health_base;


-- =========================================================
-- 14. RECENT CUSTOMER ENGAGEMENT SIGNALS
-- =========================================================

SELECT
    COUNT(*) FILTER (
        WHERE cs_interactions_90d = 0
    ) AS accounts_no_cs_interaction_90d,

    COUNT(*) FILTER (
        WHERE cs_interactions_90d > 0
    ) AS accounts_with_cs_interaction_90d,

    COUNT(*) FILTER (
        WHERE unresponsive_interactions_90d > 0
    ) AS accounts_with_unresponsive_interaction,

    COUNT(*) FILTER (
        WHERE followups_required_90d > 0
    ) AS accounts_requiring_followup,

    COUNT(*) FILTER (
        WHERE unresponsive_interactions_90d >= 2
    ) AS accounts_multiple_unresponsive_interactions

FROM vw_account_health_base;


-- =========================================================
-- 15. DAYS SINCE LAST CS INTERACTION BANDS
--
-- Exploratory only.
-- =========================================================

SELECT
    CASE

        WHEN days_since_last_cs_interaction IS NULL
            THEN 'No CS interaction history'

        WHEN days_since_last_cs_interaction <= 30
            THEN '0-30 days'

        WHEN days_since_last_cs_interaction <= 60
            THEN '31-60 days'

        WHEN days_since_last_cs_interaction <= 90
            THEN '61-90 days'

        ELSE '90+ days'

    END AS recency_band,

    COUNT(*) AS accounts,

    SUM(arr) AS arr

FROM vw_account_health_base

GROUP BY
    CASE

        WHEN days_since_last_cs_interaction IS NULL
            THEN 'No CS interaction history'

        WHEN days_since_last_cs_interaction <= 30
            THEN '0-30 days'

        WHEN days_since_last_cs_interaction <= 60
            THEN '31-60 days'

        WHEN days_since_last_cs_interaction <= 90
            THEN '61-90 days'

        ELSE '90+ days'

    END

ORDER BY
    CASE

        WHEN
            CASE

                WHEN days_since_last_cs_interaction IS NULL
                    THEN 'No CS interaction history'

                WHEN days_since_last_cs_interaction <= 30
                    THEN '0-30 days'

                WHEN days_since_last_cs_interaction <= 60
                    THEN '31-60 days'

                WHEN days_since_last_cs_interaction <= 90
                    THEN '61-90 days'

                ELSE '90+ days'

            END = '0-30 days'
            THEN 1

        WHEN
            CASE

                WHEN days_since_last_cs_interaction IS NULL
                    THEN 'No CS interaction history'

                WHEN days_since_last_cs_interaction <= 30
                    THEN '0-30 days'

                WHEN days_since_last_cs_interaction <= 60
                    THEN '31-60 days'

                WHEN days_since_last_cs_interaction <= 90
                    THEN '61-90 days'

                ELSE '90+ days'

            END = '31-60 days'
            THEN 2

        WHEN
            CASE

                WHEN days_since_last_cs_interaction IS NULL
                    THEN 'No CS interaction history'

                WHEN days_since_last_cs_interaction <= 30
                    THEN '0-30 days'

                WHEN days_since_last_cs_interaction <= 60
                    THEN '31-60 days'

                WHEN days_since_last_cs_interaction <= 90
                    THEN '61-90 days'

                ELSE '90+ days'

            END = '61-90 days'
            THEN 3

        WHEN
            CASE

                WHEN days_since_last_cs_interaction IS NULL
                    THEN 'No CS interaction history'

                WHEN days_since_last_cs_interaction <= 30
                    THEN '0-30 days'

                WHEN days_since_last_cs_interaction <= 60
                    THEN '31-60 days'

                WHEN days_since_last_cs_interaction <= 90
                    THEN '61-90 days'

                ELSE '90+ days'

            END = '90+ days'
            THEN 4

        ELSE 5
    END;


-- =========================================================
-- 16. SIGNAL SUMMARY BY SEGMENT
--
-- Useful for checking whether one customer segment
-- naturally behaves differently from another.
-- =========================================================

SELECT
    segment,

    COUNT(*) AS active_accounts,

    ROUND(
        AVG(latest_active_user_rate_pct),
        2
    ) AS avg_usage_pct,

    ROUND(
        AVG(usage_trend_percentage_points),
        2
    ) AS avg_usage_trend_pp,

    ROUND(
        AVG(latest_feature_adoption_pct),
        2
    ) AS avg_feature_adoption_pct,

    ROUND(
        AVG(tickets_90d),
        2
    ) AS avg_tickets_90d,

    ROUND(
        AVG(high_critical_tickets_90d),
        2
    ) AS avg_high_critical_tickets_90d,

    ROUND(
        AVG(payment_issue_rate_6m_pct),
        2
    ) AS avg_payment_issue_rate_pct,

    ROUND(
        AVG(days_since_last_cs_interaction)
            FILTER (
                WHERE days_since_last_cs_interaction
                IS NOT NULL
            ),
        2
    ) AS avg_days_since_last_cs_interaction,

    ROUND(
        AVG(unresponsive_interactions_90d),
        2
    ) AS avg_unresponsive_interactions_90d

FROM vw_account_health_base

GROUP BY segment

ORDER BY segment;


-- =========================================================
-- 17. ACCOUNTS SHOWING MULTIPLE OBSERVED RISK SIGNALS
--
-- This is NOT the final Health Score.
--
-- The purpose is simply to see whether behavioral
-- warning signs overlap on the same accounts.
-- =========================================================

SELECT
    account_id,
    account_name,
    segment,
    mrr,
    arr,
    days_to_renewal,

    latest_active_user_rate_pct,
    usage_trend_percentage_points,
    latest_feature_adoption_pct,

    tickets_90d,
    high_critical_tickets_90d,
    unresolved_tickets_90d,

    late_invoices_6m,
    failed_invoices_6m,

    unresponsive_interactions_90d,
    days_since_last_cs_interaction

FROM vw_account_health_base

WHERE
       latest_active_user_rate_pct < 50

    OR usage_trend_percentage_points <= -10

    OR high_critical_tickets_90d >= 2

    OR unresolved_tickets_90d > 0

    OR failed_invoices_6m > 0

    OR unresponsive_interactions_90d >= 2

ORDER BY
    mrr DESC

LIMIT 30;
