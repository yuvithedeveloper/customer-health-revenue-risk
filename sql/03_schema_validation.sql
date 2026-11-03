-- Customer Health & Revenue Risk Analytics
-- Schema validation checks


-- =========================================================
-- 1. CHECK ALL PROJECT TABLES
-- =========================================================

SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;


-- =========================================================
-- 2. CHECK TABLE ROW COUNTS
-- Expected: all tables currently contain 0 rows
-- =========================================================

SELECT 'accounts' AS table_name, COUNT(*) AS row_count
FROM accounts

UNION ALL

SELECT 'subscriptions', COUNT(*)
FROM subscriptions

UNION ALL

SELECT 'product_usage', COUNT(*)
FROM product_usage

UNION ALL

SELECT 'support_tickets', COUNT(*)
FROM support_tickets

UNION ALL

SELECT 'invoices', COUNT(*)
FROM invoices

UNION ALL

SELECT 'customer_success_interactions', COUNT(*)
FROM customer_success_interactions;


-- =========================================================
-- 3. CHECK FOREIGN KEY RELATIONSHIPS
-- =========================================================

SELECT
    tc.table_name AS child_table,
    kcu.column_name AS foreign_key_column,
    ccu.table_name AS parent_table,
    ccu.column_name AS parent_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON tc.constraint_name = ccu.constraint_name
    AND tc.table_schema = ccu.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name;


-- =========================================================
-- 4. CHECK PRIMARY KEYS
-- =========================================================

SELECT
    tc.table_name,
    kcu.column_name AS primary_key_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name;


-- =========================================================
-- 5. CHECK COLUMN COUNTS
-- =========================================================

SELECT
    table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

