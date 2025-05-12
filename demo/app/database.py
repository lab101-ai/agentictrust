from sqlmodel import SQLModel, create_engine, Session

# SQLite database URL
DATABASE_URL = "sqlite:///./.agentictrust/db/demo.db"

# Create engine with check_same_thread for FastAPI async compatibility
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Initialize the database (to be called at startup)
def init_db():
    SQLModel.metadata.create_all(engine)

# Dependency for FastAPI to get DB session
def get_session():
    with Session(engine) as session:
        yield session 