import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text

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
    # Ensure `is_deleted` column exists on `product` for soft-delete feature.
    # create_all won't alter existing tables, so attempt to add the column if missing.
    try:
        dialect = engine.dialect.name
        if dialect == 'postgresql':
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE product ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false"))
        elif dialect == 'sqlite':
            with engine.begin() as conn:
                res = conn.execute(text("PRAGMA table_info('product')")).fetchall()
                cols = [row[1] for row in res]
                if 'is_deleted' not in cols:
                    conn.execute(text("ALTER TABLE product ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        else:
            # Generic attempt: try ALTER with IF NOT EXISTS, ignore errors if unsupported
            with engine.begin() as conn:
                try:
                    conn.execute(text("ALTER TABLE product ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false"))
                except Exception:
                    pass
    except Exception:
        # If any of the above fails, we don't want to crash startup; leave existing schema as-is.
        pass
