# Twitter OAuth 2.0 Migration Guide

## ✅ What Was Changed

Your Twitter/X Content Automation SaaS backend has been successfully migrated from **OAuth 1.0a** to **OAuth 2.0** with PKCE.

---

## 🔄 Key Changes

### 1. **OAuth Flow Updated**
- **Old:** OAuth 1.0a with request tokens and signed requests
- **New:** OAuth 2.0 with PKCE (Proof Key for Code Exchange)

### 2. **Authentication Method**
- **Old:** OAuth1 signatures with consumer key/secret + token/secret
- **New:** Bearer tokens with access_token and refresh_token

### 3. **API Endpoints**
- **Old:** `https://api.twitter.com/oauth/request_token`
- **New:** `https://twitter.com/i/oauth2/authorize`

### 4. **Token Storage**
Database schema updated:
```javascript
// OLD
{
  oauth_token: "...",
  oauth_token_secret: "..."
}

// NEW
{
  access_token: "...",
  refresh_token: "..."
}
```

---

## 🔑 Required Credentials

Your `.env` file must include:

```bash
# Twitter OAuth 2.0 Credentials
TWITTER_CLIENT_ID=your_client_id_here
TWITTER_CLIENT_SECRET=your_client_secret_here
TWITTER_CALLBACK_URL=https://your-domain.com/api/twitter/callback

# Other Required Variables
MONGO_URL=mongodb+srv://...
OPENAI_API_KEY=sk-proj-...
JWT_SECRET=your-secret-key
```

---

## 🚀 How OAuth 2.0 Works

### Step 1: Get Authorization URL
```bash
curl -X GET http://localhost:8001/api/twitter/auth-url \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "auth_url": "https://twitter.com/i/oauth2/authorize?response_type=code&client_id=...",
  "state": "random_state_string"
}
```

### Step 2: User Authorization
1. Redirect user to the `auth_url`
2. User logs into Twitter and authorizes your app
3. Twitter redirects back to your callback URL with `code` and `state`

### Step 3: Complete OAuth Flow
```bash
curl -X GET "http://localhost:8001/api/twitter/callback?code=AUTH_CODE&state=STATE" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "twitter_id": "123456789",
  "screen_name": "username",
  "name": "Display Name",
  "profile_image_url": "https://...",
  "connected_at": "2024-01-15T10:30:00Z"
}
```

---

## 🔐 Security Features

1. **PKCE (RFC 7636)**: Protects against authorization code interception
2. **State Parameter**: Prevents CSRF attacks
3. **Bearer Tokens**: Industry-standard authentication
4. **Refresh Tokens**: Allows token renewal without re-authorization

---

## 📊 Code Changes Summary

### Modified Functions

1. **`generate_pkce_pair()`** - NEW
   - Generates code_verifier and code_challenge for PKCE

2. **`post_tweet_to_twitter()`** - UPDATED
   - Now uses Bearer token instead of OAuth1 signatures
   - Simplified to single access_token parameter

3. **`get_twitter_auth_url()`** - REWRITTEN
   - Generates OAuth 2.0 authorization URL with PKCE
   - Stores code_verifier and state in database

4. **`twitter_callback()`** - REWRITTEN
   - Changed from POST to GET endpoint
   - Exchanges authorization code for access token
   - Uses PKCE code_verifier
   - Fetches user info with OAuth 2.0 API

### Removed Dependencies
- ❌ `authlib` (was causing import errors)
- ❌ `requests-oauthlib` OAuth1 usage

### Added Imports
- ✅ `hashlib` (for PKCE SHA256)
- ✅ `base64` (for PKCE encoding)
- ✅ `secrets` (for secure random generation)

---

## 🧪 Testing the Implementation

### Quick Test Script

Run the provided test script:
```bash
/app/test_oauth2.sh
```

This will:
1. Create a test user
2. Generate OAuth 2.0 authorization URL
3. Provide instructions for manual authorization

### Manual Testing

```bash
# 1. Create user and get token
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123","name":"Test"}' \
  | jq -r '.access_token')

# 2. Get Twitter auth URL
curl -X GET http://localhost:8001/api/twitter/auth-url \
  -H "Authorization: Bearer $TOKEN"

# 3. Open the auth_url in browser, authorize, and get the code

# 4. Complete callback (replace CODE and STATE)
curl -X GET "http://localhost:8001/api/twitter/callback?code=CODE&state=STATE" \
  -H "Authorization: Bearer $TOKEN"

# 5. Check connected account
curl -X GET http://localhost:8001/api/twitter/account \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🐛 Common Issues & Solutions

### Issue: "Invalid OAuth session"
**Cause:** Code verifier not found in database  
**Solution:** Generate a fresh auth URL and try again

### Issue: "Invalid state parameter"
**Cause:** State mismatch (possible CSRF attempt)  
**Solution:** Use the exact state returned from `/auth-url`

### Issue: "Failed to get access token"
**Cause:** Invalid code or expired (codes expire in ~60 seconds)  
**Solution:** Request a new auth URL and complete flow quickly

### Issue: Twitter returns "unauthorized_client"
**Cause:** Client ID/Secret mismatch or app not configured correctly  
**Solution:**
1. Verify credentials in `.env` match Twitter Developer Portal
2. Ensure callback URL is whitelisted in Twitter app settings
3. Check app has read/write permissions

---

## 📱 Twitter Developer Portal Configuration

### Required Settings:

1. **App Type:** Web App, Automated App or Bot
2. **OAuth 2.0 Status:** Enabled
3. **Type of App:** Confidential client
4. **Callback URLs:** 
   - `https://backendai-29f4.onrender.com/api/twitter/callback`
   - `http://localhost:8001/api/twitter/callback` (for local testing)
5. **Required Scopes:**
   - `tweet.read`
   - `tweet.write`
   - `users.read`
   - `offline.access` (for refresh tokens)

### Where to Find Settings:
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Select your app
3. Navigate to **"User authentication settings"**
4. Ensure OAuth 2.0 is enabled with correct settings

---

## 🔄 Migration from OAuth 1.0a Data

If you have existing OAuth 1.0a tokens in your database, they need to be re-authorized:

1. Users must disconnect and reconnect their Twitter accounts
2. Old `oauth_token` and `oauth_token_secret` are replaced with OAuth 2.0 tokens
3. No automatic migration possible (Twitter security requirement)

### Clean Up Old Tokens:
```javascript
// In MongoDB
db.twitter_accounts.updateMany(
  { oauth_token: { $exists: true } },
  { $unset: { oauth_token: "", oauth_token_secret: "" } }
)
```

---

## 🎯 Benefits of OAuth 2.0

1. ✅ **Modern Standard:** Industry-standard authentication
2. ✅ **Better Security:** PKCE prevents authorization code interception
3. ✅ **Refresh Tokens:** Token renewal without re-authorization
4. ✅ **Simpler API:** Bearer tokens easier than signed requests
5. ✅ **Future-Proof:** Twitter's recommended authentication method

---

## 📚 Additional Resources

- **Twitter OAuth 2.0 Docs:** https://developer.twitter.com/en/docs/authentication/oauth-2-0
- **PKCE Specification:** https://tools.ietf.org/html/rfc7636
- **Twitter API v2:** https://developer.twitter.com/en/docs/api-reference-index

---

## ✅ Verification Checklist

- [ ] `.env` file contains all required variables
- [ ] Twitter Developer Portal has OAuth 2.0 enabled
- [ ] Callback URL matches between code and Twitter Portal
- [ ] Backend is running (`sudo supervisorctl status backend`)
- [ ] Test script generates valid authorization URL
- [ ] Manual authorization flow completes successfully
- [ ] Tweets can be posted using OAuth 2.0 tokens

---

## 🎉 Success!

Your Twitter/X Content Automation SaaS now uses **OAuth 2.0 with PKCE** for secure, modern authentication! 🚀

**Next Steps:**
1. Test the OAuth flow end-to-end
2. Deploy to production
3. Update frontend to use new OAuth flow
4. Monitor logs for any issues
