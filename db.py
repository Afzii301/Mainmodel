import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv



# Load .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create Engine
engine = create_engine(DATABASE_URL)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()
Base.metadata.create_all(bind=engine)