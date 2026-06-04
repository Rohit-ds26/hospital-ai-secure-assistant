from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os

from models import SessionLocal, User


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "hospital-dev-secret")
JWT_ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = creds.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    role = payload.get("role")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != role:
        raise HTTPException(status_code=401, detail="Role mismatch")

    return user


def get_optional_current_user(
    creds: HTTPAuthorizationCredentials = Depends(optional_security),
    db: Session = Depends(get_db)
):
    if not creds:
        return None

    return get_current_user(creds=creds, db=db)
