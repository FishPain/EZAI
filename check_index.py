from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("DATABASE_URI", "mongodb://localhost:27017/EZAI_nosql"))
db = client.get_database()

# Get indexes for a collection
indexes = db["user_model"].index_information()
for name, details in indexes.items():
    print(f"Index Name: {name}")
    print(f"Details: {details}")
user = db["user_model"].find_one({"username": "user1"})
print("Document for user1:", user)