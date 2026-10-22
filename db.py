"""db.py: every database function the Smart Banking app uses.

The screens (app.py) call these functions and never write Cypher themselves.
Read functions return a list of dictionaries (an empty list if nothing is found).
Write functions return a dictionary: {'success': True or False, 'message': '...'}.
"""
import math

from neo4j.exceptions import ConstraintError

from connection import run_query, new_id

ACCOUNT_TYPES = ['Savings', 'Current', 'Fixed Deposit', 'Recurring Deposit']
CUSTOMER_TYPES = ['Regular', 'Premium']



def _read(cypher, params=None):
    """Run a read query. On any error, print it in the terminal and return []."""
    try:
        return run_query(cypher, params)
    except Exception as e:
        print('Database error:', e)
        return []


def _ok(message, **extra):
    result = {'success': True, 'message': message}
    result.update(extra)
    return result


def _fail(message):
    return {'success': False, 'message': message}


def _to_number(value):
    """Turn a value into an int or float. Return None if it is not a usable number."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return int(number) if number.is_integer() else number


def get_customer(customer_id):
    rows = _read("""
        MATCH (c:Customer {customer_id: $customer_id})
        OPTIONAL MATCH (m:Employee)-[:MANAGES]->(c)
        RETURN c.customer_id AS customer_id,
               c.first_name + ' ' + c.last_name AS name,
               c.customer_type AS customer_type,
               c.city AS city,
               c.phone AS phone,
               c.email AS email,
               m.name AS relationship_manager
        """, {'customer_id': customer_id})
    return rows[0] if rows else None


def get_accounts(customer_id):
    return _read("""
        MATCH (c:Customer {customer_id: $customer_id})-[:OWNS]->(a:Account)-[:HELD_AT]->(b:Branch)
        RETURN a.account_number AS account_number,
               a.account_type AS account_type,
               a.balance AS balance,
               a.status AS status,
               b.branch_name AS branch_name
        ORDER BY a.account_number
        """, {'customer_id': customer_id})


def get_total_balance(customer_id):
    rows = _read("""
        MATCH (:Customer {customer_id: $customer_id})-[:OWNS]->(a:Account)
        RETURN coalesce(sum(a.balance), 0) AS total
        """, {'customer_id': customer_id})
    return rows[0]['total'] if rows else 0


def get_transactions(account_number):
    rows = _read("""
        MATCH (:Account {account_number: $account_number})-[:HAS_TXN]->(t:Transaction)
        RETURN t.txn_id AS txn_id, toString(t.txn_date) AS txn_date,
               t.txn_type AS txn_type, t.amount AS amount, null AS other_account
        UNION ALL
        MATCH (:Account {account_number: $account_number})-[r:TRANSFERRED_TO]->(b:Account)
        RETURN r.txn_id AS txn_id, toString(r.txn_date) AS txn_date,
               'Transfer Out' AS txn_type, r.amount AS amount,
               b.account_number AS other_account
        UNION ALL
        MATCH (b:Account)-[r:TRANSFERRED_TO]->(:Account {account_number: $account_number})
        RETURN r.txn_id AS txn_id, toString(r.txn_date) AS txn_date,
               'Transfer In' AS txn_type, r.amount AS amount,
               b.account_number AS other_account
        """, {'account_number': account_number})
    rows.sort(key=lambda row: row['txn_date'], reverse=True)
    return rows


def get_loans(customer_id):
    return _read("""
        MATCH (c:Customer {customer_id: $customer_id})-[:TOOK]->(l:Loan)
        OPTIONAL MATCH (e:Employee)-[:PROCESSED]->(l)
        OPTIONAL MATCH (l)-[:SANCTIONED_AT]->(b:Branch)
        RETURN l.loan_id AS loan_id,
               l.loan_type AS loan_type,
               l.amount AS amount,
               l.interest_rate AS interest_rate,
               l.term_months AS term_months,
               l.status AS status,
               e.name AS loan_officer,
               b.branch_name AS branch_name
        ORDER BY l.loan_id
        """, {'customer_id': customer_id})


def get_repayment_schedule(loan_id):
    return _read("""
        MATCH (:Loan {loan_id: $loan_id})-[:HAS_INSTALLMENT]->(i:Installment)
        RETURN i.installment_no AS installment_no,
               toString(i.due_date) AS due_date,
               i.amount_due AS amount_due,
               i.status AS status
        ORDER BY i.installment_no
        """, {'loan_id': loan_id})


def get_investments(customer_id):
    return _read("""
        MATCH (:Customer {customer_id: $customer_id})-[:INVESTED_IN]->(i:Investment)
        RETURN i.investment_id AS investment_id,
               i.investment_type AS investment_type,
               i.amount AS amount,
               toString(i.start_date) AS start_date
        ORDER BY i.investment_id
        """, {'customer_id': customer_id})


def get_service_requests(customer_id):
    return _read("""
        MATCH (:Customer {customer_id: $customer_id})-[:RAISED]->(r:ServiceRequest)
        OPTIONAL MATCH (e:Employee)-[:HANDLES]->(r)
        RETURN r.request_id AS request_id,
               r.request_type AS request_type,
               r.description AS description,
               r.status AS status,
               toString(r.request_date) AS request_date,
               e.name AS handled_by
        ORDER BY r.request_id
        """, {'customer_id': customer_id})


def get_branches():
    return _read("""
        MATCH (b:Branch)
        RETURN b.branch_id AS branch_id, b.branch_name AS branch_name
        ORDER BY b.branch_id
        """)



def add_customer(customer_id, first_name, last_name, city, phone, email, customer_type):
    if not customer_id or not first_name or not last_name:
        return _fail('Customer ID, first name and last name are required')
    if customer_type not in CUSTOMER_TYPES:
        return _fail('Customer type must be Regular or Premium')
    try:
        run_query("""
            CREATE (:Customer {customer_id: $customer_id, first_name: $first_name,
                               last_name: $last_name, city: $city, phone: $phone,
                               email: $email, customer_type: $customer_type})
            """, {'customer_id': customer_id, 'first_name': first_name,
                  'last_name': last_name, 'city': city, 'phone': phone,
                  'email': email, 'customer_type': customer_type})
        return _ok('Customer ' + customer_id + ' added')
    except ConstraintError:
        return _fail('Customer ID ' + customer_id + ' already exists')
    except Exception as e:
        return _fail(str(e))


def update_customer_contact(customer_id, phone, email):
    try:
        rows = run_query("""
            MATCH (c:Customer {customer_id: $customer_id})
            SET c.phone = $phone, c.email = $email
            RETURN c.customer_id AS customer_id
            """, {'customer_id': customer_id, 'phone': phone, 'email': email})
        if not rows:
            return _fail('Customer ' + customer_id + ' not found')
        return _ok('Contact details updated for ' + customer_id)
    except Exception as e:
        return _fail(str(e))


def open_account(account_number, customer_id, branch_id, account_type, opening_balance):
    if not account_number:
        return _fail('Account number is required')
    if account_type not in ACCOUNT_TYPES:
        return _fail('Account type must be one of: ' + ', '.join(ACCOUNT_TYPES))
    balance = _to_number(opening_balance)
    if balance is None or balance < 0:
        return _fail('Opening balance must be a number, 0 or more')
    try:
        rows = run_query("""
            MATCH (c:Customer {customer_id: $customer_id}), (b:Branch {branch_id: $branch_id})
            CREATE (a:Account {account_number: $account_number, account_type: $account_type,
                               balance: $balance, opened_date: date(), status: 'Active'})
            CREATE (c)-[:OWNS]->(a)
            CREATE (a)-[:HELD_AT]->(b)
            RETURN a.account_number AS account_number
            """, {'account_number': account_number, 'customer_id': customer_id,
                  'branch_id': branch_id, 'account_type': account_type,
                  'balance': balance})
        if not rows:
            return _fail('Customer or branch not found')
        return _ok('Account ' + account_number + ' opened for ' + customer_id)
    except ConstraintError:
        return _fail('Account number ' + account_number + ' already exists')
    except Exception as e:
        return _fail(str(e))


def close_account(account_number):
    try:
        rows = run_query("""
            MATCH (a:Account {account_number: $account_number})
            RETURN a.balance AS balance
            """, {'account_number': account_number})
        if not rows:
            return _fail('Account ' + account_number + ' not found')
        if rows[0]['balance'] != 0:
            return _fail('Cannot close an account with a balance above 0')
        run_query("""
            MATCH (a:Account {account_number: $account_number})
            OPTIONAL MATCH (a)-[:HAS_TXN]->(t:Transaction)
            DETACH DELETE t, a
            """, {'account_number': account_number})
        return _ok('Account ' + account_number + ' closed')
    except Exception as e:
        return _fail(str(e))


def raise_service_request(customer_id, request_type, description):
    if not request_type:
        return _fail('Request type is required')
    request_id = new_id('SR')
    try:
        rows = run_query("""
            MATCH (c:Customer {customer_id: $customer_id})
            MATCH (e:Employee {role: 'Customer Service Executive'})
            WITH c, e LIMIT 1
            CREATE (r:ServiceRequest {request_id: $request_id, request_type: $request_type,
                                      description: $description, status: 'Pending',
                                      request_date: date()})
            CREATE (c)-[:RAISED]->(r)
            CREATE (e)-[:HANDLES]->(r)
            RETURN r.request_id AS request_id
            """, {'customer_id': customer_id, 'request_id': request_id,
                  'request_type': request_type, 'description': description})
        if not rows:
            return _fail('Customer ' + customer_id + ' not found')
        return _ok('Request ' + request_id + ' raised', request_id=request_id)
    except Exception as e:
        return _fail(str(e))



def process_transaction(account_number, txn_type, amount):
    if txn_type not in ('Deposit', 'Withdrawal'):
        return _fail('Transaction type must be Deposit or Withdrawal')
    amount = _to_number(amount)
    if amount is None or amount <= 0:
        return _fail('Amount must be a number greater than 0')

    if txn_type == 'Deposit':
        cypher = """
            MATCH (a:Account {account_number: $account_number})
            SET a.balance = a.balance + $amount
            CREATE (a)-[:HAS_TXN]->(:Transaction {txn_id: $txn_id, txn_type: 'Deposit',
                                                   amount: $amount, txn_date: date()})
            RETURN a.balance AS new_balance
            """
    else:
        cypher = """
            MATCH (a:Account {account_number: $account_number})
            WHERE a.balance >= $amount
            SET a.balance = a.balance - $amount
            CREATE (a)-[:HAS_TXN]->(:Transaction {txn_id: $txn_id, txn_type: 'Withdrawal',
                                                   amount: $amount, txn_date: date()})
            RETURN a.balance AS new_balance
            """
    try:
        rows = run_query(cypher, {'account_number': account_number, 'amount': amount,
                                  'txn_id': new_id('T')})
        if rows:
            return _ok(txn_type + ' of ' + str(amount) + ' done on ' + account_number,
                       new_balance=rows[0]['new_balance'])
        exists = run_query("""
            MATCH (a:Account {account_number: $account_number}) RETURN a.balance AS balance
            """, {'account_number': account_number})
        if not exists:
            return _fail('Account ' + account_number + ' not found')
        return _fail('Insufficient balance')
    except Exception as e:
        return _fail(str(e))


def transfer_money(from_account, to_account, amount):
    amount = _to_number(amount)
    if amount is None or amount <= 0:
        return _fail('Amount must be a number greater than 0')
    if from_account == to_account:
        return _fail('Choose two different accounts')
    try:
        rows = run_query("""
            MATCH (a:Account {account_number: $from_account}),
                  (b:Account {account_number: $to_account})
            WHERE a.balance >= $amount
            SET a.balance = a.balance - $amount, b.balance = b.balance + $amount
            CREATE (a)-[:TRANSFERRED_TO {txn_id: $txn_id, amount: $amount,
                                         txn_date: date()}]->(b)
            RETURN a.balance AS new_balance
            """, {'from_account': from_account, 'to_account': to_account,
                  'amount': amount, 'txn_id': new_id('TR')})
        if rows:
            return _ok('Transferred ' + str(amount) + ' from ' + from_account +
                       ' to ' + to_account, new_balance=rows[0]['new_balance'])
        found = run_query("""
            MATCH (a:Account) WHERE a.account_number IN [$from_account, $to_account]
            RETURN count(a) AS n
            """, {'from_account': from_account, 'to_account': to_account})
        if found[0]['n'] < 2:
            return _fail('One of the accounts was not found')
        return _fail('Insufficient balance')
    except Exception as e:
        return _fail(str(e))



def get_branch_account_counts():
    return _read("""
        MATCH (b:Branch)
        OPTIONAL MATCH (a:Account)-[:HELD_AT]->(b)
        RETURN b.branch_name AS branch_name, count(a) AS account_count
        ORDER BY branch_name
        """)


def get_top_customers_by_balance(limit=5):
    return _read("""
        MATCH (c:Customer)-[:OWNS]->(a:Account)
        RETURN c.customer_id AS customer_id,
               c.first_name + ' ' + c.last_name AS name,
               sum(a.balance) AS total_balance
        ORDER BY total_balance DESC
        LIMIT $limit
        """, {'limit': int(limit)})


def get_large_transfers(min_amount):
    return _read("""
        MATCH (a:Account)-[r:TRANSFERRED_TO]->(b:Account)
        WHERE r.amount >= $min_amount
        RETURN r.txn_id AS txn_id,
               a.account_number AS from_account,
               b.account_number AS to_account,
               r.amount AS amount,
               toString(r.txn_date) AS txn_date
        ORDER BY r.amount DESC
        """, {'min_amount': min_amount})


def get_money_trail(account_number):
    return _read("""
        MATCH path = (:Account {account_number: $account_number})-[:TRANSFERRED_TO*1..3]->(:Account)
        RETURN [n IN nodes(path) | n.account_number] AS trail, length(path) AS hops
        ORDER BY hops
        """, {'account_number': account_number})



def get_overview():
    rows = _read("""
        MATCH (c:Customer) WITH count(c) AS customers
        OPTIONAL MATCH (a:Account)
        WITH customers, count(a) AS accounts, coalesce(sum(a.balance), 0) AS total_balance
        OPTIONAL MATCH (l:Loan)
        RETURN customers, accounts, total_balance, count(l) AS loans
        """)
    return rows[0] if rows else None


def get_branch_balances():
    return _read("""
        MATCH (b:Branch)
        OPTIONAL MATCH (a:Account)-[:HELD_AT]->(b)
        RETURN b.branch_name AS branch_name,
               count(a) AS account_count,
               coalesce(sum(a.balance), 0) AS total_balance
        ORDER BY branch_name
        """)


def get_loan_summary():
    return _read("""
        MATCH (l:Loan)
        RETURN l.loan_type AS loan_type, count(l) AS loans, sum(l.amount) AS total_amount
        ORDER BY loan_type
        """)


def get_circular_transfers():
    """Money that leaves an account and comes back to it through 2 to 4 transfers."""
    rows = _read("""
        MATCH path = (a:Account)-[:TRANSFERRED_TO*2..4]->(a)
        RETURN [n IN nodes(path)[0..-1] | n.account_number] AS cycle,
               reduce(s = 0, r IN relationships(path) | s + r.amount) AS total_amount
        """)
    seen = {}
    for row in rows:
        cycle = row['cycle']
        start = cycle.index(min(cycle))
        key = tuple(cycle[start:] + cycle[:start])
        seen[key] = row['total_amount']
    return [{'cycle': list(k), 'length': len(k), 'total_amount': v}
            for k, v in sorted(seen.items(), key=lambda item: -item[1])]



def process_transaction(account_number, txn_type, amount):
    if txn_type not in ('Deposit', 'Withdrawal'):
        return _fail('Transaction type must be Deposit or Withdrawal')
    amount = _to_number(amount)
    if amount is None or amount <= 0:
        return _fail('Amount must be a number greater than 0')

    if txn_type == 'Deposit':
        cypher = """
            MATCH (a:Account {account_number: $account_number})
            WHERE a.status = 'Active'
            SET a.balance = a.balance + $amount
            CREATE (a)-[:HAS_TXN]->(:Transaction {txn_id: $txn_id, txn_type: 'Deposit',
                                                   amount: $amount, txn_date: date()})
            RETURN a.balance AS new_balance
            """
    else:
        cypher = """
            MATCH (a:Account {account_number: $account_number})
            WHERE a.status = 'Active' AND a.balance >= $amount
            SET a.balance = a.balance - $amount
            CREATE (a)-[:HAS_TXN]->(:Transaction {txn_id: $txn_id, txn_type: 'Withdrawal',
                                                   amount: $amount, txn_date: date()})
            RETURN a.balance AS new_balance
            """
    try:
        rows = run_query(cypher, {'account_number': account_number, 'amount': amount,
                                  'txn_id': new_id('T')})
        if rows:
            return _ok(txn_type + ' of ' + str(amount) + ' done on ' + account_number,
                       new_balance=rows[0]['new_balance'])
        found = run_query("""
            MATCH (a:Account {account_number: $account_number}) RETURN a.status AS status
            """, {'account_number': account_number})
        if not found:
            return _fail('Account ' + account_number + ' not found')
        if found[0]['status'] != 'Active':
            return _fail('Account ' + account_number + ' is closed')
        return _fail('Insufficient balance')
    except Exception as e:
        return _fail(str(e))


def transfer_money(from_account, to_account, amount):
    amount = _to_number(amount)
    if amount is None or amount <= 0:
        return _fail('Amount must be a number greater than 0')
    if from_account == to_account:
        return _fail('Choose two different accounts')
    try:
        rows = run_query("""
            MATCH (a:Account {account_number: $from_account}),
                  (b:Account {account_number: $to_account})
            WHERE a.status = 'Active' AND b.status = 'Active' AND a.balance >= $amount
            SET a.balance = a.balance - $amount, b.balance = b.balance + $amount
            CREATE (a)-[:TRANSFERRED_TO {txn_id: $txn_id, amount: $amount,
                                         txn_date: date()}]->(b)
            RETURN a.balance AS new_balance
            """, {'from_account': from_account, 'to_account': to_account,
                  'amount': amount, 'txn_id': new_id('TR')})
        if rows:
            return _ok('Transferred ' + str(amount) + ' from ' + from_account +
                       ' to ' + to_account, new_balance=rows[0]['new_balance'])
        found = run_query("""
            MATCH (a:Account) WHERE a.account_number IN [$from_account, $to_account]
            RETURN a.account_number AS account_number, a.status AS status
            """, {'from_account': from_account, 'to_account': to_account})
        if len(found) < 2:
            return _fail('One of the accounts was not found')
        if any(row['status'] != 'Active' for row in found):
            return _fail('One of the accounts is closed')
        return _fail('Insufficient balance')
    except Exception as e:
        return _fail(str(e))


def close_account(account_number):
    """Mark the account Closed. The account and its history stay in the database."""
    try:
        rows = run_query("""
            MATCH (a:Account {account_number: $account_number})
            RETURN a.balance AS balance, a.status AS status
            """, {'account_number': account_number})
        if not rows:
            return _fail('Account ' + account_number + ' not found')
        if rows[0]['status'] == 'Closed':
            return _fail('Account ' + account_number + ' is already closed')
        if rows[0]['balance'] != 0:
            return _fail('Cannot close an account with a balance above 0')
        run_query("""
            MATCH (a:Account {account_number: $account_number})
            SET a.status = 'Closed', a.closed_date = date()
            """, {'account_number': account_number})
        return _ok('Account ' + account_number + ' closed')
    except Exception as e:
        return _fail(str(e))


def get_next_customer_id():
    rows = _read("""
        MATCH (c:Customer)
        RETURN max(toInteger(substring(c.customer_id, 1))) AS n
        """)
    n = rows[0]['n'] if rows and rows[0]['n'] is not None else 0
    return 'C%02d' % (n + 1)


def get_next_account_number():
    rows = _read("""
        MATCH (a:Account)
        RETURN max(toInteger(substring(a.account_number, 2))) AS n
        """)
    n = rows[0]['n'] if rows and rows[0]['n'] is not None else 1000
    return 'AC' + str(n + 1)