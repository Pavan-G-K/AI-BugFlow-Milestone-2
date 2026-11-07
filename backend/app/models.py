from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), default="Developer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Issue(Base):
    __tablename__ = "issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    steps_to_reproduce: Mapped[str] = mapped_column(Text, default="")
    issue_type: Mapped[str] = mapped_column(String(40), default="Bug")
    severity: Mapped[str] = mapped_column(String(20), default="Medium")
    priority: Mapped[str] = mapped_column(String(5), default="P3")
    module: Mapped[str] = mapped_column(String(100), default="General")
    status: Mapped[str] = mapped_column(String(30), default="Open")
    assignee: Mapped[str] = mapped_column(String(120), default="Unassigned")
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sprint_id: Mapped[int | None] = mapped_column(ForeignKey("sprints.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments: Mapped[list["Comment"]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="issue", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    issue: Mapped["Issue"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship()

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"))
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(160))
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    issue: Mapped["Issue"] = relationship(back_populates="activities")
    actor: Mapped["User"] = relationship()

class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"))
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    uploader: Mapped["User"] = relationship()

class Sprint(Base):
    __tablename__ = "sprints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    goal: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
