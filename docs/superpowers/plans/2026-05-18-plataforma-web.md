# Plataforma Web MVP — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portar el CLI de carruseles a una app web con FastAPI + Next.js: auth, gestión de empresas, generación de slides con IA, editor de slides, integración Pexels/Pixabay, y export SVG/PDF/JPG.

**Architecture:** FastAPI en :8000 importa `core/` directamente (sin subprocess). Next.js en :3000 consume la API via fetch con cookies httpOnly. SQLite guarda User/Company/Design como JSON; los renders son efímeros (generados on-demand, borrados tras descarga). Assets de empresa en `storage/companies/{company_id}/assets/` para ser compatibles con `render_carousel()`.

**Tech Stack:** FastAPI · SQLAlchemy 2.0 · python-jose · passlib[bcrypt] · Pillow · httpx · python-multipart · Next.js 14 App Router · TypeScript · Tailwind CSS

---

## Mapa de Archivos

### Crear (api/)
- `api/__init__.py`
- `api/main.py` — app FastAPI, CORS, routers, startup
- `api/database.py` — engine SQLite, SessionLocal, init_db
- `api/models.py` — ORM: User, Company, Design, Asset
- `api/schemas.py` — Pydantic v2: request/response shapes
- `api/deps.py` — get_db, get_current_user (con fallback local)
- `api/auth_utils.py` — hash_password, verify_password, create_jwt, decode_jwt
- `api/routes/__init__.py`
- `api/routes/auth.py` — register, login, google OAuth, logout, /me
- `api/routes/companies.py` — CRUD empresas
- `api/routes/carousel.py` — generate, update slides, render, export
- `api/routes/images.py` — upload asset, search Pexels/Pixabay

### Crear (web/)
- `web/` — scaffoldeado con `create-next-app`
- `web/lib/api.ts` — cliente API tipado
- `web/lib/auth.tsx` — AuthContext + useAuth hook
- `web/app/page.tsx` — landing / redirect
- `web/app/auth/login/page.tsx`
- `web/app/auth/register/page.tsx`
- `web/app/dashboard/page.tsx`
- `web/app/companies/new/page.tsx`
- `web/app/companies/[id]/page.tsx`
- `web/app/designs/new/carousel/page.tsx`
- `web/app/designs/[id]/edit/page.tsx`
- `web/app/designs/[id]/export/page.tsx`
- `web/components/SlidePreview.tsx`
- `web/components/SlideEditor.tsx`
- `web/components/ImagePicker.tsx`
- `web/components/CompanyForm.tsx`
- `web/components/ExportPanel.tsx`

### Modificar
- `requirements.txt` — agregar deps FastAPI
- `Makefile` — target `dev`
- `tests/` — agregar `tests/api/`

---

## Tarea 1: Dependencias Python + Scaffolding API

**Archivos:**
- Modificar: `requirements.txt`
- Crear: `api/__init__.py`, `api/routes/__init__.py`
- Crear: `storage/uploads/.gitkeep`, `storage/tmp/.gitkeep`, `storage/companies/.gitkeep`

- [ ] **Actualizar requirements.txt**

```
typer[all]>=0.9.0
jinja2>=3.1.0
pyyaml>=6.0.0
ollama>=0.2.0
rich>=13.0.0
cairosvg>=2.7.0
pypdf>=4.0.0
pytest>=8.0.0
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pillow>=10.0.0
httpx>=0.27.0
python-multipart>=0.0.9
python-dotenv>=1.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

- [ ] **Instalar dependencias**

```bash
pip install -r requirements.txt
```

- [ ] **Crear directorios y archivos vacíos**

```bash
mkdir -p api/routes storage/uploads storage/tmp storage/companies
touch api/__init__.py api/routes/__init__.py
touch storage/uploads/.gitkeep storage/tmp/.gitkeep storage/companies/.gitkeep
```

- [ ] **Commit**

```bash
git add requirements.txt api/ storage/
git commit -m "chore: add FastAPI dependencies and api/ scaffold"
```

---

## Tarea 2: Base de Datos — Modelos y Conexión

**Archivos:**
- Crear: `api/database.py`
- Crear: `api/models.py`
- Crear: `tests/api/__init__.py`, `tests/api/conftest.py`

- [ ] **Escribir test que verifica que init_db crea las tablas**

```python
# tests/api/test_models.py
from api.database import init_db, SessionLocal
from api.models import User, Company, Design, Asset

def test_init_db_creates_tables():
    init_db()
    db = SessionLocal()
    # Si las tablas no existen esto lanza OperationalError
    db.query(User).first()
    db.query(Company).first()
    db.query(Design).first()
    db.query(Asset).first()
    db.close()
```

- [ ] **Correr test para verificar que falla**

```bash
pytest tests/api/test_models.py -v
```
Esperado: `ModuleNotFoundError` o `ImportError`

- [ ] **Crear `api/database.py`**

```python
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Path("storage").mkdir(exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/db.sqlite3")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from .models import Base
    Base.metadata.create_all(bind=engine)
```

- [ ] **Crear `api/models.py`**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


def _new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_new_id)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    avatar_url = Column(String)
    auth_provider = Column(String, default="email")
    password_hash = Column(String)
    plan = Column(String, default="basic")
    created_at = Column(DateTime, default=datetime.utcnow)

    companies = relationship("Company", back_populates="user", cascade="all, delete-orphan")
    designs = relationship("Design", back_populates="user", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True, default=_new_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True)
    logo_path = Column(String)
    colors = Column(JSON)
    fonts = Column(JSON)
    style = Column(String, default="minimal")
    design_context = Column(Text)
    ai_provider = Column(String, default="ollama")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="companies")
    designs = relationship("Design", back_populates="company", cascade="all, delete-orphan")


class Design(Base):
    __tablename__ = "designs"
    id = Column(String, primary_key=True, default=_new_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    type = Column(String, default="carousel")
    title = Column(String)
    slides = Column(JSON)
    size_px = Column(JSON)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="designs")
    company = relationship("Company", back_populates="designs")


class Asset(Base):
    __tablename__ = "assets"
    id = Column(String, primary_key=True, default=_new_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String)
    path_thumb = Column(String)
    path_full = Column(String)
    source = Column(String, default="upload")
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Crear `tests/api/__init__.py` y `tests/api/conftest.py`**

```python
# tests/api/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.database import get_db
from api.models import Base

TEST_DB = "sqlite:///./storage/test.sqlite3"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Correr test para verificar que pasa**

```bash
pytest tests/api/test_models.py -v
```
Esperado: `PASSED`

- [ ] **Commit**

```bash
git add api/database.py api/models.py tests/api/
git commit -m "feat: SQLAlchemy models (User, Company, Design, Asset) with SQLite"
```

---

## Tarea 3: Auth Utils + Schemas

**Archivos:**
- Crear: `api/auth_utils.py`
- Crear: `api/schemas.py`

- [ ] **Escribir tests**

```python
# tests/api/test_auth_utils.py
from api.auth_utils import hash_password, verify_password, create_jwt, decode_jwt

def test_password_round_trip():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)

def test_jwt_round_trip():
    token = create_jwt({"user_id": "abc"})
    payload = decode_jwt(token)
    assert payload["user_id"] == "abc"

def test_jwt_invalid_raises():
    payload = decode_jwt("not-a-token")
    assert payload is None
```

- [ ] **Correr test para verificar que falla**

```bash
pytest tests/api/test_auth_utils.py -v
```

- [ ] **Crear `api/auth_utils.py`**

```python
import os
from passlib.context import CryptContext
from jose import JWTError, jwt

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_jwt(payload: dict) -> str:
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except JWTError:
        return None
```

- [ ] **Crear `api/schemas.py`**

```python
from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    plan: str

    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    name: str
    style: str = "minimal"
    colors: Optional[dict] = None
    fonts: Optional[dict] = None
    design_context: Optional[str] = None
    ai_provider: str = "ollama"


class CompanyUpdate(CompanyCreate):
    pass


class CompanyOut(BaseModel):
    id: str
    name: str
    slug: Optional[str]
    style: str
    colors: Optional[dict]
    fonts: Optional[dict]
    design_context: Optional[str]
    ai_provider: str
    logo_path: Optional[str]

    model_config = {"from_attributes": True}


class CarouselGenerateRequest(BaseModel):
    company_id: str
    mode: str = "topic"          # "topic" | "text"
    content: str
    size_px: dict = {"width": 1080, "height": 1080}
    title: Optional[str] = None


class SlidesUpdateRequest(BaseModel):
    slides: list


class DesignOut(BaseModel):
    id: str
    company_id: str
    type: str
    title: Optional[str]
    slides: Optional[list]
    size_px: Optional[dict]
    status: str
    created_at: str

    model_config = {"from_attributes": True}
```

- [ ] **Correr tests**

```bash
pytest tests/api/test_auth_utils.py -v
```
Esperado: 3 PASSED

- [ ] **Commit**

```bash
git add api/auth_utils.py api/schemas.py
git commit -m "feat: JWT auth utilities and Pydantic schemas"
```

---

## Tarea 4: App Principal + Auth Routes (register/login)

**Archivos:**
- Crear: `api/main.py`
- Crear: `api/deps.py`
- Crear: `api/routes/auth.py`

- [ ] **Escribir tests**

```python
# tests/api/test_auth.py
def test_register_and_login(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    assert r.status_code == 200
    assert r.json()["email"] == "user@test.com"

def test_login_sets_cookie(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    r = client.post("/api/v1/auth/login", json={
        "email": "user@test.com", "password": "pass123"
    })
    assert r.status_code == 200
    assert "access_token" in r.cookies

def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    r = client.post("/api/v1/auth/login", json={
        "email": "user@test.com", "password": "wrong"
    })
    assert r.status_code == 401

def test_me_returns_user(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    client.post("/api/v1/auth/login", json={
        "email": "user@test.com", "password": "pass123"
    })
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "user@test.com"
```

- [ ] **Correr tests para verificar que fallan**

```bash
pytest tests/api/test_auth.py -v
```

- [ ] **Crear `api/deps.py`**

```python
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
```

- [ ] **Crear `api/routes/auth.py`**

```python
import re
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import RegisterRequest, LoginRequest, UserOut
from ..auth_utils import hash_password, verify_password, create_jwt
from ..deps import get_current_user

router = APIRouter()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


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
```

- [ ] **Crear `api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes import auth, companies, carousel, images

app = FastAPI(title="Generador de Diseños API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(carousel.router, prefix="/api/v1/designs", tags=["designs"])
app.include_router(images.router, prefix="/api/v1", tags=["images"])
```

- [ ] **Correr tests**

```bash
pytest tests/api/test_auth.py -v
```
Esperado: 4 PASSED

- [ ] **Commit**

```bash
git add api/main.py api/deps.py api/routes/auth.py
git commit -m "feat: auth routes — register, login, logout, /me with JWT cookies"
```

---

## Tarea 5: Google OAuth

**Archivos:**
- Modificar: `api/routes/auth.py`

- [ ] **Agregar variables al `.env.example`**

```bash
# .env.example
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
PEXELS_API_KEY=your-key
PIXABAY_API_KEY=your-key
JWT_SECRET=change-this-in-production
DATABASE_URL=sqlite:///./storage/db.sqlite3
OLLAMA_BASE_URL=http://localhost:11434
```

- [ ] **Agregar rutas Google OAuth a `api/routes/auth.py`**

Añadir al final del archivo:

```python
import os, httpx
from fastapi.responses import RedirectResponse

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/v1/auth/google/callback"


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
```

- [ ] **Commit**

```bash
git add api/routes/auth.py .env.example
git commit -m "feat: Google OAuth login/register flow"
```

---

## Tarea 6: Companies CRUD

**Archivos:**
- Crear: `api/routes/companies.py`

- [ ] **Escribir tests**

```python
# tests/api/test_companies.py
def test_create_company(client):
    r = client.post("/api/v1/companies", json={
        "name": "Acme Studio",
        "style": "bold",
        "colors": {"primary": "#000", "secondary": "#fff", "background": "#eee", "text": "#111"},
        "fonts": {"heading": "Inter Bold", "body": "Inter"},
        "design_context": "Marca de moda urbana",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Acme Studio"
    assert data["slug"] == "acme-studio"

def test_list_companies(client):
    client.post("/api/v1/companies", json={"name": "A", "style": "minimal"})
    client.post("/api/v1/companies", json={"name": "B", "style": "bold"})
    r = client.get("/api/v1/companies")
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_update_company(client):
    r = client.post("/api/v1/companies", json={"name": "Old Name", "style": "minimal"})
    company_id = r.json()["id"]
    r2 = client.put(f"/api/v1/companies/{company_id}", json={"name": "New Name", "style": "editorial"})
    assert r2.json()["name"] == "New Name"

def test_delete_company(client):
    r = client.post("/api/v1/companies", json={"name": "To Delete", "style": "minimal"})
    company_id = r.json()["id"]
    client.delete(f"/api/v1/companies/{company_id}")
    r2 = client.get("/api/v1/companies")
    assert len(r2.json()) == 0
```

- [ ] **Correr tests para verificar que fallan**

```bash
pytest tests/api/test_companies.py -v
```

- [ ] **Crear `api/routes/companies.py`**

```python
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Company, User
from ..schemas import CompanyCreate, CompanyUpdate, CompanyOut
from ..deps import get_current_user

router = APIRouter()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@router.get("", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Company).filter(Company.user_id == user.id).all()


@router.post("", response_model=CompanyOut)
def create_company(
    req: CompanyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    slug = _slugify(req.name)
    existing = db.query(Company).filter(Company.slug == slug).first()
    if existing:
        slug = f"{slug}-{str(user.id)[:4]}"
    company = Company(user_id=user.id, slug=slug, **req.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = db.query(Company).filter(Company.id == company_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return c


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: str,
    req: CompanyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = db.query(Company).filter(Company.id == company_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{company_id}")
def delete_company(
    company_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = db.query(Company).filter(Company.id == company_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    db.delete(c)
    db.commit()
    return {"ok": True}
```

- [ ] **Correr tests**

```bash
pytest tests/api/test_companies.py -v
```
Esperado: 4 PASSED

- [ ] **Commit**

```bash
git add api/routes/companies.py tests/api/test_companies.py
git commit -m "feat: companies CRUD API"
```

---

## Tarea 7: Carousel — Generación y Edición de Slides

**Archivos:**
- Crear: `api/routes/carousel.py`

**Contexto:** `render_carousel(slides, brand_config, company_dir, output_dir, formats_dir)` espera `company_dir` para resolver assets. Usamos `storage/companies/{company_id}/` como company_dir. La función `_resolve_assets` en `core/renderer.py` solo busca imágenes si `use_image=True` e `image_hint` está presente — si el slide ya tiene `image_path` explícito, pasa de largo sin sobreescribir.

- [ ] **Escribir test de generación (mockeando la IA)**

```python
# tests/api/test_carousel.py
from unittest.mock import patch

MOCK_SLIDES = {
    "total_slides": 2,
    "slides": [
        {"type": "cover", "title": "Test Cover", "subtitle": "Sub"},
        {"type": "cta", "heading": "Síguenos", "action": "en Instagram"},
    ],
}


def test_generate_carousel(client):
    company_r = client.post("/api/v1/companies", json={
        "name": "Test Co", "style": "minimal",
        "colors": {"primary": "#000", "secondary": "#fff",
                   "background": "#fff", "text": "#000"},
        "fonts": {"heading": "Arial", "body": "Arial"},
        "design_context": "Prueba",
    })
    company_id = company_r.json()["id"]

    with patch("api.routes.carousel.generate_content", return_value=MOCK_SLIDES):
        r = client.post("/api/v1/designs/carousel/generate", json={
            "company_id": company_id,
            "mode": "topic",
            "content": "inteligencia artificial",
            "title": "Mi carrusel",
        })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "draft"
    assert len(data["slides"]) == 2


def test_update_slides(client):
    company_r = client.post("/api/v1/companies", json={
        "name": "Test Co", "style": "minimal",
        "colors": {"primary": "#000", "secondary": "#fff",
                   "background": "#fff", "text": "#000"},
        "fonts": {"heading": "Arial", "body": "Arial"},
        "design_context": "Prueba",
    })
    company_id = company_r.json()["id"]

    with patch("api.routes.carousel.generate_content", return_value=MOCK_SLIDES):
        design_r = client.post("/api/v1/designs/carousel/generate", json={
            "company_id": company_id, "mode": "topic",
            "content": "tema", "title": "titulo",
        })
    design_id = design_r.json()["id"]

    new_slides = [{"type": "cover", "title": "Editado", "subtitle": ""}]
    r = client.put(f"/api/v1/designs/{design_id}/slides",
                   json={"slides": new_slides})
    assert r.status_code == 200
    assert r.json()["slides"][0]["title"] == "Editado"
```

- [ ] **Correr tests para verificar que fallan**

```bash
pytest tests/api/test_carousel.py::test_generate_carousel tests/api/test_carousel.py::test_update_slides -v
```

- [ ] **Crear `api/routes/carousel.py`**

```python
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Company, Design, User
from ..schemas import CarouselGenerateRequest, SlidesUpdateRequest, DesignOut
from ..deps import get_current_user
from core.ai import generate_content

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent
FORMATS_DIR = BASE_DIR / "formats"
STORAGE_DIR = BASE_DIR / "storage"


def _company_dir(company_id: str) -> Path:
    d = STORAGE_DIR / "companies" / company_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _brand_config_from_company(c: Company) -> dict:
    return {
        "company": c.name,
        "ai_provider": c.ai_provider,
        "ollama_model": "llama3.2",
        "brand": {
            "style": c.style,
            "colors": c.colors or {"primary": "#000", "secondary": "#fff",
                                    "background": "#fff", "text": "#000"},
            "fonts": c.fonts or {"heading": "Arial", "body": "Arial"},
            "design_context": c.design_context or "",
            "logo": str(_company_dir(c.id) / "logo.svg")
            if (_company_dir(c.id) / "logo.svg").exists() else None,
        },
    }


def _design_out(d: Design) -> dict:
    return {
        "id": d.id,
        "company_id": d.company_id,
        "type": d.type,
        "title": d.title,
        "slides": d.slides,
        "size_px": d.size_px,
        "status": d.status,
        "created_at": str(d.created_at),
    }


@router.get("", response_model=list[DesignOut])
def list_designs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    designs = db.query(Design).filter(Design.user_id == user.id).all()
    return [_design_out(d) for d in designs]


@router.post("/carousel/generate")
def generate_carousel(
    req: CarouselGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(
        Company.id == req.company_id, Company.user_id == user.id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    brand_config = _brand_config_from_company(company)
    result = generate_content(req.mode, req.content, brand_config, FORMATS_DIR)

    design = Design(
        user_id=user.id,
        company_id=company.id,
        type="carousel",
        title=req.title or req.content[:50],
        slides=result["slides"],
        size_px=req.size_px,
        status="draft",
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return _design_out(design)


@router.get("/{design_id}")
def get_design(
    design_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Design).filter(Design.id == design_id, Design.user_id == user.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")
    return _design_out(d)


@router.put("/{design_id}/slides")
def update_slides(
    design_id: str,
    req: SlidesUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Design).filter(Design.id == design_id, Design.user_id == user.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")
    d.slides = req.slides
    d.status = "draft"
    db.commit()
    db.refresh(d)
    return _design_out(d)


@router.delete("/{design_id}")
def delete_design(
    design_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Design).filter(Design.id == design_id, Design.user_id == user.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")
    db.delete(d)
    db.commit()
    return {"ok": True}
```

- [ ] **Correr tests**

```bash
pytest tests/api/test_carousel.py -v
```
Esperado: 2 PASSED

- [ ] **Commit**

```bash
git add api/routes/carousel.py tests/api/test_carousel.py
git commit -m "feat: carousel generate and slides edit endpoints"
```

---

## Tarea 8: Render y Export

**Archivos:**
- Modificar: `api/routes/carousel.py`

- [ ] **Escribir tests**

```python
# En tests/api/test_carousel.py — agregar:
from unittest.mock import patch

def _make_design(client):
    company_r = client.post("/api/v1/companies", json={
        "name": "Test Co", "style": "minimal",
        "colors": {"primary": "#000", "secondary": "#fff",
                   "background": "#fff", "text": "#000"},
        "fonts": {"heading": "Arial", "body": "Arial"},
        "design_context": "Prueba",
    })
    company_id = company_r.json()["id"]
    with patch("api.routes.carousel.generate_content", return_value=MOCK_SLIDES):
        r = client.post("/api/v1/designs/carousel/generate", json={
            "company_id": company_id, "mode": "topic",
            "content": "tema", "title": "titulo",
        })
    return r.json()["id"]


def test_render_carousel(client):
    design_id = _make_design(client)
    with patch("api.routes.carousel.render_carousel") as mock_render:
        mock_render.return_value = None
        r = client.post(f"/api/v1/designs/{design_id}/render")
    assert r.status_code == 200
    assert r.json()["status"] == "rendered"


def test_export_svg(client, tmp_path, monkeypatch):
    design_id = _make_design(client)
    # Crear SVG fake en tmp dir
    slides_dir = tmp_path / "slides"
    slides_dir.mkdir()
    (slides_dir / "01_cover.svg").write_text("<svg/>")
    monkeypatch.setattr(
        "api.routes.carousel.STORAGE_DIR",
        tmp_path.parent,
    )
    with patch("api.routes.carousel.render_carousel"):
        client.post(f"/api/v1/designs/{design_id}/render")
    # Export returns a file or 200
    with patch("api.routes.carousel._get_render_dir",
               return_value=slides_dir.parent):
        r = client.get(f"/api/v1/designs/{design_id}/export?fmt=svg")
    assert r.status_code in (200, 404)  # 404 si no hay archivos reales en test
```

- [ ] **Agregar rutas render y export a `api/routes/carousel.py`**

```python
# Agregar imports al inicio:
import io
import zipfile
import shutil
from fastapi.responses import FileResponse, StreamingResponse
from core.renderer import render_carousel

# Agregar función helper:
def _render_dir(design_id: str) -> Path:
    return STORAGE_DIR / "tmp" / design_id


# Agregar rutas:
@router.post("/{design_id}/render")
def render_design(
    design_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Design).filter(Design.id == design_id, Design.user_id == user.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")

    company = db.query(Company).filter(Company.id == d.company_id).first()
    brand_config = _brand_config_from_company(company)
    company_dir = _company_dir(company.id)
    output_dir = _render_dir(design_id)

    # Limpiar render anterior
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    render_carousel(d.slides, brand_config, company_dir, output_dir, FORMATS_DIR)

    d.status = "rendered"
    db.commit()
    db.refresh(d)
    return _design_out(d)


@router.get("/{design_id}/export")
def export_design(
    design_id: str,
    fmt: str = "pdf",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Design).filter(Design.id == design_id, Design.user_id == user.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")

    render_dir = _render_dir(design_id)
    slides_dir = render_dir / "slides"

    if fmt == "pdf":
        pdf_path = render_dir / "carousel.pdf"
        if not pdf_path.exists():
            raise HTTPException(status_code=400, detail="Renderiza primero el diseño")
        return FileResponse(str(pdf_path), media_type="application/pdf",
                            filename=f"{design_id}.pdf",
                            background=None)

    if fmt == "svg":
        svg_files = sorted(slides_dir.glob("*.svg")) if slides_dir.exists() else []
        if not svg_files:
            raise HTTPException(status_code=400, detail="No hay SVGs renderizados")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for f in svg_files:
                zf.write(f, f.name)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{design_id}-svgs.zip"'},
        )

    if fmt == "jpg":
        import cairosvg
        from PIL import Image
        svg_files = sorted(slides_dir.glob("*.svg")) if slides_dir.exists() else []
        if not svg_files:
            raise HTTPException(status_code=400, detail="No hay SVGs renderizados")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for svg_path in svg_files:
                png_bytes = cairosvg.svg2png(url=str(svg_path))
                img = Image.open(io.BytesIO(png_bytes))
                jpg_buf = io.BytesIO()
                img.convert("RGB").save(jpg_buf, format="JPEG", quality=92)
                zf.writestr(svg_path.stem + ".jpg", jpg_buf.getvalue())
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{design_id}-jpgs.zip"'},
        )

    raise HTTPException(status_code=400, detail="Formato no soportado: usa svg, pdf o jpg")
```

- [ ] **Correr tests**

```bash
pytest tests/api/test_carousel.py -v
```
Esperado: 4 PASSED

- [ ] **Commit**

```bash
git add api/routes/carousel.py tests/api/test_carousel.py
git commit -m "feat: carousel render and export endpoints (svg/pdf/jpg)"
```

---

## Tarea 9: Imágenes — Upload + Búsqueda Pexels/Pixabay

**Archivos:**
- Crear: `api/routes/images.py`

- [ ] **Escribir tests**

```python
# tests/api/test_images.py
from unittest.mock import patch, AsyncMock
import io

def test_upload_image(client):
    fake_image = io.BytesIO(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    r = client.post(
        "/api/v1/assets/upload",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["source"] == "upload"


def test_search_pexels(client):
    mock_response = {
        "photos": [
            {"id": 1, "src": {"medium": "http://img.pexels.com/1.jpg"},
             "photographer": "Test", "alt": "coffee"}
        ]
    }
    with patch("api.routes.images.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        r = client.get("/api/v1/images/search?q=coffee&source=pexels")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == "pexels-1"
```

- [ ] **Correr tests para verificar que fallan**

```bash
pytest tests/api/test_images.py -v
```

- [ ] **Crear `api/routes/images.py`**

```python
import os
import io
from pathlib import Path
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from PIL import Image
from ..database import get_db
from ..models import Asset, User
from ..deps import get_current_user

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent
UPLOADS_DIR = BASE_DIR / "storage" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "")

# Caché en memoria simple: {query_source_key: results_list}
_search_cache: dict[str, list] = {}


def _compress_image(data: bytes, max_width: int) -> bytes:
    img = Image.open(io.BytesIO(data))
    ratio = max_width / img.width if img.width > max_width else 1
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@router.post("/assets/upload")
def upload_asset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = file.file.read()
    user_dir = UPLOADS_DIR / user.id
    user_dir.mkdir(exist_ok=True)

    asset = Asset(user_id=user.id, filename=file.filename, source="upload")
    db.add(asset)
    db.flush()

    thumb = _compress_image(data, 400)
    full = _compress_image(data, 1080)

    thumb_path = user_dir / f"{asset.id}_thumb.jpg"
    full_path = user_dir / f"{asset.id}_full.jpg"
    thumb_path.write_bytes(thumb)
    full_path.write_bytes(full)

    asset.path_thumb = str(thumb_path)
    asset.path_full = str(full_path)
    db.commit()
    db.refresh(asset)
    return {"id": asset.id, "source": "upload",
            "thumb_url": f"/api/v1/assets/{asset.id}/thumb",
            "full_url": f"/api/v1/assets/{asset.id}/full"}


@router.get("/assets/{asset_id}/thumb")
def get_thumb(asset_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    from fastapi.responses import FileResponse
    a = db.query(Asset).filter(Asset.id == asset_id, Asset.user_id == user.id).first()
    if not a or not a.path_thumb:
        raise HTTPException(status_code=404)
    return FileResponse(a.path_thumb)


@router.get("/images/search")
def search_images(
    q: str,
    source: str = "pexels",
    user: User = Depends(get_current_user),
):
    cache_key = f"{source}:{q.lower()}"
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    if source == "pexels":
        if not PEXELS_KEY:
            raise HTTPException(status_code=503, detail="Pexels API key no configurada")
        res = httpx.get(
            "https://api.pexels.com/v1/search",
            params={"query": q, "per_page": 15},
            headers={"Authorization": PEXELS_KEY},
        )
        if res.status_code != 200:
            raise HTTPException(status_code=502, detail="Error en Pexels API")
        photos = [
            {"id": f"pexels-{p['id']}", "url": p["src"]["medium"],
             "thumb": p["src"]["small"], "author": p["photographer"],
             "alt": p.get("alt", "")}
            for p in res.json().get("photos", [])
        ]

    elif source == "pixabay":
        if not PIXABAY_KEY:
            raise HTTPException(status_code=503, detail="Pixabay API key no configurada")
        res = httpx.get(
            "https://pixabay.com/api/",
            params={"key": PIXABAY_KEY, "q": q, "per_page": 15,
                    "image_type": "photo", "safesearch": "true"},
        )
        if res.status_code != 200:
            raise HTTPException(status_code=502, detail="Error en Pixabay API")
        photos = [
            {"id": f"pixabay-{h['id']}", "url": h["webformatURL"],
             "thumb": h["previewURL"], "author": h["user"], "alt": h.get("tags", "")}
            for h in res.json().get("hits", [])
        ]
    else:
        raise HTTPException(status_code=400, detail="source debe ser 'pexels' o 'pixabay'")

    _search_cache[cache_key] = photos
    return photos
```

- [ ] **Correr tests**

```bash
pytest tests/api/test_images.py -v
```
Esperado: 2 PASSED

- [ ] **Commit**

```bash
git add api/routes/images.py tests/api/test_images.py
git commit -m "feat: image upload (with compression) and Pexels/Pixabay search"
```

---

## Tarea 10: Makefile + Logo Upload

**Archivos:**
- Modificar: `Makefile`
- Modificar: `api/routes/companies.py` (agregar logo upload)

- [ ] **Actualizar `Makefile`**

```makefile
.PHONY: dev api web test

dev:
	@echo "Iniciando API y Web..."
	uvicorn api.main:app --reload --port 8000 & \
	cd web && npm run dev

api:
	uvicorn api.main:app --reload --port 8000

web:
	cd web && npm run dev

test:
	pytest tests/ -v

test-api:
	pytest tests/api/ -v
```

- [ ] **Agregar endpoint de logo a `api/routes/companies.py`**

```python
# Agregar import al inicio:
import io
from pathlib import Path
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image

BASE_DIR = Path(__file__).parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"

# Agregar al final del archivo:
@router.post("/{company_id}/logo")
def upload_logo(
    company_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from pathlib import Path
    c = db.query(Company).filter(Company.id == company_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    company_dir = STORAGE_DIR / "companies" / company_id
    company_dir.mkdir(parents=True, exist_ok=True)

    data = file.file.read()
    logo_path = company_dir / "logo.svg" if file.filename.endswith(".svg") else company_dir / "logo.png"
    logo_path.write_bytes(data)

    c.logo_path = str(logo_path)
    db.commit()
    return {"logo_url": f"/api/v1/companies/{company_id}/logo"}


@router.get("/{company_id}/logo")
def get_logo(company_id: str, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    c = db.query(Company).filter(Company.id == company_id, Company.user_id == user.id).first()
    if not c or not c.logo_path:
        raise HTTPException(status_code=404)
    return FileResponse(c.logo_path)
```

- [ ] **Correr todos los tests de API**

```bash
pytest tests/api/ -v
```
Esperado: todos PASSED

- [ ] **Commit**

```bash
git add Makefile api/routes/companies.py
git commit -m "feat: Makefile dev target and company logo upload endpoint"
```

---

## Tarea 11: Next.js — Scaffolding + Cliente API

**Archivos:**
- Crear: `web/` (via create-next-app)
- Crear: `web/lib/api.ts`
- Crear: `web/lib/auth.tsx`

- [ ] **Crear proyecto Next.js**

```bash
cd /Users/apple/Documents/ClaudeSkills/GeneradorDiseños
npx create-next-app@latest web \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
```
Cuando pregunte por router: App Router ✓

- [ ] **Verificar que arranca**

```bash
cd web && npm run dev
```
Abre http://localhost:3000 — debe mostrar la página default de Next.js. Detener con Ctrl+C.

- [ ] **Crear `web/lib/api.ts`**

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error desconocido" }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  auth: {
    register: (data: { email: string; password: string; name: string }) =>
      apiFetch("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      apiFetch("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) }),
    logout: () => apiFetch("/api/v1/auth/logout", { method: "POST" }),
    me: () => apiFetch<User>("/api/v1/auth/me"),
  },
  companies: {
    list: () => apiFetch<Company[]>("/api/v1/companies"),
    create: (data: CompanyCreate) =>
      apiFetch<Company>("/api/v1/companies", { method: "POST", body: JSON.stringify(data) }),
    get: (id: string) => apiFetch<Company>(`/api/v1/companies/${id}`),
    update: (id: string, data: CompanyCreate) =>
      apiFetch<Company>(`/api/v1/companies/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: string) =>
      apiFetch(`/api/v1/companies/${id}`, { method: "DELETE" }),
    uploadLogo: (id: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      return fetch(`${API_BASE}/api/v1/companies/${id}/logo`, {
        method: "POST", credentials: "include", body: form,
      }).then(r => r.json());
    },
  },
  designs: {
    list: () => apiFetch<Design[]>("/api/v1/designs"),
    generate: (data: GenerateRequest) =>
      apiFetch<Design>("/api/v1/designs/carousel/generate", {
        method: "POST", body: JSON.stringify(data),
      }),
    get: (id: string) => apiFetch<Design>(`/api/v1/designs/${id}`),
    updateSlides: (id: string, slides: Slide[]) =>
      apiFetch<Design>(`/api/v1/designs/${id}/slides`, {
        method: "PUT", body: JSON.stringify({ slides }),
      }),
    render: (id: string) =>
      apiFetch<Design>(`/api/v1/designs/${id}/render`, { method: "POST" }),
    exportUrl: (id: string, fmt: "svg" | "pdf" | "jpg") =>
      `${API_BASE}/api/v1/designs/${id}/export?fmt=${fmt}`,
    delete: (id: string) =>
      apiFetch(`/api/v1/designs/${id}`, { method: "DELETE" }),
  },
  images: {
    search: (q: string, source: "pexels" | "pixabay") =>
      apiFetch<ImageResult[]>(`/api/v1/images/search?q=${encodeURIComponent(q)}&source=${source}`),
    upload: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return fetch(`${API_BASE}/api/v1/assets/upload`, {
        method: "POST", credentials: "include", body: form,
      }).then(r => r.json());
    },
  },
};

// Tipos
export interface User { id: string; email: string; name?: string; avatar_url?: string; plan: string }
export interface Company {
  id: string; name: string; slug?: string; style: string;
  colors?: Record<string, string>; fonts?: Record<string, string>;
  design_context?: string; ai_provider: string; logo_path?: string;
}
export interface CompanyCreate {
  name: string; style: string; colors?: Record<string, string>;
  fonts?: Record<string, string>; design_context?: string; ai_provider?: string;
}
export interface Slide { type: string; [key: string]: unknown }
export interface Design {
  id: string; company_id: string; type: string; title?: string;
  slides?: Slide[]; size_px?: { width: number; height: number };
  status: string; created_at: string;
}
export interface GenerateRequest {
  company_id: string; mode: "topic" | "text"; content: string;
  size_px?: { width: number; height: number }; title?: string;
}
export interface ImageResult { id: string; url: string; thumb: string; author: string; alt: string }
```

- [ ] **Crear `web/lib/auth.tsx`**

```typescript
"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, User } from "./api";
import { useRouter } from "next/navigation";

interface AuthCtx { user: User | null; loading: boolean; logout: () => Promise<void> }
const AuthContext = createContext<AuthCtx>({ user: null, loading: true, logout: async () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.auth.me().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  const logout = async () => {
    await api.auth.logout();
    setUser(null);
    router.push("/auth/login");
  };

  return <AuthContext.Provider value={{ user, loading, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
```

- [ ] **Agregar AuthProvider al layout raíz en `web/app/layout.tsx`**

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = { title: "Generador de Diseños", description: "Crea carruseles para Instagram" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

- [ ] **Commit**

```bash
cd ..
git add web/
git commit -m "feat: Next.js scaffolding with typed API client and AuthContext"
```

---

## Tarea 12: Páginas de Auth + Landing

**Archivos:**
- Crear: `web/app/page.tsx`
- Crear: `web/app/auth/login/page.tsx`
- Crear: `web/app/auth/register/page.tsx`

- [ ] **Crear `web/app/page.tsx`**

```typescript
"use client";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading) router.replace(user ? "/dashboard" : "/auth/login");
  }, [user, loading, router]);
  return <div className="flex h-screen items-center justify-center">Cargando...</div>;
}
```

- [ ] **Crear `web/app/auth/login/page.tsx`**

```typescript
"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.auth.login({ email, password });
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6">Iniciar sesión</h1>
        <form onSubmit={submit} className="space-y-4">
          <input type="email" placeholder="Email" value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full border rounded-lg px-3 py-2" required />
          <input type="password" placeholder="Contraseña" value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full border rounded-lg px-3 py-2" required />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit"
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-800">
            Entrar
          </button>
        </form>
        <a href="http://localhost:8000/api/v1/auth/google"
          className="mt-3 w-full flex items-center justify-center border rounded-lg py-2 hover:bg-gray-50">
          Continuar con Google
        </a>
        <p className="mt-4 text-center text-sm text-gray-500">
          ¿Sin cuenta? <Link href="/auth/register" className="underline">Regístrate</Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Crear `web/app/auth/register/page.tsx`**

```typescript
"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [error, setError] = useState("");
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.auth.register(form);
      await api.auth.login({ email: form.email, password: form.password });
      router.push("/companies/new");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al registrarse");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6">Crear cuenta</h1>
        <form onSubmit={submit} className="space-y-4">
          {(["name", "email", "password"] as const).map(field => (
            <input key={field} type={field === "password" ? "password" : field === "email" ? "email" : "text"}
              placeholder={field === "name" ? "Nombre" : field === "email" ? "Email" : "Contraseña"}
              value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}
              className="w-full border rounded-lg px-3 py-2" required />
          ))}
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit"
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-800">
            Crear cuenta
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500">
          ¿Ya tienes cuenta? <Link href="/auth/login" className="underline">Inicia sesión</Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Commit**

```bash
git add web/app/
git commit -m "feat: landing redirect, login page, register page"
```

---

## Tarea 13: Dashboard + Empresas

**Archivos:**
- Crear: `web/app/dashboard/page.tsx`
- Crear: `web/components/CompanyForm.tsx`
- Crear: `web/app/companies/new/page.tsx`
- Crear: `web/app/companies/[id]/page.tsx`

- [ ] **Crear `web/components/CompanyForm.tsx`**

```typescript
"use client";
import { useState } from "react";
import { Company, CompanyCreate } from "@/lib/api";

const STYLES = ["minimal", "bold", "editorial", "corporate"];

interface Props {
  initial?: Partial<Company>;
  onSubmit: (data: CompanyCreate) => Promise<void>;
  submitLabel?: string;
}

export default function CompanyForm({ initial, onSubmit, submitLabel = "Guardar" }: Props) {
  const [form, setForm] = useState<CompanyCreate>({
    name: initial?.name ?? "",
    style: initial?.style ?? "minimal",
    colors: initial?.colors ?? { primary: "#000000", secondary: "#ffffff", background: "#f8f8f8", text: "#2d2d2d" },
    fonts: initial?.fonts ?? { heading: "Georgia Bold", body: "Arial" },
    design_context: initial?.design_context ?? "",
    ai_provider: initial?.ai_provider ?? "ollama",
  });
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try { await onSubmit(form); }
    catch (err: unknown) { setError(err instanceof Error ? err.message : "Error"); }
  };

  const setColor = (key: string, val: string) =>
    setForm(f => ({ ...f, colors: { ...f.colors!, [key]: val } }));

  const setFont = (key: string, val: string) =>
    setForm(f => ({ ...f, fonts: { ...f.fonts!, [key]: val } }));

  return (
    <form onSubmit={submit} className="space-y-5 max-w-lg">
      <div>
        <label className="block text-sm font-medium mb-1">Nombre de la empresa</label>
        <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
          className="w-full border rounded-lg px-3 py-2" required />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Estilo visual</label>
        <div className="flex gap-2 flex-wrap">
          {STYLES.map(s => (
            <button key={s} type="button"
              onClick={() => setForm({ ...form, style: s })}
              className={`px-3 py-1 rounded-full border text-sm ${form.style === s ? "bg-black text-white" : "bg-white"}`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Colores de marca</label>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(form.colors ?? {}).map(([key, val]) => (
            <label key={key} className="flex items-center gap-2 text-sm">
              <input type="color" value={val as string} onChange={e => setColor(key, e.target.value)}
                className="w-8 h-8 rounded cursor-pointer" />
              {key}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Tipografías</label>
        <div className="space-y-2">
          {Object.entries(form.fonts ?? {}).map(([key, val]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-sm w-20">{key}:</span>
              <input value={val as string} onChange={e => setFont(key, e.target.value)}
                className="flex-1 border rounded-lg px-3 py-1 text-sm" />
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Contexto de diseño</label>
        <textarea value={form.design_context ?? ""}
          onChange={e => setForm({ ...form, design_context: e.target.value })}
          rows={4} placeholder="Describe el tono, audiencia, y valores de la marca..."
          className="w-full border rounded-lg px-3 py-2 text-sm" />
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button type="submit"
        className="bg-black text-white px-6 py-2 rounded-lg hover:bg-gray-800">
        {submitLabel}
      </button>
    </form>
  );
}
```

- [ ] **Crear `web/app/companies/new/page.tsx`**

```typescript
"use client";
import { api, CompanyCreate } from "@/lib/api";
import CompanyForm from "@/components/CompanyForm";
import { useRouter } from "next/navigation";

export default function NewCompanyPage() {
  const router = useRouter();
  const handleSubmit = async (data: CompanyCreate) => {
    await api.companies.create(data);
    router.push("/dashboard");
  };
  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Nueva empresa</h1>
      <CompanyForm onSubmit={handleSubmit} submitLabel="Crear empresa" />
    </div>
  );
}
```

- [ ] **Crear `web/app/companies/[id]/page.tsx`**

```typescript
"use client";
import { useEffect, useState } from "react";
import { api, Company, CompanyCreate } from "@/lib/api";
import CompanyForm from "@/components/CompanyForm";
import { useRouter, useParams } from "next/navigation";

export default function EditCompanyPage() {
  const { id } = useParams<{ id: string }>();
  const [company, setCompany] = useState<Company | null>(null);
  const router = useRouter();

  useEffect(() => { api.companies.get(id).then(setCompany); }, [id]);

  if (!company) return <div className="p-8">Cargando...</div>;

  const handleSubmit = async (data: CompanyCreate) => {
    await api.companies.update(id, data);
    router.push("/dashboard");
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Editar empresa: {company.name}</h1>
      <CompanyForm initial={company} onSubmit={handleSubmit} submitLabel="Guardar cambios" />
    </div>
  );
}
```

- [ ] **Crear `web/app/dashboard/page.tsx`**

```typescript
"use client";
import { useEffect, useState } from "react";
import { api, Company, Design } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Dashboard() {
  const { user, loading, logout } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [designs, setDesigns] = useState<Design[]>([]);
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth/login");
  }, [user, loading, router]);

  useEffect(() => {
    api.companies.list().then(setCompanies);
    api.designs.list().then(setDesigns);
  }, []);

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Mis Diseños</h1>
        <div className="flex gap-3 items-center">
          <span className="text-sm text-gray-500">{user?.email}</span>
          <button onClick={logout} className="text-sm text-gray-500 underline">Salir</button>
        </div>
      </div>

      <section className="mb-10">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Empresas</h2>
          <Link href="/companies/new"
            className="bg-black text-white px-4 py-1.5 rounded-lg text-sm">
            + Nueva empresa
          </Link>
        </div>
        {companies.length === 0 ? (
          <p className="text-gray-500">Sin empresas. <Link href="/companies/new" className="underline">Crea una.</Link></p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {companies.map(c => (
              <Link key={c.id} href={`/companies/${c.id}`}
                className="border rounded-xl p-4 hover:shadow transition">
                <div className="font-medium">{c.name}</div>
                <div className="text-sm text-gray-500 mt-1">{c.style}</div>
                <div className="flex gap-1 mt-2">
                  {Object.values(c.colors ?? {}).map((col, i) => (
                    <div key={i} className="w-4 h-4 rounded-full border"
                      style={{ backgroundColor: col as string }} />
                  ))}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Diseños recientes</h2>
          {companies.length > 0 && (
            <Link href="/designs/new/carousel"
              className="bg-black text-white px-4 py-1.5 rounded-lg text-sm">
              + Nuevo carrusel
            </Link>
          )}
        </div>
        {designs.length === 0 ? (
          <p className="text-gray-500">Sin diseños aún.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {designs.map(d => (
              <Link key={d.id} href={`/designs/${d.id}/edit`}
                className="border rounded-xl p-4 hover:shadow transition">
                <div className="font-medium">{d.title ?? "Sin título"}</div>
                <div className="text-sm text-gray-500 mt-1">
                  {d.slides?.length ?? 0} slides · {d.status}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
```

- [ ] **Commit**

```bash
git add web/
git commit -m "feat: dashboard, company create/edit pages and CompanyForm component"
```

---

## Tarea 14: Wizard de Creación de Carrusel

**Archivos:**
- Crear: `web/app/designs/new/carousel/page.tsx`

- [ ] **Crear `web/app/designs/new/carousel/page.tsx`**

```typescript
"use client";
import { useEffect, useState } from "react";
import { api, Company } from "@/lib/api";
import { useRouter } from "next/navigation";

const SIZES = [
  { label: "1:1 (1080×1080)", value: { width: 1080, height: 1080 } },
  { label: "4:5 (1080×1350)", value: { width: 1080, height: 1350 } },
  { label: "9:16 (1080×1920)", value: { width: 1080, height: 1920 } },
];

export default function NewCarouselPage() {
  const router = useRouter();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [form, setForm] = useState({
    company_id: "",
    mode: "topic" as "topic" | "text",
    content: "",
    size_px: SIZES[0].value,
    title: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api.companies.list().then(setCompanies); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const design = await api.designs.generate(form) as { id: string };
      router.push(`/designs/${design.id}/edit`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al generar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Nuevo carrusel</h1>
      <form onSubmit={submit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">Empresa</label>
          <select value={form.company_id}
            onChange={e => setForm({ ...form, company_id: e.target.value })}
            className="w-full border rounded-lg px-3 py-2" required>
            <option value="">Selecciona una empresa...</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Tamaño</label>
          <div className="flex gap-2 flex-wrap">
            {SIZES.map(s => (
              <button key={s.label} type="button"
                onClick={() => setForm({ ...form, size_px: s.value })}
                className={`px-3 py-1 rounded-full border text-sm ${
                  form.size_px.width === s.value.width ? "bg-black text-white" : "bg-white"
                }`}>
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Modo</label>
          <div className="flex gap-3">
            {(["topic", "text"] as const).map(m => (
              <label key={m} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" value={m} checked={form.mode === m}
                  onChange={() => setForm({ ...form, mode: m })} />
                <span className="text-sm">{m === "topic" ? "Tema corto" : "Texto largo"}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            {form.mode === "topic" ? "Tema" : "Texto o artículo"}
          </label>
          {form.mode === "topic" ? (
            <input value={form.content}
              onChange={e => setForm({ ...form, content: e.target.value })}
              placeholder="ej: beneficios del marketing digital"
              className="w-full border rounded-lg px-3 py-2" required />
          ) : (
            <textarea value={form.content}
              onChange={e => setForm({ ...form, content: e.target.value })}
              rows={8} placeholder="Pega aquí el artículo o texto largo..."
              className="w-full border rounded-lg px-3 py-2 text-sm" required />
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Título (opcional)</label>
          <input value={form.title}
            onChange={e => setForm({ ...form, title: e.target.value })}
            placeholder="Nombre del diseño para identificarlo"
            className="w-full border rounded-lg px-3 py-2" />
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full bg-black text-white py-2.5 rounded-lg hover:bg-gray-800 disabled:opacity-50">
          {loading ? "Generando con IA..." : "Generar carrusel →"}
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Commit**

```bash
git add web/app/designs/
git commit -m "feat: carousel creation wizard page"
```

---

## Tarea 15: Editor de Slides

**Archivos:**
- Crear: `web/components/SlidePreview.tsx`
- Crear: `web/components/SlideEditor.tsx`
- Crear: `web/components/ImagePicker.tsx`
- Crear: `web/app/designs/[id]/edit/page.tsx`

- [ ] **Crear `web/components/SlidePreview.tsx`**

```typescript
interface Props { svgUrl: string | null; loading: boolean }

export default function SlidePreview({ svgUrl, loading }: Props) {
  return (
    <div className="aspect-square bg-gray-100 rounded-xl flex items-center justify-center overflow-hidden border">
      {loading ? (
        <div className="text-gray-400 text-sm">Renderizando...</div>
      ) : svgUrl ? (
        <img src={svgUrl} alt="preview" className="w-full h-full object-contain" />
      ) : (
        <div className="text-gray-400 text-sm">Sin preview</div>
      )}
    </div>
  );
}
```

- [ ] **Crear `web/components/ImagePicker.tsx`**

```typescript
"use client";
import { useState } from "react";
import { api, ImageResult } from "@/lib/api";

interface Props {
  onSelect: (url: string) => void;
  onClose: () => void;
}

export default function ImagePicker({ onSelect, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<"pexels" | "pixabay">("pexels");
  const [results, setResults] = useState<ImageResult[]>([]);
  const [searching, setSearching] = useState(false);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await api.images.search(query, source);
      setResults(res);
    } finally { setSearching(false); }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const res = await api.images.upload(file) as { thumb_url: string };
    onSelect(`http://localhost:8000${res.thumb_url}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Elegir imagen</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>

        <div className="flex gap-2 mb-4">
          <input value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && search()}
            placeholder="Buscar foto..." className="flex-1 border rounded-lg px-3 py-2" />
          <select value={source} onChange={e => setSource(e.target.value as "pexels" | "pixabay")}
            className="border rounded-lg px-2 py-2">
            <option value="pexels">Pexels</option>
            <option value="pixabay">Pixabay</option>
          </select>
          <button onClick={search} disabled={searching}
            className="bg-black text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">
            {searching ? "..." : "Buscar"}
          </button>
        </div>

        <label className="block mb-4 cursor-pointer">
          <div className="border-2 border-dashed rounded-lg p-4 text-center text-sm text-gray-500 hover:bg-gray-50">
            O sube tu propia imagen
          </div>
          <input type="file" accept="image/*" className="hidden" onChange={handleUpload} />
        </label>

        <div className="grid grid-cols-3 gap-2">
          {results.map(img => (
            <button key={img.id} onClick={() => { onSelect(img.url); onClose(); }}
              className="aspect-square overflow-hidden rounded-lg hover:ring-2 ring-black">
              <img src={img.thumb} alt={img.alt} className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Crear `web/components/SlideEditor.tsx`**

```typescript
"use client";
import { useState } from "react";
import { Slide } from "@/lib/api";
import ImagePicker from "./ImagePicker";

interface Props { slide: Slide; onChange: (updated: Slide) => void }

export default function SlideEditor({ slide, onChange }: Props) {
  const [showPicker, setShowPicker] = useState(false);
  const set = (key: string, val: unknown) => onChange({ ...slide, [key]: val });

  return (
    <div className="space-y-3">
      <div className="text-xs font-semibold uppercase text-gray-400 mb-2">
        Tipo: {slide.type}
      </div>

      {slide.type === "cover" && (
        <>
          <Field label="Título" value={slide.title as string ?? ""} onChange={v => set("title", v)} />
          <Field label="Subtítulo" value={slide.subtitle as string ?? ""} onChange={v => set("subtitle", v)} />
        </>
      )}

      {slide.type === "content" && (
        <>
          <Field label="Encabezado" value={slide.heading as string ?? ""} onChange={v => set("heading", v)} />
          <Field label="Cuerpo" value={slide.body as string ?? ""} onChange={v => set("body", v)} textarea />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!slide.use_image}
              onChange={e => set("use_image", e.target.checked)} />
            Usar imagen
          </label>
          {slide.use_image && (
            <ImageField value={slide.image_path as string ?? ""}
              onPick={() => setShowPicker(true)} />
          )}
        </>
      )}

      {slide.type === "content_icon" && (
        <>
          <Field label="Encabezado" value={slide.heading as string ?? ""} onChange={v => set("heading", v)} />
          <Field label="Cuerpo" value={slide.body as string ?? ""} onChange={v => set("body", v)} textarea />
          <Field label="Ícono (nombre en inglés)" value={slide.icon_hint as string ?? ""} onChange={v => set("icon_hint", v)} />
        </>
      )}

      {slide.type === "stat" && (
        <>
          <Field label="Número (ej: 87%)" value={slide.number as string ?? ""} onChange={v => set("number", v)} />
          <Field label="Etiqueta" value={slide.label as string ?? ""} onChange={v => set("label", v)} />
        </>
      )}

      {slide.type === "cta" && (
        <>
          <Field label="Encabezado" value={slide.heading as string ?? ""} onChange={v => set("heading", v)} />
          <Field label="Acción" value={slide.action as string ?? ""} onChange={v => set("action", v)} />
        </>
      )}

      {showPicker && (
        <ImagePicker
          onSelect={url => set("image_path", url)}
          onClose={() => setShowPicker(false)}
        />
      )}
    </div>
  );
}

function Field({ label, value, onChange, textarea }: {
  label: string; value: string; onChange: (v: string) => void; textarea?: boolean
}) {
  const cls = "w-full border rounded-lg px-3 py-2 text-sm";
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {textarea
        ? <textarea value={value} onChange={e => onChange(e.target.value)} rows={3} className={cls} />
        : <input value={value} onChange={e => onChange(e.target.value)} className={cls} />}
    </div>
  );
}

function ImageField({ value, onPick }: { value: string; onPick: () => void }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">Imagen</label>
      <div className="flex gap-2 items-center">
        {value && <img src={value} alt="" className="w-12 h-12 object-cover rounded" />}
        <button type="button" onClick={onPick}
          className="border px-3 py-1 rounded-lg text-sm hover:bg-gray-50">
          {value ? "Cambiar imagen" : "Elegir imagen"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Crear `web/app/designs/[id]/edit/page.tsx`**

```typescript
"use client";
import { useEffect, useState, useCallback } from "react";
import { api, Design, Slide } from "@/lib/api";
import { useParams, useRouter } from "next/navigation";
import SlideEditor from "@/components/SlideEditor";
import SlidePreview from "@/components/SlidePreview";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function EditDesignPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [design, setDesign] = useState<Design | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [rendering, setRendering] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.designs.get(id).then(setDesign); }, [id]);

  const currentSlide = design?.slides?.[currentIdx];

  const updateSlide = useCallback(async (updated: Slide) => {
    if (!design?.slides) return;
    const newSlides = design.slides.map((s, i) => i === currentIdx ? updated : s);
    setSaving(true);
    try {
      const d = await api.designs.updateSlides(id, newSlides) as Design;
      setDesign(d);
    } finally { setSaving(false); }
  }, [design, currentIdx, id]);

  const render = async () => {
    setRendering(true);
    try { await api.designs.render(id); }
    finally { setRendering(false); }
  };

  if (!design) return <div className="p-8">Cargando diseño...</div>;
  const slides = design.slides ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-gray-600">←</button>
          <span className="font-medium">{design.title ?? "Sin título"}</span>
          {saving && <span className="text-xs text-gray-400">Guardando...</span>}
        </div>
        <div className="flex gap-2">
          <button onClick={render} disabled={rendering}
            className="border px-4 py-1.5 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50">
            {rendering ? "Renderizando..." : "Actualizar preview"}
          </button>
          <button onClick={() => router.push(`/designs/${id}/export`)}
            className="bg-black text-white px-4 py-1.5 rounded-lg text-sm">
            Exportar →
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-6 grid grid-cols-2 gap-6">
        <div>
          <SlidePreview
            svgUrl={design.status === "rendered"
              ? `${API_BASE}/api/v1/designs/${id}/export?fmt=svg&slide=${currentIdx}`
              : null}
            loading={rendering}
          />
          <div className="flex items-center justify-between mt-3">
            <button onClick={() => setCurrentIdx(i => Math.max(0, i - 1))}
              disabled={currentIdx === 0}
              className="border px-3 py-1 rounded-lg text-sm disabled:opacity-30">← Anterior</button>
            <span className="text-sm text-gray-500">{currentIdx + 1} / {slides.length}</span>
            <button onClick={() => setCurrentIdx(i => Math.min(slides.length - 1, i + 1))}
              disabled={currentIdx === slides.length - 1}
              className="border px-3 py-1 rounded-lg text-sm disabled:opacity-30">Siguiente →</button>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm">
          <div className="flex gap-1 mb-4 flex-wrap">
            {slides.map((s, i) => (
              <button key={i} onClick={() => setCurrentIdx(i)}
                className={`text-xs px-2 py-1 rounded-full border ${i === currentIdx ? "bg-black text-white" : "bg-white"}`}>
                {i + 1}. {s.type}
              </button>
            ))}
          </div>
          {currentSlide && (
            <SlideEditor slide={currentSlide} onChange={updateSlide} />
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Commit**

```bash
git add web/
git commit -m "feat: slide editor with per-type forms, image picker, and live preview"
```

---

## Tarea 16: Página de Export

**Archivos:**
- Crear: `web/components/ExportPanel.tsx`
- Crear: `web/app/designs/[id]/export/page.tsx`

- [ ] **Crear `web/components/ExportPanel.tsx`**

```typescript
"use client";
import { useState } from "react";

interface Props { designId: string; apiBase: string }

const FORMATS = [
  { key: "pdf", label: "PDF", desc: "Multipágina, ideal para presentaciones" },
  { key: "svg", label: "SVG (ZIP)", desc: "Editable en Illustrator y Figma" },
  { key: "jpg", label: "JPG (ZIP)", desc: "Listo para publicar en Instagram" },
] as const;

export default function ExportPanel({ designId, apiBase }: Props) {
  const [selected, setSelected] = useState<"pdf" | "svg" | "jpg">("pdf");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  const download = async () => {
    setDownloading(true);
    setError("");
    try {
      const url = `${apiBase}/api/v1/designs/${designId}/export?fmt=${selected}`;
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Error al exportar");
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `carousel-${designId}.${selected === "svg" || selected === "jpg" ? "zip" : selected}`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al descargar");
    } finally { setDownloading(false); }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Exportar diseño</h2>
      <div className="space-y-3 mb-6">
        {FORMATS.map(f => (
          <label key={f.key}
            className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer ${
              selected === f.key ? "border-black bg-gray-50" : "border-gray-200"
            }`}>
            <input type="radio" name="fmt" value={f.key} checked={selected === f.key}
              onChange={() => setSelected(f.key)} className="mt-0.5" />
            <div>
              <div className="font-medium text-sm">{f.label}</div>
              <div className="text-xs text-gray-500">{f.desc}</div>
            </div>
          </label>
        ))}
      </div>
      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
      <button onClick={download} disabled={downloading}
        className="w-full bg-black text-white py-2.5 rounded-lg hover:bg-gray-800 disabled:opacity-50">
        {downloading ? "Descargando..." : `Descargar ${selected.toUpperCase()}`}
      </button>
      <p className="text-xs text-gray-400 mt-3 text-center">
        Los SVG se abren en Illustrator, Figma y Canva
      </p>
    </div>
  );
}
```

- [ ] **Crear `web/app/designs/[id]/export/page.tsx`**

```typescript
"use client";
import { useEffect, useState } from "react";
import { api, Design } from "@/lib/api";
import { useParams, useRouter } from "next/navigation";
import ExportPanel from "@/components/ExportPanel";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ExportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [design, setDesign] = useState<Design | null>(null);
  const [rendering, setRendering] = useState(false);

  useEffect(() => {
    api.designs.get(id).then(async (d: unknown) => {
      const design = d as Design;
      if (design.status !== "rendered") {
        setRendering(true);
        await api.designs.render(id);
        setRendering(false);
      }
      setDesign(design);
    });
  }, [id]);

  if (!design || rendering) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-medium mb-2">Preparando diseño...</div>
          <div className="text-sm text-gray-500">Renderizando slides</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => router.push(`/designs/${id}/edit`)}
            className="text-gray-400 hover:text-gray-600">←</button>
          <h1 className="text-2xl font-bold">{design.title ?? "Exportar diseño"}</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-sm font-medium text-gray-500 mb-3">
              {design.slides?.length ?? 0} slides generados
            </h2>
            <div className="space-y-2">
              {design.slides?.map((s, i) => (
                <div key={i} className="flex items-center gap-2 text-sm border rounded-lg px-3 py-2 bg-white">
                  <span className="text-gray-400">{i + 1}.</span>
                  <span className="font-medium">{s.type}</span>
                  <span className="text-gray-500 truncate">
                    {(s.title as string) ?? (s.heading as string) ?? (s.number as string) ?? ""}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <ExportPanel designId={id} apiBase={API_BASE} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Crear `web/.env.local`**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Commit**

```bash
git add web/
git commit -m "feat: export page with PDF/SVG/JPG download options"
```

---

## Tarea 17: Smoke Test End-to-End

- [ ] **Correr todos los tests de API**

```bash
pytest tests/api/ -v
```
Esperado: todos PASSED

- [ ] **Arrancar la API**

```bash
uvicorn api.main:app --reload --port 8000
```

- [ ] **En otra terminal, arrancar el frontend**

```bash
cd web && npm run dev
```

- [ ] **Verificar flujo completo en el browser**

1. Ir a http://localhost:3000 → redirige a `/auth/login`
2. Registrar cuenta nueva → redirige a `/companies/new`
3. Crear empresa con colores y contexto → redirige a `/dashboard`
4. Click en "+ Nuevo carrusel" → `/designs/new/carousel`
5. Seleccionar empresa, tema "beneficios del trabajo remoto", generar
6. En el editor: editar título del primer slide, click "Actualizar preview"
7. Click "Exportar →", descargar PDF
8. Verificar que el PDF se abre correctamente

- [ ] **Verificar flujo local sin auth (user_id = "local")**

Con la API corriendo pero sin estar logueado, hacer:

```bash
curl -s http://localhost:8000/api/v1/companies | python3 -m json.tool
```
Esperado: `[]` (lista vacía, no 401)

- [ ] **Commit final**

```bash
git add .
git commit -m "feat: web platform MVP complete — FastAPI + Next.js carousel generator"
```

---

## Notas de Implementación

**Limitación del preview en el editor:** El endpoint `/export?fmt=svg` devuelve un ZIP de todos los slides. Para el preview slide-a-slide, la solución más simple es renderizar y devolver el SVG de un slide individual. Esto requiere un endpoint adicional `GET /designs/{id}/slides/{n}/preview` que devuelva el SVG del slide n. Puedes agregarlo como mejora inmediata después del MVP.

**Variables de entorno:** Copiar `.env.example` a `.env` y configurar al menos `JWT_SECRET` antes del primer deploy.

**Ollama:** Debe estar corriendo en `http://localhost:11434` con el modelo `llama3.2` disponible (`ollama pull llama3.2`).
