"""load_data.py: wipe the database and load the shared sample data.

Run it with:  python load_data.py
WARNING: it deletes everything in the database first, so you can run it any time
to get back to the starting data (for example after testing the write functions).
"""
from connection import run_query

print('Deleting everything in the database ...')
run_query('MATCH (n) DETACH DELETE n')

with open('load_data.cypher', encoding='utf-8') as f:
    text = f.read()

statements = [s.strip() for s in text.split(';') if s.strip()]

for number, statement in enumerate(statements, start=1):
    run_query(statement)
    print('Ran statement', number, 'of', len(statements))

total = run_query('MATCH (n) RETURN count(n) AS nodes')[0]['nodes']
print('Done. Nodes in the database:', total, '(expected 47)')
