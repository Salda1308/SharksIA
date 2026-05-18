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
