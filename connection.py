import os
import uuid
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD')),
        )
    return _driver


def run_query(cypher, params=None):
    records, summary, keys = get_driver().execute_query(cypher, params or {})
    return [record.data() for record in records]


def new_id(prefix):
    return prefix + uuid.uuid4().hex[:8].upper()

