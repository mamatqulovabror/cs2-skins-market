from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skins.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    trade_link = Column(String, nullable=True)
    steam_id = Column(String, nullable=True)
    language = Column(String, default="en")
    notifications = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Skin(Base):
    __tablename__ = "skins"
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer)
    name = Column(String)
    price = Column(Float)
    exterior = Column(String)
    float_value = Column(Float, nullable=True)
    pattern = Column(Integer, nullable=True)
    skin_type = Column(String)
    image_url = Column(String)
    description = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    tg_username = Column(String, nullable=True)
    is_sold = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Skin).count() == 0:
        demo_skins = [
            Skin(seller_id=1, name="Kukri Knife | Crimson Web", price=299.99, exterior="Factory New",
                 float_value=0.0312, pattern=412, skin_type="Knife",
                 image_url="https://community.cloudflare.steamstatic.com/economy/image/class/730/310776770/200fx200f",
                 description="Rare pattern #412 Crimson Web"),
            Skin(seller_id=1, name="AK-47 | Fire Serpent", price=189.50, exterior="Field-Tested",
                 float_value=0.2341, pattern=None, skin_type="Rifle",
                 image_url="https://community.cloudflare.steamstatic.com/economy/image/class/730/310776770/200fx200f",
                 description="Battle-worn beauty"),
        ]
        db.add_all(demo_skins)
        db.commit()
    db.close()
