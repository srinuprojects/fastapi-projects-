from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection URL
# Format: postgresql://username:password@host:port/database_name
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/TodoApplicationDatabase"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

