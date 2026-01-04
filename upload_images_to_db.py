import os
import certifi
from pymongo import MongoClient
import bson
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]
assets_collection = db["assets"]

images = {
    "logo": r"c:\Users\asus\Desktop\New Project AIML\ai_recruiter\ui\logo.png",
    "login_avatar": r"C:/Users/asus/.gemini/antigravity/brain/fc91c5b2-0984-4354-af74-6f4b718230a3/login_ai_avatar_1767498879681.png",
    "dashboard_illustration": r"C:/Users/asus/.gemini/antigravity/brain/6fbc6a3c-93c6-4de4-9527-b6c47074775c/enterprise_dashboard_illustration_1767372168013.png"
}

def upload_image(name, path):
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return
    
    with open(path, "rb") as f:
        data = f.read()
        
    assets_collection.update_one(
        {"name": name},
        {"$set": {
            "name": name,
            "data": bson.Binary(data),
            "mime_type": "image/png"
        }},
        upsert=True
    )
    print(f"✅ Uploaded: {name}")

if __name__ == "__main__":
    for name, path in images.items():
        upload_image(name, path)
    print("🚀 All images uploaded to MongoDB Atlas!")
