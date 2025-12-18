# Twitter OAuth 2.0 Testing Guide

Complete guide for testing the OAuth 2.0 implementation end-to-end.

---

## 🚀 Quick Start

### Automated Verification

Run the verification script to check all components:

```bash
cd /app/backend
python verify_oauth2.py
```

This will check:
- ✅ Environment variables
- ✅ Backend server health
- ✅ OAuth endpoints
- ✅ Twitter credentials format
- ✅ Database connection

---

## 🧪 Manual Testing

### Test 1: Backend Health Check

```bash
curl http://localhost:8001/
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "Backend AI",
  "message": "API is running"
}
```

---

### Test 2: User Authentication

#### Sign Up
```bash
curl -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "securepass123",
    "name": "Test User"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "email": "testuser@example.com",
    "name": "Test User",
    "created_at": "2024-..."
  }
}
```

Save the `access_token` for subsequent requests:
```bash
export TOKEN="your_access_token_here"
```

---

### Test 3: Twitter OAuth 2.0 Flow

#### Step 1: Get Authorization URL

```bash
curl -X GET http://localhost:8001/api/twitter/auth-url \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "auth_url": "https://twitter.com/i/oauth2/authorize?response_type=code&client_id=...",
  "state": "random_state_value"
}
```

**Verify the URL contains:**
- `https://twitter.com/i/oauth2/authorize` ✅
- `response_type=code` ✅
- `client_id=YOUR_CLIENT_ID` ✅
- `redirect_uri=YOUR_CALLBACK_URL` ✅
- `code_challenge` ✅
- `code_challenge_method=S256` ✅
- `state` parameter ✅
- `scope=tweet.read tweet.write users.read offline.access` ✅

#### Step 2: Authorize on Twitter

1. Copy the `auth_url` from the response
2. Open it in your web browser
3. Log in to Twitter/X if not already logged in
4. Click **"Authorize app"**
5. You'll be redirected to:
   ```
   https://backendai-29f4.onrender.com/api/twitter/callback?code=AUTHORIZATION_CODE&state=STATE_VALUE
   ```

#### Step 3: Complete OAuth Callback

Copy the `code` and `state` from the redirect URL and call:

```bash
curl -X GET "http://localhost:8001/api/twitter/callback?code=AUTHORIZATION_CODE&state=STATE_VALUE" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "twitter_id": "123456789",
  "screen_name": "your_username",
  "name": "Your Display Name",
  "profile_image_url": "https://pbs.twimg.com/profile_images/...",
  "connected_at": "2024-01-15T10:30:00Z"
}
```

---

### Test 4: Verify Twitter Account Connection

```bash
curl -X GET http://localhost:8001/api/twitter/account \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "twitter_id": "123456789",
  "screen_name": "your_username",
  "name": "Your Display Name",
  "profile_image_url": "https://...",
  "connected_at": "2024-..."
}
```

---

### Test 5: Configure Content Settings

```bash
curl -X POST http://localhost:8001/api/content-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Technology and AI",
    "tone": "professional",
    "length": "medium",
    "hashtags": true,
    "emojis": false
  }'
```

**Expected Response:**
```json
{
  "id": "uuid",
  "topic": "Technology and AI",
  "tone": "professional",
  "length": "medium",
  "hashtags": true,
  "emojis": false,
  "created_at": "2024-...",
  "updated_at": "2024-..."
}
```

---

### Test 6: Generate and Post Tweet

```bash
curl -X POST http://localhost:8001/api/posts/generate \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (Success):**
```json
{
  "id": "uuid",
  "content": "Exploring the transformative power of AI in modern technology... #TechInnovation #AI",
  "twitter_id": "1234567890123456789",
  "status": "success",
  "error_message": null,
  "created_at": "2024-...",
  "posted_at": "2024-..."
}
```

**Verify on Twitter:**
1. Go to https://twitter.com/your_username
2. You should see the posted tweet!

---

### Test 7: View Post History

```bash
curl -X GET http://localhost:8001/api/posts \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": "uuid",
    "content": "Tweet content...",
    "twitter_id": "1234567890",
    "status": "success",
    "error_message": null,
    "created_at": "2024-...",
    "posted_at": "2024-..."
  }
]
```

---

### Test 8: Get Statistics

```bash
curl -X GET http://localhost:8001/api/stats \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "total_posts": 1,
  "successful_posts": 1,
  "failed_posts": 0,
  "scheduled_posts": 0
}
```

---

### Test 9: Create Schedule

```bash
curl -X POST http://localhost:8001/api/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "daily",
    "time_of_day": "09:00",
    "timezone": "UTC",
    "enabled": true
  }'
```

**Expected Response:**
```json
{
  "id": "uuid",
  "frequency": "daily",
  "time_of_day": "09:00",
  "timezone": "UTC",
  "enabled": true,
  "created_at": "2024-...",
  "updated_at": "2024-..."
}
```

---

## 🎯 Automated Test Script

Use the provided test script for quick testing:

```bash
/app/test_oauth2.sh
```

This script will:
1. Create a test user
2. Generate OAuth URL
3. Provide instructions for authorization

---

## 🐛 Troubleshooting

### Issue: "Not authenticated"

**Cause:** Missing or invalid JWT token

**Solution:**
```bash
# Get a fresh token
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com","password":"pass123","name":"User"}' \
  | jq -r '.access_token')
```

---

### Issue: "No Twitter account connected"

**Cause:** OAuth flow not completed

**Solution:**
1. Get authorization URL: `/api/twitter/auth-url`
2. Authorize on Twitter
3. Complete callback: `/api/twitter/callback?code=...&state=...`

---

### Issue: "Failed to get access token"

**Common Causes:**
1. **Expired authorization code** (codes expire in ~60 seconds)
   - Solution: Get a new auth URL and authorize again quickly
   
2. **Invalid client credentials**
   - Solution: Verify `TWITTER_CLIENT_ID` and `TWITTER_CLIENT_SECRET` in `.env`
   
3. **Callback URL mismatch**
   - Solution: Ensure callback URL in code matches Twitter Developer Portal

---

### Issue: "Invalid state parameter"

**Cause:** State mismatch (CSRF protection triggered)

**Solution:** Use the exact `state` value returned from `/api/twitter/auth-url`

---

### Issue: Tweet posting fails with 401

**Cause:** Invalid or expired access token

**Solution:**
1. Check token storage in database
2. Re-authorize Twitter account (disconnect and reconnect)
3. Ensure app has correct permissions in Twitter Developer Portal

---

## 📊 Expected Database State

After successful OAuth, check MongoDB:

```javascript
// twitter_accounts collection
{
  "user_id": "uuid",
  "twitter_id": "123456789",
  "screen_name": "username",
  "name": "Display Name",
  "profile_image_url": "https://...",
  "access_token": "base64_encoded_token",
  "refresh_token": "base64_encoded_token",
  "connected_at": "2024-01-15T10:30:00Z"
}

// twitter_temp_tokens collection (during OAuth flow)
{
  "user_id": "uuid",
  "code_verifier": "random_string",
  "state": "random_state",
  "created_at": "2024-01-15T10:30:00Z"
}
// Note: This is deleted after successful OAuth completion
```

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] All environment variables set correctly
- [ ] Backend running without errors
- [ ] MongoDB connection working
- [ ] User signup/login works
- [ ] OAuth authorization URL generates correctly
- [ ] Twitter authorization completes successfully
- [ ] Twitter account appears in database
- [ ] Tweet generation works (OpenAI API)
- [ ] Tweet posting works (Twitter API)
- [ ] Post history shows correct data
- [ ] Scheduled posts configuration works
- [ ] All logs show no errors

---

## 🔐 Security Testing

### Test CSRF Protection

Try using an incorrect state parameter:

```bash
# This should fail with "Invalid state parameter"
curl -X GET "http://localhost:8001/api/twitter/callback?code=test&state=wrong_state" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** `400 Bad Request` with error about invalid state

---

### Test Token Expiration

JWT tokens expire after 24 hours. Test with an expired token:

```bash
# Generate a token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdCIsImV4cCI6MH0.test"

# Try to use it
curl -X GET http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** `401 Unauthorized` with "Token expired" or "Invalid token"

---

## 📈 Performance Testing

### Test API Response Times

```bash
# Measure response time
time curl -X GET http://localhost:8001/api/twitter/auth-url \
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** < 200ms for local server

---

## 🎓 Learning Resources

- **API Reference:** `/app/backend/API_REFERENCE.md`
- **OAuth Migration Guide:** `/app/backend/OAUTH2_MIGRATION.md`
- **Implementation Guide:** `/app/backend/IMPLEMENTATION_GUIDE.md`

---

## 🆘 Support

If tests fail:

1. Check backend logs:
   ```bash
   tail -f /var/log/supervisor/backend.err.log
   ```

2. Verify environment:
   ```bash
   python /app/backend/verify_oauth2.py
   ```

3. Check Twitter Developer Portal settings:
   - OAuth 2.0 enabled?
   - Callback URL correct?
   - App has required permissions?

4. Restart backend:
   ```bash
   sudo supervisorctl restart backend
   ```

---

**Happy Testing! 🚀**
