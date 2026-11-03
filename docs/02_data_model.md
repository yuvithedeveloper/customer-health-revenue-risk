# Data Model

## Purpose

The database will combine customer, subscription, product usage, support, payment, and Customer Success data so that customer health and recurring revenue risk can be analyzed in one place.

## Core Tables

### 1. accounts

Stores one record for each CloudPath customer account.

Grain: One row per customer account.

### 2. subscriptions

Stores subscription and recurring revenue information for each customer.

Grain: One row per subscription period.

### 3. product_usage

Stores monthly product usage activity for each customer.

Grain: One row per account per month.

### 4. support_tickets

Stores customer support issues.

Grain: One row per support ticket.

### 5. invoices

Stores customer billing and payment information.

Grain: One row per invoice.

### 6. customer_success_interactions

Stores interactions between Customer Success Managers and customer accounts.

Grain: One row per Customer Success interaction.

## Detailed Table Design

### accounts

Purpose: Stores one record for each CloudPath customer account.

Grain: One row per customer account.

| Column | Data Type | Key | Description |
|---|---|---|---|
| account_id | INTEGER | Primary Key | Unique identifier for each customer account |
| account_name | VARCHAR(100) |  | Customer company name |
| industry | VARCHAR(50) |  | Customer industry |
| segment | VARCHAR(20) |  | SMB, Mid-Market, or Enterprise |
| region | VARCHAR(30) |  | Geographic region of the customer |
| signup_date | DATE |  | Date the customer first joined CloudPath |
| customer_status | VARCHAR(20) |  | Active or Churned |
| churn_date | DATE |  | Date the customer churned, if applicable |
| assigned_csm | VARCHAR(100) |  | Customer Success Manager assigned to the account |

#### Business Rules

- `account_id` must be unique for every account.
- `segment` should contain only SMB, Mid-Market, or Enterprise.
- `customer_status` should contain Active or Churned.
- Active customers should normally have a NULL `churn_date`.
- Churned customers should have a `churn_date`.
- `churn_date` cannot occur before `signup_date`.

### subscriptions

Purpose: Stores subscription terms and recurring revenue information for each customer account.

Grain: One row per subscription period.

| Column | Data Type | Key | Description |
|---|---|---|---|
| subscription_id | INTEGER | Primary Key | Unique identifier for each subscription period |
| account_id | INTEGER | Foreign Key | Customer account associated with the subscription |
| plan_name | VARCHAR(30) |  | Subscription plan such as Standard, Professional, or Enterprise |
| subscription_start_date | DATE |  | Start date of the subscription period |
| subscription_end_date | DATE |  | End date of the subscription period |
| billing_frequency | VARCHAR(20) |  | Monthly or Annual billing |
| mrr | DECIMAL(10,2) |  | Monthly recurring revenue for the subscription |
| subscription_status | VARCHAR(20) |  | Active, Renewed, Churned, or Expired |
| renewal_date | DATE |  | Date when the subscription is expected to renew |

#### Business Rules

- `subscription_id` must be unique for every subscription period.
- `account_id` must match an existing `account_id` in the `accounts` table.
- One account may have multiple subscription periods over time.
- `subscription_end_date` cannot occur before `subscription_start_date`.
- `mrr` cannot be negative.
- `billing_frequency` should contain only Monthly or Annual.
- `subscription_status` should contain Active, Renewed, Churned, or Expired.

### product_usage

Purpose: Stores monthly product activity for each customer account.

Grain: One row per account per month.

| Column | Data Type | Key | Description |
|---|---|---|---|
| usage_id | INTEGER | Primary Key | Unique identifier for each monthly usage record |
| account_id | INTEGER | Foreign Key | Customer account associated with the usage record |
| usage_month | DATE |  | Month represented by the usage record |
| licensed_users | INTEGER |  | Number of users licensed to use the platform |
| active_users | INTEGER |  | Number of users who were active during the month |
| login_count | INTEGER |  | Total account logins during the month |
| dashboards_viewed | INTEGER |  | Total dashboards viewed during the month |
| reports_generated | INTEGER |  | Total reports generated during the month |
| alerts_created | INTEGER |  | Total alerts created during the month |
| core_features_used | INTEGER |  | Number of core product features used during the month |

#### Business Rules

- `usage_id` must be unique for every usage record.
- `account_id` must match an existing `account_id` in the `accounts` table.
- Each account should have only one usage record for each `usage_month`.
- `licensed_users` cannot be negative.
- `active_users` cannot be negative.
- `active_users` cannot exceed `licensed_users`.
- Usage activity fields such as `login_count`, `dashboards_viewed`, `reports_generated`, and `alerts_created` cannot be negative.
- `core_features_used` must be between 0 and 8.

### support_tickets

Purpose: Stores support issues reported by customer accounts.

Grain: One row per support ticket.

| Column | Data Type | Key | Description |
|---|---|---|---|
| ticket_id | INTEGER | Primary Key | Unique identifier for each support ticket |
| account_id | INTEGER | Foreign Key | Customer account associated with the ticket |
| created_date | DATE |  | Date the support ticket was created |
| resolved_date | DATE |  | Date the ticket was resolved, if applicable |
| priority | VARCHAR(20) |  | Priority level of the support issue |
| category | VARCHAR(50) |  | Type of support issue |
| ticket_status | VARCHAR(20) |  | Current status of the ticket |
| resolution_hours | DECIMAL(10,2) |  | Number of hours taken to resolve the ticket |
| customer_satisfaction_score | INTEGER |  | Customer satisfaction score after resolution |

#### Business Rules

- `ticket_id` must be unique for every support ticket.
- `account_id` must match an existing `account_id` in the `accounts` table.
- `priority` should contain Low, Medium, High, or Critical.
- `ticket_status` should contain Open, In Progress, or Resolved.
- `resolved_date` cannot occur before `created_date`.
- Open or In Progress tickets may have a NULL `resolved_date`.
- `resolution_hours` cannot be negative.
- `customer_satisfaction_score` should be between 1 and 5 when available.

### invoices

Purpose: Stores billing and payment information for each customer account.

Grain: One row per invoice.

| Column | Data Type | Key | Description |
|---|---|---|---|
| invoice_id | INTEGER | Primary Key | Unique identifier for each invoice |
| account_id | INTEGER | Foreign Key | Customer account associated with the invoice |
| invoice_date | DATE |  | Date the invoice was issued |
| due_date | DATE |  | Date payment is due |
| payment_date | DATE |  | Date payment was completed, if paid |
| invoice_amount | DECIMAL(10,2) |  | Total amount billed |
| payment_status | VARCHAR(20) |  | Current payment status |
| days_late | INTEGER |  | Number of days the payment was late |
| payment_method | VARCHAR(30) |  | Method used for payment |

#### Business Rules

- `invoice_id` must be unique for every invoice.
- `account_id` must match an existing `account_id` in the `accounts` table.
- `due_date` cannot occur before `invoice_date`.
- `payment_date` cannot occur before `invoice_date`.
- `invoice_amount` must be greater than 0.
- `payment_status` should contain Paid, Late, Pending, or Failed.
- `days_late` cannot be negative.
- Paid invoices should normally have a `payment_date`.
- Pending or Failed invoices may have a NULL `payment_date`.

### customer_success_interactions

Purpose: Stores interactions between Customer Success Managers and customer accounts.

Grain: One row per Customer Success interaction.

| Column | Data Type | Key | Description |
|---|---|---|---|
| interaction_id | INTEGER | Primary Key | Unique identifier for each Customer Success interaction |
| account_id | INTEGER | Foreign Key | Customer account associated with the interaction |
| interaction_date | DATE |  | Date the interaction occurred |
| interaction_type | VARCHAR(30) |  | Type of Customer Success interaction |
| csm_name | VARCHAR(100) |  | Customer Success Manager responsible for the interaction |
| engagement_status | VARCHAR(20) |  | Customer engagement level during the interaction |
| follow_up_required | BOOLEAN |  | Indicates whether follow-up is required |
| notes_category | VARCHAR(50) |  | High-level reason or topic discussed |
| next_follow_up_date | DATE |  | Planned date for the next follow-up, if required |

#### Business Rules

- `interaction_id` must be unique for every interaction.
- `account_id` must match an existing `account_id` in the `accounts` table.
- `interaction_type` should contain Email, Call, Meeting, QBR, or Training.
- `engagement_status` should contain Engaged, Neutral, or Unresponsive.
- `follow_up_required` should contain TRUE or FALSE.
- `next_follow_up_date` should normally be NULL when `follow_up_required` is FALSE.
- `next_follow_up_date` cannot occur before `interaction_date`.

## Table Relationships

The `accounts` table is the central customer table.

Each activity or transaction table connects back to `accounts` using `account_id`.

| Parent Table | Child Table | Relationship |
|---|---|---|
| accounts | subscriptions | One account can have many subscription periods |
| accounts | product_usage | One account can have many monthly usage records |
| accounts | support_tickets | One account can have many support tickets |
| accounts | invoices | One account can have many invoices |
| accounts | customer_success_interactions | One account can have many Customer Success interactions |

## Expected Data Volumes

The project will simulate approximately two years of customer activity from January 2025 through December 2026.

| Table | Approximate Rows | Reason |
|---|---:|---|
| accounts | 500 | Approximately 500 customer accounts |
| subscriptions | 700-900 | Customers may have multiple subscription periods or renewals |
| product_usage | 9,000-11,000 | Monthly usage records for active accounts |
| support_tickets | 3,000-5,000 | Customers generate different numbers of support requests |
| invoices | 5,000-7,000 | Monthly and annual billing creates multiple invoices |
| customer_success_interactions | 2,500-4,000 | Accounts receive different levels of Customer Success engagement |

These are approximate targets for synthetic data generation. Final row counts may vary based on account activity, signup dates, churn, and billing frequency.

