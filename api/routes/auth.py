import re
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import RegisterRequest, LoginRequest, UserOut
from ..auth_utils import hash_password, verify_password, create_jwt
from ..deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user = User(
        email=req.email,
        name=req.name,
        password_hash=hash_password(req.password),
        auth_provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=UserOut)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash or ""):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_jwt({"user_id": user.id})
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
