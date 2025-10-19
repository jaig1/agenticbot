
## Tables and Columns (with Business Intelligence):

### insurance_agents
**Description:** Insurance agents data for Knowledge Graph Text-to-SQL demonstration | Contains 0 records

**Columns:**
  - **agent_id** (INTEGER, REQUIRED) 🔑 PRIMARY KEY
    Primary key identifier (INTEGER)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Agent unique identifier

  - **email** (VARCHAR, NULLABLE) 🔒 PII (restricted access) [MEDIUM SENSITIVITY]
    Customer email address | BigQuery Type: STRING | 🔒 PII (Personally Identifiable Information) - Contact PII | Sensitivity: MEDIUM (Access: restricted) | Validation: Email format validation | Pattern: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer email address
    *Validation:* Email format validation
    *Pattern:* `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
    *Statistics:* Distinct: 8 | Cardinality: 1.00

  - **name** (VARCHAR, REQUIRED)
    BigQuery Type: STRING
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Statistics:* Distinct: 8 | Cardinality: 1.00

  - **phone** (VARCHAR, NULLABLE) 🔒 PII (restricted access) [MEDIUM SENSITIVITY]
    Customer phone number | BigQuery Type: STRING | 🔒 PII (Personally Identifiable Information) - Contact PII | Sensitivity: MEDIUM (Access: restricted) | Validation: US phone number format | Pattern: ^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer phone number
    *Validation:* US phone number format
    *Pattern:* `^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$`
    *Statistics:* Distinct: 8 | Cardinality: 1.00


### insurance_claims
**Description:** Insurance claims data for Knowledge Graph Text-to-SQL demonstration | Contains 0 records

**Columns:**
  - **claim_amount** (DECIMAL, REQUIRED) [MEDIUM SENSITIVITY]
    Claimed amount | BigQuery Type: NUMERIC | Sensitivity: MEDIUM (Access: business) | Validation: Non-negative monetary amount
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Claimed amount
    *Validation:* Non-negative monetary amount

  - **claim_date** (DATE, REQUIRED) [LOW SENSITIVITY]
    Date claim was filed | Sensitivity: LOW (Access: business)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Date claim was filed
    *Statistics:* Distinct: 20 | Cardinality: 0.80

  - **claim_id** (INTEGER, REQUIRED) 🔑 PRIMARY KEY [LOW SENSITIVITY]
    Primary key identifier (INTEGER)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Claim unique identifier

  - **claim_number** (VARCHAR, REQUIRED)
    BigQuery Type: STRING
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Statistics:* Distinct: 25 | Cardinality: 1.00

  - **claim_status** (VARCHAR, REQUIRED) [LOW SENSITIVITY]
    Claim processing status | BigQuery Type: STRING | Sensitivity: LOW (Access: business)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Claim processing status
    *Statistics:* Distinct: 4 | Cardinality: 0.16

  - **description** (VARCHAR, NULLABLE) [LOW SENSITIVITY]
    BigQuery Type: STRING | Sensitivity: LOW (Access: business)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Statistics:* Distinct: 25 | Cardinality: 1.00

  - **policy_id** (INTEGER, REQUIRED) 🔑 PRIMARY KEY [LOW SENSITIVITY]
    Primary key identifier (INTEGER)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Policy unique identifier


### insurance_customers
**Description:** Insurance customers data for Knowledge Graph Text-to-SQL demonstration | Contains 0 records

**Columns:**
  - **address** (VARCHAR, NULLABLE) 🔒 PII (restricted access) [HIGH SENSITIVITY]
    Customer address | BigQuery Type: STRING | 🔒 PII (Personally Identifiable Information) - Physical location PII | Sensitivity: HIGH (Access: restricted)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer address
    *Statistics:* Distinct: 14 | Null: 6.7% | Cardinality: 1.00

  - **customer_id** (INTEGER, REQUIRED) 🔑 PRIMARY KEY
    Primary key identifier (INTEGER)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer unique identifier

  - **date_of_birth** (DATE, NULLABLE) 🔒 PII (restricted access) [HIGH SENSITIVITY]
    Customer birth date | 🔒 PII (Personally Identifiable Information) - Age/demographic PII | Sensitivity: HIGH (Access: restricted) | Validation: Must be at least 18 years ago
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer birth date
    *Validation:* Must be at least 18 years ago
    *Statistics:* Distinct: 13 | Null: 13.3% | Cardinality: 1.00

  - **email** (VARCHAR, NULLABLE) 🔒 PII (restricted access) [MEDIUM SENSITIVITY]
    Customer email address | BigQuery Type: STRING | 🔒 PII (Personally Identifiable Information) - Contact PII | Sensitivity: MEDIUM (Access: restricted) | Validation: Email format validation | Pattern: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer email address
    *Validation:* Email format validation
    *Pattern:* `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
    *Statistics:* Distinct: 13 | Null: 13.3% | Cardinality: 1.00

  - **name** (VARCHAR, REQUIRED)
    BigQuery Type: STRING
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Statistics:* Distinct: 15 | Cardinality: 1.00

  - **phone** (VARCHAR, NULLABLE) 🔒 PII (restricted access) [MEDIUM SENSITIVITY]
    Customer phone number | BigQuery Type: STRING | 🔒 PII (Personally Identifiable Information) - Contact PII | Sensitivity: MEDIUM (Access: restricted) | Validation: US phone number format | Pattern: ^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer phone number
    *Validation:* US phone number format
    *Pattern:* `^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$`
    *Statistics:* Distinct: 13 | Null: 13.3% | Cardinality: 1.00


### insurance_policies
**Description:** Insurance policies data for Knowledge Graph Text-to-SQL demonstration | Contains 0 records

**Columns:**
  - **agent_id** (INTEGER, REQUIRED) 🔑 PRIMARY KEY
    Primary key identifier (INTEGER)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Agent unique identifier

  - **customer_id** (INTEGER, REQUIRED) 🔑 PRIMARY KEY
    Primary key identifier (INTEGER)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Customer unique identifier

  - **end_date** (DATE, REQUIRED)
    Data column of type DATE
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Statistics:* Distinct: 28 | Cardinality: 0.82

  - **policy_id** (INTEGER, REQUIRED) 🔑 PRIMARY KEY [LOW SENSITIVITY]
    Primary key identifier (INTEGER)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Policy unique identifier

  - **policy_number** (VARCHAR, REQUIRED)
    BigQuery Type: STRING
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Statistics:* Distinct: 34 | Cardinality: 1.00

  - **policy_type** (VARCHAR, REQUIRED) [LOW SENSITIVITY]
    BigQuery Type: STRING | Sensitivity: LOW (Access: business)
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Statistics:* Distinct: 5 | Cardinality: 0.15

  - **premium_amount** (DECIMAL, REQUIRED) [MEDIUM SENSITIVITY]
    BigQuery Type: NUMERIC | Sensitivity: MEDIUM (Access: business) | Validation: Non-negative monetary amount
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Validation:* Non-negative monetary amount

  - **start_date** (DATE, REQUIRED)
    Validation: Cannot be in the future
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Validation:* Cannot be in the future
    *Statistics:* Distinct: 25 | Cardinality: 0.74

  - **status** (VARCHAR, REQUIRED)
    Current status | BigQuery Type: STRING
    *Allowed Values:* `Active`, `Approved`, `Cancelled`, `Denied`, `Inactive`, `Pending`, `Pending`, `Settled`, `Under_Review`
      - `Active`: Currently active and operational
      - `Approved`: Claim approved for payment
      - `Cancelled`: Permanently cancelled
      - `Denied`: Claim was denied
      - `Inactive`: Temporarily inactive
      - `Pending`: Awaiting approval or processing
      - `Settled`: Claim has been paid and closed
      - `Under_Review`: Claim under investigation or review
    *Business Meaning:* Current status
    *Statistics:* Distinct: 2 | Cardinality: 0.06


## Query Guidelines (BigQuery Specific):

### BigQuery SQL Best Practices:
- Use `SELECT *` sparingly in production queries
- Always use `LIMIT` for exploratory queries
- Use `DATE()` functions for date comparisons
- Use `IFNULL()` or `COALESCE()` for null handling
- Use `ARRAY_AGG()` for aggregating arrays
- Use standard SQL `COUNT(*)`, `SUM()`, `AVG()` functions

### Query Patterns from Knowledge Graph:

**http://bigquery.org/query-guidelines/patterns/1**
- Description: Get customer with their policies
- Business Purpose: Customer portfolio analysis

**http://bigquery.org/query-guidelines/patterns/2**
- Description: Analyze claims with policy and customer context
- Business Purpose: Claims investigation and analysis

**http://bigquery.org/query-guidelines/patterns/3**
- Description: Agent performance with policy and premium metrics
- Business Purpose: Agent performance evaluation

## Synonym and Alias Mappings:

### Table Synonyms:
- **insurance_agents**: account managers, advisors, agents, brokers, distributors, producers, representatives, reps, sales agents, sales force, sales team, sellers
- **insurance_claims**: claims, damage reports, filed claims, incidents, insurance claims, loss claims, loss events, loss notices, losses, reported losses, settlements
- **insurance_customers**: account holders, clients, customer base, customers, individuals, insured, insureds, members, people, policy holders, policyholders, subscribers
- **insurance_policies**: agreements, contracts, coverage, coverages, insurance contracts, insurance policies, insurance products, plans, policies, protection

### Column Synonyms:
- **insurance_agents.email**: agent email, producer email, rep email
- **insurance_agents.first_name**: agent first name, agent name
- **insurance_agents.last_name**: agent last name, agent surname
- **insurance_claims.claim_amount**: damage amount, loss, loss amount, settlement amount
- **insurance_claims.claim_date**: filing date, incident date, loss date
- **insurance_claims.claim_status**: claim state, processing status, status
- **insurance_claims.description**: details, incident description, loss description
- **insurance_customers.address**: customer address, home address, location, residence
- **insurance_customers.date_of_birth**: DOB, age, birth date, birthday, customer age
- **insurance_customers.email**: contact email, customer email, email address
- **insurance_customers.first_name**: customer name, first name, given name
- **insurance_customers.last_name**: family name, last name, surname
- **insurance_customers.phone**: contact number, mobile, phone number, telephone
- **insurance_policies.policy_end_date**: coverage end, end date, expiration date, termination date
- **insurance_policies.policy_id**: contract number, coverage number, policy number
- **insurance_policies.policy_start_date**: coverage start, effective date, inception date, start date
- **insurance_policies.policy_status**: coverage status, policy status, state, status
- **insurance_policies.policy_type**: coverage, coverage type, insurance type, product type
- **insurance_policies.premium**: amount, cost, payment, premium amount, price, rate

## Business Rules and Logic Patterns:

### Agent Performance Rules:
- **New Agent**: Agent with less than 5 policies sold
  - Logic: `COUNT(policy_id) < 5`
  - Applies to: insurance_agents

- **Top Performer**: Agent with above-average policy sales
  - Logic: `COUNT(policy_id) > (SELECT AVG(policy_count) FROM (SELECT agent_id, COUNT(policy_id) as policy_count FROM insurance_policies GROUP BY agent_id))`
  - Applies to: insurance_agents

### Claims Severity Rules:
- **Large Loss Event**: Significant claim requiring special handling
  - Logic: `claim_amount > 50000`
  - Applies to: insurance_claims

### Claims Status Rules:
- **Approved Claim**: Claim that has been approved for payment
  - Logic: `claim_status = 'Approved'`
  - Applies to: insurance_claims

- **Pending Claim**: Claim still under review or processing
  - Logic: `claim_status IN ('Pending', 'Under Review')`
  - Applies to: insurance_claims

### Claims Timing Rules:
- **Recent Claim**: Claim filed in the last 90 days
  - Logic: `claim_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)`
  - Applies to: insurance_claims

### Claims Value Rules:
- **High Value Claim**: Claim exceeding $10,000 in damages
  - Logic: `claim_amount > 10000`
  - Applies to: insurance_claims

### Compliance Rules:
- **Requires KYC Review**: Customer profile requiring Know Your Customer verification
  - Logic: `date_of_birth IS NULL OR address IS NULL`
  - Applies to: insurance_customers

### Data Quality Rules:
- **Complete Customer Profile**: Customer with all required information populated
  - Logic: `first_name IS NOT NULL AND last_name IS NOT NULL AND email IS NOT NULL AND date_of_birth IS NOT NULL`
  - Applies to: insurance_customers

- **Incomplete Customer Profile**: Customer missing critical information
  - Logic: `first_name IS NULL OR last_name IS NULL OR email IS NULL OR date_of_birth IS NULL`
  - Applies to: insurance_customers

### Demographics Rules:
- **Middle Aged**: Customer aged 35-55
  - Logic: `DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) BETWEEN 35 AND 55`
  - Applies to: insurance_customers

- **Senior Customer**: Customer aged 65 or older
  - Logic: `DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) >= 65`
  - Applies to: insurance_customers

- **Young Adult**: Customer aged 18-25
  - Logic: `DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) BETWEEN 18 AND 25`
  - Applies to: insurance_customers

### Financial Metrics Rules:
- **High Premium Policy**: Policy with premium above $5,000 annually
  - Logic: `premium > 5000`
  - Applies to: insurance_policies

- **Low Premium Policy**: Policy with premium below $1,000 annually
  - Logic: `premium < 1000`
  - Applies to: insurance_policies

### Policy Lifecycle Rules:
- **Expiring Soon**: Policy expiring within the next 30 days
  - Logic: `end_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY)`
  - Applies to: insurance_policies

- **New Policy**: Policy issued in the last 30 days
  - Logic: `start_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)`
  - Applies to: insurance_policies

### Policy Status Rules:
- **Active Policy**: Policy currently in force with valid dates and active status
  - Logic: `status = 'Active' AND CURRENT_DATE() BETWEEN start_date AND end_date`
  - Applies to: insurance_policies

- **Expired Policy**: Policy that has passed its end date
  - Logic: `status = 'Expired' OR end_date < CURRENT_DATE()`
  - Applies to: insurance_policies

### Premium Segmentation Rules:
- **Premium Segment - Budget**: Budget tier policies under $2,000
  - Logic: `premium <= 2000`
  - Applies to: insurance_policies

- **Premium Segment - Premium**: Premium tier policies above $5,000
  - Logic: `premium > 5000`
  - Applies to: insurance_policies

- **Premium Segment - Standard**: Standard tier policies $2,000-$5,000
  - Logic: `premium BETWEEN 2000 AND 5000`
  - Applies to: insurance_policies

### Composite Business Rules:
- **Retention Risk** (customer_retention): Customer with expiring policies and recent claims
  - Complex Logic: ```sql
customer_id IN (
                    SELECT DISTINCT p.customer_id
                    FROM insurance_policies p
                    JOIN insurance_claims c ON p.policy_id = c.policy_id
                    WHERE p.policy_end_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY)
                    AND c.claim_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                )
  ```

- **Profitable Customer** (profitability): Customer with high premiums and low claims
  - Complex Logic: ```sql
customer_id IN (
                    SELECT p.customer_id
                    FROM insurance_policies p
                    LEFT JOIN insurance_claims c ON p.policy_id = c.policy_id
                    GROUP BY p.customer_id
                    HAVING SUM(p.premium) > IFNULL(SUM(c.claim_amount), 0) * 2
                )
  ```

- **High Risk Customer** (risk_assessment): Customer with multiple recent high-value claims
  - Complex Logic: ```sql
customer_id IN (
                    SELECT p.customer_id
                    FROM insurance_policies p
                    JOIN insurance_claims c ON p.policy_id = c.policy_id
                    WHERE c.claim_amount > 10000
                    AND c.claim_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
                    GROUP BY p.customer_id
                    HAVING COUNT(*) > 1
                )
  ```

## Canonical Join Patterns (BigQuery Optimized):

Use these proven join patterns to avoid syntax errors:

### Agent→Customer→Policy
**Description**: Complete agent-customer-policy relationship

**Pattern**:
```sql
insurance_agents a JOIN insurance_policies p ON a.agent_id = p.agent_id JOIN insurance_customers c ON p.customer_id = c.customer_id
```

**Usage**: Use for agent performance and customer portfolio analysis

**Business Purpose**: Complete sales relationship mapping

**Join Type**: INNER

**Relationship**: one-to-many-to-many

**Example Query**: Show agent performance with customer details

---

### Customer→Agent
**Description**: Customer to agent join via policy relationship

**Pattern**:
```sql
insurance_customers c JOIN insurance_policies p ON c.customer_id = p.customer_id JOIN insurance_agents a ON p.agent_id = a.agent_id
```

**Usage**: Use for queries involving customer-agent relationships

**Business Purpose**: Links customers to their servicing agents through policies

**Join Type**: INNER

**Relationship**: many-to-many

**Example Query**: Show which agent serves each customer

---

### Customer→Claim
**Description**: Customer to claim join via policy relationship

**Pattern**:
```sql
insurance_customers c JOIN insurance_policies p ON c.customer_id = p.customer_id JOIN insurance_claims cl ON p.policy_id = cl.policy_id
```

**Usage**: Use for customer claim history and loss analysis

**Business Purpose**: Links customers to their claim events through policies

**Join Type**: INNER

**Relationship**: one-to-many

**Example Query**: Show claim history per customer

---

### Customer→Policy
**Description**: Standard customer to policy join for policy analysis

**Pattern**:
```sql
insurance_customers c JOIN insurance_policies p ON c.customer_id = p.customer_id
```

**Usage**: Use for queries involving customer demographics and policy details

**Business Purpose**: Links customers to their insurance policies

**Join Type**: INNER

**Relationship**: one-to-many

**Example Query**: Show policies per customer

---

### Policy→Agent
**Description**: Standard policy to agent join for sales analysis

**Pattern**:
```sql
insurance_policies p JOIN insurance_agents a ON p.agent_id = a.agent_id
```

**Usage**: Use for queries involving agent performance and sales metrics

**Business Purpose**: Links policies to selling agents

**Join Type**: INNER

**Relationship**: many-to-one

**Example Query**: Show policies per agent

---

### Policy→Claim
**Description**: Standard policy to claim join for claims analysis

**Pattern**:
```sql
insurance_policies p JOIN insurance_claims cl ON p.policy_id = cl.policy_id
```

**Usage**: Use for queries involving policy coverage and claim events

**Business Purpose**: Links policies to their associated claims

**Join Type**: INNER

**Relationship**: one-to-many

**Example Query**: Show claims per policy

---

## Data Validation Rules:

- **claim_amount**: Non-negative monetary amount
- **date_of_birth**: Must be at least 18 years ago
- **email**: Email format validation
- **email** Pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- **email**: Email format validation
- **email** Pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- **phone**: US phone number format
- **phone** Pattern: `^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$`
- **phone**: US phone number format
- **phone** Pattern: `^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$`
- **premium_amount**: Non-negative monetary amount
- **start_date**: Cannot be in the future

## Common Query Patterns:

### Agent Performance
**Description**: Agent performance with policy and premium metrics

**Use Case**: Agent performance evaluation

**SQL Pattern**:
```sql

                SELECT a.agent_id, a.first_name, a.last_name,
                       COUNT(p.policy_id) as policy_count,
                       SUM(p.premium) as total_premium
                FROM agents a
                LEFT JOIN policies p ON a.agent_id = p.agent_id
                GROUP BY a.agent_id, a.first_name, a.last_name
               
```

### Claims Analysis
**Description**: Analyze claims with policy and customer context

**Use Case**: Claims investigation and analysis

**SQL Pattern**:
```sql

                SELECT c.claim_id, c.claim_amount, c.claim_status,
                       p.policy_id, p.premium, cust.first_name, cust.last_name
                FROM claims c
                JOIN policies p ON c.policy_id = p.policy_id
                JOIN customers cust ON p.customer_id = cust.customer_id
               
```

### Customer Policy Summary
**Description**: Get customer with their policies

**Use Case**: Customer portfolio analysis

**SQL Pattern**:
```sql

                SELECT c.*, p.policy_id, p.policy_status, p.premium
                FROM customers c
                LEFT JOIN policies p ON c.customer_id = p.customer_id
               
```


## BigQuery Execution Guidelines:

### 1. Query Performance:
- **Partitioning**: Use `WHERE` clauses on partitioned columns when available
- **Clustering**: Take advantage of clustered columns for filtering
- **SELECT Optimization**: Avoid `SELECT *` in production queries
- **LIMIT Usage**: Always use `LIMIT` for exploratory analysis

### 2. BigQuery-Specific Syntax:
- **Date Functions**: Use `DATE()`, `DATETIME()`, `TIMESTAMP()` functions
- **String Functions**: Use `CONCAT()`, `SUBSTR()`, `REGEXP_CONTAINS()`
- **Array Functions**: Use `ARRAY_AGG()`, `UNNEST()` for array operations
- **Window Functions**: Use `ROW_NUMBER()`, `RANK()`, `LAG()`, `LEAD()`

### 3. Data Types and Casting:
- **Casting**: Use `CAST(column AS TYPE)` or `SAFE_CAST()` for safe casting
- **Null Handling**: Use `IFNULL()`, `COALESCE()`, `NULLIF()`
- **Date Arithmetic**: Use `DATE_ADD()`, `DATE_SUB()`, `DATE_DIFF()`

### 4. Privacy and Security:
- **PII Columns**: Be cautious with columns marked as PII (🔒)
- **Access Controls**: Respect sensitivity levels (HIGH, MEDIUM, LOW)
- **Data Masking**: Consider using `EXCEPT()` to exclude sensitive columns

### 5. Default Query Behavior:
- **Row Limits**: Add `LIMIT 100` for exploratory queries unless specified
- **Ordering**: Use `ORDER BY` for consistent results
- **Aggregations**: Group by non-aggregate columns in SELECT

### 6. Insurance Domain Context:
- **Customer Analysis**: Join customers with policies for portfolio analysis
- **Claims Analysis**: Join policies with claims for loss analysis
- **Agent Performance**: Join agents with policies for sales metrics
- **Risk Assessment**: Use business rules for risk categorization