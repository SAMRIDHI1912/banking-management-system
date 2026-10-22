# Smart Banking

A small banking application. Customers, accounts, branches, employees, loans, transfers and service requests are stored as a graph in Neo4j Aura, and a Streamlit app reads and updates it.

## Why Neo4j?

Money moving between accounts is a network. Questions such as "where did this money go next?" (money trail) and "does money come back to the account it left?" (circular flow) are path queries. In Neo4j, these can be expressed using Cypher graph patterns. In a relational database, similar queries may require repeated self-joins.

## Graph model

| Node | Main properties |
| :---- | :---- |
| `Customer` | customer_id, first_name, last_name, city, phone, email, customer_type (Regular or Premium) |
| `Account` | account_number, account_type, balance, opened_date, status |
| `Branch` | branch_id, branch_name, city, ifsc_code |
| `Employee` | employee_id, name, role |
| `Loan` | loan_id, loan_type, amount, interest_rate, term_months, status |
| `Installment` | installment_no, due_date, amount_due, status |
| `Investment` | investment_id, investment_type, amount, start_date |
| `Transaction` | txn_id, txn_type (Deposit or Withdrawal), amount, txn_date |
| `ServiceRequest` | request_id, request_type, description, status, request_date |

| Relationship | Meaning |
| :---- | :---- |
| `(Customer)-[:OWNS]->(Account)` | Customer owns an account |
| `(Account)-[:HELD_AT]->(Branch)` | Account is held at a branch |
| `(Employee)-[:WORKS_AT]->(Branch)` | Employee works at a branch |
| `(Customer)-[:TOOK]->(Loan)` | Customer took a loan |
| `(Loan)-[:SANCTIONED_AT]->(Branch)` | Loan sanctioned at a branch |
| `(Employee)-[:PROCESSED]->(Loan)` | Loan officer processed the loan |
| `(Loan)-[:HAS_INSTALLMENT]->(Installment)` | Repayment schedule |
| `(Customer)-[:INVESTED_IN]->(Investment)` | Customer investment |
| `(Employee)-[:MANAGES]->(Customer)` | Relationship manager of a Premium customer |
| `(Account)-[:HAS_TXN]->(Transaction)` | Deposits and withdrawals |
| `(Account)-[:TRANSFERRED_TO {txn_id, amount, txn_date}]->(Account)` | Money sent between accounts |
| `(Customer)-[:RAISED]->(ServiceRequest)` | Customer raised a request |
| `(Employee)-[:HANDLES]->(ServiceRequest)` | Employee handles the request |

## Screens

- **Customer**: Displays a customer's profile, total balance, accounts and service requests. Users can raise a new service request, which is assigned a date, a Pending status and a Customer Service Executive.
- **Accounts and Transactions**: Displays account balances and transaction history. Supports deposits, withdrawals and transfers between accounts.
- **Loans and Investments**: Displays a customer's loans, repayment schedule and investments.
- **Analytics**: Provides branch balance summaries, loan summaries, top customers by balance, large transfer analysis, money trails and circular transfer flows.
- **Manage**: Provides administrative operations through four tabs:
  - **Add customer**: Registers a new customer with their name, city, phone number, email and customer type. The next customer ID is generated automatically.
  - **Open account**: Opens an account for an existing customer, with a selected branch, account type and opening balance. The next account number is generated automatically.
  - **Update contact**: Updates a customer's phone number and email address.
  - **Close account**: Closes an account when its balance is zero, retaining the account record with a Closed status.

## Files

| File | Purpose |
| :---- | :---- |
| `app.py` | Streamlit front end, navigation and screens, including Manage |
| `db.py` | Database functions used by the app; contains the Cypher queries |
| `connection.py` | Neo4j connection setup; reads credentials from Streamlit Secrets or a local `.env` file |
| `load_data.cypher` | Schema constraints and starting sample data |
| `load_data.py` | Loads the starting data into the database; check its behaviour before running because it may clear existing data |
| `generate_data.py` | Adds customers C07 to C40 with accounts, transfers, loans and more |
| `loan_off.py` | Adds loan officers and distributes loans across them |
| `check_db.py` | Quick checks of database functions |
| `requirements.txt` | Python packages required by the project |
| `.streamlit/config.toml` | Streamlit app theme |
| `.env` | Local Aura credentials |

