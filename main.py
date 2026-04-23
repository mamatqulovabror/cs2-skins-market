from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, init_db, User, Skin
from typing import Optional
import os, shutil, uuid, httpx

app = FastAPI(title="CS2 Skins Market")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
APP_URL = os.getenv("APP_URL", "https://cs2-skins-market-production.up.railway.app")

@app.on_event("startup")
def startup():
    init_db()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return FileResponse("index.html")

# --- TELEGRAM WEBHOOK ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if not BOT_TOKEN:
        return {"ok": False}
    data = await request.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    first_name = message.get("from", {}).get("first_name", "User")
    if not chat_id:
        return {"ok": True}
    if text in ["/start", "/market"]:
        payload = {
            "chat_id": chat_id,
            "text": f"Salom, {first_name}! CS2 Skins Market ga xush kelibsiz! Skinlarni ko'rish va sotish uchun tugmani bosing.",
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🎮 CS2 Market ochish", "web_app": {"url": APP_URL}}
                ]]
            }
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
    return {"ok": True}

# --- USERS ---
@app.post("/api/users/auth")
def auth_user(
    telegram_id: int = Form(...),
    first_name: str = Form(...),
    username: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    photo_url: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, first_name=first_name,
                    username=username, last_name=last_name, photo_url=photo_url)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@app.get("/api/users/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.patch("/api/users/{telegram_id}")
def update_user(
    telegram_id: int,
    trade_link: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    notifications: Optional[bool] = Form(None),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if trade_link is not None: user.trade_link = trade_link
    if language is not None: user.language = language
    if notifications is not None: user.notifications = notifications
    db.commit()
    db.refresh(user)
    return user

# --- SKINS ---
@app.get("/api/skins")
def get_skins(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    skins = db.query(Skin).filter(Skin.is_sold == False).offset(skip).limit(limit).all()
    return skins

@app.post("/api/skins")
async def create_skin(
    seller_id: int = Form(...),
    name: str = Form(...),
    price: float = Form(...),
    exterior: str = Form(...),
    float_value: Optional[float] = Form(None),
    pattern: Optional[int] = Form(None),
    skin_type: str = Form(...),
    description: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = f"{UPLOAD_DIR}/{filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(image.file, f)
    skin = Skin(
        seller_id=seller_id, name=name, price=price, exterior=exterior,
        float_value=float_value, pattern=pattern, skin_type=skin_type,
        description=description, image_url=f"/uploads/{filename}"
    )
    db.add(skin)
    db.commit()
    db.refresh(skin)
    return skin

@app.post("/api/skins/{skin_id}/buy")
def buy_skin(skin_id: int, buyer_id: int = Form(...), db: Session = Depends(get_db)):
    skin = db.query(Skin).filter(Skin.id == skin_id).first()
    if not skin or skin.is_sold:
        raise HTTPException(400, "Skin not available")
    skin.is_sold = True
    db.commit()
    return {"status": "success", "message": "Purchase request sent"}
