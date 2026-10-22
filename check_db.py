"""check_db.py: runs every db.py function on the sample data and prints PASS or FAIL.

Run it with:  python check_db.py
Before running, reset the data with:  python load_data.py
(The write checks change the data, so reset again afterwards.)
"""
import db

passed = 0
total = 0


def check(name, condition):
    global passed, total
    total += 1
    if condition:
        passed += 1
    print(('PASS  ' if condition else 'FAIL  ') + name)


def balance_of(customer_id, account_number):
    for account in db.get_accounts(customer_id):
        if account['account_number'] == account_number:
            return account['balance']
    return None


print('--- Read functions ---')
customer = db.get_customer('C01')
check('get_customer C01', customer is not None
      and customer['name'] == 'Ishita Sharma'
      and customer['customer_type'] == 'Premium'
      and customer['relationship_manager'] == 'Priya Menon')
check('get_customer C99 returns None', db.get_customer('C99') is None)

accounts = db.get_accounts('C01')
check('get_accounts C01 has AC1001 and AC1002',
      sorted(a['account_number'] for a in accounts) == ['AC1001', 'AC1002'])
check('get_accounts C99 returns []', db.get_accounts('C99') == [])
check('get_total_balance C01 is 235000', db.get_total_balance('C01') == 235000)

transactions = db.get_transactions('AC1001')
check('get_transactions AC1001 has 4 rows', len(transactions) == 4)
check('get_transactions AC1001 has all 4 types',
      sorted(t['txn_type'] for t in transactions)
      == ['Deposit', 'Transfer In', 'Transfer Out', 'Withdrawal'])

loans = db.get_loans('C01')
check('get_loans C01', len(loans) == 1 and loans[0]['loan_id'] == 'L01'
      and loans[0]['loan_officer'] == 'Divya Rao'
      and loans[0]['branch_name'] == 'Anna Nagar Branch')

schedule = db.get_repayment_schedule('L01')
check('get_repayment_schedule L01: 3 rows, third Pending',
      len(schedule) == 3 and schedule[2]['status'] == 'Pending')

investments = db.get_investments('C01')
check('get_investments C01 has I01 and I03',
      sorted(i['investment_id'] for i in investments) == ['I01', 'I03'])

requests = db.get_service_requests('C01')
check('get_service_requests C01', len(requests) == 1
      and requests[0]['request_id'] == 'SR03'
      and requests[0]['handled_by'] == 'Karthik Suresh')

check('get_branches returns 3 branches', len(db.get_branches()) == 3)

print('--- Analytics functions ---')
counts = {r['branch_name']: r['account_count'] for r in db.get_branch_account_counts()}
check('get_branch_account_counts',
      counts == {'Anna Nagar Branch': 3, 'T Nagar Branch': 3, 'Koramangala Branch': 2})
top = db.get_top_customers_by_balance(3)
check('get_top_customers_by_balance(3) is C01, C03, C06',
      [t['customer_id'] for t in top] == ['C01', 'C03', 'C06'])
large = db.get_large_transfers(20000)
check('get_large_transfers(20000) is TR6 then TR4',
      [t['txn_id'] for t in large] == ['TR6', 'TR4'])
trail = db.get_money_trail('AC1001')
check('get_money_trail AC1001 has hops 1, 2, 3',
      sorted(t['hops'] for t in trail) == [1, 2, 3])
check('get_money_trail longest trail is AC1001, AC1003, AC1005, AC1006',
      any(t['trail'] == ['AC1001', 'AC1003', 'AC1005', 'AC1006'] for t in trail))

print('--- Process functions (these change the data) ---')
result = db.process_transaction('AC1003', 'Deposit', 5000)
check('deposit 5000 into AC1003 succeeds, new balance 47000',
      result['success'] and result['new_balance'] == 47000)
result = db.process_transaction('AC1003', 'Withdrawal', 99999999)
check('withdrawal of 99999999 fails', not result['success'])
result = db.transfer_money('AC1001', 'AC1003', 5000)
check('transfer 5000 AC1001 to AC1003 succeeds', result['success'])
check('AC1001 is now 80000', balance_of('C01', 'AC1001') == 80000)
check('AC1003 is now 52000', balance_of('C02', 'AC1003') == 52000)
result = db.transfer_money('AC1001', 'AC1003', 99999999)
check('transfer of 99999999 fails', not result['success'])

print('--- Manage functions (these change the data) ---')
result = db.add_customer('C01', 'X', 'Y', 'Z', '1', 'x@x.com', 'Regular')
check('add_customer with existing ID C01 fails', not result['success'])
result = db.add_customer('C07', 'Deepa', 'Iyer', 'Chennai', '9840077777',
                         'deepa@mail.com', 'Regular')
check('add_customer C07 succeeds', result['success'] and db.get_customer('C07') is not None)
result = db.update_customer_contact('C07', '9999999999', 'new@mail.com')
check('update_customer_contact C07 succeeds',
      result['success'] and db.get_customer('C07')['phone'] == '9999999999')
result = db.open_account('AC1009', 'C02', 'BR02', 'Savings', 0)
check('open_account AC1009 succeeds', result['success'])
result = db.close_account('AC1008')
check('close_account AC1008 fails (balance is not 0)', not result['success'])
result = db.close_account('AC1009')
check('close_account AC1009 succeeds (balance is 0)', result['success'])
result = db.raise_service_request('C02', 'Cheque Book', 'Need a new cheque book')
check('raise_service_request C02 succeeds', result['success'] and 'request_id' in result)

print()
print(passed, 'of', total, 'checks passed.')
print('Now reset the data with:  python load_data.py')
