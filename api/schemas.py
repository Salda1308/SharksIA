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
