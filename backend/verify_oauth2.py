#!/usr/bin/env python3
"""
Twitter OAuth 2.0 Verification Script
Validates all components of the OAuth 2.0 implementation
"""
import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def check_environment_variables():
    """Verify all required environment variables are set"""
    print_header("1. Environment Variables Check")
    
    required_vars = {
        'TWITTER_CLIENT_ID': 'Twitter OAuth 2.0 Client ID',
        'TWITTER_CLIENT_SECRET': 'Twitter OAuth 2.0 Client Secret',
        'TWITTER_CALLBACK_URL': 'Twitter OAuth Callback URL',
        'OPENAI_API_KEY': 'OpenAI API Key',
        'MONGO_URL': 'MongoDB Connection String',
        'JWT_SECRET': 'JWT Secret Key',
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value and value != f'your-{var.lower()}-here':
            print_success(f"{description}: Set")
            if var in ['TWITTER_CLIENT_ID', 'TWITTER_CLIENT_SECRET', 'OPENAI_API_KEY']:
                print(f"   Value: {value[:15]}...{value[-5:]}")
            else:
                print(f"   Value: {value}")
        else:
            print_error(f"{description}: NOT SET")
            all_present = False
    
    return all_present

def check_backend_health():
    """Check if backend server is running"""
    print_header("2. Backend Server Health Check")
    
    try:
        response = requests.get('http://localhost:8001/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            return True
        else:
            print_error(f"Backend returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Backend is not running or not accessible")
        print_info("Run: sudo supervisorctl restart backend")
        return False
    except Exception as e:
        print_error(f"Error checking backend: {str(e)}")
        return False

def check_oauth_endpoints():
    """Check if OAuth endpoints are accessible"""
    print_header("3. OAuth 2.0 Endpoints Check")
    
    # First, create a test user
    try:
        signup_data = {
            "email": "verify_oauth@test.com",
            "password": "testpass123",
            "name": "OAuth Verifier"
        }
        
        response = requests.post(
            'http://localhost:8001/api/auth/signup',
            json=signup_data,
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print_success("Test user created successfully")
            print(f"   Token: {token[:20]}...")
        elif response.status_code == 400:
            # User already exists, try login
            login_data = {
                "email": signup_data["email"],
                "password": signup_data["password"]
            }
            response = requests.post(
                'http://localhost:8001/api/auth/login',
                json=login_data,
                timeout=5
            )
            token = response.json().get('access_token')
            print_success("Test user login successful")
        else:
            print_error(f"Failed to create/login test user: {response.text}")
            return False
        
        # Test OAuth auth-url endpoint
        headers = {'Authorization': f'Bearer {token}'}
        auth_response = requests.get(
            'http://localhost:8001/api/twitter/auth-url',
            headers=headers,
            timeout=5
        )
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            auth_url = auth_data.get('auth_url')
            state = auth_data.get('state')
            
            print_success("OAuth authorization URL generated")
            print(f"   URL: {auth_url[:80]}...")
            print(f"   State: {state}")
            
            # Validate URL components
            if 'twitter.com/i/oauth2/authorize' in auth_url:
                print_success("URL format is correct (OAuth 2.0)")
            else:
                print_error("URL format is incorrect")
                return False
            
            if 'code_challenge' in auth_url and 'code_challenge_method=S256' in auth_url:
                print_success("PKCE is enabled (code_challenge + S256)")
            else:
                print_error("PKCE not properly configured")
                return False
            
            if os.environ.get('TWITTER_CLIENT_ID') in auth_url:
                print_success("Client ID is included in URL")
            else:
                print_error("Client ID not found in URL")
                return False
            
            return True
        else:
            print_error(f"Failed to get auth URL: {auth_response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error testing OAuth endpoints: {str(e)}")
        return False

def check_twitter_credentials():
    """Validate Twitter API credentials format"""
    print_header("4. Twitter Credentials Validation")
    
    client_id = os.environ.get('TWITTER_CLIENT_ID')
    client_secret = os.environ.get('TWITTER_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print_error("Twitter credentials not set")
        return False
    
    # OAuth 2.0 client IDs are typically base64-like strings
    if len(client_id) > 10:
        print_success("Client ID format looks valid")
        print(f"   Length: {len(client_id)} characters")
    else:
        print_error("Client ID seems too short")
        return False
    
    if len(client_secret) > 20:
        print_success("Client Secret format looks valid")
        print(f"   Length: {len(client_secret)} characters")
    else:
        print_error("Client Secret seems too short")
        return False
    
    return True

def check_database_connection():
    """Check MongoDB connection"""
    print_header("5. Database Connection Check")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        mongo_url = os.environ.get('MONGO_URL')
        
        async def test_connection():
            client = AsyncIOMotorClient(mongo_url)
            try:
                # Ping the database
                await client.admin.command('ping')
                return True
            except Exception as e:
                print_error(f"MongoDB connection failed: {str(e)}")
                return False
            finally:
                client.close()
        
        result = asyncio.run(test_connection())
        if result:
            print_success("MongoDB connection successful")
            return True
        else:
            return False
            
    except Exception as e:
        print_error(f"Error testing database: {str(e)}")
        return False

def print_summary(checks):
    """Print final summary"""
    print_header("Verification Summary")
    
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total} checks")
    print()
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    if passed == total:
        print("\n🎉 All checks passed! OAuth 2.0 is configured correctly.")
        print("\nNext steps:")
        print("1. Test the OAuth flow manually:")
        print("   /app/test_oauth2.sh")
        print()
        print("2. Open the generated URL in browser and authorize")
        print()
        print("3. Complete the callback with the authorization code")
        return True
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
        return False

def main():
    print("\n" + "🔍 Twitter OAuth 2.0 Verification Tool" + "\n")
    
    checks = {
        'Environment Variables': check_environment_variables(),
        'Backend Server': check_backend_health(),
        'OAuth Endpoints': check_oauth_endpoints(),
        'Twitter Credentials': check_twitter_credentials(),
        'Database Connection': check_database_connection(),
    }
    
    success = print_summary(checks)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
