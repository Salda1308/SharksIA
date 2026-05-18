import re
import io
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image
from ..database import get_db
from ..models import Company, User
from ..schemas import CompanyCreate, CompanyUpdate, CompanyOut
from ..deps import get_current_user

BASE_DIR = Path(__file__).parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"

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


@router.post("/{company_id}/logo")
def upload_logo(
    company_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = db.query(Company).filter(Company.id == company_id, Company.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    company_dir = STORAGE_DIR / "companies" / company_id
    company_dir.mkdir(parents=True, exist_ok=True)

    data = file.file.read()
    ext = "svg" if (file.filename or "").endswith(".svg") else "png"
    logo_path = company_dir / f"logo.{ext}"
    logo_path.write_bytes(data)

    c.logo_path = str(logo_path)
    db.commit()
    return {"logo_url": f"/api/v1/companies/{company_id}/logo"}


@router.get("/{company_id}/logo")
def get_logo(
    company_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = db.query(Company).filter(Company.id == company_id, Company.user_id == user.id).first()
    if not c or not c.logo_path:
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    return FileResponse(c.logo_path)
