import os
from dotenv import load_dotenv

#load environment variables from .env file
load_dotenv()

def main():
    print("Running Backend Starter")
    token = os.getenv("EUROPEAN_SOURCING_TOKEN")
    print("status:local environment active")
    print(f"Token loaded successfully:{token}")

if __name__ == "__main__":
    main()