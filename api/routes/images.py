import os
import io
from pathlib import Path
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image, ImageFile
from ..database import get_db
from ..models import Asset, User
from ..deps import get_current_user

# Allow Pillow to open truncated images (e.g. minimal test fixtures)
ImageFile.LOAD_TRUNCATED_IMAGES = True

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent
UPLOADS_DIR = BASE_DIR / "storage" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Simple in-memory cache: {query_source_key: results_list}
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
    return {
        "id": asset.id,
        "source": "upload",
        "thumb_url": f"/api/v1/assets/{asset.id}/thumb",
        "full_url": f"/api/v1/assets/{asset.id}/full",
    }


@router.get("/assets/{asset_id}/thumb")
def get_thumb(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
        pexels_key = os.getenv("PEXELS_API_KEY", "")
        if not pexels_key:
            raise HTTPException(status_code=503, detail="Pexels API key no configurada")
        res = httpx.get(
            "https://api.pexels.com/v1/search",
            params={"query": q, "per_page": 15},
            headers={"Authorization": pexels_key},
        )
        if res.status_code != 200:
            raise HTTPException(status_code=502, detail="Error en Pexels API")
        photos = [
            {
                "id": f"pexels-{p['id']}",
                "url": p["src"]["medium"],
                "thumb": p["src"]["small"],
                "author": p["photographer"],
                "alt": p.get("alt", ""),
            }
            for p in res.json().get("photos", [])
        ]

    elif source == "pixabay":
        pixabay_key = os.getenv("PIXABAY_API_KEY", "")
        if not pixabay_key:
            raise HTTPException(status_code=503, detail="Pixabay API key no configurada")
        res = httpx.get(
            "https://pixabay.com/api/",
            params={
                "key": pixabay_key,
                "q": q,
                "per_page": 15,
                "image_type": "photo",
                "safesearch": "true",
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=502, detail="Error en Pixabay API")
        photos = [
            {
                "id": f"pixabay-{h['id']}",
                "url": h["webformatURL"],
                "thumb": h["previewURL"],
                "author": h["user"],
                "alt": h.get("tags", ""),
            }
            for h in res.json().get("hits", [])
        ]
    else:
        raise HTTPException(status_code=400, detail="source debe ser 'pexels' o 'pixabay'")

    _search_cache[cache_key] = photos
    return photos
