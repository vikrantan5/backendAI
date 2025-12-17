from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
from requests_oauthlib import OAuth1

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# OAuth Configuration
config = Config(environ=os.environ)
oauth = OAuth(config)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize scheduler
scheduler = AsyncIOScheduler()

# ===== Models =====
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TwitterAccountResponse(BaseModel):
    twitter_id: str
    screen_name: str
    name: str
    profile_image_url: str
    connected_at: str

class ContentConfigCreate(BaseModel):
    topic: str
    tone: str = "professional"
    length: str = "medium"
    hashtags: bool = True
    emojis: bool = False

class ContentConfigResponse(BaseModel):
    id: str
    topic: str
    tone: str
    length: str
    hashtags: bool
    emojis: bool
    created_at: str
    updated_at: str

class ScheduleCreate(BaseModel):
    frequency: str
    time_of_day: str
    timezone: str = "UTC"
    enabled: bool = True

class ScheduleResponse(BaseModel):
    id: str
    frequency: str
    time_of_day: str
    timezone: str
    enabled: bool
    created_at: str
    updated_at: str

class PostResponse(BaseModel):
    id: str
    content: str
    twitter_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: str
    posted_at: Optional[str] = None

class StatsResponse(BaseModel):
    total_posts: int
    successful_posts: int
    failed_posts: int
    scheduled_posts: int

# ===== Utility Functions =====
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===== AI Tweet Generation =====
async def generate_tweet(content_config: dict, user_id: str) -> str:
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    length_map = {
        "short": "50-100 characters",
        "medium": "100-200 characters",
        "long": "200-280 characters"
    }
    
    system_message = f"You are an expert social media content creator. Generate engaging tweets that are exactly within Twitter's 280 character limit."
    
    user_prompt = f"""Generate a tweet about: {content_config['topic']}
    
Tone: {content_config['tone']}
Length: {length_map.get(content_config['length'], 'medium')}
Include hashtags: {'Yes' if content_config.get('hashtags') else 'No'}
Include emojis: {'Yes' if content_config.get('emojis') else 'No'}

Rules:
1. Must be under 280 characters
2. Be engaging and authentic
3. No quotes around the tweet
4. Just return the tweet text, nothing else"""
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"tweet_gen_{user_id}_{datetime.now(timezone.utc).isoformat()}",
        system_message=system_message
    ).with_model("openai", "gpt-5.1")
    
    user_message = UserMessage(text=user_prompt)
    response = await chat.send_message(user_message)
    
    tweet = response.strip()
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    
    return tweet

# ===== Twitter API Functions =====
def post_tweet_to_twitter(oauth_token: str, oauth_token_secret: str, tweet_text: str) -> dict:
    consumer_key = os.environ.get('TWITTER_CLIENT_ID')
    consumer_secret = os.environ.get('TWITTER_CLIENT_SECRET')
    
    if not consumer_key or not consumer_secret:
        raise HTTPException(status_code=500, detail="Twitter API credentials not configured")
    
    auth = OAuth1(consumer_key, consumer_secret, oauth_token, oauth_token_secret)
    url = "https://api.twitter.com/2/tweets"
    
    payload = {"text": tweet_text}
    response = requests.post(url, json=payload, auth=auth)
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Twitter API error: {response.text}")

# ===== Scheduled Job Function =====
async def process_scheduled_posts():
    try:
        schedules = await db.schedules.find({"enabled": True}, {"_id": 0}).to_list(None)
        
        for schedule in schedules:
            user_id = schedule['user_id']
            
            twitter_account = await db.twitter_accounts.find_one({"user_id": user_id}, {"_id": 0})
            if not twitter_account:
                continue
            
            content_config = await db.content_configs.find_one({"user_id": user_id}, {"_id": 0})
            if not content_config:
                continue
            
            try:
                tweet_text = await generate_tweet(content_config, user_id)
                
                try:
                    twitter_response = post_tweet_to_twitter(
                        twitter_account['oauth_token'],
                        twitter_account['oauth_token_secret'],
                        tweet_text
                    )
                    
                    post_doc = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "content": tweet_text,
                        "twitter_id": twitter_response['data']['id'],
                        "status": "success",
                        "error_message": None,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "posted_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.posts.insert_one(post_doc)
                    
                except Exception as twitter_error:
                    post_doc = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "content": tweet_text,
                        "twitter_id": None,
                        "status": "failed",
                        "error_message": str(twitter_error),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "posted_at": None
                    }
                    await db.posts.insert_one(post_doc)
                    
            except Exception as gen_error:
                logging.error(f"Tweet generation error for user {user_id}: {gen_error}")
                
    except Exception as e:
        logging.error(f"Scheduled post processing error: {e}")

# ===== Auth Routes =====
@api_router.post("/auth/signup", response_model=TokenResponse)
async def signup(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hashed_pw,
        "name": user_data.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_jwt_token(user_id, user_data.email)
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        created_at=user_doc["created_at"]
    )
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"], user["email"])
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"]
    )
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        created_at=current_user["created_at"]
    )

# ===== Twitter OAuth Routes =====
@api_router.get("/twitter/auth-url")
async def get_twitter_auth_url(current_user: dict = Depends(get_current_user)):
    consumer_key = os.environ.get('TWITTER_CLIENT_ID')
    consumer_secret = os.environ.get('TWITTER_CLIENT_SECRET')
    
    if not consumer_key or not consumer_secret:
        raise HTTPException(status_code=500, detail="Twitter API credentials not configured. Please set TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET in .env file.")
    
    callback_url = "https://x-content-hub-2.preview.emergentagent.com/twitter-callback"
    
    auth = OAuth1(consumer_key, consumer_secret, callback_uri=callback_url)
    request_token_url = "https://api.twitter.com/oauth/request_token"
    
    try:
        response = requests.post(request_token_url, auth=auth)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to get request token: {response.text}")
        
        credentials = dict(item.split('=') for item in response.text.split('&'))
        oauth_token = credentials.get('oauth_token')
        oauth_token_secret = credentials.get('oauth_token_secret')
        
        await db.twitter_temp_tokens.insert_one({
            "user_id": current_user["id"],
            "oauth_token": oauth_token,
            "oauth_token_secret": oauth_token_secret,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        auth_url = f"https://api.twitter.com/oauth/authenticate?oauth_token={oauth_token}"
        return {"auth_url": auth_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter OAuth error: {str(e)}")

@api_router.post("/twitter/callback")
async def twitter_callback(oauth_token: str, oauth_verifier: str, current_user: dict = Depends(get_current_user)):
    consumer_key = os.environ.get('TWITTER_CLIENT_ID')
    consumer_secret = os.environ.get('TWITTER_CLIENT_SECRET')
    
    temp_token = await db.twitter_temp_tokens.find_one({"oauth_token": oauth_token}, {"_id": 0})
    if not temp_token:
        raise HTTPException(status_code=400, detail="Invalid OAuth token")
    
    auth = OAuth1(
        consumer_key,
        consumer_secret,
        temp_token['oauth_token'],
        temp_token['oauth_token_secret'],
        verifier=oauth_verifier
    )
    
    access_token_url = "https://api.twitter.com/oauth/access_token"
    response = requests.post(access_token_url, auth=auth)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token")
    
    credentials = dict(item.split('=') for item in response.text.split('&'))
    
    auth = OAuth1(
        consumer_key,
        consumer_secret,
        credentials['oauth_token'],
        credentials['oauth_token_secret']
    )
    
    user_info_response = requests.get(
        "https://api.twitter.com/1.1/account/verify_credentials.json",
        auth=auth
    )
    
    if user_info_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to verify credentials")
    
    twitter_user = user_info_response.json()
    
    twitter_account_doc = {
        "user_id": current_user["id"],
        "twitter_id": twitter_user['id_str'],
        "screen_name": twitter_user['screen_name'],
        "name": twitter_user['name'],
        "profile_image_url": twitter_user['profile_image_url_https'],
        "oauth_token": credentials['oauth_token'],
        "oauth_token_secret": credentials['oauth_token_secret'],
        "connected_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.twitter_accounts.delete_many({"user_id": current_user["id"]})
    await db.twitter_accounts.insert_one(twitter_account_doc)
    await db.twitter_temp_tokens.delete_many({"oauth_token": oauth_token})
    
    return TwitterAccountResponse(
        twitter_id=twitter_account_doc["twitter_id"],
        screen_name=twitter_account_doc["screen_name"],
        name=twitter_account_doc["name"],
        profile_image_url=twitter_account_doc["profile_image_url"],
        connected_at=twitter_account_doc["connected_at"]
    )

@api_router.get("/twitter/account", response_model=TwitterAccountResponse)
async def get_twitter_account(current_user: dict = Depends(get_current_user)):
    account = await db.twitter_accounts.find_one({"user_id": current_user["id"]}, {"_id": 0, "oauth_token": 0, "oauth_token_secret": 0})
    if not account:
        raise HTTPException(status_code=404, detail="No Twitter account connected")
    
    return TwitterAccountResponse(**account)

@api_router.delete("/twitter/disconnect")
async def disconnect_twitter(current_user: dict = Depends(get_current_user)):
    result = await db.twitter_accounts.delete_many({"user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No Twitter account connected")
    return {"message": "Twitter account disconnected successfully"}

# ===== Content Config Routes =====
@api_router.post("/content-config", response_model=ContentConfigResponse)
async def create_content_config(config: ContentConfigCreate, current_user: dict = Depends(get_current_user)):
    config_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    config_doc = {
        "id": config_id,
        "user_id": current_user["id"],
        **config.model_dump(),
        "created_at": now,
        "updated_at": now
    }
    
    await db.content_configs.delete_many({"user_id": current_user["id"]})
    await db.content_configs.insert_one(config_doc)
    
    return ContentConfigResponse(**{k: v for k, v in config_doc.items() if k != "user_id"})

@api_router.get("/content-config", response_model=ContentConfigResponse)
async def get_content_config(current_user: dict = Depends(get_current_user)):
    config = await db.content_configs.find_one({"user_id": current_user["id"]}, {"_id": 0, "user_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="No content configuration found")
    return ContentConfigResponse(**config)

# ===== Schedule Routes =====
@api_router.post("/schedule", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, current_user: dict = Depends(get_current_user)):
    schedule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    schedule_doc = {
        "id": schedule_id,
        "user_id": current_user["id"],
        **schedule.model_dump(),
        "created_at": now,
        "updated_at": now
    }
    
    await db.schedules.delete_many({"user_id": current_user["id"]})
    await db.schedules.insert_one(schedule_doc)
    
    return ScheduleResponse(**{k: v for k, v in schedule_doc.items() if k != "user_id"})

@api_router.get("/schedule", response_model=ScheduleResponse)
async def get_schedule(current_user: dict = Depends(get_current_user)):
    schedule = await db.schedules.find_one({"user_id": current_user["id"]}, {"_id": 0, "user_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found")
    return ScheduleResponse(**schedule)

@api_router.patch("/schedule/toggle")
async def toggle_schedule(enabled: bool, current_user: dict = Depends(get_current_user)):
    result = await db.schedules.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"enabled": enabled, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No schedule found")
    
    return {"message": f"Automation {'enabled' if enabled else 'disabled'} successfully", "enabled": enabled}

# ===== Post Routes =====
@api_router.post("/posts/generate", response_model=PostResponse)
async def generate_test_post(current_user: dict = Depends(get_current_user)):
    twitter_account = await db.twitter_accounts.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not twitter_account:
        raise HTTPException(status_code=400, detail="No Twitter account connected")
    
    content_config = await db.content_configs.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not content_config:
        raise HTTPException(status_code=400, detail="No content configuration found")
    
    try:
        tweet_text = await generate_tweet(content_config, current_user["id"])
        
        try:
            twitter_response = post_tweet_to_twitter(
                twitter_account['oauth_token'],
                twitter_account['oauth_token_secret'],
                tweet_text
            )
            
            post_doc = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "content": tweet_text,
                "twitter_id": twitter_response['data']['id'],
                "status": "success",
                "error_message": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "posted_at": datetime.now(timezone.utc).isoformat()
            }
            await db.posts.insert_one(post_doc)
            
            return PostResponse(**{k: v for k, v in post_doc.items() if k != "user_id"})
            
        except Exception as twitter_error:
            post_doc = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "content": tweet_text,
                "twitter_id": None,
                "status": "failed",
                "error_message": str(twitter_error),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "posted_at": None
            }
            await db.posts.insert_one(post_doc)
            
            return PostResponse(**{k: v for k, v in post_doc.items() if k != "user_id"})
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tweet: {str(e)}")

@api_router.get("/posts", response_model=List[PostResponse])
async def get_posts(limit: int = 50, current_user: dict = Depends(get_current_user)):
    posts = await db.posts.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "user_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(None)
    
    return [PostResponse(**post) for post in posts]

@api_router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: dict = Depends(get_current_user)):
    total_posts = await db.posts.count_documents({"user_id": current_user["id"]})
    successful_posts = await db.posts.count_documents({"user_id": current_user["id"], "status": "success"})
    failed_posts = await db.posts.count_documents({"user_id": current_user["id"], "status": "failed"})
    
    schedule = await db.schedules.find_one({"user_id": current_user["id"], "enabled": True}, {"_id": 0})
    scheduled_posts = 1 if schedule else 0
    
    return StatsResponse(
        total_posts=total_posts,
        successful_posts=successful_posts,
        failed_posts=failed_posts,
        scheduled_posts=scheduled_posts
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(
        process_scheduled_posts,
        CronTrigger(hour='*', minute=0),
        id='scheduled_posts',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    client.close()
    logger.info("Application shutdown")