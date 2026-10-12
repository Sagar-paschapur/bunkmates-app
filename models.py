from datetime import datetime, timezone, date, timedelta

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time

from database import Base

LOCAL_TZ = timezone(timedelta(hours=5, minutes=30))

# IST = pytz.timezone("Asia/Kolkata")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True)
    name = Column(String(50))
    password = Column(String(255))
    flag = Column(Integer)
    joined_date = Column(Date, default=lambda: datetime.now(LOCAL_TZ).date())


class Roommate(Base):
    __tablename__ = "roommates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    role = Column(String(50))
    joined_date = Column(Date, default=lambda: datetime.now(LOCAL_TZ).date())
    left_date = Column(Date, nullable=True)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    roommate_id = Column(Integer, ForeignKey("roommates.id"))
    name = Column(String(100))
    amount = Column(Integer)
    date = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    # time = Column(Time, default=lambda: datetime.now(IST).time())
    time = Column(
        Time,
        default=lambda: (datetime.utcnow() + timedelta(hours=5, minutes=30)).time(),
    )
    note = Column(String(200))
