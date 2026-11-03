-- Customer Health & Revenue Risk Analytics
-- Load cleaned support ticket data into PostgreSQL


-- =========================================================
-- STOP SCRIPT IF ANY COMMAND FAILS
-- =========================================================

\set ON_ERROR_STOP on


-- =========================================================
-- PRE-LOAD CHECK
-- Expected before first load: 0
-- =========================================================

SELECT
    COUNT(*) AS existing_support_ticket_rows
FROM support_tickets;


-- =========================================================
-- LOAD SUPPORT TICKETS
-- Source:
-- data/processed/support_tickets.csv
-- =========================================================

BEGIN;

\copy support_tickets (ticket_id, account_id, created_date, resolved_date, priority, category, ticket_status, resolution_hours, customer_satisfaction_score) FROM 'C:/Yuvraj/Stevens/Projects/customer-health-revenue-risk/data/processed/support_tickets.csv' WITH (FORMAT csv, HEADER true, NULL '');


-- =========================================================
-- SYNCHRONIZE IDENTITY SEQUENCE
-- =========================================================

SELECT setval(
    pg_get_serial_sequence(
        'support_tickets',
        'ticket_id'
    ),
    (
        SELECT MAX(ticket_id)
        FROM support_tickets
    ),
    true
);


COMMIT;


-- =========================================================
-- VALIDATION 1
-- TOTAL ROW COUNT
-- Expected: 3792
-- =========================================================

SELECT
    COUNT(*) AS total_support_tickets
FROM support_tickets;


-- =========================================================
-- VALIDATION 2
-- UNIQUE TICKET IDS
-- Expected: 3792
-- =========================================================

SELECT
    COUNT(DISTINCT ticket_id)
        AS unique_ticket_ids
FROM support_tickets;


-- =========================================================
-- VALIDATION 3
-- TICKET ID RANGE
-- Expected:
-- Minimum = 1
-- Maximum = 3792
-- =========================================================

SELECT
    MIN(ticket_id) AS minimum_ticket_id,
    MAX(ticket_id) AS maximum_ticket_id
FROM support_tickets;


-- =========================================================
-- VALIDATION 4
-- ACCOUNT COVERAGE
-- Expected: 488
-- =========================================================

SELECT
    COUNT(DISTINCT account_id)
        AS accounts_with_support_tickets
FROM support_tickets;


-- =========================================================
-- VALIDATION 5
-- ORPHAN ACCOUNT CHECK
-- Expected: 0 rows
-- =========================================================

SELECT
    s.ticket_id,
    s.account_id
FROM support_tickets AS s
LEFT JOIN accounts AS a
    ON s.account_id = a.account_id
WHERE a.account_id IS NULL;


-- =========================================================
-- VALIDATION 6
-- STATUS DISTRIBUTION
--
-- Expected:
-- Resolved    = 3457
-- Open        = 129
-- In Progress = 206
-- =========================================================

SELECT
    ticket_status,
    COUNT(*) AS ticket_count
FROM support_tickets
GROUP BY ticket_status
ORDER BY ticket_status;


-- =========================================================
-- VALIDATION 7
-- PRIORITY DISTRIBUTION
-- =========================================================

SELECT
    priority,
    COUNT(*) AS ticket_count
FROM support_tickets
GROUP BY priority
ORDER BY ticket_count DESC;


-- =========================================================
-- VALIDATION 8
-- CATEGORY DISTRIBUTION
-- =========================================================

SELECT
    category,
    COUNT(*) AS ticket_count
FROM support_tickets
GROUP BY category
ORDER BY ticket_count DESC;


-- =========================================================
-- VALIDATION 9
-- NEGATIVE RESOLUTION HOURS
-- Expected: 0 rows
-- =========================================================

SELECT
    ticket_id,
    account_id,
    resolution_hours
FROM support_tickets
WHERE resolution_hours < 0;


-- =========================================================
-- VALIDATION 10
-- INVALID CSAT
-- Expected: 0 rows
-- =========================================================

SELECT
    ticket_id,
    account_id,
    customer_satisfaction_score
FROM support_tickets
WHERE customer_satisfaction_score < 1
   OR customer_satisfaction_score > 5;


-- =========================================================
-- VALIDATION 11
-- RESOLVED TICKETS MISSING RESOLUTION DATA
-- Expected: 0 rows
-- =========================================================

SELECT
    ticket_id,
    account_id,
    resolved_date,
    resolution_hours
FROM support_tickets
WHERE ticket_status = 'Resolved'
  AND (
        resolved_date IS NULL
        OR resolution_hours IS NULL
      );


-- =========================================================
-- VALIDATION 12
-- UNRESOLVED TICKETS WITH RESOLUTION DATA
-- Expected: 0 rows
-- =========================================================

SELECT
    ticket_id,
    account_id,
    ticket_status,
    resolved_date,
    resolution_hours,
    customer_satisfaction_score
FROM support_tickets
WHERE ticket_status <> 'Resolved'
  AND (
        resolved_date IS NOT NULL
        OR resolution_hours IS NOT NULL
        OR customer_satisfaction_score IS NOT NULL
      );


-- =========================================================
-- VALIDATION 13
-- INVALID DATE ORDER
-- Expected: 0 rows
-- =========================================================

SELECT
    ticket_id,
    account_id,
    created_date,
    resolved_date
FROM support_tickets
WHERE resolved_date < created_date;


-- =========================================================
-- VALIDATION 14
-- SUPPORT DATE RANGE
-- =========================================================

SELECT
    MIN(created_date) AS earliest_ticket_date,
    MAX(created_date) AS latest_ticket_date
FROM support_tickets;


-- =========================================================
-- VALIDATION 15
-- AVERAGE RESOLUTION TIME
-- Expected approximately: 28.17 hours
-- =========================================================

SELECT
    ROUND(
        AVG(resolution_hours),
        2
    ) AS average_resolution_hours
FROM support_tickets
WHERE ticket_status = 'Resolved';


-- =========================================================
-- VALIDATION 16
-- AVERAGE CSAT
-- Expected approximately: 4.23
-- =========================================================

SELECT
    ROUND(
        AVG(
            customer_satisfaction_score
        ),
        2
    ) AS average_csat
FROM support_tickets
WHERE ticket_status = 'Resolved'
  AND customer_satisfaction_score IS NOT NULL;


-- =========================================================
-- VALIDATION 17
-- SUPPORT ACTIVITY BY SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(s.ticket_id)
        AS total_tickets,

    COUNT(DISTINCT s.account_id)
        AS accounts_with_tickets,

    ROUND(
        COUNT(s.ticket_id)::NUMERIC
        / NULLIF(
            COUNT(DISTINCT s.account_id),
            0
        ),
        2
    ) AS avg_tickets_per_account

FROM support_tickets AS s

INNER JOIN accounts AS a
    ON s.account_id = a.account_id

GROUP BY a.segment

ORDER BY total_tickets DESC;


-- =========================================================
-- VALIDATION 18
-- RESOLUTION METRICS BY PRIORITY
-- =========================================================

SELECT
    priority,

    COUNT(*) AS resolved_tickets,

    ROUND(
        AVG(resolution_hours),
        2
    ) AS avg_resolution_hours,

    ROUND(
        AVG(
            customer_satisfaction_score
        ),
        2
    ) AS avg_csat

FROM support_tickets

WHERE ticket_status = 'Resolved'

GROUP BY priority

ORDER BY
    CASE priority
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
    END;


-- =========================================================
-- VALIDATION 19
-- SAMPLE RECORDS
-- =========================================================

SELECT
    ticket_id,
    account_id,
    created_date,
    resolved_date,
    priority,
    category,
    ticket_status,
    resolution_hours,
    customer_satisfaction_score
FROM support_tickets
ORDER BY ticket_id
LIMIT 10;
