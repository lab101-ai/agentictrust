import os
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import select, Session, SQLModel, Field, Relationship
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from .database import init_db, get_session
from .models import User, Ticket, UserCreate, UserRead, UserProfile, TicketRead, Company, CompanyTicketStats, UserTicketStatusStats, OverallTicketStats
from .auth import create_token, get_current_user, get_optional_current_user, get_password_hash
from .agent import get_agent_response
from .seed import seed_data

load_dotenv(dotenv_path="demo/.env")

# Create FastAPI app
app = FastAPI(title="Customer Support Demo")

# Mount static files
app.mount("/static", StaticFiles(directory="demo/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="demo/templates")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://0.0.0.0:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve index.html
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            # No longer need to pass OAuth vars - using window.location.origin in template
        }
    )

# Initialize the database on startup
@app.on_event("startup")
def on_startup():
    init_db()
    # Seed data on startup
    db_session = next(get_session()) # Obtain a session
    try:
        print("Running seed_data on startup...")
        seed_data(db_session)
        print("seed_data on startup completed.")
    finally:
        db_session.close() # Ensure session is closed

# --- New Endpoint to List Users for Dropdown Login ---
@app.get("/api/users", response_model=list[UserRead])
def list_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

# OAuth2 token endpoint
@app.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    return create_token(form_data, session)

# Signup endpoint
@app.post("/signup", response_model=UserRead)
def signup(user_data: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, hashed_password=hashed_password)
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user

# Get tickets for the authenticated user
@app.get("/tickets", response_model=list[TicketRead])
def read_tickets(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    tickets_query = (
        select(Ticket)
        .options(
            selectinload(Ticket.owner)
            .selectinload(User.profile)
            .selectinload(UserProfile.company)
        )
        .where(Ticket.user_id == current_user.id)
    )
    tickets = session.exec(tickets_query).all()

    return [
        TicketRead(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            public=ticket.public,
            status=ticket.status,
            owner_id=ticket.user_id,
            owner_name=(
                f"{ticket.owner.profile.first_name} {ticket.owner.profile.last_name}"
                if ticket.owner and ticket.owner.profile
                else None
            ),
            owner_company=(
                ticket.owner.profile.company.name
                if ticket.owner and ticket.owner.profile and ticket.owner.profile.company
                else None
            ),
        )
        for ticket in tickets
    ]

# Get all public tickets
@app.get("/api/public_tickets", response_model=list[TicketRead])
def read_public_tickets(session: Session = Depends(get_session)):
    tickets_query = (
        select(Ticket)
        .options(
            selectinload(Ticket.owner)
            .selectinload(User.profile)
            .selectinload(UserProfile.company)
        )
        .where(Ticket.public == True)
    )
    tickets = session.exec(tickets_query).all()
    return [
        TicketRead(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            public=ticket.public,
            status=ticket.status,
            owner_id=ticket.user_id,
            owner_name=(
                f"{ticket.owner.profile.first_name} {ticket.owner.profile.last_name}"
                if ticket.owner and ticket.owner.profile
                else None
            ),
            owner_company=(
                ticket.owner.profile.company.name
                if ticket.owner and ticket.owner.profile and ticket.owner.profile.company
                else None
            ),
        )
        for ticket in tickets
    ]

# --- Statistics Endpoints ---
@app.get("/api/stats/company_tickets", response_model=list[CompanyTicketStats])
def get_company_ticket_stats(session: Session = Depends(get_session)):
    query = (
        select(
            Company.name.label("company_name"),
            func.count(Ticket.id).label("ticket_count")
        )
        .select_from(Ticket)
        .join(User, Ticket.user_id == User.id)
        .join(UserProfile, User.id == UserProfile.user_id)
        .join(Company, UserProfile.company_id == Company.id)
        .group_by(Company.name)
        .order_by(Company.name)
    )
    results = session.exec(query).all()
    return [CompanyTicketStats(company_name=row.company_name, ticket_count=row.ticket_count) for row in results]

@app.get("/api/stats/user_ticket_status", response_model=UserTicketStatusStats)
def get_user_ticket_status_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    open_tickets = session.scalar(
        select(func.count(Ticket.id))
        .where(Ticket.user_id == current_user.id, Ticket.status == "Open")
    ) or 0
    in_progress_tickets = session.scalar(
        select(func.count(Ticket.id))
        .where(Ticket.user_id == current_user.id, Ticket.status == "In Progress")
    ) or 0
    closed_tickets = session.scalar(
        select(func.count(Ticket.id))
        .where(Ticket.user_id == current_user.id, Ticket.status == "Closed")
    ) or 0
    return UserTicketStatusStats(
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets
    )

@app.get("/api/stats/overall_tickets", response_model=OverallTicketStats)
def get_overall_ticket_stats(session: Session = Depends(get_session)):
    total_tickets = session.scalar(select(func.count(Ticket.id))) or 0
    public_tickets = session.scalar(select(func.count(Ticket.id)).where(Ticket.public == True)) or 0
    private_tickets = session.scalar(select(func.count(Ticket.id)).where(Ticket.public == False)) or 0
    return OverallTicketStats(
        total_tickets=total_tickets,
        public_tickets=public_tickets,
        private_tickets=private_tickets
    )

# Chat endpoint for AI responses
@app.post("/chat")
def chat(payload: dict, current_user: User = Depends(get_optional_current_user)):
    prompt = payload.get("prompt") or payload.get("query")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    if current_user and current_user.profile:
        first_name = current_user.profile.first_name
        last_name = current_user.profile.last_name
        
    response = get_agent_response(prompt, first_name=first_name, last_name=last_name)
    return {"response": response}

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}

# Get the authenticated user
@app.get("/users/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # The UserProfile is now eager-loaded with the User object by get_current_user
    
    first_name = current_user.profile.first_name if current_user.profile else None
    last_name = current_user.profile.last_name if current_user.profile else None
    user_role = current_user.profile.role if current_user.profile else None

    return UserRead(
        id=current_user.id, 
        username=current_user.username, 
        first_name=first_name,
        last_name=last_name,
        role=user_role
    )

# Statistics Endpoints