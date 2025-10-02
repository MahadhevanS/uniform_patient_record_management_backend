from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings
from app.db.database import Base, engine
from contextlib import asynccontextmanager
import time

# --- Database Table Initialization ---

def create_db_tables():
    """
    Attempts to create all tables defined by SQLAlchemy Base.
    This function will wait for the database to be available.
    """
    MAX_RETRIES = 5
    RETRY_DELAY = 5 # seconds
    
    print("Attempting to connect to the database and create tables...")
    
    for attempt in range(MAX_RETRIES):
        try:
            # This creates the tables based on all models that inherit from Base
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully (if they didn't exist).")
            return
        except Exception as e:
            print(f"❌ Database connection failed on attempt {attempt + 1}/{MAX_RETRIES}. Error: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("🔴 Failed to connect to the database after multiple retries. Exiting.")
                raise e # Re-raise the exception after exhausting retries

# --- Application Lifespan Management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # 1. Database Initialization
    create_db_tables()
    
    # 2. Yield control to the application
    yield

# --- FastAPI Application Initialization ---

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/openapi.json",
    lifespan=lifespan # Use the lifespan manager
)

origins = [
    "http://localhost:5176",  # Your React/Vite frontend URL
    "http://127.0.0.1:5176",
    "https://*.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # Allows requests from your frontend origin
    allow_credentials=True,            # Allows cookies/authorization headers
    allow_methods=["*"],               # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],               # Allows all headers (including Authorization header for JWT)
)   
# Include the main router
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Uniform Patient Record Platform API"}

if __name__ == "__main__":
    # This block is for direct execution (e.g., python main.py)
    # Note: Uvicorn is usually run via the command line for production/development
    import uvicorn
    # The 'main:app' syntax is common when running Uvicorn from the command line
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
