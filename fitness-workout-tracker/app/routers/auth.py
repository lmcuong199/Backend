from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut
from app.security import create_access_token, hash_password, verify_password

# APIRouter is a group of related endpoints
# prefix="/auth" gets glued onto the front of every path below
# tags=["auth"] groups them under an "auth" heading on the /docs page
router = APIRouter(prefix="/auth", tags=["auth"])

# /auth/signup
# response_model=UserOut filters the response through the schema. 
# This is the line that guarantees hashed_password never escapes
# 201: created - the correct code when a request makes a new resource
@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    # build the database object
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    # stage it. Nothing has hit the database yet
    db.add(user)
    # actually write it. Permanently
    db.commit()
    # re-read the row back from the database
    db.refresh(user)
    return user

# /auth/login
@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return Token(access_token=create_access_token(user.id))

# /auth/me
@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

# /auth/logout
@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"detail": "Logged out. Discard your access token."}
