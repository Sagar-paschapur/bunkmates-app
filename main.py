from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import models, schemas, database, auth
from datetime import date, datetime, timezone
from sqlalchemy import extract
from fastapi import Query

from sqlalchemy import func
from database import engine

# ✅ Create app ONLY ONCE
app = FastAPI()

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# models.Base.metadata.create_all(bind=database.engine)


@app.on_event("startup")
def on_startup():
    import models
    models.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# from database import engine, Base
# import models

# @app.get("/reset-db")
# def reset_db():
#     Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)
#     return {"message": "Database reset successful"}


@app.get("/db_init")
def init_db(db: Session = Depends(get_db)):

    # ✅ Create tables
    models.Base.metadata.create_all(bind=database.engine)

    create_user = models.User(
        phone="8722053941",
        name="sagar",
        password=auth.hash_password("password123"),
        flag=1,
        joined_date=datetime.now(timezone.utc).date(),
    )

    db.add(create_user)
    db.commit()
    db.refresh(create_user)

    return {"message": "Database initialized successfully"}


@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):

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
        joined_date=date.today(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "data": {"phone": new_user.phone, "name": new_user.name, "flag": new_user.flag},
    }


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):

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


# @app.get("/dashboard")
# def get_dashboard(db: Session = Depends(get_db)):

#     now = datetime.now()

#     # ✅ Get roommates
#     roommates = db.query(models.Roommate).all()
#     roommate_list = [{"id": r.id, "name": r.name} for r in roommates]
#     roommates_count = len(roommate_list)

#     # ✅ Get ONLY current month items (IMPORTANT)
#     items = db.query(models.Item).filter(
#         extract("month", models.Item.date) == now.month,
#         extract("year", models.Item.date) == now.year
#     ).all()

#     # ✅ Monthly total (FAST)
#     monthly_total = sum(item.amount for item in items)

#     # ✅ Split
#     per_head = round(monthly_total / roommates_count) if roommates_count else 0
#     split = [{"name": r["name"], "amount": per_head} for r in roommate_list]

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
def get_dashboard(db: Session = Depends(get_db)):

    now = datetime.now()

    # ✅ Month range (FAST instead of extract)
    start = date(now.year, now.month, 1)

    if now.month == 12:
        end = date(now.year + 1, 1, 1)
    else:
        end = date(now.year, now.month + 1, 1)

    # ✅ Get roommates
    roommates = db.query(models.Roommate).all()
    roommate_list = [{"id": r.id, "name": r.name} for r in roommates]
    roommates_count = len(roommates)

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

    # ✅ Map roommates (avoid extra DB queries)
    roommate_map = {r.id: r.name for r in roommates}

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
def add_roommate(roommate: schemas.RoommateCreate, db: Session = Depends(get_db)):

    new_roommate = models.Roommate(
        name=roommate.name, role=roommate.role, joined_date=str(date.today())
    )

    db.add(new_roommate)
    db.commit()
    db.refresh(new_roommate)

    return {"message": "Roommate added successfully", "data": new_roommate}


@app.get("/roommates")
def get_roommates(db: Session = Depends(get_db)):
    roommates = db.query(models.Roommate).all()

    return [
        {"id": r.id, "name": r.name, "role": r.role, "joined_date": r.joined_date}
        for r in roommates
    ]


@app.delete("/deleteroommates/{id}")
def delete_roommate(id: int, db: Session = Depends(get_db)):

    roommate = db.query(models.Roommate).filter(models.Roommate.id == id).first()

    if not roommate:
        raise HTTPException(status_code=404, detail="Roommate not found")

    # ✅ DELETE CHILD RECORDS FIRST
    db.query(models.Item).filter(models.Item.roommate_id == id).delete()

    # ✅ THEN DELETE ROOMMATE
    db.delete(roommate)
    db.commit()

    return {"message": "Roommate deleted successfully"}


@app.get("/singleroommatedetails/{id}")
def get_roommate(id: int, db: Session = Depends(get_db)):

    roommate = db.query(models.Roommate).filter(models.Roommate.id == id).first()

    if not roommate:
        raise HTTPException(status_code=404, detail="Roommate not found")

    return {"id": roommate.id, "name": roommate.name, "joined": roommate.joined_date}


@app.get("/items/roommate/{roommate_id}")
def get_items(roommate_id: int, db: Session = Depends(get_db)):

    now = datetime.now()
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
def add_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):

    now = datetime.now()

    new_item = models.Item(
        roommate_id=item.roommate_id,
        name=item.name,
        amount=item.amount,
        note=item.note,
        date=now.strftime("%Y-%m-%d"),
        # time=now.strftime("%I:%M %p"),
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {"message": "Item added successfully", "data": new_item}


@app.delete("/deleteitems/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):

    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return {"message": "Item deleted successfully"}


@app.post("/logout")
def logout(request: Request):

    return {"message": "Logout successful"}


@app.get("/history")
def get_history(month: str, db: Session = Depends(get_db)):

    year, month_num = map(int, month.split("-"))

    items = (
        db.query(models.Item)
        .filter(
            extract("year", models.Item.date) == year,
            extract("month", models.Item.date) == month_num,
        )
        .all()
    )

    result = []

    for item in items:
        roommate = (
            db.query(models.Roommate)
            .filter(models.Roommate.id == item.roommate_id)
            .first()
        )

        result.append(
            {
                "person": roommate.name,
                "description": item.name,
                "amount": item.amount,
                "date": item.date,
            }
        )

    total = sum(i["amount"] for i in result)

    return {"total": total, "transactions": result}


@app.get("/reports")
def get_reports(
    month: str = Query(None, description="Format: YYYY-MM"),
    db: Session = Depends(get_db),
):
    # ✅ Default to current month
    if not month:
        now = datetime.now()
        year = now.year
        month_num = now.month
        month = f"{year}-{str(month_num).zfill(2)}"
    else:
        year, month_num = map(int, month.split("-"))

    # ✅ Get roommates
    roommates = db.query(models.Roommate).all()

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
