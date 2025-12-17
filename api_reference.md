# API Reference Guide

Complete reference for all API endpoints in the Twitter/X Content Automation SaaS.

**Base URL:** `http://localhost:8001/api`

---

## 🔐 Authentication Endpoints

### 1. Sign Up
Create a new user account.

**Endpoint:** `POST /api/auth/signup`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-15T10:30:00.000000Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "John Doe"
  }'
```

---

### 2. Login
Authenticate existing user.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK` (same as signup)

**cURL Example:**
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

---

### 3. Get Current User
Get authenticated user details.

**Endpoint:** `GET /api/auth/me`

**Headers:** 
```
Authorization: Bearer YOUR_TOKEN_HERE
```

**Response:** `200 OK`
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-15T10:30:00.000000Z"
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🐦 Twitter OAuth Endpoints

### 4. Get Twitter Auth URL
Get URL to authorize Twitter account.

**Endpoint:** `GET /api/twitter/auth-url`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Response:** `200 OK`
```json
{
  "auth_url": "https://api.twitter.com/oauth/authenticate?oauth_token=xxx"
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8001/api/twitter/auth-url \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Usage Flow:**
1. Call this endpoint to get `auth_url`
2. Redirect user to that URL in browser
3. User authorizes on Twitter
4. Twitter redirects back with `oauth_token` and `oauth_verifier`
5. Call `/api/twitter/callback` with those parameters

---

### 5. Twitter Callback
Complete Twitter OAuth flow.

**Endpoint:** `POST /api/twitter/callback`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Query Parameters:**
- `oauth_token`: Token from Twitter redirect
- `oauth_verifier`: Verifier from Twitter redirect

**Response:** `200 OK`
```json
{
  "twitter_id": "123456789",
  "screen_name": "johndoe",
  "name": "John Doe",
  "profile_image_url": "https://pbs.twimg.com/profile_images/...",
  "connected_at": "2024-01-15T10:30:00.000000Z"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8001/api/twitter/callback?oauth_token=xxx&oauth_verifier=yyy" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 6. Get Twitter Account
Get connected Twitter account details.

**Endpoint:** `GET /api/twitter/account`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Response:** `200 OK` (same as callback response)

**Error:** `404 Not Found` if no account connected

---

### 7. Disconnect Twitter
Disconnect Twitter account.

**Endpoint:** `DELETE /api/twitter/disconnect`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Response:** `200 OK`
```json
{
  "message": "Twitter account disconnected successfully"
}
```

---

## ⚙️ Content Configuration Endpoints

### 8. Create/Update Content Config
Configure AI tweet generation settings.

**Endpoint:** `POST /api/content-config`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Request Body:**
```json
{
  "topic": "AI and Technology",
  "tone": "professional",
  "length": "medium",
  "hashtags": true,
  "emojis": false
}
```

**Field Options:**
- `tone`: "professional", "casual", "humorous", "inspirational", "educational"
- `length`: "short" (50-100 chars), "medium" (100-200), "long" (200-280)
- `hashtags`: true/false
- `emojis`: true/false

**Response:** `200 OK`
```json
{
  "id": "uuid-here",
  "topic": "AI and Technology",
  "tone": "professional",
  "length": "medium",
  "hashtags": true,
  "emojis": false,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "updated_at": "2024-01-15T10:30:00.000000Z"
}
```

---

### 9. Get Content Config
Get current content configuration.

**Endpoint:** `GET /api/content-config`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Response:** `200 OK` (same as create response)

**Error:** `404 Not Found` if no config exists

---

## 📅 Schedule Endpoints

### 10. Create/Update Schedule
Set up automated posting schedule.

**Endpoint:** `POST /api/schedule`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Request Body:**
```json
{
  "frequency": "daily",
  "time_of_day": "09:00",
  "timezone": "UTC",
  "enabled": true
}
```

**Field Options:**
- `frequency`: "hourly", "daily", "weekly"
- `time_of_day`: "HH:MM" format (24-hour)
- `timezone`: Any valid timezone (e.g., "America/New_York", "Europe/London")
- `enabled`: true/false

**Response:** `200 OK`
```json
{
  "id": "uuid-here",
  "frequency": "daily",
  "time_of_day": "09:00",
  "timezone": "UTC",
  "enabled": true,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "updated_at": "2024-01-15T10:30:00.000000Z"
}
```

---

### 11. Get Schedule
Get current schedule configuration.

**Endpoint:** `GET /api/schedule`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Response:** `200 OK` (same as create response)

**Error:** `404 Not Found` if no schedule exists

---

### 12. Toggle Automation
Enable or disable automated posting.

**Endpoint:** `PATCH /api/schedule/toggle`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Query Parameters:**
- `enabled`: true or false

**Response:** `200 OK`
```json
{
  "message": "Automation enabled successfully",
  "enabled": true
}
```

**cURL Example:**
```bash
# Enable automation
curl -X PATCH "http://localhost:8001/api/schedule/toggle?enabled=true" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Disable automation
curl -X PATCH "http://localhost:8001/api/schedule/toggle?enabled=false" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📝 Post Management Endpoints

### 13. Generate & Post Tweet
Manually generate and post a tweet immediately.

**Endpoint:** `POST /api/posts/generate`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Response:** `200 OK`
```json
{
  "id": "uuid-here",
  "content": "Exploring the future of AI and its impact on society... #AI #Technology",
  "twitter_id": "1234567890123456789",
  "status": "success",
  "error_message": null,
  "created_at": "2024-01-15T10:30:00.000000Z",
  "posted_at": "2024-01-15T10:30:05.000000Z"
}
```

**Status Values:**
- `"success"`: Tweet posted successfully
- `"failed"`: Tweet generation or posting failed

**Requirements:**
- Twitter account must be connected
- Content config must be set up
- OpenAI API key must be configured

---

### 14. Get Post History
Retrieve history of generated/posted tweets.

**Endpoint:** `GET /api/posts`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Query Parameters:**
- `limit` (optional): Number of posts to return (default: 50, max: 50)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid-1",
    "content": "Tweet content here...",
    "twitter_id": "1234567890",
    "status": "success",
    "error_message": null,
    "created_at": "2024-01-15T10:30:00Z",
    "posted_at": "2024-01-15T10:30:05Z"
  },
  {
    "id": "uuid-2",
    "content": "Another tweet...",
    "twitter_id": null,
    "status": "failed",
    "error_message": "Rate limit exceeded",
    "created_at": "2024-01-15T09:30:00Z",
    "posted_at": null
  }
]
```

**cURL Example:**
```bash
# Get last 50 posts (default)
curl -X GET http://localhost:8001/api/posts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get last 20 posts
curl -X GET "http://localhost:8001/api/posts?limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 15. Get Statistics
Get posting statistics overview.

**Endpoint:** `GET /api/stats`

**Headers:** `Authorization: Bearer YOUR_TOKEN_HERE`

**Response:** `200 OK`
```json
{
  "total_posts": 150,
  "successful_posts": 142,
  "failed_posts": 8,
  "scheduled_posts": 1
}
```

**Field Descriptions:**
- `total_posts`: Total number of tweets attempted
- `successful_posts`: Successfully posted tweets
- `failed_posts`: Failed tweet attempts
- `scheduled_posts`: Number of active schedules (0 or 1)

---

## 🚨 Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid token"
}
```
or
```json
{
  "detail": "Token expired"
}
```

### 404 Not Found
```json
{
  "detail": "No Twitter account connected"
}
```

### 500 Internal Server Error
```json
{
  "detail": "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
}
```

---

## 📊 Rate Limits

### Twitter API Limits:
- **Tweet Creation:** 300 tweets per 3 hours
- **OAuth Tokens:** 300 requests per 15 minutes

### OpenAI API Limits:
- Depends on your account tier
- Free tier: ~3 requests/minute
- Paid tier: 60-3000 requests/minute

**Recommendation:** Keep scheduled posting frequency reasonable to avoid hitting limits.

---

## 🧪 Complete Testing Flow

Here's a complete example of testing all endpoints:

```bash
# 1. Sign up
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Get user info
curl -X GET http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Set content config
curl -X POST http://localhost:8001/api/content-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Technology and Innovation",
    "tone": "professional",
    "length": "medium",
    "hashtags": true,
    "emojis": false
  }'

# 4. Set schedule
curl -X POST http://localhost:8001/api/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "daily",
    "time_of_day": "10:00",
    "timezone": "UTC",
    "enabled": true
  }'

# 5. Get Twitter auth URL (need to complete in browser)
curl -X GET http://localhost:8001/api/twitter/auth-url \
  -H "Authorization: Bearer $TOKEN"

# After connecting Twitter account:

# 6. Generate test tweet
curl -X POST http://localhost:8001/api/posts/generate \
  -H "Authorization: Bearer $TOKEN"

# 7. View post history
curl -X GET http://localhost:8001/api/posts \
  -H "Authorization: Bearer $TOKEN"

# 8. Get stats
curl -X GET http://localhost:8001/api/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📝 Notes

1. **All authenticated endpoints require the `Authorization` header** with Bearer token
2. **Tokens expire after 24 hours** (configurable in server.py)
3. **Each user can have only one Twitter account connected** at a time
4. **Content config and schedule are per-user** (one config per user)
5. **Scheduled posts run every hour** at minute 0 (configurable with APScheduler)

---

## 🔗 Related Files

- **Implementation Guide:** `/app/backend/IMPLEMENTATION_GUIDE.md`
- **Server Code:** `/app/backend/server.py`
- **Environment Config:** `/app/backend/.env`
- **Dependencies:** `/app/backend/requirements.txt`
