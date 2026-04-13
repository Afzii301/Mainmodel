import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
port=int(os.getenv("PORT", 8000))
Debug=os.getenv("DEBUG", "False").lower() == "true"