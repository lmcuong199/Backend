import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event
from sqlalchemy.engine import Engine
from datetime import timezone

from sqlalchemy import DateTime, TypeDecorator


class UtcDateTime(TypeDecorator):
    """Always store UTC; always hand back a timezone-aware UTC datetime.

    SQLite silently drops timezone offsets, so we convert to UTC before
    writing and re-attach UTC when reading.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Python -> database."""
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)   # no offset given: assume UTC
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        """Database -> Python."""
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


# reads a .env file into environment variables
load_dotenv()

# use the env var if set, otherwise fall back to a local file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workout.db")

# engine is the connection pool - the low-level thing that actually opens SQLite
engine = create_engine(
    DATABASE_URL,
    # check_same_thread: False is a SQLite-only quirk
    # SQLite normally refuses to be used from a different thread than the one that opened it, but FastAPI handles requests across threads
    # This flag is safe here bcs SQLAlchemy gives each request its own session anyway
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# calling SessionLocal() produces a new session
# a session is your workspace for 1 request - you add any query objects in it, then commit() to write them 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all your table classes inherit from. It's how SQLAlchemy collects the list of tables it knows about
Base = declarative_base()

# SQLite disables foreign key enforcement by default; turn it on per connection
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# get_db() is the most FastAPI-specific idea
def get_db():
    db = SessionLocal()
    try:
        # yield makes it a dependency: FastAPI runs everything before the yield, hands the session to your endpoint, and after theresponse is sent runs the finally block to clse it
        # You get a fresh session per request that's guaranteed to be cleaned up, even if your code raises
        yield db
    finally:
        db.close()
