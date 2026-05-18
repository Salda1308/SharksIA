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
