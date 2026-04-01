from pydantic import BaseModel

class UserLogin(BaseModel):
    phone: str
    password: str
    
class RoommateCreate(BaseModel):
    name: str
    role: str
    

class ItemCreate(BaseModel):
    roommate_id: int   # ✅ ADD THIS
    name: str
    amount: int
    note: str