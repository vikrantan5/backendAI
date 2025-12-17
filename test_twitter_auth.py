#!/usr/bin/env python3
"""
Twitter OAuth 1.0a Diagnostic Script
Tests Twitter API credentials and OAuth flow
"""
import os
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

def test_twitter_credentials():
    """Test Twitter API credentials"""
    
    consumer_key = os.environ.get('TWITTER_CLIENT_ID')
    consumer_secret = os.environ.get('TWITTER_CLIENT_SECRET')
    callback_url = os.environ.get('TWITTER_CALLBACK_URL')
    
    print("=" * 60)
    print("TWITTER API CREDENTIALS TEST")
    print("=" * 60)
    
    print(f"\n1. Checking credentials:")
    print(f"   Consumer Key: {consumer_key[:10]}...{consumer_key[-5:] if consumer_key else 'NOT SET'}")
    print(f"   Consumer Secret: {consumer_secret[:10]}...{consumer_secret[-5:] if consumer_secret else 'NOT SET'}")
    print(f"   Callback URL: {callback_url}")
    
    if not consumer_key or not consumer_secret:
        print("\n❌ ERROR: Twitter credentials not configured!")
        return False
    
    print("\n2. Testing OAuth 1.0a request token...")
    
    # Test with callback URL
    auth = OAuth1(
        consumer_key,
        consumer_secret,
        callback_uri=callback_url
    )
    
    request_token_url = "https://api.twitter.com/oauth/request_token"
    
    try:
        response = requests.post(request_token_url, auth=auth)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Twitter OAuth credentials are valid!")
            credentials = dict(item.split('=') for item in response.text.split('&'))
            print(f"   OAuth Token: {credentials.get('oauth_token', 'N/A')[:20]}...")
            return True
        else:
            print(f"\n❌ ERROR: Twitter API returned error")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            # Try to parse error
            try:
                import json
                error_data = json.loads(response.text)
                if 'errors' in error_data:
                    for error in error_data['errors']:
                        print(f"   Error Code: {error.get('code')}")
                        print(f"   Error Message: {error.get('message')}")
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        return False

if __name__ == "__main__":
    test_twitter_credentials()
