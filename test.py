from pymongo import MongoClient
import os

client = MongoClient(os.getenv("DATABASE_URI", "mongodb://localhost:27017/EZAI_nosql"))
db = client.get_database()

try:
    db["test_collection"].insert_one({"test": "data"})
    print("Successfully connected to MongoDB and inserted data.")
except Exception as e:
    print(f"Error: {e}")
