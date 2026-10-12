from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Session

import auth
import database
import models
import schemas
from database import engine

LOCAL_TZ = timezone(timedelta(hours=5, minutes=30))

app = FastAPI()

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_session = Depends(get_db)


@app.post("/register")
def register(user: schemas.UserCreate, db: Session = db_session):

    # Check if user already exists
    existing_user = (
        db.query(models.User).filter(models.User.phone == user.phone).first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password
    hashed_password = auth.hash_password(user.password)

    # Create new user
    new_user = models.User(
        phone=user.phone,
        name=user.name,
        password=hashed_password,
        flag=user.flag,
        joined_date=datetime.now(LOCAL_TZ).date(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "data": {"phone": new_user.phone, "name": new_user.name, "flag": new_user.flag},
    }


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = db_session):

    db_user = db.query(models.User).filter(models.User.phone == user.phone).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid phone number")

    if not auth.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = auth.create_token({"sub": db_user.phone})

    return {
        "message": "Login successful",
        "token": token,
        "name": db_user.name,
        "flag": db_user.flag,
        "joined_date": db_user.joined_date,
    }

#     # ✅ Recent activity (NO extra queries)
#     recent = []

#     # preload roommates in dict (IMPORTANT)
#     roommate_map = {r.id: r.name for r in roommates}

#     sorted_items = sorted(items, key=lambda x: (x.date, x.time), reverse=True)

#     for item in sorted_items[:5]:
#         recent.append({
#             "person": roommate_map.get(item.roommate_id, "Unknown"),
#             "description": item.name,
#             "amount": item.amount,
#             "date": item.date,
#         })

#     return {
#         "user_name": "jaggu",
#         "roommates": roommate_list,
#         "roommates_count": roommates_count,
#         "monthly_total": monthly_total,
#         "split": split,
#         "recent_activity": recent,
#     }




@app.get("/dashboard")
def get_dashboard(db: Session = db_session):

    now = datetime.now(LOCAL_TZ)

    # ✅ Month range (FAST instead of extract)
    start = date(now.year, now.month, 1)

    if now.month == 12:
        end = date(now.year + 1, 1, 1)
    else:
        end = date(now.year, now.month + 1, 1)

    # ✅ Load all roommates once and filter active in Python
    roommate_rows = db.query(models.Roommate).all()
    active_roommates = [r for r in roommate_rows if r.left_date is None]
    roommate_list = [{"id": r.id, "name": r.name} for r in active_roommates]
    roommates_count = len(active_roommates)

    # ✅ Monthly total (DB calculation, not Python loop)
    monthly_total = (
        db.query(func.sum(models.Item.amount))
        .filter(models.Item.date >= start, models.Item.date < end)
        .scalar()
        or 0
    )

    # ✅ Split calculation
    per_head = round(monthly_total / roommates_count) if roommates_count else 0
    split = [{"name": r["name"], "amount": per_head} for r in roommate_list]

    # ✅ Get recent activity directly from DB (NO Python sorting)
    recent_items = (
        db.query(models.Item)
        .filter(models.Item.date >= start, models.Item.date < end)
        .order_by(models.Item.date.desc(), models.Item.time.desc())
        .limit(5)
        .all()
    )

    # ✅ Map roommates from the single load
    roommate_map = {r.id: r.name for r in roommate_rows}

    recent = [
        {
            "person": roommate_map.get(item.roommate_id, "Unknown"),
            "description": item.name,
            "amount": item.amount,
            "date": item.date,
        }
        for item in recent_items
    ]

    return {
        "user_name": "jaggu",
        "roommates": roommate_list,
        "roommates_count": roommates_count,
        "monthly_total": monthly_total,
        "split": split,
        "recent_activity": recent,
    }


@app.post("/addroommates")
def add_roommate(roommate: schemas.RoommateCreate, db: Session = db_session):

    new_roommate = models.Roommate(
        name=roommate.name, role=roommate.role, joined_date=datetime.now(LOCAL_TZ).date()
    )

    db.add(new_roommate)
    db.commit()
    db.refresh(new_roommate)

    return {"message": "Roommate added successfully", "data": new_roommate}


@app.get("/roommates")
def get_roommates(db: Session = db_session):
    roommates = db.query(models.Roommate).filter(models.Roommate.left_date == None).all()

    return [
        {"id": r.id, "name": r.name, "role": r.role, "joined_date": r.joined_date}
        for r in roommates
    ]


@app.get("/roommates/all")
def get_all_roommates(db: Session = db_session):
    roommates = db.query(models.Roommate).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "role": r.role,
            "joined_date": r.joined_date,
            "left_date": r.left_date,
        }
        for r in roommates
    ]


@app.delete("/deleteroommates/{id}")
def delete_roommate(id: int, db: Session = db_session):

    roommate = db.query(models.Roommate).filter(models.Roommate.id == id).first()

    if not roommate:
        raise HTTPException(status_code=404, detail="Roommate not found")

    if roommate.left_date is not None:
        raise HTTPException(status_code=400, detail="Roommate already removed")

    roommate.left_date = datetime.now(LOCAL_TZ).date()
    db.commit()

    return {"message": "Roommate marked as left successfully", "left_date": roommate.left_date}


@app.get("/singleroommatedetails/{id}")
def get_roommate(id: int, db: Session = db_session):

    roommate = db.query(models.Roommate).filter(models.Roommate.id == id).first()

    if not roommate:
        raise HTTPException(status_code=404, detail="Roommate not found")

    return {
        "id": roommate.id,
        "name": roommate.name,
        "joined": roommate.joined_date,
        "left_date": roommate.left_date,
    }


@app.get("/items/roommate/{roommate_id}")
def get_items(roommate_id: int, db: Session = db_session):

    now = datetime.now(LOCAL_TZ)
    start = date(now.year, now.month, 1)

    if now.month == 12:
        end = date(now.year + 1, 1, 1)
    else:
        end = date(now.year, now.month + 1, 1)

    items = (
        db.query(models.Item)
        .filter(
            models.Item.roommate_id == roommate_id,
            models.Item.date >= start,
            models.Item.date < end,
        )
        .all()
    )

    return items  


@app.post("/items")
def add_item(item: schemas.ItemCreate, db: Session = db_session):

    now = datetime.now(LOCAL_TZ)

    new_item = models.Item(
        roommate_id=item.roommate_id,
        name=item.name,
        amount=item.amount,
        note=item.note,
        date=now.date(),
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {"message": "Item added successfully", "data": new_item}


@app.delete("/deleteitems/{item_id}")
def delete_item(item_id: int, db: Session = db_session):

    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return {"message": "Item deleted successfully"}


@app.post("/logout")
def logout():
    return {"message": "Logout successful"}


@app.get("/history")
def get_history(month: str, db: Session = db_session):

    year, month_num = map(int, month.split("-"))

    item_rows = (
        db.query(models.Item, models.Roommate)
        .outerjoin(models.Roommate, models.Roommate.id == models.Item.roommate_id)
        .filter(
            extract("year", models.Item.date) == year,
            extract("month", models.Item.date) == month_num,
        )
        .all()
    )

    result = [
        {
            "person": roommate.name if roommate else "Unknown",
            "description": item.name,
            "amount": item.amount,
            "date": item.date,
        }
        for item, roommate in item_rows
    ]

    total = sum(i["amount"] for i in result)

    return {"total": total, "transactions": result}


@app.get("/reports")
def get_reports(
    month: str = Query(None, description="Format: YYYY-MM"),
    db: Session = db_session,
):
    # ✅ Default to current month
    if not month:
        now = datetime.now(LOCAL_TZ)
        year = now.year
        month_num = now.month
        month = f"{year}-{str(month_num).zfill(2)}"
    else:
        year, month_num = map(int, month.split("-"))

    # ✅ Month range
    start = date(year, month_num, 1)
    if month_num == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month_num + 1, 1)

    # ✅ Get roommates who were present during the requested month
    roommates = (
        db.query(models.Roommate)
        .filter(
            models.Roommate.joined_date < end,
            or_(
                models.Roommate.left_date == None,
                models.Roommate.left_date >= start,
            ),
        )
        .all()
    )

    # ✅ Get items for selected month
    items = (
        db.query(models.Item)
        .filter(
            extract("year", models.Item.date) == year,
            extract("month", models.Item.date) == month_num,
        )
        .all()
    )

    # ✅ Total
    total_amount = sum(item.amount for item in items)

    count = len(roommates)
    per_head = round(total_amount / count) if count > 0 else 0

    report = []

    for r in roommates:
        spent = sum(item.amount for item in items if item.roommate_id == r.id)
        balance = spent - per_head

        report.append(
            {
                "roommate_id": r.id,
                "name": r.name,
                "spent": spent,
                "split": per_head,
                "balance": balance,
            }
        )

    return {
        "month": month,
        "total": total_amount,
        "per_head": per_head,
        "roommates_count": count,
        "report": report,
    }
