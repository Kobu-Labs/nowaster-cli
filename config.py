from dotenv import load_dotenv
import os


load_dotenv()

ADDRESS = os.getenv("ADDRESS") or ""
print(ADDRESS)
