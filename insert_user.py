import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    return pwd_context.hash(password)

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

users = [
    # ("8722053941", "sagar", hash_password("king"), 3, "2024-01-10"),
    # ("8197996001", "rachappa", hash_password("king"), 2, "2024-02-15")
    # ("8904217658", "santosh", hash_password("santosh"),, 3, "2024-01-10")
]

cursor.executemany(
    "INSERT INTO users (phone, name, password, roommates, joined_date) VALUES (?, ?, ?, ?, ?)",
    users
)

conn.commit()
conn.close()

print(users)

print("Users inserted successfully ✅")