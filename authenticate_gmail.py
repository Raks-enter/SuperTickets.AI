"""
Gmail Authentication Script
Run this on your local machine to authenticate Gmail API
"""

import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send', 
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def authenticate_gmail():
    """Authenticate Gmail API and save token"""
    
    # Paths
    credentials_path = "./credentials/gmail_credentials.json"
    token_path = "./credentials/gmail_token.json"
    
    print("🔐 Starting Gmail Authentication...")
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"❌ Error: Gmail credentials file not found at {credentials_path}")
        print("Please make sure your gmail_credential.json file is in the ./credential/ folder")
        return False
    
    print(f"✅ Found credentials file: {credentials_path}")
    
    creds = None
    
    # Load existing token if available
    if os.path.exists(token_path):
        print("📄 Loading existing token...")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🌐 Starting OAuth flow...")
            print("📱 Your browser will open for Gmail authentication")
            print("👆 Please authorize the application in your browser")
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        print("💾 Saving authentication token...")
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    # Test the connection
    print("🧪 Testing Gmail connection...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        
        print("🎉 Gmail Authentication Successful!")
        print(f"📧 Connected to: {profile.get('emailAddress', 'Unknown')}")
        print(f"📊 Total messages: {profile.get('messagesTotal', 0)}")
        print(f"📁 Total threads: {profile.get('threadsTotal', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("  SuperTickets.AI Gmail Authentication")
    print("=" * 50)
    
    # Create credentials directory if it doesn't exist
    os.makedirs("./credentials", exist_ok=True)
    
    success = authenticate_gmail()
    
    if success:
        print("\n✅ Authentication completed successfully!")
        print("🐳 You can now restart your Docker containers")
        print("🤖 The AI will automatically connect to Gmail")
    else:
        print("\n❌ Authentication failed!")
        print("🔧 Please check your gmail_credential.json file")
    
    print("=" * 50)