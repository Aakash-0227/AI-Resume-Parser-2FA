
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.resume import router as resume_router
from app.routers.users import router as users_router
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.profile import router as profile_router


app = FastAPI(
    title="AI Resume Parser and 2FA Onboarding API",
    description="Resume parsing and secure user onboarding system",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(resume_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(profile_router)


@app.get("/")
async def root():
    return {
        "message": "AI Resume Parser and 2FA Onboarding API is running",
        "status": "success"
    }
