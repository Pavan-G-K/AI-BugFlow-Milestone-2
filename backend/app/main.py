import os, uuid, shutil
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .database import Base, engine, get_db
from .models import User, Issue, Comment, Activity, Attachment, Sprint
from .schemas import RegisterIn, LoginIn, IssueIn, IssueUpdate, CommentIn, SprintIn, PredictIn
from .security import hash_password, verify_password, create_token, current_user
from .ml import predict_severity

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AI BugFlow API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ISSUE_TYPES = {"Bug", "Feature Request", "Enhancement", "Technical Debt"}
SEVERITIES = {"Critical", "High", "Medium", "Low"}
PRIORITIES = {"P1", "P2", "P3", "P4"}
STATUSES = {"Open", "In Progress", "Testing", "Resolved", "Closed"}
TRANSITIONS = {"Open": {"In Progress"}, "In Progress": {"Testing"}, "Testing": {"Resolved", "In Progress"}, "Resolved": {"Closed", "In Progress"}, "Closed": set()}

def seed():
    db = next(get_db())
    try:
        if not db.query(User).filter_by(email="admin@bugflow.local").first():
            user = User(name="BugFlow Admin", email="admin@bugflow.local", password_hash=hash_password("Admin@123"), role="Admin")
            db.add(user); db.commit(); db.refresh(user)
            samples = [
                ("BUG-1001", "Checkout returns 500 error", "Customers cannot complete purchases after submitting payment.", "Payment", "High", "P1"),
                ("BUG-1002", "Dashboard chart labels overlap", "Labels overlap on smaller laptop screens.", "Dashboard", "Low", "P4"),
                ("BUG-1003", "Search filter returns stale results", "Changing date filters sometimes shows previous results.", "Search", "Medium", "P3"),
            ]
            for key,title,desc,module,severity,priority in samples:
                db.add(Issue(key=key,title=title,description=desc,module=module,severity=severity,priority=priority,reporter_id=user.id))
            db.commit()
    finally:
        db.close()
seed()

def log_activity(db, issue, user, action, details=""):
    db.add(Activity(issue_id=issue.id, actor_id=user.id, action=action, details=details))

def issue_dict(i):
    return {"id":i.id,"key":i.key,"title":i.title,"description":i.description,"steps_to_reproduce":i.steps_to_reproduce,"issue_type":i.issue_type,"severity":i.severity,"priority":i.priority,"module":i.module,"status":i.status,"assignee":i.assignee,"reporter_id":i.reporter_id,"sprint_id":i.sprint_id,"created_at":i.created_at.isoformat(),"updated_at":i.updated_at.isoformat()}

@app.get("/")
def root():
    return {"name":"AI BugFlow API","version":"2.0.0","docs":"/docs"}

@app.post("/api/auth/register")
def register(data: RegisterIn, db: Session=Depends(get_db)):
    if db.query(User).filter_by(email=data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user=User(name=data.name,email=data.email.lower(),password_hash=hash_password(data.password),role=data.role)
    db.add(user); db.commit(); db.refresh(user)
    return {"token":create_token(user.id),"user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role}}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session=Depends(get_db)):
    user=db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password,user.password_hash):
        raise HTTPException(401,"Incorrect email or password")
    return {"token":create_token(user.id),"user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role}}

@app.get("/api/auth/me")
def me(user: User=Depends(current_user)):
    return {"id":user.id,"name":user.name,"email":user.email,"role":user.role}

@app.get("/api/users")
def users(db: Session=Depends(get_db), user: User=Depends(current_user)):
    return [{"id":u.id,"name":u.name,"email":u.email,"role":u.role} for u in db.query(User).order_by(User.name).all()]

@app.get("/api/dashboard")
def dashboard(db: Session=Depends(get_db), user: User=Depends(current_user)):
    issues=db.query(Issue).all()
    return {"total":len(issues),"open":sum(i.status=="Open" for i in issues),"in_progress":sum(i.status=="In Progress" for i in issues),"testing":sum(i.status=="Testing" for i in issues),"resolved":sum(i.status in ("Resolved","Closed") for i in issues),"critical":sum(i.severity=="Critical" for i in issues),"by_severity":{s:sum(i.severity==s for i in issues) for s in SEVERITIES}}

@app.get("/api/issues")
def list_issues(search: str="", status: str="", severity: str="", issue_type: str="", sprint_id: int|None=None, backlog: bool=False, db: Session=Depends(get_db), user: User=Depends(current_user)):
    q=db.query(Issue)
    if search: q=q.filter((Issue.title.ilike(f"%{search}%")) | (Issue.key.ilike(f"%{search}%")) | (Issue.description.ilike(f"%{search}%")))
    if status: q=q.filter(Issue.status==status)
    if severity: q=q.filter(Issue.severity==severity)
    if issue_type: q=q.filter(Issue.issue_type==issue_type)
    if backlog: q=q.filter(Issue.sprint_id.is_(None))
    elif sprint_id is not None: q=q.filter(Issue.sprint_id==sprint_id)
    return [issue_dict(i) for i in q.order_by(desc(Issue.created_at)).all()]

@app.post("/api/issues")
def create_issue(data: IssueIn, db: Session=Depends(get_db), user: User=Depends(current_user)):
    if data.issue_type not in ISSUE_TYPES or data.severity not in SEVERITIES or data.priority not in PRIORITIES: raise HTTPException(400,"Invalid issue classification")
    issue=Issue(key=f"BUG-{uuid.uuid4().hex[:6].upper()}",**data.model_dump(),reporter_id=user.id)
    db.add(issue); db.commit(); db.refresh(issue); log_activity(db,issue,user,"Issue created",f"{issue.key} created"); db.commit()
    return issue_dict(issue)

@app.get("/api/issues/{issue_id}")
def get_issue(issue_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.get(Issue,issue_id)
    if not i: raise HTTPException(404,"Issue not found")
    return issue_dict(i)

@app.patch("/api/issues/{issue_id}")
def update_issue(issue_id:int, data:IssueUpdate, db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.get(Issue,issue_id)
    if not i: raise HTTPException(404,"Issue not found")
    values=data.model_dump(exclude_unset=True)
    for field, allowed in [("issue_type",ISSUE_TYPES),("severity",SEVERITIES),("priority",PRIORITIES)]:
        if field in values and values[field] not in allowed: raise HTTPException(400,f"Invalid {field}")
    if "status" in values:
        new=values["status"]
        if new not in STATUSES: raise HTTPException(400,"Unknown status")
        if new != i.status and new not in TRANSITIONS[i.status]:
            raise HTTPException(400,f"Invalid transition: {i.status} → {new}")
        if new != i.status: log_activity(db,i,user,"Status changed",f"{i.status} → {new}")
    if "sprint_id" in values and values["sprint_id"] is not None and not db.get(Sprint,values["sprint_id"]):
        raise HTTPException(404,"Sprint not found")
    for k,v in values.items():
        if k!="status" or v!=i.status: setattr(i,k,v)
    db.commit(); db.refresh(i)
    return issue_dict(i)

@app.delete("/api/issues/{issue_id}")
def delete_issue(issue_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.get(Issue,issue_id)
    if not i: raise HTTPException(404,"Issue not found")
    db.delete(i); db.commit()
    return {"message":"Issue deleted"}

@app.post("/api/issues/{issue_id}/comments")
def add_comment(issue_id:int, data:CommentIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.get(Issue,issue_id)
    if not i: raise HTTPException(404,"Issue not found")
    c=Comment(issue_id=i.id,author_id=user.id,body=data.body.strip()); db.add(c); log_activity(db,i,user,"Comment added",data.body[:120]); db.commit(); db.refresh(c)
    return {"id":c.id,"body":c.body,"author":user.name,"created_at":c.created_at.isoformat()}

@app.get("/api/issues/{issue_id}/comments")
def comments(issue_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    if not db.get(Issue,issue_id): raise HTTPException(404,"Issue not found")
    return [{"id":c.id,"body":c.body,"author":c.author.name,"created_at":c.created_at.isoformat()} for c in db.query(Comment).filter_by(issue_id=issue_id).order_by(Comment.created_at).all()]

@app.get("/api/issues/{issue_id}/activity")
def activity(issue_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    if not db.get(Issue,issue_id): raise HTTPException(404,"Issue not found")
    rows=db.query(Activity).filter_by(issue_id=issue_id).order_by(desc(Activity.created_at)).all()
    return [{"id":a.id,"actor":a.actor.name,"action":a.action,"details":a.details,"created_at":a.created_at.isoformat()} for a in rows]

@app.post("/api/issues/{issue_id}/attachments")
def upload_attachment(issue_id:int, file:UploadFile=File(...), db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.get(Issue,issue_id)
    if not i: raise HTTPException(404,"Issue not found")
    if not file.filename or len(file.filename)>240: raise HTTPException(400,"Invalid filename")
    ext=os.path.splitext(file.filename)[1]
    stored=f"{uuid.uuid4().hex}{ext}"
    path=os.path.join(UPLOAD_DIR,stored)
    with open(path,"wb") as out: shutil.copyfileobj(file.file,out)
    a=Attachment(issue_id=i.id,uploader_id=user.id,filename=os.path.basename(file.filename),stored_name=stored,content_type=file.content_type or "application/octet-stream")
    db.add(a); log_activity(db,i,user,"Attachment uploaded",a.filename); db.commit(); db.refresh(a)
    return {"id":a.id,"filename":a.filename,"url":f"/api/attachments/{a.id}"}

@app.get("/api/issues/{issue_id}/attachments")
def attachments(issue_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    return [{"id":a.id,"filename":a.filename,"uploader":a.uploader.name,"created_at":a.created_at.isoformat(),"url":f"/api/attachments/{a.id}"} for a in db.query(Attachment).filter_by(issue_id=issue_id).all()]

@app.get("/api/attachments/{attachment_id}")
def download_attachment(attachment_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    a=db.get(Attachment,attachment_id)
    if not a: raise HTTPException(404,"Attachment not found")
    path=os.path.join(UPLOAD_DIR,a.stored_name)
    if not os.path.isfile(path): raise HTTPException(404,"File missing")
    return FileResponse(path,filename=a.filename,media_type=a.content_type)

@app.post("/api/sprints")
def create_sprint(data:SprintIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    if data.end_date < data.start_date: raise HTTPException(400,"End date must be on or after start date")
    s=Sprint(**data.model_dump(),created_by=user.id); db.add(s); db.commit(); db.refresh(s)
    return {"id":s.id,"name":s.name,"start_date":s.start_date.isoformat(),"end_date":s.end_date.isoformat(),"goal":s.goal}

@app.get("/api/sprints")
def list_sprints(db:Session=Depends(get_db), user:User=Depends(current_user)):
    return [{"id":s.id,"name":s.name,"start_date":s.start_date.isoformat(),"end_date":s.end_date.isoformat(),"goal":s.goal,"issue_count":db.query(Issue).filter_by(sprint_id=s.id).count()} for s in db.query(Sprint).order_by(desc(Sprint.id)).all()]

@app.get("/api/sprints/{sprint_id}/board")
def sprint_board(sprint_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    if not db.get(Sprint,sprint_id): raise HTTPException(404,"Sprint not found")
    rows=[issue_dict(i) for i in db.query(Issue).filter_by(sprint_id=sprint_id).order_by(desc(Issue.created_at)).all()]
    return {"To Do":[i for i in rows if i["status"]=="Open"],"In Progress":[i for i in rows if i["status"] in ("In Progress","Testing")],"Done":[i for i in rows if i["status"] in ("Resolved","Closed")]}

@app.post("/api/issues/{issue_id}/assign-sprint/{sprint_id}")
def assign_sprint(issue_id:int,sprint_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.get(Issue,issue_id); s=db.get(Sprint,sprint_id)
    if not i or not s: raise HTTPException(404,"Issue or sprint not found")
    old=i.sprint_id; i.sprint_id=s.id; log_activity(db,i,user,"Sprint assigned",f"Sprint {s.name} (previous sprint: {old or 'Backlog'})"); db.commit()
    return issue_dict(i)

@app.delete("/api/issues/{issue_id}/sprint")
def remove_from_sprint(issue_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.get(Issue,issue_id)
    if not i: raise HTTPException(404,"Issue not found")
    i.sprint_id=None; log_activity(db,i,user,"Moved to backlog","Sprint assignment removed"); db.commit()
    return issue_dict(i)

@app.post("/api/ml/predict-severity")
def ml_predict(data:PredictIn, user:User=Depends(current_user)):
    return predict_severity(data.title,data.description)
