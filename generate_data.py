"""generate_data.py: adds 34 more customers (C07-C40) with accounts, transactions,
transfers, loans, installments, investments and service requests.

Safe to run more than once: everything uses MERGE on its ID, so nothing is duplicated
and balances you changed through the app are not overwritten.
Run it from the project folder:  python generate_data.py
"""
import random
from datetime import date, timedelta

FIRST = ['Aarav', 'Meera', 'Kiran', 'Divya', 'Rohan', 'Sneha', 'Arvind', 'Pooja', 'Naveen',
         'Kavya', 'Manoj', 'Revathi', 'Sanjay', 'Deepa', 'Harish', 'Nisha', 'Gautam',
         'Swathi', 'Ajay', 'Bhavna', 'Tarun', 'Ananya', 'Yash', 'Janani']
LAST = ['Reddy', 'Iyer', 'Menon', 'Gupta', 'Nair', 'Pillai', 'Joshi', 'Das', 'Rao',
        'Chopra', 'Kumar', 'Bose', 'Patel', 'Mehta', 'Subramanian', 'Shetty']
BRANCHES = {'Chennai': ['BR01', 'BR02'], 'Bengaluru': ['BR03']}
LOAN_KINDS = [('Home Loan', 8.5, 240, 1500000, 5000000), ('Personal Loan', 12.0, 36, 100000, 500000),
              ('Vehicle Loan', 9.5, 60, 400000, 1200000), ('Education Loan', 9.0, 84, 300000, 1500000)]
SERVICE_KINDS = [('Card Block', 'Lost debit card'), ('Address Update', 'Change registered address'),
                 ('Cheque Book', 'Request new cheque book'), ('Statement', 'Request 6 month statement')]


def rand_date(rng, start, end):
    return (start + timedelta(days=rng.randint(0, (end - start).days))).isoformat()


def build_data():
    rng = random.Random(42)
    d = {k: [] for k in ['customers', 'accounts', 'txns', 'transfers', 'loans',
                          'installments', 'investments', 'requests']}
    acc_no = 1009
    for i in range(7, 41):
        cid = 'C%02d' % i
        city = rng.choice(['Chennai', 'Chennai', 'Bengaluru'])
        premium = rng.random() < 0.3
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        d['customers'].append({'id': cid, 'fn': fn, 'ln': ln, 'city': city,
                               'phone': '98400%05d' % i,
                               'email': '%s.%s%d@mail.com' % (fn.lower(), ln.lower(), i),
                               'type': 'Premium' if premium else 'Regular',
                               'rm': 'E02' if premium else None})
        for _ in range(rng.choice([1, 1, 2, 2, 3])):
            kind = rng.choices(['Savings', 'Current', 'Fixed Deposit', 'Recurring Deposit'],
                               weights=[50, 20, 15, 15])[0]
            low, high = {'Savings': (5000, 250000), 'Current': (50000, 500000),
                         'Fixed Deposit': (100000, 1000000),
                         'Recurring Deposit': (10000, 100000)}[kind]
            d['accounts'].append({'no': 'AC%d' % acc_no, 'type': kind,
                                  'bal': rng.randint(low // 100, high // 100) * 100,
                                  'opened': rand_date(rng, date(2019, 1, 1), date(2024, 6, 30)),
                                  'cust': cid, 'branch': rng.choice(BRANCHES[city])})
            acc_no += 1

    n = 1
    for a in d['accounts']:
        for _ in range(rng.randint(2, 5)):
            kind = rng.choice(['Deposit', 'Withdrawal'])
            amt = rng.randint(1, 100) * 500
            if kind == 'Withdrawal':
                amt = min(amt, max(500, a['bal'] // 3 // 500 * 500))
            d['txns'].append({'id': 'TX%04d' % n, 'acc': a['no'], 'type': kind, 'amt': amt,
                              'd': rand_date(rng, date(2026, 1, 1), date(2026, 9, 30))})
            n += 1

    pool = [a['no'] for a in d['accounts']]
    n = 1
    for _ in range(45):
        src, dst = rng.sample(pool, 2)
        d['transfers'].append({'id': 'TRX%04d' % n, 'src': src, 'dst': dst,
                               'amt': rng.randint(5, 600) * 100,
                               'd': rand_date(rng, date(2026, 1, 1), date(2026, 8, 31))})
        n += 1
    planted = rng.sample(pool, 8)
    chain, loop = planted[:5], planted[5:]
    for k, amt in enumerate([90000, 88000, 86500, 85000]):      # layering chain
        d['transfers'].append({'id': 'TRX%04d' % n, 'src': chain[k], 'dst': chain[k + 1],
                               'amt': amt, 'd': date(2026, 9, 1 + k).isoformat()})
        n += 1
    for k, amt in enumerate([50000, 49000, 48000]):             # circular flow
        d['transfers'].append({'id': 'TRX%04d' % n, 'src': loop[k], 'dst': loop[(k + 1) % 3],
                               'amt': amt, 'd': date(2026, 9, 10 + k).isoformat()})
        n += 1

    branch_of = {}
    for a in d['accounts']:
        branch_of.setdefault(a['cust'], a['branch'])
    customers = [c['id'] for c in d['customers']]
    for k, cid in enumerate(rng.sample(customers, 14)):
        kind, rate, term, low, high = rng.choice(LOAN_KINDS)
        amount = rng.randint(low // 10000, high // 10000) * 10000
        status = 'Closed' if k < 2 else 'Active'
        lid = 'L%02d' % (4 + k)
        d['loans'].append({'id': lid, 'type': kind, 'amt': amount, 'rate': rate, 'term': term,
                           'status': status, 'cust': cid, 'branch': branch_of[cid],
                           'officer': 'E04'})
        r = rate / 1200
        emi = round(amount * r * (1 + r) ** term / ((1 + r) ** term - 1))
        count = rng.randint(3, 6)
        overdue = status == 'Active' and rng.random() < 0.25
        for m in range(1, count + 1):
            if status == 'Closed' or m < count:
                st = 'Paid'
            else:
                st = 'Overdue' if overdue else 'Pending'
            d['installments'].append({'loan': lid, 'no': m, 'due': date(2026, 5 + m, 1).isoformat(),
                                      'amt': emi, 'status': st})

    for k in range(16):
        d['investments'].append({'id': 'I%02d' % (5 + k),
                                 'type': rng.choice(['Mutual Fund', 'Insurance', 'Wealth Management',
                                                     'Fixed Income']),
                                 'amt': rng.randint(1, 50) * 10000,
                                 'd': rand_date(rng, date(2020, 1, 1), date(2025, 12, 31)),
                                 'cust': rng.choice(customers)})
    for k in range(8):
        kind, descr = rng.choice(SERVICE_KINDS)
        d['requests'].append({'id': 'SR%02d' % (4 + k), 'type': kind, 'descr': descr,
                              'status': rng.choice(['Pending', 'Resolved']),
                              'd': rand_date(rng, date(2026, 1, 1), date(2026, 9, 30)),
                              'cust': rng.choice(customers), 'emp': 'E05'})
    return d


def load(d):
    from connection import run_query

    found = run_query('MATCH (b:Branch) RETURN count(b) AS n')
    if not found or found[0]['n'] < 3:
        raise SystemExit('Branches BR01-BR03 are missing. Run load_data.cypher first.')

    run_query("""
        UNWIND $rows AS row
        MERGE (c:Customer {customer_id: row.id})
        ON CREATE SET c.first_name = row.fn, c.last_name = row.ln, c.city = row.city,
                      c.phone = row.phone, c.email = row.email, c.customer_type = row.type
        """, {'rows': d['customers']})
    run_query("""
        UNWIND $rows AS row
        MATCH (c:Customer {customer_id: row.id}), (e:Employee {employee_id: row.rm})
        MERGE (e)-[:MANAGES]->(c)
        """, {'rows': [c for c in d['customers'] if c['rm']]})
    run_query("""
        UNWIND $rows AS row
        MATCH (c:Customer {customer_id: row.cust}), (b:Branch {branch_id: row.branch})
        MERGE (a:Account {account_number: row.no})
        ON CREATE SET a.account_type = row.type, a.balance = row.bal,
                      a.opened_date = date(row.opened), a.status = 'Active'
        MERGE (c)-[:OWNS]->(a)
        MERGE (a)-[:HELD_AT]->(b)
        """, {'rows': d['accounts']})
    run_query("""
        UNWIND $rows AS row
        MATCH (a:Account {account_number: row.acc})
        MERGE (t:Transaction {txn_id: row.id})
        ON CREATE SET t.txn_type = row.type, t.amount = row.amt, t.txn_date = date(row.d)
        MERGE (a)-[:HAS_TXN]->(t)
        """, {'rows': d['txns']})
    run_query("""
        UNWIND $rows AS row
        MATCH (a:Account {account_number: row.src}), (b:Account {account_number: row.dst})
        MERGE (a)-[r:TRANSFERRED_TO {txn_id: row.id}]->(b)
        ON CREATE SET r.amount = row.amt, r.txn_date = date(row.d)
        """, {'rows': d['transfers']})
    run_query("""
        UNWIND $rows AS row
        MATCH (c:Customer {customer_id: row.cust}), (b:Branch {branch_id: row.branch}),
              (e:Employee {employee_id: row.officer})
        MERGE (l:Loan {loan_id: row.id})
        ON CREATE SET l.loan_type = row.type, l.amount = row.amt, l.interest_rate = row.rate,
                      l.term_months = row.term, l.status = row.status
        MERGE (c)-[:TOOK]->(l)
        MERGE (l)-[:SANCTIONED_AT]->(b)
        MERGE (e)-[:PROCESSED]->(l)
        """, {'rows': d['loans']})
    run_query("""
        UNWIND $rows AS row
        MATCH (l:Loan {loan_id: row.loan})
        MERGE (l)-[:HAS_INSTALLMENT]->(i:Installment {installment_no: row.no})
        ON CREATE SET i.due_date = date(row.due), i.amount_due = row.amt, i.status = row.status
        """, {'rows': d['installments']})
    run_query("""
        UNWIND $rows AS row
        MATCH (c:Customer {customer_id: row.cust})
        MERGE (i:Investment {investment_id: row.id})
        ON CREATE SET i.investment_type = row.type, i.amount = row.amt,
                      i.start_date = date(row.d)
        MERGE (c)-[:INVESTED_IN]->(i)
        """, {'rows': d['investments']})
    run_query("""
        UNWIND $rows AS row
        MATCH (c:Customer {customer_id: row.cust}), (e:Employee {employee_id: row.emp})
        MERGE (r:ServiceRequest {request_id: row.id})
        ON CREATE SET r.request_type = row.type, r.description = row.descr,
                      r.status = row.status, r.request_date = date(row.d)
        MERGE (c)-[:RAISED]->(r)
        MERGE (e)-[:HANDLES]->(r)
        """, {'rows': d['requests']})

    for label in ['Customer', 'Account', 'Transaction', 'Loan', 'Investment']:
        n = run_query('MATCH (x:%s) RETURN count(x) AS n' % label)[0]['n']
        print('%-12s %d' % (label, n))
    t = run_query('MATCH ()-[r:TRANSFERRED_TO]->() RETURN count(r) AS n')[0]['n']
    print('%-12s %d' % ('Transfers', t))


if __name__ == '__main__':
    load(build_data())