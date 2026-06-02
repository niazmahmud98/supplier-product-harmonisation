# Backend starter - loads environment variables

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    print("Running Backend Starter")

    # Check all required environment variables are loaded
    token  = os.getenv("EUROPEAN_SOURCING_TOKEN")
    db_host   = os.getenv("DB_HOST")
    db_name   = os.getenv("DB_NAME")

    print("Status: Local environment active")
    print(f"European Sourcing Token: {token[:8]}...")  # show first 8 chars only
    print(f"Database Host: {db_host}")
    print(f"Database Name: {db_name}")


if __name__ == "__main__":
    main()