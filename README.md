# Customer Health & Revenue Risk Analytics

An end-to-end analytics portfolio project that simulates how a B2B SaaS company can identify declining customer health, estimate recurring revenue exposure, prioritize Customer Success interventions, and monitor retention performance.

The project combines **PostgreSQL, SQL, Python, Power BI, and DAX** to transform operational customer data into an explainable customer-health and revenue-risk decision system.

> **Note:** All customer and business data in this project is synthetic and was generated specifically for analytical practice.

---

## Project Snapshot

| Metric | Result |
|---|---:|
| Active Customer Accounts | 426 |
| Annual Recurring Revenue | $18.90M |
| Gross ARR Exposed | $6.64M |
| Estimated Revenue at Risk | $2.32M |
| Critical / High Priority Accounts | 48 |
| 2026 Net Revenue Retention | 97.42% |

### Dashboard Preview

![Customer Health & Revenue Risk Executive Dashboard](images/01_executive_overview.png)

---

## Business Problem

CloudPath Analytics is a fictional B2B SaaS company that provides operational analytics, dashboards, alerts, workflow monitoring, and reporting tools.

The Customer Success organization needs to answer several business questions:

- Which customers are showing signs of declining health?
- What factors are contributing to customer risk?
- How much recurring revenue is associated with customers requiring attention?
- Which accounts should Customer Success contact first?
- Which customers are approaching renewal?
- How are retention and recurring revenue changing over time?
- Which customer segments have the strongest and weakest retention?
- How are product adoption and support activity changing?

The primary stakeholder for the analysis is the **VP of Customer Success**, with additional relevance for Customer Success Managers, Revenue Operations, Finance, Product, and executive leadership.

---

## Project Objectives

The project was designed to:

1. Build a relational PostgreSQL database representing a realistic B2B SaaS environment.
2. Generate and clean synthetic operational data with realistic data-quality issues.
3. Develop reusable SQL analysis for customer health and revenue risk.
4. Create an explainable Customer Health Score using multiple business signals.
5. Estimate scenario-based Revenue at Risk.
6. Prioritize Customer Success interventions using health, ARR, and renewal timing.
7. Analyze Logo Retention, Gross Revenue Retention, and Net Revenue Retention.
8. Create a five-page Power BI dashboard for executive and operational decision-making.

---

## Technology Stack

- **PostgreSQL** — relational database and analytical SQL
- **SQL** — joins, CTEs, CASE logic, window functions, aggregations, views, cohort analysis, and retention analysis
- **Python** — synthetic data generation and data cleaning
- **Faker** — synthetic customer and operational records
- **Power BI** — dashboard development, interactive filtering, and visualization
- **DAX** — business measures, KPI calculations, and dashboard logic
- **Git / GitHub** — version control and portfolio documentation

---

## End-to-End Workflow

```text
Business Problem
        ↓
Synthetic Data Generation
        ↓
Data Cleaning & Validation
        ↓
PostgreSQL Database
        ↓
Exploratory SQL Analysis
        ↓
Customer Health Scoring
        ↓
Revenue-at-Risk Modeling
        ↓
Customer Success Prioritization
        ↓
Retention & Revenue Analysis
        ↓
Power BI Dashboard
        ↓
Business Recommendations
```

---

## Data Model

The analytical database contains six core tables.

### Accounts

Customer master data including:

- customer segment
- region
- industry
- signup date
- customer status
- churn date
- assigned Customer Success Manager

### Subscriptions

Subscription and recurring-revenue data including:

- plan
- billing frequency
- MRR
- subscription dates
- renewal date
- subscription status

### Product Usage

Monthly product-behavior data including:

- licensed users
- active users
- login activity
- dashboard usage
- reports generated
- alerts created
- feature adoption

### Support Tickets

Support activity including:

- ticket priority
- issue category
- ticket status
- resolution time
- customer satisfaction score

### Invoices

Billing and payment behavior including:

- invoice amount
- payment status
- payment date
- days late
- payment method

### Customer Success Interactions

Customer Success engagement including:

- interaction type
- engagement status
- Customer Success Manager
- follow-up requirement
- interaction category
- next follow-up date

---

## Dataset Scale

The final PostgreSQL database contains:

| Dataset | Rows |
|---|---:|
| Accounts | 500 |
| Subscriptions | 980 |
| Product Usage | 8,184 |
| Support Tickets | 3,792 |
| Invoices | 4,420 |
| Customer Success Interactions | 3,086 |

The primary analytical period is **January 2025 through December 2026**.

The December 2026 snapshot contains:

- **426 active customer accounts**
- **$1.57M monthly recurring revenue**
- **$18.90M annual recurring revenue**

---

## Data Quality

The synthetic datasets intentionally included realistic data-quality problems such as:

- duplicate records
- missing values
- inconsistent category labels
- invalid dates
- negative values
- inconsistent payment statuses
- invalid usage metrics
- inconsistent boolean values
- missing Customer Success assignments

Cleaning scripts were created before loading the data into PostgreSQL.

A final database-validation layer checks:

- expected table row counts
- primary-key uniqueness
- foreign-key integrity
- account and subscription consistency
- product-usage constraints
- support-ticket rules
- invoice rules
- Customer Success interaction rules
- recurring-revenue reconciliation

---

## Customer Health Framework

The Customer Health Score combines six explainable business components.

| Component | Weight |
|---|---:|
| Product Usage | 25% |
| Usage Trend | 20% |
| Feature Adoption | 15% |
| Support Health | 15% |
| Payment Health | 10% |
| Customer Engagement | 15% |

Accounts are classified into:

- **Healthy:** 75–100
- **Monitor:** 55–74.99
- **At Risk:** below 55

Current results:

| Health Status | Accounts | Share |
|---|---:|---:|
| Healthy | 273 | 64.08% |
| Monitor | 129 | 30.28% |
| At Risk | 24 | 5.63% |

The framework is intentionally explainable and designed as Customer Success decision support rather than a black-box churn-prediction model.

---

## Revenue at Risk

The project distinguishes between two different concepts.

### Gross ARR Exposed

ARR associated with customers requiring Customer Success attention.

**Gross ARR Exposed: approximately $6.64M**

### Estimated Revenue at Risk

A scenario-based estimate that applies different exposure assumptions according to customer health.

**Estimated Revenue at Risk: approximately $2.32M**

This metric is used for prioritization and should not be interpreted as a guaranteed churn forecast.

---

## Customer Success Prioritization

A separate prioritization model determines which accounts Customer Success should review first.

The model combines:

- customer health severity
- renewal urgency
- account ARR
- modeled revenue exposure

The current model identifies:

**48 Critical or High priority accounts**

This allows Customer Success to distinguish between customers requiring immediate intervention and customers where preventive action can still be taken before renewal.

---

## Primary Risk Drivers

Among the **153 accounts requiring Customer Success attention**, the primary risk drivers are:

| Primary Risk Driver | Accounts |
|---|---:|
| Product Usage | 90 |
| Usage Trend | 25 |
| Customer Engagement | 22 |
| Support Health | 11 |
| Payment Health | 5 |

Product Usage alone represents approximately **$1.46M in modeled Revenue at Risk**, making it the largest risk driver in the analysis.

---

## Retention Analysis

The project calculates:

- Logo Retention
- Gross Revenue Retention (GRR)
- Net Revenue Retention (NRR)
- Expansion MRR
- Contraction MRR
- Churned MRR

### Overall Retention

| Metric | 2025 | 2026 |
|---|---:|---:|
| Logo Retention | 91.67% | 90.35% |
| GRR | 94.05% | 92.47% |
| NRR | 99.27% | 97.42% |

Retention weakened in 2026 despite stronger expansion activity because churned recurring revenue also increased.

### 2026 Retention by Segment

| Segment | Logo Retention | GRR | NRR |
|---|---:|---:|---:|
| Enterprise | 98.11% | 97.70% | 103.54% |
| Mid-Market | 90.60% | 89.47% | 93.79% |
| SMB | 87.79% | 87.16% | 91.47% |

Enterprise is the only segment with NRR above 100%.

---

## Key Business Findings

### 1. More than one-third of active accounts require attention

Of the 426 active customer accounts:

- 273 are Healthy
- 129 are Monitor
- 24 are At Risk

This means **153 accounts, or approximately 36% of the active customer base**, require some level of Customer Success attention.

---

### 2. Product Usage is the dominant risk driver

Product Usage is the primary risk driver for **90 of the 153 accounts requiring action**.

Approximately **$1.46M of modeled Revenue at Risk** is associated with Product Usage.

This suggests that customer behavior may provide an earlier warning signal than payment problems alone.

---

### 3. Health score alone is not enough for prioritization

The prioritization model identifies **48 Critical or High priority accounts** by combining health severity, account value, and renewal timing.

An account with moderate health but high ARR and an upcoming renewal may therefore require action before a lower-value account with a worse health score.

---

### 4. Revenue exposure exists well before renewal

Estimated Revenue at Risk is distributed across multiple renewal horizons.

Approximately:

| Renewal Window | Estimated Revenue at Risk |
|---|---:|
| 0–30 days | $0.13M |
| 31–60 days | $0.18M |
| 61–90 days | $0.28M |
| 91–180 days | $0.42M |
| 181–270 days | $0.65M |
| 271+ days | $0.66M |

A significant amount of exposed revenue belongs to accounts more than six months away from renewal.

This supports proactive adoption intervention rather than waiting until the final renewal window.

---

### 5. Retention weakened in 2026

Between 2025 and 2026:

- Logo Retention declined from **91.67% to 90.35%**
- GRR declined from **94.05% to 92.47%**
- NRR declined from **99.27% to 97.42%**

Expansion increased during 2026, but higher churn and contraction prevented NRR from exceeding 100%.

---

### 6. Enterprise customers show stronger retention

Enterprise customers achieved:

- **97.70% GRR**
- **103.54% NRR**

Mid-Market and SMB both remained below 100% NRR.

This suggests that Enterprise customers are both more resilient and more capable of generating expansion revenue.

---

### 7. Mid-Market creates the largest absolute churn impact

Approximate 2026 churned MRR:

- Mid-Market: **$46K**
- SMB: **$29K**
- Enterprise: **$9K**

SMB has weaker retention percentages, but Mid-Market generates the greatest absolute recurring-revenue loss.

This shows why percentage-based retention metrics and absolute financial impact should be evaluated together.

---

### 8. Product adoption recovered while support demand increased

By December 2026:

- Active User Rate: **65.4%**
- Feature Adoption: **72.7%**
- Average Resolution Time: **27.1 hours**
- Average CSAT: **4.24**

Usage recovered during 2026, while support-ticket volume and High/Critical ticket volume generally increased over the analysis period.

This indicates that support capacity should be monitored as product adoption grows.

---

## Recommended Business Actions

Based on the analysis, CloudPath Analytics should:

1. Review Critical and High priority accounts during recurring Customer Success operating reviews.
2. Prioritize direct intervention for accounts approaching renewal within 90 days.
3. Launch proactive adoption programs for customers showing weak Product Usage or Usage Trend signals.
4. Focus Mid-Market retention initiatives on reducing absolute recurring-revenue loss.
5. Develop scalable onboarding and lifecycle programs for SMB customers.
6. Study successful Enterprise retention and expansion patterns for practices that could be adapted to other segments.
7. Monitor support capacity as product adoption increases.
8. Track Health Score, Revenue at Risk, renewal exposure, GRR, NRR, and Logo Retention together.

---

## Power BI Dashboard

The final Power BI report contains five pages.

### 1. Executive Overview

Provides an executive view of:

- active customer accounts
- current ARR
- average health score
- estimated Revenue at Risk
- urgent priority accounts
- ARR by segment
- health-status distribution
- monthly ARR trend

![Executive Overview](images/01_executive_overview.png)

---

### 2. Customer Health & Risk

Analyzes:

- At Risk and Monitor accounts
- Gross ARR exposure
- primary customer-risk drivers
- Revenue at Risk by risk driver
- detailed account-level risk information

![Customer Health and Risk](images/02_customer_health_risk.png)

---

### 3. CS Priority Accounts

Supports Customer Success operations through:

- urgent account counts
- prioritized account ranking
- revenue exposure by renewal window
- account-level Customer Success priority details

![CS Priority Accounts](images/03_cs_priority_accounts.png)

---

### 4. Retention & Revenue

Tracks:

- Logo Retention
- GRR
- NRR
- Expansion MRR
- Contraction MRR
- Churned MRR
- segment-level retention performance

![Retention and Revenue](images/04_retention_revenue.png)

---

### 5. Usage & Support Drivers

Tracks:

- active-user rate
- feature adoption
- support-ticket volume
- resolution time
- CSAT
- High/Critical support-ticket trends

![Usage and Support Drivers](images/05_usage_support_drivers.png)

---

## SQL Analysis

The SQL layer demonstrates:

- multi-table joins
- Common Table Expressions
- window functions
- conditional business logic
- date calculations
- aggregations
- customer segmentation
- data-quality validation
- customer health scoring
- revenue-risk calculations
- priority ranking
- cohort analysis
- retention calculations
- reusable analytical views

The final SQL layer also creates Power BI-ready views so dashboard logic is separated from the underlying transactional tables.

---

## Repository Structure

```text
customer-health-revenue-risk/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docs/
│   ├── 01_business_understanding.md
│   ├── 02_data_model.md
│   └── 03_business_findings.md
│
├── python/
│   ├── generate_synthetic_data.py
│   ├── clean_accounts.py
│   ├── generate_subscriptions.py
│   ├── clean_subscriptions.py
│   ├── generate_product_usage.py
│   ├── clean_product_usage.py
│   ├── generate_support_tickets.py
│   ├── clean_support_tickets.py
│   ├── generate_invoices.py
│   ├── clean_invoices.py
│   ├── generate_cs_interactions.py
│   └── clean_cs_interactions.py
│
├── sql/
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_schema_validation.sql
│   ├── 04_load_accounts.sql
│   ├── 05_load_subscriptions.sql
│   ├── 06_load_product_usage.sql
│   ├── 07_load_support_tickets.sql
│   ├── 08_load_invoices.sql
│   ├── 09_load_cs_interactions.sql
│   ├── 10_full_database_validation.sql
│   ├── 11_exploratory_analysis.sql
│   ├── 12_create_account_health_base.sql
│   ├── 13_health_signal_distribution.sql
│   ├── 14_create_customer_health_score.sql
│   ├── 15_revenue_at_risk_prioritization.sql
│   ├── 16_retention_revenue_analysis.sql
│   └── 17_create_powerbi_views.sql
│
├── powerbi/
│   └── Customer_Health_Revenue_Risk.pbix
│
└── images/
    ├── 01_executive_overview.png
    ├── 02_customer_health_risk.png
    ├── 03_cs_priority_accounts.png
    ├── 04_retention_revenue.png
    └── 05_usage_support_drivers.png
```

---

## Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/yuvithedeveloper/customer-health-revenue-risk.git
cd customer-health-revenue-risk
```

### 2. Create a Python virtual environment

```bash
python -m venv .venv
```

Activate the environment.

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Generate and clean the synthetic datasets

Run the generation and cleaning scripts in the `python/` directory.

The generated raw datasets are stored in:

```text
data/raw/
```

Cleaned datasets are stored in:

```text
data/processed/
```

### 4. Create the PostgreSQL database

Execute the SQL scripts in numerical order.

The project database is:

```text
cloudpath_analytics
```

### 5. Validate the database

Run:

```text
sql/10_full_database_validation.sql
```

before beginning the analytical SQL layer.

### 6. Run the analytical SQL

Execute:

```text
sql/11_exploratory_analysis.sql
sql/12_create_account_health_base.sql
sql/13_health_signal_distribution.sql
sql/14_create_customer_health_score.sql
sql/15_revenue_at_risk_prioritization.sql
sql/16_retention_revenue_analysis.sql
sql/17_create_powerbi_views.sql
```

These scripts create the analytical views, health scoring, revenue-risk calculations, Customer Success prioritization, retention analysis, and Power BI-ready datasets.

### 7. Open the Power BI report

Open:

```text
powerbi/Customer_Health_Revenue_Risk.pbix
```

and connect it to the local PostgreSQL database.

---

## Analytical Limitations

This project uses synthetic data designed to simulate realistic B2B SaaS customer behavior.

The results therefore demonstrate an analytical methodology and business decision framework rather than conclusions about a real company.

The Customer Health Score and Estimated Revenue at Risk are explainable business-rule models created for this simulation. They should not be interpreted as statistically validated churn predictions.

Estimated Revenue at Risk represents modeled revenue exposure for prioritization rather than a guaranteed forecast of future customer churn.

---

## Project Outcome

This project demonstrates an end-to-end analytics workflow:

**Business Problem → Data Generation → Data Cleaning → PostgreSQL → SQL Analysis → Customer Health Scoring → Revenue Risk → Customer Prioritization → Retention Analysis → Power BI → Business Recommendations**

The final output helps a Customer Success organization answer not only:

**Which customers are at risk?**

but also:

**Why are they at risk, how much recurring revenue is exposed, and which accounts should be prioritized first?**
