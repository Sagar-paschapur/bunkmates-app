from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import models, schemas, database, auth
from datetime import date, datetime, timezone
from sqlalchemy import extract

from database import engine, Base
import models

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

# ✅ Create tables
models.Base.metadata.create_all(bind=database.engine)


# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        


@app.get("/reset-db")
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"message": "Database reset successful"}


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


# ----------------------
# Login API
# ----------------------
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


@app.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):

    roommates = db.query(models.Roommate).all()
    items = db.query(models.Item).all()

    # ✅ Roommates
    roommate_list = [{"id": r.id, "name": r.name} for r in roommates]

    roommates_count = len(roommate_list)

    # ✅ Monthly total
    now = datetime.now()
    monthly_total = 0

    for item in items:
        item_date = datetime.strptime(item.date, "%Y-%m-%d")
        if item_date.month == now.month and item_date.year == now.year:
            monthly_total += item.amount

    # ✅ Split per person
    per_head = 0
    if roommates_count > 0:
        per_head = round(monthly_total / roommates_count)

    split = [{"name": r["name"], "amount": per_head} for r in roommate_list]

    # ✅ Recent Activity (latest 5)
    sorted_items = sorted(items, key=lambda x: f"{x.date} {x.time}", reverse=True)

    recent = []
    for item in sorted_items[:5]:
        roommate = (
            db.query(models.Roommate)
            .filter(models.Roommate.id == item.roommate_id)
            .first()
        )

        recent.append(
            {
                "person": roommate.name,
                "description": item.name,
                "amount": item.amount,
                "date": item.date,
            }
        )

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

    items = db.query(models.Item).filter(models.Item.roommate_id == roommate_id).all()

    return items


from datetime import datetime


@app.post("/items")
def add_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):

    now = datetime.now()

    new_item = models.Item(
        roommate_id=item.roommate_id,
        name=item.name,
        amount=item.amount,
        note=item.note,
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%I:%M %p"),
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
