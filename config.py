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
else:
    # We are running locally, so load secrets from .env file
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIRECT_URI = os.getenv("REDIRECT_URI")

# --- VALIDATION ---
# Ensure that all necessary configurations are loaded.
if not all([GEMINI_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, DATABASE_URL, REDIRECT_URI]):
    # Determine which secrets are missing for a helpful error message
    secrets_to_check = ["GEMINI_API_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "DATABASE_URL", "REDIRECT_URI"]
    missing_secrets = []
    
    for secret in secrets_to_check:
        if IS_DEPLOYED:
            if not st.secrets.get(secret):
                missing_secrets.append(secret)
        else:
            if not os.getenv(secret):
                missing_secrets.append(secret)
    
    error_message = f"Missing required secrets: {', '.join(missing_secrets)}. "
    if IS_DEPLOYED:
        error_message += "Please set them in your Streamlit Cloud app settings."
    else:
        error_message += "Please create a .env file in your project root and set them there."
    raise ValueError(error_message)