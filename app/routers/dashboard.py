
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)


@router.get("/redirect")
async def dashboard_redirect(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "Dashboard access granted",
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified
        },
        "redirect_url": "/dashboard/student",
        "dashboard": "student"
    }
