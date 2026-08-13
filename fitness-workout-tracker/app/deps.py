# This file is the gate. 
# Every protected endpoint in your app will lean on this one function to answer:
# who is making this request, and are they allowed in?
# ------------------------------------------------------------------------------

# HTTPException: raise this to send an error response back to the client
# status: named constants like status.HTTP_401_UNAUTHORIZED instead of the bare number 401 -> more readable
from fastapi import Depends, HTTPException, status
# HTTPBearer: pulls the token out of the Authorization header for you
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# Session: a SQLAlchemy database session; used here only as a type hint
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

# auto_error=False: if the header is missing, don't raise, just give me None and let me handle it
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    invalid = HTTPException(
        # I don't know who you are
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise invalid

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise invalid

    user = db.get(User, user_id)
    if user is None:
        raise invalid

    return user
