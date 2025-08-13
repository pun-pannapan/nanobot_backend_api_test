from fastapi import FastAPI, Depends, HTTPException, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import os

from .db import Base, engine
from .models import User
from .schemas import UserCreate, UserUpdate, UserOut, Token
from .auth import get_db, authenticate_user, create_access_token, get_current_user
from .utils import get_password_hash
from .websocket import manager

app = FastAPI(title="user_api", version="1.0.0")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _public_user_dict(u: User) -> dict:
    return {"id": u.id, "username": u.username, "full_name": u.full_name, "email": u.email}

Base.metadata.create_all(bind=engine)

@app.post("/auth/login", response_model=Token, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/users", response_model=UserOut, tags=["users"], status_code=201)
async def create_user(payload: UserCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, "Username already exists")
    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    await manager.broadcast({"event": "user_created", "user_id": user.id, "username": user.username})
    return user

@app.get("/users", response_model=List[UserOut], tags=["users"])
async def list_users(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(User).order_by(User.id).all()

@app.get("/users/{user_id}", response_model=UserOut, tags=["users"])
async def get_user(user_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.put("/users/{user_id}", response_model=UserOut, tags=["users"])
async def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    before = _public_user_dict(user)
    changes = {}

    if payload.username is not None and payload.username != user.username:
        if db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(400, "Username already exists")
        user.username = payload.username
        changes["username"] = payload.username

    if payload.full_name is not None and payload.full_name != user.full_name:
        user.full_name = payload.full_name
        changes["full_name"] = payload.full_name

    if payload.email is not None and payload.email != user.email:
        user.email = payload.email
        changes["email"] = payload.email

    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)

    await manager.broadcast({
        "event": "user_updated",
        "user_id": user.id,
        "changes": changes, 
        "data": _public_user_dict(user),
        "before": before
    })
    return user

@app.delete("/users/{user_id}", status_code=204, tags=["users"])
async def delete_user(user_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    snapshot = _public_user_dict(user)
    db.delete(user)
    db.commit()
    await manager.broadcast({
        "event": "user_deleted",
        "user_id": user_id,
        "data": snapshot
    })
    return

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        manager.disconnect(ws)

@app.on_event("startup")
async def ensure_admin():
    from .auth import get_db
    db = next(get_db())
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(username="admin", full_name="Admin", email=None, hashed_password=get_password_hash("admin1234"))
        db.add(admin)
        db.commit()