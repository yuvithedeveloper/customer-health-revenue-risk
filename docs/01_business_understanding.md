# Customer Health & Revenue Risk Analytics

## Company

CloudPath Analytics is a fictional B2B SaaS company that provides an operations analytics and workflow monitoring platform.

Customers use the platform to monitor business KPIs, create dashboards and alerts, generate reports, and track operational performance.

This project uses synthetic data and does not represent a real company.

## Business Problem

CloudPath Analytics has customer information spread across subscription, product usage, support, payment, and Customer Success data.

The company needs a consistent way to identify accounts showing signs of declining health, understand why they are at risk, estimate the recurring revenue exposed, and help Customer Success prioritize accounts for proactive outreach.

## Primary Stakeholder

VP of Customer Success

## Supporting Stakeholders

- Customer Success Managers
- Revenue Operations / Finance
- Product Team
- Executive Leadership

## Customer Base

The project will simulate approximately 500 B2B customer accounts across a two-year period from January 2025 through December 2026.

Customers will primarily be divided into:

- SMB
- Mid-Market
- Enterprise

The simulated company will have approximately $18 million in annual recurring revenue, although the final value will depend on the generated customer data.

## Core Business Questions

1. What is the current customer and recurring revenue base?
2. Which customer accounts are healthy, declining, or at risk?
3. What signals are most commonly associated with unhealthy accounts?
4. How much recurring revenue is currently exposed to at-risk accounts?
5. Which accounts should Customer Success prioritize for proactive outreach?
6. How do customer retention and revenue retention differ across customer segments?
7. How does customer behavior change over time?
8. Which accounts show expansion opportunities rather than churn risk?

## Initial KPIs

- Active Customers
- Monthly Recurring Revenue (MRR)
- Annual Recurring Revenue (ARR)
- Logo Retention
- Renewal Rate
- Gross Revenue Retention
- Net Revenue Retention
- Revenue at Risk
- Customer Health Score
- Active User Rate
- Feature Adoption
- Usage Trend
- Support Activity
- Payment Health

## Initial Customer Health Score

The Customer Health Score will be transparent and business-driven rather than based on a black-box machine learning model.

| Dimension | Weight |
|---|---:|
| Product Usage | 25% |
| Usage Trend | 20% |
| Feature Adoption | 15% |
| Support Health | 15% |
| Payment Health | 10% |
| Customer Engagement | 15% |

Initial health categories:

- Healthy: 75-100
- Monitor: 55-74
- At Risk: 0-54

These weights and thresholds are initial project assumptions and may be adjusted after analyzing the generated data.

## Project Scope

The project will include analysis of:

- Customer accounts
- Subscriptions
- Recurring revenue
- Product usage
- Feature adoption
- Support activity
- Payment behavior
- Customer Success interactions
- Retention
- Revenue expansion and contraction
- Customer health
- Revenue at risk
- Account prioritization

## Out of Scope

The first version will not include:

- Machine learning churn prediction
- Marketing attribution
- Sales lead scoring
- Real-time systems
- Full-stack application development
- Cloud infrastructure