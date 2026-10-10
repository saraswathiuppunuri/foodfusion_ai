from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.permissions import get_current_user
from app.models.entities import User, UserRole
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserOut, UserProfileUpdate

router = APIRouter(prefix="/auth", tags=["Authentication & Profiles"])

@router.post("/register", response_model=TokenResponse)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Registers a new user with role assignment and returns JWT access token."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    # Validate role
    role = user_in.role.lower()
    valid_roles = [r.value for r in UserRole]
    if role not in valid_roles:
        role = UserRole.CUSTOMER.value

    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=role,
        phone=user_in.phone,
        dietary_preference=user_in.dietary_preference or "none",
        spice_preference=user_in.spice_preference or "medium"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        name=user.name
    )

@router.post("/login", response_model=TokenResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """Authenticates user credentials and issues a signed JWT token."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        name=user.name
    )

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile and declared dietary habits."""
    return current_user

@router.put("/me", response_model=UserOut)
def update_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user preferences (dietary, spice, budget, favorite cuisines)."""
    if profile_in.name is not None:
        current_user.name = profile_in.name
    if profile_in.phone is not None:
        current_user.phone = profile_in.phone
    if profile_in.dietary_preference is not None:
        current_user.dietary_preference = profile_in.dietary_preference
    if profile_in.spice_preference is not None:
        current_user.spice_preference = profile_in.spice_preference
    if profile_in.preferred_cuisines is not None:
        current_user.preferred_cuisines = profile_in.preferred_cuisines
    if profile_in.avg_budget is not None:
        current_user.avg_budget = profile_in.avg_budget

    db.commit()
    db.refresh(current_user)
    return current_user
