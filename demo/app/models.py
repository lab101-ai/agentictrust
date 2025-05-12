from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str 
    profile: Optional["UserProfile"] = Relationship(back_populates="user")
    tickets: List["Ticket"] = Relationship(back_populates="owner")

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None

class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    profiles: List["UserProfile"] = Relationship(back_populates="company")

class TicketBase(SQLModel):
    title: str
    description: str
    public: bool = False
    status: str = Field(default="Open")

class TicketRead(TicketBase):
    id: int
    owner_id: Optional[int]
    owner_name: Optional[str] = None
    owner_company: Optional[str] = None

class Ticket(TicketBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id") 
    owner: Optional[User] = Relationship(back_populates="tickets")

class UserProfileBase(SQLModel):
    first_name: str
    last_name: str
    email: str = Field(index=True, unique=True) 
    company_id: Optional[int] = Field(default=None, foreign_key="company.id") 
    role: Optional[str] = None

class UserProfile(UserProfileBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True) 
    user: Optional[User] = Relationship(back_populates="profile")
    company: Optional[Company] = Relationship(back_populates="profiles")

# Pydantic models for Statistics
class CompanyTicketStats(SQLModel):
    company_name: str
    ticket_count: int

class UserTicketStatusStats(SQLModel):
    open_tickets: int
    in_progress_tickets: int
    closed_tickets: int

class OverallTicketStats(SQLModel):
    total_tickets: int
    public_tickets: int
    private_tickets: int