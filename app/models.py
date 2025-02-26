# app/models.py
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True)
    short_code = Column(String(100), unique=True, nullable=False)
    long_url = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    expire_at = Column(TIMESTAMP, nullable=True)

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True)
    short_code = Column(
        String(100),
        ForeignKey("urls.short_code", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    clicked_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
