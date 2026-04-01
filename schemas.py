from pydantic import BaseModel


class UserCreate(BaseModel):
    phone: str
    name: str
    password: str
    flag: int


class UserLogin(BaseModel):
    phone: str
    password: str


class RoommateCreate(BaseModel):
    name: str
    role: str


class ItemCreate(BaseModel):
    roommate_id: int  # ✅ ADD THIS
    name: str
    amount: int
    note: str
