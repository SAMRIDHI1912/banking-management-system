"""fix_loan_officers.py: adds more loan officers and spreads the loans across them.

Each loan is given one officer who works at the branch that sanctioned it.
Safe to run more than once. Run it after load_data.cypher and generate_data.py:
    python fix_loan_officers.py
"""
from connection import run_query

NEW_OFFICERS = [
    {'id': 'E07', 'name': 'Sunil Raghavan', 'branch': 'BR01'},
    {'id': 'E08', 'name': 'Nandini Prabhu', 'branch': 'BR03'},
    {'id': 'E09', 'name': 'Faizal Ahmed', 'branch': 'BR02'},
    {'id': 'E10', 'name': 'Lavanya Krishnan', 'branch': 'BR01'},
    {'id': 'E11', 'name': 'Rohit Bhat', 'branch': 'BR03'},
]

run_query("""
    UNWIND $rows AS row
    MATCH (b:Branch {branch_id: row.branch})
    MERGE (e:Employee {employee_id: row.id})
    ON CREATE SET e.name = row.name, e.role = 'Loan Officer'
    MERGE (e)-[:WORKS_AT]->(b)
    """, {'rows': NEW_OFFICERS})

run_query("""
    MATCH (l:Loan)-[:SANCTIONED_AT]->(b:Branch)
    OPTIONAL MATCH (:Employee)-[p:PROCESSED]->(l)
    DELETE p
    WITH DISTINCT l, b
    MATCH (e:Employee {role: 'Loan Officer'})-[:WORKS_AT]->(b)
    WITH l, e ORDER BY e.employee_id
    WITH l, collect(e) AS officers
    WITH l, officers[toInteger(substring(l.loan_id, 1)) % size(officers)] AS officer
    MERGE (officer)-[:PROCESSED]->(l)
    """)

rows = run_query("""
    MATCH (e:Employee)-[:PROCESSED]->(l:Loan)
    RETURN e.name AS officer, count(l) AS loans ORDER BY loans DESC
    """)
for row in rows:
    print('%-20s %d' % (row['officer'], row['loans']))