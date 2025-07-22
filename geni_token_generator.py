import msal
import os
from dotenv import load_dotenv, set_key

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ['api://8a2ecaf5-fb85-4534-81aa-2df3e7f24907/API.Read']  # Define the scopes you want to request

# Get username and password from environment variables
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def authenticate_user():
    # Create a confidential client application
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
    )
   
    # Acquire token using username and password
    result = app.acquire_token_by_username_password(
        username=USERNAME,
        password=PASSWORD,
        scopes=SCOPE
    )
   
    if "access_token" in result:
        token = result["access_token"]
        # Save the token to .env file
        set_key('.env', 'ACCESS_TOKEN', token)
        return token
    else:
        print("Failed to authenticate.")
        print(result.get("error"))
        print(result.get("error_description"))
        return None

def get_token():
    """Get the access token from environment variables or generate a new one"""
    # First try to get existing token from .env
    existing_token = os.getenv("ACCESS_TOKEN")
    if existing_token:
        return existing_token
    
    # If no existing token, authenticate and generate new one
    return authenticate_user()

if __name__ == "__main__":
    token = authenticate_user()
    if token:
        print("Token generated and saved to .env file successfully!")
    else:
        print("Failed to generate token.")