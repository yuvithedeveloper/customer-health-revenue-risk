-- Customer Health & Revenue Risk Analytics
-- Load cleaned invoice data into PostgreSQL


-- =========================================================
-- STOP SCRIPT IF ANY COMMAND FAILS
-- =========================================================

\set ON_ERROR_STOP on


-- =========================================================
-- PRE-LOAD CHECK
-- Expected before first load: 0
-- =========================================================

SELECT
    COUNT(*) AS existing_invoice_rows
FROM invoices;


-- =========================================================
-- LOAD INVOICES
-- Source:
-- data/processed/invoices.csv
-- =========================================================

BEGIN;

\copy invoices (invoice_id, account_id, invoice_date, due_date, payment_date, invoice_amount, payment_status, days_late, payment_method) FROM 'C:/Yuvraj/Stevens/Projects/customer-health-revenue-risk/data/processed/invoices.csv' WITH (FORMAT csv, HEADER true, NULL '');


-- =========================================================
-- SYNCHRONIZE IDENTITY SEQUENCE
-- =========================================================

SELECT setval(
    pg_get_serial_sequence(
        'invoices',
        'invoice_id'
    ),
    (
        SELECT MAX(invoice_id)
        FROM invoices
    ),
    true
);


COMMIT;


-- =========================================================
-- VALIDATION 1
-- TOTAL ROW COUNT
-- Expected: 4420
-- =========================================================

SELECT
    COUNT(*) AS total_invoices
FROM invoices;


-- =========================================================
-- VALIDATION 2
-- UNIQUE INVOICE IDS
-- Expected: 4420
-- =========================================================

SELECT
    COUNT(DISTINCT invoice_id)
        AS unique_invoice_ids
FROM invoices;


-- =========================================================
-- VALIDATION 3
-- INVOICE ID RANGE
-- Expected:
-- Minimum = 1
-- Maximum = 4420
-- =========================================================

SELECT
    MIN(invoice_id) AS minimum_invoice_id,
    MAX(invoice_id) AS maximum_invoice_id
FROM invoices;


-- =========================================================
-- VALIDATION 4
-- ACCOUNT COVERAGE
-- Expected: 497
-- =========================================================

SELECT
    COUNT(DISTINCT account_id)
        AS accounts_with_invoices
FROM invoices;


-- =========================================================
-- VALIDATION 5
-- ORPHAN ACCOUNT CHECK
-- Expected: 0 rows
-- =========================================================

SELECT
    i.invoice_id,
    i.account_id
FROM invoices AS i

LEFT JOIN accounts AS a
    ON i.account_id = a.account_id

WHERE a.account_id IS NULL;


-- =========================================================
-- VALIDATION 6
-- PAYMENT STATUS DISTRIBUTION
--
-- Expected:
-- Paid    = 3571
-- Late    = 584
-- Pending = 131
-- Failed  = 134
-- =========================================================

SELECT
    payment_status,
    COUNT(*) AS invoice_count
FROM invoices
GROUP BY payment_status
ORDER BY payment_status;


-- =========================================================
-- VALIDATION 7
-- PAYMENT METHOD DISTRIBUTION
-- Missing payment method values are intentionally retained.
-- =========================================================

SELECT
    COALESCE(
        payment_method,
        'Missing'
    ) AS payment_method,

    COUNT(*) AS invoice_count

FROM invoices

GROUP BY
    COALESCE(
        payment_method,
        'Missing'
    )

ORDER BY invoice_count DESC;


-- =========================================================
-- VALIDATION 8
-- MISSING PAYMENT METHODS
-- Expected: 15
-- =========================================================

SELECT
    COUNT(*) AS missing_payment_methods
FROM invoices
WHERE payment_method IS NULL;


-- =========================================================
-- VALIDATION 9
-- INVALID INVOICE AMOUNTS
-- Expected: 0 rows
-- =========================================================

SELECT
    invoice_id,
    account_id,
    invoice_amount
FROM invoices
WHERE invoice_amount <= 0;


-- =========================================================
-- VALIDATION 10
-- NEGATIVE DAYS LATE
-- Expected: 0 rows
-- =========================================================

SELECT
    invoice_id,
    account_id,
    payment_status,
    days_late
FROM invoices
WHERE days_late < 0;


-- =========================================================
-- VALIDATION 11
-- INVALID DUE DATE
-- Expected: 0 rows
-- =========================================================

SELECT
    invoice_id,
    account_id,
    invoice_date,
    due_date
FROM invoices
WHERE due_date < invoice_date;


-- =========================================================
-- VALIDATION 12
-- PAYMENT BEFORE INVOICE DATE
-- Expected: 0 rows
-- =========================================================

SELECT
    invoice_id,
    account_id,
    invoice_date,
    payment_date
FROM invoices
WHERE payment_date < invoice_date;


-- =========================================================
-- VALIDATION 13
-- PAID INVOICE RULES
-- Expected: 0 rows
--
-- Paid means:
-- payment date exists
-- payment was on or before due date
-- days_late = 0
-- =========================================================

SELECT
    invoice_id,
    account_id,
    due_date,
    payment_date,
    days_late
FROM invoices
WHERE payment_status = 'Paid'
  AND (
        payment_date IS NULL
        OR payment_date > due_date
        OR days_late <> 0
      );


-- =========================================================
-- VALIDATION 14
-- LATE INVOICE RULES
-- Expected: 0 rows
--
-- Late means:
-- payment date exists
-- payment is after due date
-- days_late > 0
-- =========================================================

SELECT
    invoice_id,
    account_id,
    due_date,
    payment_date,
    days_late
FROM invoices
WHERE payment_status = 'Late'
  AND (
        payment_date IS NULL
        OR payment_date <= due_date
        OR days_late <= 0
      );


-- =========================================================
-- VALIDATION 15
-- LATE DAYS MATCH PAYMENT DATE
-- Expected: 0 rows
-- =========================================================

SELECT
    invoice_id,
    account_id,
    due_date,
    payment_date,
    days_late
FROM invoices
WHERE payment_status = 'Late'
  AND (
        payment_date - due_date
      ) <> days_late;


-- =========================================================
-- VALIDATION 16
-- PENDING INVOICE RULES
-- Expected: 0 rows
-- =========================================================

SELECT
    invoice_id,
    account_id,
    payment_date,
    days_late
FROM invoices
WHERE payment_status = 'Pending'
  AND (
        payment_date IS NOT NULL
        OR days_late <> 0
      );


-- =========================================================
-- VALIDATION 17
-- FAILED INVOICE RULES
-- Expected: 0 rows
-- =========================================================

SELECT
    invoice_id,
    account_id,
    payment_date,
    days_late
FROM invoices
WHERE payment_status = 'Failed'
  AND (
        payment_date IS NOT NULL
        OR days_late <= 0
      );


-- =========================================================
-- VALIDATION 18
-- INVOICE DATE RANGE
-- =========================================================

SELECT
    MIN(invoice_date)
        AS earliest_invoice_date,

    MAX(invoice_date)
        AS latest_invoice_date

FROM invoices;


-- =========================================================
-- VALIDATION 19
-- TOTAL INVOICE VALUE
-- Expected: 31,880,975.00
-- =========================================================

SELECT
    SUM(invoice_amount)
        AS total_invoice_value
FROM invoices;


-- =========================================================
-- VALIDATION 20
-- AVERAGE DAYS LATE
-- Expected approximately: 13.52
-- =========================================================

SELECT
    ROUND(
        AVG(days_late),
        2
    ) AS average_days_late
FROM invoices
WHERE payment_status = 'Late';


-- =========================================================
-- VALIDATION 21
-- PAYMENT PERFORMANCE
-- =========================================================

SELECT
    payment_status,

    COUNT(*) AS invoice_count,

    ROUND(
        COUNT(*)::NUMERIC
        / (
            SELECT COUNT(*)
            FROM invoices
        )
        * 100,
        2
    ) AS percentage_of_invoices

FROM invoices

GROUP BY payment_status

ORDER BY invoice_count DESC;


-- =========================================================
-- VALIDATION 22
-- PAYMENT PERFORMANCE BY CUSTOMER SEGMENT
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

    COUNT(*) FILTER (
        WHERE i.payment_status = 'Pending'
    ) AS pending_invoices,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE i.payment_status IN (
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

ORDER BY a.segment;


-- =========================================================
-- VALIDATION 23
-- INVOICE VALUE BY CUSTOMER SEGMENT
-- =========================================================

SELECT
    a.segment,

    COUNT(i.invoice_id)
        AS invoice_count,

    SUM(i.invoice_amount)
        AS invoice_value

FROM invoices AS i

INNER JOIN accounts AS a
    ON i.account_id = a.account_id

GROUP BY a.segment

ORDER BY invoice_value DESC;


-- =========================================================
-- VALIDATION 24
-- SAMPLE RECORDS
-- =========================================================

SELECT
    invoice_id,
    account_id,
    invoice_date,
    due_date,
    payment_date,
    invoice_amount,
    payment_status,
    days_late,
    payment_method
FROM invoices
ORDER BY invoice_id
LIMIT 10;
