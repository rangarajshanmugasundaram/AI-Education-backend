# db_connection.py
import sys
from pymongo import MongoClient

try:
    # Connects to your local MongoDB server instance
    client = MongoClient('mongodb://localhost:27017/')

    # Select the target database name
    db = client['ai_education']

    # Ping the server to verify the connection is active immediately on startup
    client.admin.command('ping')
    print("SUCCESS: Connected to the 'ai_education' database!")

except Exception as e:
    print(f"CRITICAL DATABASE ERROR: Could not connect to MongoDB. Details: {e}")
    sys.exit(1)