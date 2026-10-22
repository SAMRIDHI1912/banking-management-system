# Smart Banking 

A small banking application. Customers, accounts, branches, employees, loans, transfers and service requests are stored as a graph in Neo4j (Aura), and a Streamlit app reads and updates it.

## Why Neo4j?

Money moving between accounts is a network. Questions such as "where did this money go next?" (money trail) and "does money come back to the account it left?" (circular flow) are path queries. In Neo4j there is one short Cypher pattern. In a relational database they need repeated self-joins.

## Graph model

| Node | Main properties |
| :---- | :---- |
| `Customer` | customer\_id, first\_name, last\_name, city, phone, email, customer\_type (Regular or Premium) |
| `Account` | account\_number, account\_type, balance, opened\_date, status |
| `Branch` | branch\_id, branch\_name, city, ifsc\_code |
| `Employee` | employee\_id, name, role |
| `Loan` | loan\_id, loan\_type, amount, interest\_rate, term\_months, status |
| `Installment` | installment\_no, due\_date, amount\_due, status |
| `Investment` | investment\_id, investment\_type, amount, start\_date |
| `Transaction` | txn\_id, txn\_type (Deposit or Withdrawal), amount, txn\_date |
| `ServiceRequest` | request\_id, request\_type, description, status, request\_date |

| Relationship | Meaning |
| :---- | :---- |
| `(Customer)-[:OWNS]->(Account)` | customer owns an account |
| `(Account)-[:HELD_AT]->(Branch)` | account is held at a branch |
| `(Employee)-[:WORKS_AT]->(Branch)` | employee works at a branch |
| `(Customer)-[:TOOK]->(Loan)` | customer took a loan |
| `(Loan)-[:SANCTIONED_AT]->(Branch)` | loan sanctioned at a branch |
| `(Employee)-[:PROCESSED]->(Loan)` | loan officer processed the loan |
| `(Loan)-[:HAS_INSTALLMENT]->(Installment)` | repayment schedule |
| `(Customer)-[:INVESTED_IN]->(Investment)` | customer investment |
| `(Employee)-[:MANAGES]->(Customer)` | relationship manager of a Premium customer |
| `(Account)-[:HAS_TXN]->(Transaction)` | deposits and withdrawals |
| `(Account)-[:TRANSFERRED_TO {txn_id, amount, txn_date}]->(Account)` | money sent between accounts |
| `(Customer)-[:RAISED]->(ServiceRequest)` | customer raised a request |
| `(Employee)-[:HANDLES]->(ServiceRequest)` | employee handles the request |

## Screens

- **Customer**: profile, total balance, accounts and service requests. A new request can be raised from this screen. It gets today's date, the status Pending and is assigned to a Customer Service Executive.  
- **Accounts and Transactions**: history, deposit, withdrawal and transfer  
- **Loans and Investments**: loans, repayment schedule and investments  
- **Analytics**: branch balances, large transfers, money trail and circular flows

## Files

| File | Purpose |
| :---- | :---- |
| `app.py` | Streamlit front end |
| `db.py` | Every database function the app uses (all Cypher is here) |
| `connection.py` | Neo4j connection, reads credentials from `.env` |
| `load_data.cypher` | Schema constraints and the starting sample data |
| `load_data.py` | Wipes the database and runs `load_data.cypher` |
| `generate_data.py` | Adds customers C07 to C40 with accounts, transfers, loans and more |
| `loan_off.py` | Adds loan officers and spreads loans across them |
| `check_db.py` | Quick checks of the database functions |
| `requirements.txt` | Python packages the project needs |
| `.streamlit/config.toml` | App theme |
| `.env` | The Aura login details |

