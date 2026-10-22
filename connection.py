
import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

_driver = None


def get_setting(key):
    # Streamlit Cloud secrets first; local .env as fallback
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass

    return os.getenv(key)


def get_driver():
    global _driver
    if _driver is None:
        uri = get_setting("NEO4J_URI")
        user = get_setting("NEO4J_USER") or get_setting("NEO4J_USERNAME")
        password = get_setting("NEO4J_PASSWORD")

        if not uri or not user or not password:
            raise ValueError(
                "Neo4j credentials are missing. Check Streamlit Cloud Secrets."
            )

        _driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
        )
    return _driver


def run_query(cypher, params=None):
    records, summary, keys = get_driver().execute_query(
        cypher, params or {}
    )
    return [record.data() for record in records]


def new_id(prefix):
    return prefix + uuid.uuid4().hex[:8].upper()
