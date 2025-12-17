# Twitter/X Content Automation SaaS

🚀 **AI-Powered Twitter automation platform for automated content generation and scheduled posting**

---

## 📋 Overview

This is a production-ready backend API for a Twitter/X Content Automation SaaS platform. It allows users to:

✅ Connect their Twitter/X account via OAuth  
✅ Configure AI-generated content (topic, tone, style)  
✅ Schedule automated posting  
✅ Track post history and statistics  
✅ Control automation with a simple API  

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                     Backend API                        │
│                   (FastAPI/Python)                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Auth      │  │   Twitter   │  │   Content   │     │
│  │   System    │  │   OAuth     │  │   Config    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Scheduler  │  │    Posts    │  │    Stats    │     │
│  │(APScheduler)│  │  Tracking   │  │  Analytics  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                        │
└────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │ MongoDB │      │ OpenAI  │      │ Twitter │
   │Database │      │   API   │      │   API   │
   └─────────┘      └─────────┘      └─────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend Framework** | FastAPI (Python) |
| **Database** | MongoDB (Motor async driver) |
| **AI Engine** | OpenAI API (GPT-4) |
| **Authentication** | JWT (PyJWT + bcrypt) |
| **OAuth** | Twitter OAuth 1.0a |
| **Scheduler** | APScheduler (Cron-based) |
| **Server** | Uvicorn (ASGI) |

---

## 📁 Project Structure

```
/app/
├── backend/
│   ├── server.py                    # Main FastAPI application
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables (add your keys!)
│   ├── IMPLEMENTATION_GUIDE.md      # OpenAI SDK implementation details
│   └── API_REFERENCE.md             # Complete API documentation
│
└── README.md                        # This file
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- MongoDB running on localhost:27017
- OpenAI API key
- Twitter API credentials (Client ID & Secret)

### 2. Environment Setup

Edit `/app/backend/.env` and add your credentials:

```bash
# Database
MONGO_URL="mongodb://localhost:27017"
DB_NAME="twitter_saas_db"

# API Keys
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
TWITTER_CLIENT_ID=your-twitter-client-id
TWITTER_CLIENT_SECRET=your-twitter-client-secret

# Security
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# CORS (optional)
CORS_ORIGINS="*"
```

### 3. Install Dependencies

```bash
cd /app/backend
pip install -r requirements.txt
```

### 4. Start the Server

The server is managed by supervisor and runs automatically:

```bash
# Check status
sudo supervisorctl status backend

# Restart if needed
sudo supervisorctl restart backend

# View logs
tail -f /var/log/supervisor/backend.err.log
```

### 5. Test the API

```bash
# Health check
curl http://localhost:8001/api/auth/me
# Expected: {"detail": "Not authenticated"}

# Sign up
curl -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "name": "Test User"
  }'
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`IMPLEMENTATION_GUIDE.md`](/app/backend/IMPLEMENTATION_GUIDE.md) | OpenAI SDK implementation details, migration guide, troubleshooting |
| [`API_REFERENCE.md`](/app/backend/API_REFERENCE.md) | Complete API endpoint reference with examples |

---

## 🔑 Key Features

### 1. **User Authentication**
- JWT-based authentication
- Secure password hashing (bcrypt)
- 24-hour token expiration

### 2. **Twitter OAuth Integration**
- OAuth 1.0a flow
- Secure token storage
- Account linking/unlinking

### 3. **AI Content Generation**
- OpenAI GPT-4 powered tweets
- Customizable tone, length, style
- Hashtag and emoji support
- 280-character limit enforcement

### 4. **Automated Scheduling**
- Hourly/Daily/Weekly posting
- Timezone support
- Enable/disable controls
- Retry logic for failures

### 5. **Post Management**
- Full post history
- Success/failure tracking
- Error logging
- Statistics dashboard

---

## 🔄 How It Works

### Automated Posting Flow

```
1. User configures content settings
   ↓
2. User sets posting schedule
   ↓
3. Scheduler runs at configured time
   ↓
4. AI generates tweet based on config
   ↓
5. Tweet posted to Twitter via OAuth
   ↓
6. Result logged in database
   ↓
7. Repeat at next scheduled time
```

### Manual Posting Flow

```
1. User calls /api/posts/generate
   ↓
2. AI generates tweet immediately
   ↓
3. Tweet posted to Twitter
   ↓
4. Result returned in API response
```

---

## 📊 Database Collections

### users
```javascript
{
  id: "uuid",
  email: "user@example.com",
  password: "hashed_password",
  name: "User Name",
  created_at: "ISO timestamp"
}
```

### twitter_accounts
```javascript
{
  user_id: "uuid",
  twitter_id: "123456789",
  screen_name: "username",
  name: "Display Name",
  profile_image_url: "https://...",
  oauth_token: "encrypted_token",
  oauth_token_secret: "encrypted_secret",
  connected_at: "ISO timestamp"
}
```

### content_configs
```javascript
{
  id: "uuid",
  user_id: "uuid",
  topic: "AI and Technology",
  tone: "professional",
  length: "medium",
  hashtags: true,
  emojis: false,
  created_at: "ISO timestamp",
  updated_at: "ISO timestamp"
}
```

### schedules
```javascript
{
  id: "uuid",
  user_id: "uuid",
  frequency: "daily",
  time_of_day: "09:00",
  timezone: "UTC",
  enabled: true,
  created_at: "ISO timestamp",
  updated_at: "ISO timestamp"
}
```

### posts
```javascript
{
  id: "uuid",
  user_id: "uuid",
  content: "Tweet text...",
  twitter_id: "1234567890",  // null if failed
  status: "success",          // or "failed"
  error_message: null,        // or error string
  created_at: "ISO timestamp",
  posted_at: "ISO timestamp"  // null if failed
}
```

---

## 🔐 Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ Token expiration (24 hours)
- ✅ OAuth token encryption
- ✅ CORS configuration
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (MongoDB)
- ✅ Rate limit awareness

---

## 🧪 Testing

### Manual Testing with cURL

See [`API_REFERENCE.md`](/app/backend/API_REFERENCE.md) for complete testing examples.

### Quick Test Script

```bash
#!/bin/bash

# Sign up and get token
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test"}' \
  | jq -r '.access_token')

# Create content config
curl -X POST http://localhost:8001/api/content-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Technology",
    "tone": "professional",
    "length": "medium",
    "hashtags": true,
    "emojis": false
  }'

echo "✅ Setup complete! Token: $TOKEN"
```

---

## 📈 Scaling Considerations

### Current Implementation (MVP)
- ✅ Single server
- ✅ APScheduler (in-memory)
- ✅ Cron-based scheduling

### Production Scaling
- 🔄 Use BullMQ + Redis for distributed job queue
- 🔄 Horizontal scaling with load balancer
- 🔄 Database replication
- 🔄 API rate limiting
- 🔄 Caching layer (Redis)
- 🔄 Monitoring (Prometheus + Grafana)

---

## 💰 Cost Estimation

### Per User (Monthly)
| Service | Usage | Cost |
|---------|-------|------|
| MongoDB Atlas | 1GB storage | $0 (Free tier) |
| OpenAI API | 1000 tweets | ~$7.50 |
| Twitter API | Free tier | $0 |
| **Total** | | **~$7.50/user/month** |

### At Scale (1000 users)
- **Monthly Cost:** ~$7,500
- **Revenue Target:** $15-20/user/month = $15-20k MRR
- **Profit Margin:** ~50-60%

---

## 🚨 Troubleshooting

### Backend won't start
```bash
# Check logs
tail -f /var/log/supervisor/backend.err.log

# Check if MongoDB is running
pgrep -f mongod

# Restart backend
sudo supervisorctl restart backend
```

### OpenAI API errors
```bash
# Verify API key is set
grep OPENAI_API_KEY /app/backend/.env

# Test key validity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY_HERE"
```

### Twitter OAuth not working
- Verify callback URL matches Twitter app settings
- Check Twitter API credentials in `.env`
- Ensure Twitter app has read/write permissions

---

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_URL` | Yes | - | MongoDB connection string |
| `DB_NAME` | Yes | - | Database name |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `TWITTER_CLIENT_ID` | Yes | - | Twitter OAuth client ID |
| `TWITTER_CLIENT_SECRET` | Yes | - | Twitter OAuth client secret |
| `JWT_SECRET` | Yes | - | Secret for JWT signing |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins |

---

## 🎯 Roadmap

### ✅ Phase 1 (Complete)
- User authentication
- Twitter OAuth integration
- AI tweet generation (OpenAI SDK)
- Basic scheduling
- Post tracking

### 🔄 Phase 2 (Future)
- [ ] Frontend dashboard (Next.js)
- [ ] Multi-platform support (LinkedIn, Facebook)
- [ ] Advanced analytics
- [ ] Team/agency features
- [ ] Content calendar view
- [ ] A/B testing for content

### 🔮 Phase 3 (Future)
- [ ] Image generation integration
- [ ] Thread/carousel support
- [ ] Sentiment analysis
- [ ] Engagement tracking
- [ ] Payment integration (Stripe)
- [ ] White-label options

---

## 🤝 Contributing

This is a private SaaS project. For internal development:

1. Create feature branch from `main`
2. Make changes and test thoroughly
3. Submit PR with description
4. Get review approval
5. Merge to `main`

---

## 📄 License

Proprietary - All rights reserved

---

## 🆘 Support

For issues or questions:

1. Check [`IMPLEMENTATION_GUIDE.md`](/app/backend/IMPLEMENTATION_GUIDE.md) for troubleshooting
2. Review [`API_REFERENCE.md`](/app/backend/API_REFERENCE.md) for API usage
3. Check logs: `tail -f /var/log/supervisor/backend.err.log`

---

## ✅ Checklist for Deployment

- [ ] Add OpenAI API key to `.env`
- [ ] Add Twitter API credentials to `.env`
- [ ] Change `JWT_SECRET` to a secure random string
- [ ] Update `CORS_ORIGINS` to your frontend domain
- [ ] Set `MONGO_URL` to production MongoDB
- [ ] Verify backend is running: `sudo supervisorctl status backend`
- [ ] Test all API endpoints
- [ ] Monitor logs for errors
- [ ] Set up backup strategy for MongoDB
- [ ] Configure monitoring/alerts

---

**Built with ❤️ using FastAPI, OpenAI, and modern Python practices**

🎉 **Ready to automate Twitter content at scale!**
