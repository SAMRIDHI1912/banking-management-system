CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;
CREATE CONSTRAINT account_number_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.account_number IS UNIQUE;
CREATE CONSTRAINT branch_id_unique IF NOT EXISTS FOR (b:Branch) REQUIRE b.branch_id IS UNIQUE;
CREATE CONSTRAINT employee_id_unique IF NOT EXISTS FOR (e:Employee) REQUIRE e.employee_id IS UNIQUE;
CREATE CONSTRAINT loan_id_unique IF NOT EXISTS FOR (l:Loan) REQUIRE l.loan_id IS UNIQUE;
CREATE CONSTRAINT investment_id_unique IF NOT EXISTS FOR (i:Investment) REQUIRE i.investment_id IS UNIQUE;
CREATE CONSTRAINT request_id_unique IF NOT EXISTS FOR (r:ServiceRequest) REQUIRE r.request_id IS UNIQUE;
CREATE CONSTRAINT txn_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.txn_id IS UNIQUE;

UNWIND [
  {id:'BR01', name:'Anna Nagar Branch', city:'Chennai', ifsc:'IFSC0001'},
  {id:'BR02', name:'T Nagar Branch', city:'Chennai', ifsc:'IFSC0002'},
  {id:'BR03', name:'Koramangala Branch', city:'Bengaluru', ifsc:'IFSC0003'}
] AS row
CREATE (:Branch {branch_id: row.id, branch_name: row.name, city: row.city, ifsc_code: row.ifsc});

UNWIND [
  {id:'E01', name:'Ramesh Iyer', role:'Branch Manager', branch:'BR01'},
  {id:'E02', name:'Priya Menon', role:'Relationship Manager', branch:'BR01'},
  {id:'E03', name:'Arjun Nair', role:'Cashier', branch:'BR02'},
  {id:'E04', name:'Divya Rao', role:'Loan Officer', branch:'BR02'},
  {id:'E05', name:'Karthik Suresh', role:'Customer Service Executive', branch:'BR03'},
  {id:'E06', name:'Meena Pillai', role:'System Administrator', branch:'BR03'}
] AS row
MATCH (b:Branch {branch_id: row.branch})
CREATE (e:Employee {employee_id: row.id, name: row.name, role: row.role})
CREATE (e)-[:WORKS_AT]->(b);

UNWIND [
  {id:'C01', fn:'Ishita', ln:'Sharma', city:'Chennai', phone:'9840011111', email:'ishita.sharma@mail.com', type:'Premium', rm:'E02'},
  {id:'C02', fn:'Rahul', ln:'Verma', city:'Chennai', phone:'9840022222', email:'rahul@mail.com', type:'Regular', rm:null},
  {id:'C03', fn:'Anita', ln:'Krishnan', city:'Chennai', phone:'9840033333', email:'anita@mail.com', type:'Premium', rm:'E02'},
  {id:'C04', fn:'Suresh', ln:'Babu', city:'Bengaluru', phone:'9840044444', email:'suresh@mail.com', type:'Regular', rm:null},
  {id:'C05', fn:'Lakshmi', ln:'Narayan', city:'Bengaluru', phone:'9840055555', email:'lakshmi@mail.com', type:'Regular', rm:null},
  {id:'C06', fn:'Vikram', ln:'Singh', city:'Chennai', phone:'9840066666', email:'vikram@mail.com', type:'Premium', rm:'E02'}
] AS row
CREATE (c:Customer {customer_id: row.id, first_name: row.fn, last_name: row.ln, city: row.city, phone: row.phone, email: row.email, customer_type: row.type})
WITH c, row
OPTIONAL MATCH (e:Employee {employee_id: row.rm})
FOREACH (_ IN CASE WHEN e IS NULL THEN [] ELSE [1] END | CREATE (e)-[:MANAGES]->(c));

UNWIND [
  {no:'AC1001', type:'Savings', bal:85000, opened:'2020-01-10', cust:'C01', branch:'BR01'},
  {no:'AC1002', type:'Current', bal:150000, opened:'2019-05-15', cust:'C01', branch:'BR01'},
  {no:'AC1003', type:'Savings', bal:42000, opened:'2021-03-22', cust:'C02', branch:'BR02'},
  {no:'AC1004', type:'Fixed Deposit', bal:200000, opened:'2022-01-05', cust:'C03', branch:'BR01'},
  {no:'AC1005', type:'Savings', bal:15000, opened:'2021-07-19', cust:'C04', branch:'BR03'},
  {no:'AC1006', type:'Recurring Deposit', bal:30000, opened:'2022-06-01', cust:'C05', branch:'BR03'},
  {no:'AC1007', type:'Current', bal:95000, opened:'2020-11-11', cust:'C06', branch:'BR02'},
  {no:'AC1008', type:'Savings', bal:5000, opened:'2023-02-14', cust:'C02', branch:'BR02'}
] AS row
MATCH (c:Customer {customer_id: row.cust}), (b:Branch {branch_id: row.branch})
CREATE (a:Account {account_number: row.no, account_type: row.type, balance: row.bal, opened_date: date(row.opened), status: 'Active'})
CREATE (c)-[:OWNS]->(a)
CREATE (a)-[:HELD_AT]->(b);

UNWIND [
  {id:'T1', acc:'AC1001', type:'Deposit', amt:20000, d:'2026-01-05'},
  {id:'T2', acc:'AC1001', type:'Withdrawal', amt:5000, d:'2026-02-10'},
  {id:'T3', acc:'AC1002', type:'Deposit', amt:50000, d:'2026-01-15'},
  {id:'T4', acc:'AC1002', type:'Deposit', amt:30000, d:'2026-03-01'},
  {id:'T5', acc:'AC1003', type:'Deposit', amt:10000, d:'2026-01-20'},
  {id:'T6', acc:'AC1003', type:'Withdrawal', amt:2000, d:'2026-02-25'},
  {id:'T7', acc:'AC1004', type:'Deposit', amt:200000, d:'2026-01-01'},
  {id:'T8', acc:'AC1005', type:'Deposit', amt:5000, d:'2026-02-05'}
] AS row
MATCH (a:Account {account_number: row.acc})
CREATE (a)-[:HAS_TXN]->(:Transaction {txn_id: row.id, txn_type: row.type, amount: row.amt, txn_date: date(row.d)});

UNWIND [
  {id:'TR1', src:'AC1001', dst:'AC1003', amt:8000, d:'2026-03-05'},
  {id:'TR2', src:'AC1003', dst:'AC1005', amt:6000, d:'2026-03-06'},
  {id:'TR3', src:'AC1005', dst:'AC1006', amt:5500, d:'2026-03-07'},
  {id:'TR4', src:'AC1002', dst:'AC1007', amt:25000, d:'2026-03-10'},
  {id:'TR5', src:'AC1007', dst:'AC1008', amt:12000, d:'2026-03-12'},
  {id:'TR6', src:'AC1004', dst:'AC1002', amt:40000, d:'2026-03-15'},
  {id:'TR7', src:'AC1008', dst:'AC1003', amt:3000, d:'2026-03-18'},
  {id:'TR8', src:'AC1006', dst:'AC1001', amt:2000, d:'2026-03-20'}
] AS row
MATCH (a:Account {account_number: row.src}), (b:Account {account_number: row.dst})
CREATE (a)-[:TRANSFERRED_TO {txn_id: row.id, amount: row.amt, txn_date: date(row.d)}]->(b);

UNWIND [
  {id:'L01', type:'Home Loan', amt:2500000, rate:8.5, term:240, status:'Active', cust:'C01', branch:'BR01', officer:'E04'},
  {id:'L02', type:'Personal Loan', amt:300000, rate:12.0, term:36, status:'Active', cust:'C02', branch:'BR02', officer:'E04'},
  {id:'L03', type:'Vehicle Loan', amt:800000, rate:9.5, term:60, status:'Active', cust:'C04', branch:'BR03', officer:'E04'}
] AS row
MATCH (c:Customer {customer_id: row.cust}), (b:Branch {branch_id: row.branch}), (e:Employee {employee_id: row.officer})
CREATE (l:Loan {loan_id: row.id, loan_type: row.type, amount: row.amt, interest_rate: row.rate, term_months: row.term, status: row.status})
CREATE (c)-[:TOOK]->(l)
CREATE (l)-[:SANCTIONED_AT]->(b)
CREATE (e)-[:PROCESSED]->(l);

UNWIND [
  {loan:'L01', no:1, due:'2026-02-01', amt:21700, status:'Paid'},
  {loan:'L01', no:2, due:'2026-03-01', amt:21700, status:'Paid'},
  {loan:'L01', no:3, due:'2026-04-01', amt:21700, status:'Pending'},
  {loan:'L02', no:1, due:'2026-02-01', amt:9967, status:'Paid'},
  {loan:'L02', no:2, due:'2026-03-01', amt:9967, status:'Pending'},
  {loan:'L03', no:1, due:'2026-02-01', amt:16800, status:'Paid'}
] AS row
MATCH (l:Loan {loan_id: row.loan})
CREATE (l)-[:HAS_INSTALLMENT]->(:Installment {installment_no: row.no, due_date: date(row.due), amount_due: row.amt, status: row.status});

UNWIND [
  {id:'I01', type:'Mutual Fund', amt:100000, d:'2022-01-10', cust:'C01'},
  {id:'I02', type:'Insurance', amt:50000, d:'2021-06-15', cust:'C03'},
  {id:'I03', type:'Wealth Management', amt:300000, d:'2020-09-01', cust:'C01'},
  {id:'I04', type:'Mutual Fund', amt:75000, d:'2023-02-20', cust:'C06'}
] AS row
MATCH (c:Customer {customer_id: row.cust})
CREATE (c)-[:INVESTED_IN]->(:Investment {investment_id: row.id, investment_type: row.type, amount: row.amt, start_date: date(row.d)});

UNWIND [
  {id:'SR01', type:'Card Block', descr:'Lost debit card', status:'Resolved', d:'2026-01-15', cust:'C02', emp:'E05'},
  {id:'SR02', type:'Address Update', descr:'Change registered address', status:'Pending', d:'2026-02-20', cust:'C04', emp:'E05'},
  {id:'SR03', type:'Cheque Book', descr:'Request new cheque book', status:'Resolved', d:'2026-01-25', cust:'C01', emp:'E05'}
] AS row
MATCH (c:Customer {customer_id: row.cust}), (e:Employee {employee_id: row.emp})
CREATE (r:ServiceRequest {request_id: row.id, request_type: row.type, description: row.descr, status: row.status, request_date: date(row.d)})
CREATE (c)-[:RAISED]->(r)
CREATE (e)-[:HANDLES]->(r);
