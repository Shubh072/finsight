import os
from dotenv import load_dotenv

print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir())
load_dotenv()
print("SECRET_KEY:", os.getenv("SECRET_KEY"))
print("JWT_SECRET_KEY:", os.getenv("JWT_SECRET_KEY"))
