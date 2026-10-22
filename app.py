import html

import pandas as pd
import streamlit as st

import db

st.set_page_config(page_title='Smart Banking', page_icon='🏦', layout='wide')

PAGES = [
    'Customer',
    'Accounts and Transactions',
    'Loans and Investments',
    'Analytics',
    'Manage',
]
REQUEST_TYPES = ['Card Block', 'Address Update', 'Cheque Book', 'Loan Query', 'Statement', 'Other']

GREEN, AMBER, RED, GREY = '#10D9A0', '#FFB020', '#FF5C6C', '#A1A1AA'

# Words in a table or card that get a colour (status, transaction type, customer type)
STATUS_COLORS = {
    'Paid': GREEN, 'Active': GREEN, 'Resolved': GREEN,
    'Pending': AMBER, 'Overdue': RED, 'Closed': GREY,
    'Deposit': GREEN, 'Withdrawal': RED,
    'Transfer In': '#4FC3F7', 'Transfer Out': '#C77DFF',
    'Premium': AMBER, 'Regular': GREY,
}

CSS = """
<style>
.block-container { max-width: 1200px; padding-top: 2.5rem; }
[data-testid="stAppDeployButton"] { display: none; }

.page-title { font-size: 2.3rem; font-weight: 800; margin: 0 0 1.2rem 0; }

[data-testid="stSidebar"] { border-right: 1px solid #262626; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 6px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 10px 14px; border-radius: 14px; width: 100%; cursor: pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #262626; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #4F46E5; }

[data-testid="stMetric"] {
    background: #1E1E1E; border: 1px solid #333333; border-radius: 28px; padding: 20px 26px;
}
[data-testid="stMetricLabel"] p {
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.8rem; color: #A1A1AA;
}
[data-testid="stMetricValue"] { font-weight: 800; }
[data-testid="stMetricValue"] > div { overflow: visible; text-overflow: clip; white-space: normal; }

.row-card {
    display: flex; justify-content: space-between; align-items: center;
    background: #1E1E1E; border: 1px solid #333333; border-radius: 28px;
    padding: 18px 26px; margin-bottom: 12px;
}
.rc-title { font-size: 1.1rem; font-weight: 800; }
.rc-sub { font-size: 0.85rem; color: #A1A1AA; margin-top: 2px; }
.rc-right { text-align: right; }
.rc-value { font-size: 1.5rem; font-weight: 800; }
.rc-cap { font-size: 0.75rem; font-weight: 700; color: #A1A1AA; }

[data-baseweb="tab-list"] { gap: 10px; }
button[data-baseweb="tab"] {
    background: #262626; border-radius: 999px; padding: 8px 20px; height: auto;
}
button[data-baseweb="tab"] p { font-weight: 700; color: #D4D4D8; }
button[data-baseweb="tab"][aria-selected="true"] { background: #4F46E5; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #FFFFFF; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }

div[data-baseweb="input"], div[data-baseweb="select"] > div {
    border-radius: 999px; background: #1E1E1E; border: 1px solid #333333;
}
[data-testid="stDataFrame"] { border-radius: 20px; overflow: hidden; border: 1px solid #333333; }

.stButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 999px; border: none; font-weight: 700; color: #FFFFFF; background: #4F46E5;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    background: #6366F1; color: #FFFFFF;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

st.sidebar.title('Smart Banking')
page = st.sidebar.radio('Go to', PAGES, label_visibility='collapsed')


def page_title(title):
    st.markdown('<div class="page-title">' + html.escape(title) + '</div>', unsafe_allow_html=True)


def rs(amount):
    return 'Rs. ' + format(amount, ',.2f')


def rs_short(amount):
    """Compact amount for small cards: Rs. 1.36 Cr, Rs. 4.20 L."""
    if amount >= 10000000:
        return 'Rs. ' + format(amount / 10000000, '.2f') + ' Cr'
    if amount >= 100000:
        return 'Rs. ' + format(amount / 100000, '.2f') + ' L'
    return rs(amount)


def row_card(title, subtitle, value, caption, color='#FFFFFF'):
    """One rounded row: title and subtitle on the left, a big coloured value on the right."""
    st.markdown(
        '<div class="row-card"><div>'
        '<div class="rc-title">' + html.escape(str(title)) + '</div>'
        '<div class="rc-sub">' + html.escape(str(subtitle)) + '</div></div>'
        '<div class="rc-right"><div class="rc-value" style="color:' + color + '">'
        + html.escape(str(value)) + '</div>'
        '<div class="rc-cap">' + html.escape(str(caption)) + '</div></div></div>',
        unsafe_allow_html=True)


def flash(result):
    """Keep a success/error message across the rerun that refreshes the balances."""
    st.session_state['notice'] = result
    st.rerun()


def show_notice():
    notice = st.session_state.pop('notice', None)
    if not notice:
        return
    if notice['success']:
        st.success(notice['message'])
    else:
        st.error(notice['message'])


def paint(value):
    color = STATUS_COLORS.get(value)
    return 'color: ' + color + '; font-weight: 700' if color else ''


def show_table(rows):
    """Show a list of dictionaries as a table, with coloured status words."""
    df = pd.DataFrame(rows)
    columns = [c for c in ['status', 'txn_type', 'customer_type'] if c in df.columns]
    if columns:
        st.dataframe(df.style.map(paint, subset=columns), hide_index=True)
    else:
        st.dataframe(df, hide_index=True)


def account_cards(accounts):
    for a in accounts:
        row_card(a['account_number'], a['account_type'] + '  |  ' + str(a['branch_name']),
                 rs(a['balance']), a['status'], STATUS_COLORS.get(a['status'], '#FFFFFF'))


def customer_screen():
    page_title('Customer')
    show_notice()
    customer_id = st.text_input('Customer ID', value='C01').strip().upper()

    customer = db.get_customer(customer_id)
    if customer is None:
        st.error('No customer found with ID ' + customer_id)
        return

    st.subheader(customer['name'])
    col1, col2, col3 = st.columns(3)
    col1.metric('Type', customer['customer_type'])
    col2.metric('City', customer['city'])
    col3.metric('Total balance', rs(db.get_total_balance(customer_id)))
    st.write('Phone: ' + str(customer['phone']))
    st.write('Email: ' + str(customer['email']))
    if customer['relationship_manager']:
        st.write('Relationship manager: ' + customer['relationship_manager'])

    st.subheader('Accounts')
    accounts = db.get_accounts(customer_id)
    if accounts:
        account_cards(accounts)
    else:
        st.info('No accounts yet for ' + customer_id)

    st.subheader('Service requests')
    service_requests = db.get_service_requests(customer_id)
    if service_requests:
        for r in service_requests:
            row_card(r['request_type'],
                     r['request_id'] + '  |  ' + str(r['request_date']) + '  |  ' + str(r['description']),
                     r['status'], 'Handled by ' + str(r['handled_by']),
                     STATUS_COLORS.get(r['status'], '#FFFFFF'))
    else:
        st.info('No service requests yet for ' + customer_id)

    with st.expander('Raise a new request'):
        with st.form('request_form', clear_on_submit=True):
            request_type = st.selectbox('Request type', REQUEST_TYPES)
            description = st.text_input('Describe the problem')
            if st.form_submit_button('Raise request'):
                if not description.strip():
                    flash({'success': False, 'message': 'Please describe the request'})
                else:
                    flash(db.raise_service_request(customer_id, request_type, description.strip()))


def transactions_screen():
    page_title('Accounts and Transactions')
    show_notice()

    customer_id = st.text_input('Customer ID', value='C01', key='txn_customer_id').strip().upper()
    accounts = db.get_accounts(customer_id)
    if not accounts:
        st.info('No accounts found for ' + customer_id)
        return

    labels = {a['account_number']: a['account_number'] + '  |  ' + a['account_type']
              for a in accounts}
    account_number = st.selectbox('Account', list(labels), format_func=lambda n: labels[n])
    balance = next(a['balance'] for a in accounts if a['account_number'] == account_number)
    st.metric('Balance', rs(balance))

    tab_history, tab_cash, tab_transfer = st.tabs(['History', 'Deposit / Withdraw', 'Transfer'])

    with tab_history:
        history = db.get_transactions(account_number)
        if not history:
            st.info('No transactions on ' + account_number)
        else:
            show_table(history)

    with tab_cash:
        with st.form('cash_form', clear_on_submit=True):
            txn_type = st.radio('Type', ['Deposit', 'Withdrawal'], horizontal=True)
            amount = st.number_input('Amount', min_value=0.0, step=100.0)
            if st.form_submit_button('Submit'):
                flash(db.process_transaction(account_number, txn_type, amount))

    with tab_transfer:
        with st.form('transfer_form', clear_on_submit=True):
            to_account = st.text_input('Send to account number').strip().upper()
            amount = st.number_input('Amount', min_value=0.0, step=100.0, key='transfer_amount')
            if st.form_submit_button('Send money'):
                flash(db.transfer_money(account_number, to_account, amount))


def loans_screen():
    page_title('Loans and Investments')
    customer_id = st.text_input('Customer ID', value='C01', key='loans_customer_id').strip().upper()

    st.subheader('Loans')
    loans = db.get_loans(customer_id)
    if not loans:
        st.info('No loans found for ' + customer_id)
    else:
        for loan in loans:
            row_card(loan['loan_type'],
                     loan['loan_id'] + '  |  ' + str(loan['interest_rate']) + '%  |  '
                     + str(loan['term_months']) + ' months  |  Officer: ' + str(loan['loan_officer']),
                     rs(loan['amount']), loan['status'], STATUS_COLORS.get(loan['status'], '#FFFFFF'))
        loan_id = st.selectbox(
            'Pick a loan to see its repayment schedule',
            [loan['loan_id'] for loan in loans],
        )
        schedule = db.get_repayment_schedule(loan_id)
        if schedule:
            paid = sum(1 for row in schedule if row['status'] == 'Paid')
            st.progress(paid / len(schedule),
                        text=str(paid) + ' of ' + str(len(schedule)) + ' installments paid')
            show_table(schedule)

    st.subheader('Investments')
    investments = db.get_investments(customer_id)
    if not investments:
        st.info('No investments found for ' + customer_id)
    else:
        for inv in investments:
            row_card(inv['investment_type'], inv['investment_id'] + '  |  Started ' + str(inv['start_date']),
                     rs(inv['amount']), 'Invested')
        st.metric('Total invested', rs(sum(i['amount'] for i in investments)))


def analytics_screen():
    page_title('Analytics')
    overview = db.get_overview()
    if overview is None:
        st.error('Could not read from the database. Check the terminal for the error.')
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Customers', overview['customers'])
    col2.metric('Accounts', overview['accounts'])
    col3.metric('Loans', overview['loans'])
    col4.metric('Total deposits', rs_short(overview['total_balance']))

    tab_overview, tab_large, tab_trail, tab_cycles = st.tabs(
        ['Overview', 'Large transfers', 'Money trail', 'Circular flows'])

    with tab_overview:
        left, right = st.columns(2)
        with left:
            st.subheader('Balance by branch')
            branches = db.get_branch_balances()
            if branches:
                st.bar_chart(pd.DataFrame(branches).set_index('branch_name')['total_balance'],
                             color='#6366F1')
        with right:
            st.subheader('Loan amount by type')
            summary = db.get_loan_summary()
            if summary:
                st.bar_chart(pd.DataFrame(summary).set_index('loan_type')['total_amount'],
                             color='#10D9A0')
        st.subheader('Top 10 customers by balance')
        for c in db.get_top_customers_by_balance(10):
            row_card(c['name'], c['customer_id'], rs(c['total_balance']), 'Total balance', GREEN)

    with tab_large:
        threshold = st.slider('Minimum transfer amount', 1000, 100000, 20000, step=1000)
        large = db.get_large_transfers(threshold)
        if not large:
            st.info('No transfers of ' + rs(threshold) + ' or more')
        else:
            st.dataframe(large, hide_index=True)

    with tab_trail:
        start = st.text_input('Start from account', value='AC1001', key='trail_account').strip().upper()
        trails = db.get_money_trail(start)
        if not trails:
            st.info('No outgoing transfers from ' + start)
        else:
            st.dataframe([{'hops': t['hops'], 'trail': ' -> '.join(t['trail'])} for t in trails],
                         hide_index=True)

    with tab_cycles:
        cycles = db.get_circular_transfers()
        if not cycles:
            st.success('No circular flows found')
        else:
            st.warning(str(len(cycles)) + ' circular flow(s) found')
            st.dataframe([{'path': ' -> '.join(c['cycle'] + [c['cycle'][0]]),
                           'transfers': c['length'], 'total_amount': c['total_amount']}
                          for c in cycles], hide_index=True)


def manage_screen():
    page_title('Manage')
    show_notice()

    tab_customer, tab_account, tab_contact, tab_close = st.tabs(
        ['Add customer', 'Open account', 'Update contact', 'Close account'])

    with tab_customer:
        st.caption('The next customer ID will be ' + db.get_next_customer_id())
        with st.form('add_customer_form', clear_on_submit=True):
            first_name = st.text_input('First name').strip()
            last_name = st.text_input('Last name').strip()
            city = st.text_input('City').strip()
            phone = st.text_input('Phone').strip()
            email = st.text_input('Email').strip()
            customer_type = st.selectbox('Customer type', db.CUSTOMER_TYPES)
            if st.form_submit_button('Add customer'):
                flash(db.add_customer(db.get_next_customer_id(), first_name, last_name,
                                      city, phone, email, customer_type))

    with tab_account:
        branch_names = {b['branch_id']: b['branch_name'] for b in db.get_branches()}
        with st.form('open_account_form', clear_on_submit=True):
            customer_id = st.text_input('Customer ID').strip().upper()
            if not branch_names:
                st.warning('No branches are available. Add branches to the database first.')
            else:
                branch_id = st.selectbox('Branch', list(branch_names),
                                         format_func=lambda b: branch_names[b])
                account_type = st.selectbox('Account type', db.ACCOUNT_TYPES)
                opening = st.number_input('Opening balance', min_value=0.0, step=1000.0)
                if st.form_submit_button('Open account'):
                    flash(db.open_account(db.get_next_account_number(), customer_id, branch_id,
                                          account_type, opening))

    with tab_contact:
        with st.form('contact_form', clear_on_submit=True):
            customer_id = st.text_input('Customer ID', key='contact_customer_id').strip().upper()
            phone = st.text_input('New phone', key='contact_phone').strip()
            email = st.text_input('New email', key='contact_email').strip()
            if st.form_submit_button('Update contact details'):
                flash(db.update_customer_contact(customer_id, phone, email))

    with tab_close:
        st.caption('An account can only be closed when its balance is 0. '
                   'It stays in the database with status Closed.')
        with st.form('close_form', clear_on_submit=True):
            account_number = st.text_input('Account number').strip().upper()
            confirm = st.checkbox('I confirm this account should be closed')
            if st.form_submit_button('Close account'):
                if not confirm:
                    flash({'success': False, 'message': 'Tick the confirmation box first'})
                else:
                    flash(db.close_account(account_number))


# Route to the selected page only after all screen functions are defined.
if page == 'Customer':
    customer_screen()
elif page == 'Accounts and Transactions':
    transactions_screen()
elif page == 'Loans and Investments':
    loans_screen()
elif page == 'Analytics':
    analytics_screen()
elif page == 'Manage':
    manage_screen()
