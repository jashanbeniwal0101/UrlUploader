from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import MONGODB_URI, DB_NAME, DEFAULT_UPLOAD_MODE, DEFAULT_SPLIT_SETTING
from bot.config import DEFAULT_CAPTION_ENABLED, DEFAULT_THUMBNAIL_GENERATION, DEFAULT_GENERATE_SCREENSHOTS, DEFAULT_SAMPLE_VIDEO
import datetime
import logging
from datetime import timedelta
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGODB_URI)
        self.db = self.client[DB_NAME]
        self.users = self.db["users"]
        self.urls = self.db["urls"]
        self.daily_tasks = self.db["daily_tasks"]
        logger.info("Database connection established")
        
    async def initialize(self):
        """Asynchronous initialization method to create indexes."""
        await self.create_indexes()

    async def create_indexes(self):
        """Create indexes for users and urls collections."""
        await self.users.create_index("user_id", unique=True)
        await self.urls.create_index("url_id", unique=True)  
        await self.daily_tasks.create_index([("user_id", 1), ("date", 1)], unique=True)

    async def add_user(self, user_id, username=None):
        """Add new user to database or update existing user"""
        user_data = {
            "user_id": user_id,
            "username": username,
            "upload_mode": DEFAULT_UPLOAD_MODE,
            "split_enabled": DEFAULT_SPLIT_SETTING,
            "caption": None,
            "caption_enabled": DEFAULT_CAPTION_ENABLED,
            "thumbnail": None,
            "generate_screenshots": DEFAULT_GENERATE_SCREENSHOTS,
            "generate_sample_video": DEFAULT_SAMPLE_VIDEO,
            "banned": False,
            "is_paid": False,
            "subscription_start": None,
            "paid_expiry": None
        }
        
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
            logger.info(f"User {user_id} added/updated")
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    async def get_user(self, user_id):
        """Get user data from database and check paid status expiry"""
        user_data = await self.users.find_one({"user_id": user_id})
        
        if user_data and user_data.get("is_paid", False) and "paid_expiry" in user_data:
            # Check if paid status has expired
            if user_data["paid_expiry"] < datetime.datetime.now():
                # If expired, update the paid status to False
                await self.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"is_paid": False}}
                )
                user_data["is_paid"] = False
                logger.info(f"User {user_id} paid subscription has expired and been updated")
        
        return user_data
    
    async def update_user_settings(self, user_id, settings):
        """Update user settings"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": settings}
            )
            logger.info(f"Updated settings for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False
    
    async def ban_user(self, user_id, banned=True):
        """Ban or unban a user"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"banned": banned}}
            )
            logger.info(f"User {user_id} {'banned' if banned else 'unbanned'}")
            return True
        except Exception as e:
            logger.error(f"Error changing ban status: {e}")
            return False
    
    async def set_paid_status(self, user_id, is_paid=True, expiry_date=None):
        """
        Set user paid status with optional expiry date
        
        Parameters:
        - user_id: The ID of the user
        - is_paid: Boolean indicating paid status
        - expiry_date: Datetime object for when the paid status expires
        """
        try:
            update_data = {
                "is_paid": is_paid,
                "subscription_start": datetime.datetime.now() if is_paid else None
            }
            
            # Add expiry date if provided
            if expiry_date:
                update_data["paid_expiry"] = expiry_date
            
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            logger.info(f"User {user_id} paid status set to {is_paid}" + 
                        (f" with expiry {expiry_date}" if expiry_date else ""))
            return True
        except Exception as e:
            logger.error(f"Error setting paid status: {e}")
            return False
    
    async def get_subscription_details(self, user_id):
        """Get user subscription details including days remaining"""
        user_data = await self.get_user(user_id)
        
        if not user_data:
            return None
            
        subscription = {
            "is_paid": user_data.get("is_paid", False),
            "subscription_start": user_data.get("subscription_start"),
            "expiry_date": user_data.get("paid_expiry"),
            "days_remaining": 0
        }
        
        if subscription["is_paid"] and subscription["expiry_date"]:
            now = datetime.datetime.now()
            if subscription["expiry_date"] > now:
                delta = subscription["expiry_date"] - now
                subscription["days_remaining"] = delta.days
        
        return subscription
    
    async def set_thumbnail(self, user_id, file_id):
        """Set user thumbnail"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"thumbnail": file_id}}
            )
            logger.info(f"Thumbnail set for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}")
            return False
            
    async def set_caption(self, user_id, caption):
        """Set user caption"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"caption": caption}}
            )
            logger.info(f"Caption set for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting caption: {e}")
            return False
    
    async def delete_caption(self, user_id):
        """Delete user caption"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"caption": None, "caption_enabled": False}}
            )
            logger.info(f"Caption deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting caption: {e}")
            return False
    
    async def get_all_users(self):
        """Get all users"""
        return [user async for user in self.users.find({})]
    
    async def get_banned_users(self):
        """Get all banned users"""
        return [user async for user in self.users.find({"banned": True})]
    
    async def get_paid_users(self):
        """Get all paid users with valid subscriptions"""
        now = datetime.datetime.now()
        
        # First, get all users that are marked as paid
        paid_users = [user async for user in self.users.find({"is_paid": True})]
        
        # Filter out expired users and update their status
        valid_paid_users = []
        for user in paid_users:
            if "paid_expiry" in user and user["paid_expiry"] < now:
                # Update expired status
                await self.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {"is_paid": False}}
                )
                logger.info(f"User {user['user_id']} paid subscription has expired and been updated")
            else:
                valid_paid_users.append(user)
        
        return valid_paid_users
    
    async def store_url(self, url_id, url, user_id, status="pending"):
        """Store URL in database"""
        url_data = {
            "url_id": url_id,
            "url": url,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.datetime.now()
        }
        
        try:
            await self.urls.update_one(
                {"url_id": url_id},
                {"$set": url_data},
                upsert=True
            )
            logger.info(f"URL {url_id} stored")
            return True
        except Exception as e:
            logger.error(f"Error storing URL: {e}")
            return False
    
    async def update_url_status(self, url_id, status):
        """Update URL status"""
        try:
            await self.urls.update_one(
                {"url_id": url_id},
                {"$set": {"status": status}}
            )
            logger.info(f"URL {url_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating URL status: {e}")
            return False

    async def track_daily_task(self, user_id):
        """Track a task for daily limit purposes"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            # Try to update an existing record for today
            result = await self.daily_tasks.update_one(
                {"user_id": user_id, "date": today},
                {"$inc": {"count": 1}},
                upsert=True
            )
            
            # If inserted a new document, return 1 as the count
            if result.upserted_id:
                logger.info(f"First task of the day for user {user_id}")
                return 1
                
            # Otherwise, get the current count
            task_data = await self.daily_tasks.find_one({"user_id": user_id, "date": today})
            count = task_data.get("count", 0)
            logger.info(f"User {user_id} has used {count} tasks today")
            return count
            
        except Exception as e:
            logger.error(f"Error tracking daily task: {e}")
            return -1  # Error code
    
    async def get_daily_task_count(self, user_id):
        """Get the number of tasks used today by a user"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            task_data = await self.daily_tasks.find_one({"user_id": user_id, "date": today})
            if task_data:
                return task_data.get("count", 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting daily task count: {e}")
            return 0
    
    async def get_url(self, url_id):
        """Get URL data"""
        return await self.urls.find_one({"url_id": url_id})
    
    async def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("Database connection closed")
