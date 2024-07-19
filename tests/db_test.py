import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import engine, local

# test db connection
try:
    with engine.connect() as connection:
        print("Connected to the database successfully!")
        session = local()
        print("Session created successfully!")
except Exception as e:
    print(f"Error connecting to the database: {e}")
