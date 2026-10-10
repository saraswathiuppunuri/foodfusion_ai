import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings:
    PROJECT_NAME: str = "FoodFusion AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "foodfusion-super-secret-jwt-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SQLite default with clean PostgreSQL migration path
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{os.path.join(BASE_DIR, 'foodfusion.db')}"
    )
    
    # CORS
    ALLOWED_ORIGINS: list = ["*"]
    
    # Demo credentials
    ADMIN_EMAIL: str = "admin@foodfusion.ai"
    ADMIN_PASSWORD: str = "Admin@123"
    
    RESTAURANT_EMAIL: str = "owner@spicevilla.com"
    RESTAURANT_PASSWORD: str = "Owner@123"
    
    DELIVERY_EMAIL: str = "rider@foodfusion.ai"
    DELIVERY_PASSWORD: str = "Rider@123"
    
    CUSTOMER_EMAIL: str = "customer@foodfusion.ai"
    CUSTOMER_PASSWORD: str = "Customer@123"

settings = Settings()
