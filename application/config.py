import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST")
RABBIT_SERVER_URL = os.getenv("RABBIT_SERVER_URL")
