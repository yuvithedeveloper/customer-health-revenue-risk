-- Customer Health & Revenue Risk Analytics
-- Core relational tables


-- =========================================================
-- ACCOUNTS
-- Grain: One row per customer account
-- =========================================================

CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    segment VARCHAR(20) NOT NULL,
    region VARCHAR(30),
    signup_date DATE NOT NULL,
    customer_status VARCHAR(20) NOT NULL,
    churn_date DATE,
    assigned_csm VARCHAR(100),

    CONSTRAINT chk_accounts_segment
        CHECK (
            segment IN (
                'SMB',
                'Mid-Market',
                'Enterprise'
            )
        ),

    CONSTRAINT chk_accounts_status
        CHECK (
            customer_status IN (
                'Active',
                'Churned'
            )
        ),

    CONSTRAINT chk_accounts_churn_date
        CHECK (
            churn_date IS NULL
            OR churn_date >= signup_date
        ),

    CONSTRAINT chk_accounts_status_churn
        CHECK (
            (customer_status = 'Active' AND churn_date IS NULL)
            OR
            (customer_status = 'Churned' AND churn_date IS NOT NULL)
        )
);


-- =========================================================
-- SUBSCRIPTIONS
-- Grain: One row per subscription period
-- =========================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,
    plan_name VARCHAR(30) NOT NULL,
    subscription_start_date DATE NOT NULL,
    subscription_end_date DATE NOT NULL,
    billing_frequency VARCHAR(20) NOT NULL,
    mrr DECIMAL(10,2) NOT NULL,
    subscription_status VARCHAR(20) NOT NULL,
    renewal_date DATE,

    CONSTRAINT fk_subscriptions_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),

    CONSTRAINT chk_subscriptions_dates
        CHECK (
            subscription_end_date >= subscription_start_date
        ),

    CONSTRAINT chk_subscriptions_mrr
        CHECK (
            mrr >= 0
        ),

    CONSTRAINT chk_subscriptions_billing_frequency
        CHECK (
            billing_frequency IN (
                'Monthly',
                'Annual'
            )
        ),

    CONSTRAINT chk_subscriptions_status
        CHECK (
            subscription_status IN (
                'Active',
                'Renewed',
                'Churned',
                'Expired'
            )
        )
);


-- =========================================================
-- PRODUCT USAGE
-- Grain: One row per account per month
-- =========================================================

CREATE TABLE IF NOT EXISTS product_usage (
    usage_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,
    usage_month DATE NOT NULL,
    licensed_users INTEGER NOT NULL,
    active_users INTEGER NOT NULL,
    login_count INTEGER NOT NULL,
    dashboards_viewed INTEGER NOT NULL,
    reports_generated INTEGER NOT NULL,
    alerts_created INTEGER NOT NULL,
    core_features_used INTEGER NOT NULL,

    CONSTRAINT fk_product_usage_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),

    CONSTRAINT uq_product_usage_account_month
        UNIQUE (account_id, usage_month),

    CONSTRAINT chk_product_usage_licensed_users
        CHECK (
            licensed_users >= 0
        ),

    CONSTRAINT chk_product_usage_active_users
        CHECK (
            active_users >= 0
            AND active_users <= licensed_users
        ),

    CONSTRAINT chk_product_usage_login_count
        CHECK (
            login_count >= 0
        ),

    CONSTRAINT chk_product_usage_dashboards
        CHECK (
            dashboards_viewed >= 0
        ),

    CONSTRAINT chk_product_usage_reports
        CHECK (
            reports_generated >= 0
        ),

    CONSTRAINT chk_product_usage_alerts
        CHECK (
            alerts_created >= 0
        ),

    CONSTRAINT chk_product_usage_features
        CHECK (
            core_features_used BETWEEN 0 AND 8
        )
);


-- =========================================================
-- SUPPORT TICKETS
-- Grain: One row per support ticket
-- =========================================================

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,
    created_date DATE NOT NULL,
    resolved_date DATE,
    priority VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    ticket_status VARCHAR(20) NOT NULL,
    resolution_hours DECIMAL(10,2),
    customer_satisfaction_score INTEGER,

    CONSTRAINT fk_support_tickets_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),

    CONSTRAINT chk_support_tickets_priority
        CHECK (
            priority IN (
                'Low',
                'Medium',
                'High',
                'Critical'
            )
        ),

    CONSTRAINT chk_support_tickets_status
        CHECK (
            ticket_status IN (
                'Open',
                'In Progress',
                'Resolved'
            )
        ),

    CONSTRAINT chk_support_tickets_dates
        CHECK (
            resolved_date IS NULL
            OR resolved_date >= created_date
        ),

    CONSTRAINT chk_support_tickets_resolution_hours
        CHECK (
            resolution_hours IS NULL
            OR resolution_hours >= 0
        ),

    CONSTRAINT chk_support_tickets_csat
        CHECK (
            customer_satisfaction_score IS NULL
            OR customer_satisfaction_score BETWEEN 1 AND 5
        ),

    CONSTRAINT chk_support_tickets_resolved_status
        CHECK (
            ticket_status <> 'Resolved'
            OR resolved_date IS NOT NULL
        )
);


-- =========================================================
-- INVOICES
-- Grain: One row per invoice
-- =========================================================

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    invoice_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    days_late INTEGER NOT NULL DEFAULT 0,
    payment_method VARCHAR(30),

    CONSTRAINT fk_invoices_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),

    CONSTRAINT chk_invoices_due_date
        CHECK (
            due_date >= invoice_date
        ),

    CONSTRAINT chk_invoices_payment_date
        CHECK (
            payment_date IS NULL
            OR payment_date >= invoice_date
        ),

    CONSTRAINT chk_invoices_amount
        CHECK (
            invoice_amount > 0
        ),

    CONSTRAINT chk_invoices_status
        CHECK (
            payment_status IN (
                'Paid',
                'Late',
                'Pending',
                'Failed'
            )
        ),

    CONSTRAINT chk_invoices_days_late
        CHECK (
            days_late >= 0
        ),

    CONSTRAINT chk_invoices_paid_date
        CHECK (
            payment_status <> 'Paid'
            OR payment_date IS NOT NULL
        )
);


-- =========================================================
-- CUSTOMER SUCCESS INTERACTIONS
-- Grain: One row per Customer Success interaction
-- =========================================================

CREATE TABLE IF NOT EXISTS customer_success_interactions (
    interaction_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,
    interaction_date DATE NOT NULL,
    interaction_type VARCHAR(30) NOT NULL,
    csm_name VARCHAR(100) NOT NULL,
    engagement_status VARCHAR(20) NOT NULL,
    follow_up_required BOOLEAN NOT NULL,
    notes_category VARCHAR(50),
    next_follow_up_date DATE,

    CONSTRAINT fk_customer_success_interactions_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),

    CONSTRAINT chk_customer_success_interaction_type
        CHECK (
            interaction_type IN (
                'Email',
                'Call',
                'Meeting',
                'QBR',
                'Training'
            )
        ),

    CONSTRAINT chk_customer_success_engagement
        CHECK (
            engagement_status IN (
                'Engaged',
                'Neutral',
                'Unresponsive'
            )
        ),

    CONSTRAINT chk_customer_success_follow_up_date
        CHECK (
            next_follow_up_date IS NULL
            OR next_follow_up_date >= interaction_date
        ),

    CONSTRAINT chk_customer_success_follow_up_required
        CHECK (
            follow_up_required
            OR next_follow_up_date IS NULL
        )
);
