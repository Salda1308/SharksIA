import re
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import RegisterRequest, LoginRequest, UserOut
from ..auth_utils import hash_password, verify_password, create_jwt
from ..deps import get_current_user

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/v1/auth/google/callback"

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


@router.get("/google")
def google_login():
    params = (
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid+email+profile"
    )
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
def google_callback(code: str, response: Response, db: Session = Depends(get_db)):
    token_res = httpx.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Error en OAuth de Google")

    access = token_res.json().get("access_token")
    profile_res = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access}"},
    )
    profile = profile_res.json()
    email = profile.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No se pudo obtener email de Google")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=profile.get("name"),
            avatar_url=profile.get("picture"),
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_jwt({"user_id": user.id})
    redirect = RedirectResponse(url="http://localhost:3000/dashboard")
    redirect.set_cookie("access_token", token, httponly=True, samesite="lax")
    return redirect
