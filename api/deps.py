import os
from fastapi import Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .auth_utils import decode_jwt

LOCAL_USER_ID = "local"


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if access_token is None:
        user = db.query(User).filter(User.id == LOCAL_USER_ID).first()
        if not user:
            user = User(
                id=LOCAL_USER_ID,
                email="local@localhost",
                name="Local User",
                plan="ultra",
                auth_provider="email",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    payload = decode_jwt(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
