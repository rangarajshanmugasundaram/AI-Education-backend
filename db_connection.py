from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

db = client['ai_education']

print("SUCCESS: Connected to the 'ai_education' database!")