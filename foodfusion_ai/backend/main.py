from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data import seed_database

# Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.restaurants import router as restaurants_router
from app.api.v1.cart import router as cart_router
from app.api.v1.orders import router as orders_router
from app.api.v1.recommendations import router as recs_router
from app.api.v1.budget_planner import router as budget_router
from app.api.v1.surplus import router as surplus_router
from app.api.v1.group_orders import router as group_router
from app.api.v1.ai_assistant import router as ai_chat_router
from app.api.v1.restaurant_dashboard import router as rest_admin_router
from app.api.v1.delivery_dashboard import router as delivery_router
from app.api.v1.admin_dashboard import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables and seed realistic production-grade data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="FoodFusion AI — Smart Food Ordering & Sustainable Delivery",
    description="Advanced AI-powered food ordering platform with explainable recommendations, smart budget meal planner, zero-waste surplus marketplace, group ordering, and predictive kitchen analytics.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=prefix)
app.include_router(restaurants_router, prefix=prefix)
app.include_router(cart_router, prefix=prefix)
app.include_router(orders_router, prefix=prefix)
app.include_router(recs_router, prefix=prefix)
app.include_router(budget_router, prefix=prefix)
app.include_router(surplus_router, prefix=prefix)
app.include_router(group_router, prefix=prefix)
app.include_router(ai_chat_router, prefix=prefix)
app.include_router(rest_admin_router, prefix=prefix)
app.include_router(delivery_router, prefix=prefix)
app.include_router(admin_router, prefix=prefix)

@app.get("/")
def root():
    return {
        "app": "FoodFusion AI",
        "status": "online",
        "documentation": "/docs",
        "version": "1.0.0",
        "message": "Welcome to FoodFusion AI backend. Complete REST APIs ready."
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "foodfusion-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
