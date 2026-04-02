# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# import os

# # Absolute path (important for Render)
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(BASE_DIR, "bunkmates.db")

# # SQLite database URL
# DATABASE_URL = f"sqlite:///{DB_PATH}"

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False},  # required for SQLite
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()
# Base.metadata.create_all(bind=engine)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("postgresql://bunkmaster_user:k4HkAGO0jvLk6c3erpwR4XnJDQ3yQg6Q@dpg-d7717rfkijhs739n0pg0-a.ohio-postgres.render.com/bunkmaster")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
Base.metadata.create_all(bind=engine)
