from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")

# Add tlsCAFile=certifi.where() to fix SSL handshake errors
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]

candidates_collection = db["candidates"]
assets_collection = db["assets"]
recruiters_collection = db["recruiters"]
