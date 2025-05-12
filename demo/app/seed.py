from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from passlib.context import CryptContext

from .database import engine, init_db, get_session
from .models import User, UserProfile, Ticket, Company

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_PASSWORD = "password123" # Changed for consistency with frontend dropdown login

COMPANY_NAMES = [
    "Cisco",
    "Google",
    "Meta"
]

USER_PROFILES_DATA = [
    {"email": "cmeyer@cisco.com", "first_name": "Carol", "last_name": "Meyer", "company_name": "Cisco", "role": "executive"},
    {"email": "epatel@cisco.com", "first_name": "Eve", "last_name": "Patel", "company_name": "Cisco", "role": "executive"},
    {"email": "gkim@cisco.com", "first_name": "Grace", "last_name": "Kim", "company_name": "Cisco", "role": "sales"},
    {"email": "hfu@cisco.com", "first_name": "Henry", "last_name": "Fu", "company_name": "Cisco", "role": "sales"},
    {"email": "gking@google.com", "first_name": "Gina", "last_name": "King", "company_name": "Google", "role": "executive"},
    {"email": "hyoung@google.com", "first_name": "Harold", "last_name": "Young", "company_name": "Google", "role": "executive"},
    {"email": "idavis@google.com", "first_name": "Ivan", "last_name": "Davis", "company_name": "Google", "role": "sales"},
    {"email": "jroberts@meta.com", "first_name": "Julia", "last_name": "Roberts", "company_name": "Meta", "role": "executive"},
    {"email": "kwright@meta.com", "first_name": "Kevin", "last_name": "Wright", "company_name": "Meta", "role": "executive"},
    {"email": "lgreen@meta.com", "first_name": "Liam", "last_name": "Green", "company_name": "Meta", "role": "sales"},
]

TICKET_DATA = [
    # User 1 (cmeyer@cisco.com)
    {"title": 'Project Alpha Kickoff', "description": 'Agenda and milestones for Project Alpha.', "public": True, "status": "Open"},
    {"title": 'Q3 Budget Review', "description": 'Review finance reports for Q3.', "public": False, "status": "In Progress"},
    # User 2 (epatel@cisco.com)
    {"title": 'Client Meeting Prep - Cisco', "description": 'Prepare presentation for upcoming client meeting.', "public": True, "status": "Open"},
    {"title": 'Performance Review Notes', "description": 'Notes for team performance reviews.', "public": False, "status": "Closed"},
    # User 3 (gkim@cisco.com) - Assuming 2 tickets per user for round-robin
    {"title": 'New Lead Follow-up', "description": 'Follow up with leads from last week\'s conference.', "public": False, "status": "Open"},
    {"title": 'Sales Target Analysis', "description": 'Analyze Q3 sales targets vs actuals.', "public": True, "status": "In Progress"},
]

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_data(session: Session):
    print("Seeding data...")
    hashed_default_password = get_password_hash(DEFAULT_PASSWORD)

    # Seed Companies
    created_companies = {}
    for company_name in COMPANY_NAMES:
        existing_company = session.query(Company).filter(Company.name == company_name).first()
        if existing_company:
            print(f"Company {company_name} already exists.")
            created_companies[company_name] = existing_company
        else:
            db_company = Company(name=company_name)
            session.add(db_company)
            session.flush() # Flush to get ID if needed immediately, or commit later
            created_companies[company_name] = db_company
            print(f"Created company: {db_company.name}")
    # It's safer to commit companies first if other parts depend on their IDs being finalized
    # For this script structure, flushing and using the objects might be okay if not committing until the end.
    # However, to ensure IDs are definitely available if UserProfile creation relies on committed Company IDs:
    try:
        session.commit() # Commit companies
        print("Companies committed.")
        # Re-fetch or use flushed objects if their IDs are stable post-flush and pre-commit for UserProfile
        # For simplicity here, we'll re-query or assume flushed IDs are usable IF NOT COMMITTING TILL END.
        # Let's adjust to ensure robust ID fetching for UserProfile.
        for name, company_obj in created_companies.items():
            if not company_obj.id: # If somehow ID is not set (e.g. after rollback and re-run without full clear)
                 refetched_company = session.query(Company).filter(Company.name == name).first()
                 if refetched_company:
                     created_companies[name] = refetched_company
                 else:
                     # This case should ideally not happen if commit was successful or creation was fine
                     print(f"ERROR: Company {name} was not found after attempted creation/commit.")
                     # Handle error appropriately, maybe skip users of this company or raise error

    except IntegrityError as e:
        session.rollback()
        print(f"Error committing companies (likely duplicate names if run multiple times without clearing DB): {e}")
        # If companies failed, we might not want to proceed or handle carefully
        # For now, we'll try to proceed but UserProfiles might fail to link
    except Exception as e:
        session.rollback()
        print(f"An unexpected error occurred during company seeding: {e}")
        raise


    created_users = []
    for profile_data in USER_PROFILES_DATA:
        # Check if user already exists by username (email)
        existing_user = session.query(User).filter(User.username == profile_data["email"]).first()
        if existing_user:
            print(f"User {profile_data['email']} already exists, skipping user and profile creation.")
            created_users.append(existing_user) # Add existing user for ticket creation
            continue

        db_user = User(
            username=profile_data["email"],
            hashed_password=hashed_default_password
        )
        session.add(db_user)
        session.flush() # Flush to get the db_user.id for the profile

        # Fetch company_id based on company_name
        company_name_for_profile = profile_data["company_name"]
        company_obj = session.query(Company).filter(Company.name == company_name_for_profile).first()
        
        profile_company_id = None
        if company_obj:
            profile_company_id = company_obj.id
        else:
            print(f"Warning: Company '{company_name_for_profile}' not found for user {profile_data['email']}. Skipping company linkage.")
            # Optionally, create the company here if it's missing and should be auto-created
            # Or ensure COMPANY_NAMES covers all possibilities in USER_PROFILES_DATA

        db_user_profile = UserProfile(
            first_name=profile_data["first_name"],
            last_name=profile_data["last_name"],
            email=profile_data["email"],
            company_id=profile_company_id, # Use fetched company_id
            role=profile_data["role"],
            user_id=db_user.id
        )
        session.add(db_user_profile)
        created_users.append(db_user)
        print(f"Created user: {db_user.username} and profile: {db_user_profile.email}")

    # Create tickets, associating them round-robin or specifically if needed
    # This example gives first two tickets to first user, next two to second, etc.
    for i, ticket_info in enumerate(TICKET_DATA):
        if not created_users: # No users to assign tickets to
            print("No users available to assign tickets.")
            break
        
        # Simple round-robin assignment for this example
        # Adjust user_index logic if ticket_data is not a multiple of users or specific assignment is needed.
        user_index = i // 2 # Assigns 2 tickets per user based on current TICKET_DATA structure
        if user_index < len(created_users):
            assignee_user = created_users[user_index]
            existing_ticket = session.query(Ticket).filter(Ticket.title == ticket_info["title"], Ticket.user_id == assignee_user.id).first()
            if existing_ticket:
                print(f"Ticket '{ticket_info['title']}' for user {assignee_user.username} already exists, skipping.")
                continue

            db_ticket = Ticket(
                title=ticket_info["title"],
                description=ticket_info["description"],
                public=ticket_info["public"],
                status=ticket_info["status"], # Added status
                user_id=assignee_user.id
            )
            session.add(db_ticket)
            print(f"Created ticket: '{db_ticket.title}' for user {assignee_user.username}")
        else:
            print(f"Skipping ticket '{ticket_info['title']}' as there are not enough users for round-robin assignment.")

    try:
        session.commit()
        print("Data seeding committed.")
    except IntegrityError as e:
        session.rollback()
        print(f"Error during commit (likely due to existing data): {e}")
    except Exception as e:
        session.rollback()
        print(f"An unexpected error occurred: {e}")
        raise

if __name__ == "__main__":
    print("Initializing database...")
    init_db()  # Ensures tables are created
    
    # Get a session for seeding
    db_session = next(get_session())
    try:
        seed_data(db_session)
    finally:
        db_session.close()
    print("Seeding process finished.")
