from sqlalchemy import Column, Integer, String, Date, ForeignKey, Time
from datetime import datetime, timezone
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True)
    name = Column(String(50))
    password = Column(String(255))
    flag = Column(Integer)
    joined_date = Column(Date, default=datetime.now(timezone.utc).date())


class Roommate(Base):
    __tablename__ = "roommates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    role = Column(String(50))
    joined_date = Column(String(20))


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    roommate_id = Column(Integer, ForeignKey("roommates.id"))
    name = Column(String(100))
    amount = Column(Integer)
    date = Column(Date, default=datetime.utcnow)
    time = Column(Time, default=datetime.utcnow)
    note = Column(String(200))
