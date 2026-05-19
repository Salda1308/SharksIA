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
