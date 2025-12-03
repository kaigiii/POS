import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///pos.db'

# Render provides DATABASE_URL that may start with 'postgres://'.
# SQLAlchemy/psycopg prefer the 'postgresql://' scheme — convert if needed.
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# sqlite needs check_same_thread flag
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {}

# Create engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
