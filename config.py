# ZenithPlanner/config.py

import streamlit as st
import os
from dotenv import load_dotenv

# --- Determine Environment and Load Secrets ---

# A robust way to check if we are running on Streamlit Cloud
# We'll use a try-except block to safely check for secrets
try:
    # Try to access secrets - this will work in cloud deployment
    st.secrets.get("GEMINI_API_KEY")
    IS_DEPLOYED = True
except:
    # If accessing secrets fails, we're running locally
    IS_DEPLOYED = False

if IS_DEPLOYED:
    # We are in the cloud, so load secrets from st.secrets
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET")
    DATABASE_URL = st.secrets.get("DATABASE_URL")
    REDIRECT_URI = st.secrets.get("REDIRECT_URI")
    # Add this line for the cookie password
    COOKIE_PASSWORD = st.secrets.get("COOKIE_PASSWORD") 
else:
    # We are running locally, so load secrets from .env file
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    # Add this line for the cookie password
    COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD")

# --- VALIDATION ---
# Ensure that all necessary configurations are loaded.
# Update the validation list to include COOKIE_PASSWORD
if not all([GEMINI_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, DATABASE_URL, REDIRECT_URI, COOKIE_PASSWORD]):
    # Determine which secrets are missing for a helpful error message
    # Update the secrets to check list
    secrets_to_check = ["GEMINI_API_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "DATABASE_URL", "REDIRECT_URI", "COOKIE_PASSWORD"]
    missing_secrets = []
    
    for secret in secrets_to_check:
        # Check based on the environment
        env_value = st.secrets.get(secret) if IS_DEPLOYED else os.getenv(secret)
        if not env_value:
            missing_secrets.append(secret)
    
    error_message = f"Missing required secrets: {', '.join(missing_secrets)}. "
    if IS_DEPLOYED:
        error_message += "Please set them in your Streamlit Cloud app settings."
    else:
        error_message += "Please create a .env file in your project root and set them there."
    raise ValueError(error_message)