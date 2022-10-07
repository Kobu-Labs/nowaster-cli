import os

from dotenv import load_dotenv

load_dotenv()

ADDRESS = os.getenv("ADDRESS") or ""
print(ADDRESS)
