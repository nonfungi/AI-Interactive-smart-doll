# app/models.py

import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # --- FIX: Use eager loading to prevent async errors ---
    children = relationship("Child", back_populates="parent", lazy="selectin")

class Child(Base):
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # --- FIX: Use eager loading ---
    parent = relationship("User", back_populates="children", lazy="selectin")
    doll = relationship("Doll", back_populates="child", uselist=False, lazy="selectin")

class Doll(Base):
    __tablename__ = "dolls"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=True)
    
    # --- FIX: Use eager loading ---
    child = relationship("Child", back_populates="doll", lazy="selectin")
