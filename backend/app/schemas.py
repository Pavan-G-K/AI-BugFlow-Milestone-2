from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8)
    role: str = "Developer"

class LoginIn(BaseModel):
    email: str
    password: str

class IssueIn(BaseModel):
    title: str = Field(min_length=4, max_length=240)
    description: str = ""
    steps_to_reproduce: str = ""
    issue_type: str = "Bug"
    severity: str = "Medium"
    priority: str = "P3"
    module: str = "General"
    assignee: str = "Unassigned"

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    module: Optional[str] = None
    assignee: Optional[str] = None
    status: Optional[str] = None
    sprint_id: Optional[int] = None

class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

class SprintIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    start_date: date
    end_date: date
    goal: str = ""

class PredictIn(BaseModel):
    title: str
    description: str = ""
