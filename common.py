import os
import ssl
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("MEALIE_URL")
API_TOKEN = os.getenv("API_TOKEN")

if not BASE_URL or not API_TOKEN:
    print("Missing environment variables: MEALIE_URL and/or API_TOKEN")
    exit(1)

if os.getenv("SSL_VERIFY", "1") == "0":
    ssl._create_default_https_context = ssl._create_unverified_context
    ssl.create_default_context = lambda *args, **kwargs: ssl._create_unverified_context()
