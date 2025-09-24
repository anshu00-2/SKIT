from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: str
    role: str = "patient"  # patient or doctor
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DoctorProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    specialization: str
    experience_years: int
    license_number: str
    bio: str
    consultation_fee: float
    available: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    scheduled_time: Optional[datetime] = None
    status: str = "pending"  # pending, active, completed, cancelled
    type: str = "scheduled"  # scheduled, instant
    video_room_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request Models
class DoctorProfileCreate(BaseModel):
    specialization: str
    experience_years: int
    license_number: str
    bio: str
    consultation_fee: float

class AppointmentCreate(BaseModel):
    doctor_id: str
    scheduled_time: Optional[datetime] = None
    type: str = "scheduled"

# Authentication Helper
async def get_current_user(request: Request) -> Optional[User]:
    # Check session_token from cookie first, then Authorization header
    session_token = request.cookies.get('session_token')
    if not session_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header.split(' ')[1]
    
    if not session_token:
        return None
    
    # Find active session
    session = await db.user_sessions.find_one({
        "session_token": session_token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        return None
    
    # Get user
    user = await db.users.find_one({"id": session["user_id"]}, {"_id": 0})
    return User(**user) if user else None

async def require_auth(request: Request) -> User:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_doctor(request: Request) -> User:
    user = await require_auth(request)
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required")
    return user

# Authentication Routes
@api_router.post("/auth/session")
async def process_session(request: Request, response: Response):
    """Process session_id from Emergent Auth and create local session"""
    try:
        body = await request.json()
        session_id = body.get('session_id')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get user data from Emergent Auth
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            user_data = auth_response.json()
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": user_data["email"]})
        
        if not existing_user:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data["picture"],
                role="patient"  # Default to patient
            )
            await db.users.insert_one(user.dict())
        else:
            user = User(**existing_user)
        
        # Create session
        session_token = user_data["session_token"]
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Remove existing sessions for this user
        await db.user_sessions.delete_many({"user_id": user.id})
        
        # Create new session
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at
        )
        await db.user_sessions.insert_one(session.dict())
        
        # Set secure cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        return {"user": user.dict(), "success": True}
        
    except Exception as e:
        print(f"Session processing error: {e}")
        raise HTTPException(status_code=500, detail="Session processing failed")

@api_router.get("/auth/me")
async def get_current_user_info(user: User = Depends(require_auth)):
    """Get current user information"""
    return {"user": user.dict()}

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    session_token = request.cookies.get('session_token')
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie("session_token", path="/", samesite="none")
    return {"success": True}

# Doctor Routes
@api_router.post("/doctors/profile")
async def create_doctor_profile(
    profile_data: DoctorProfileCreate,
    user: User = Depends(require_auth)
):
    """Create doctor profile and update user role"""
    # Update user role to doctor
    await db.users.update_one(
        {"id": user.id},
        {"$set": {"role": "doctor"}}
    )
    
    # Create doctor profile
    profile = DoctorProfile(
        user_id=user.id,
        **profile_data.dict()
    )
    await db.doctor_profiles.insert_one(profile.dict())
    
    return {"profile": profile.dict(), "success": True}

@api_router.get("/doctors")
async def get_available_doctors():
    """Get all available doctors"""
    doctors = await db.doctor_profiles.find({"available": True}, {"_id": 0}).to_list(None)
    
    # Get user data for each doctor
    for doctor in doctors:
        user = await db.users.find_one({"id": doctor["user_id"]}, {"_id": 0})
        if user:
            doctor["user"] = {
                "name": user["name"],
                "picture": user["picture"]
            }
    
    return {"doctors": doctors}

@api_router.get("/doctors/profile")
async def get_doctor_profile(user: User = Depends(require_doctor)):
    """Get current doctor's profile"""
    profile = await db.doctor_profiles.find_one({"user_id": user.id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return {"profile": profile}

@api_router.put("/doctors/availability")
async def update_availability(
    available: bool,
    user: User = Depends(require_doctor)
):
    """Update doctor availability"""
    await db.doctor_profiles.update_one(
        {"user_id": user.id},
        {"$set": {"available": available}}
    )
    return {"success": True}

# Appointment Routes
@api_router.post("/appointments")
async def create_appointment(
    appointment_data: AppointmentCreate,
    user: User = Depends(require_auth)
):
    """Create new appointment"""
    # Verify doctor exists and is available
    doctor = await db.doctor_profiles.find_one({
        "id": appointment_data.doctor_id,
        "available": True
    })
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not available")
    
    appointment = Appointment(
        patient_id=user.id,
        doctor_id=appointment_data.doctor_id,
        scheduled_time=appointment_data.scheduled_time,
        type=appointment_data.type,
        video_room_id=str(uuid.uuid4())  # Generate unique room ID for WebRTC
    )
    
    await db.appointments.insert_one(appointment.dict())
    return {"appointment": appointment.dict(), "success": True}

@api_router.get("/appointments")
async def get_user_appointments(user: User = Depends(require_auth)):
    """Get user's appointments"""
    if user.role == "doctor":
        # Get appointments for this doctor
        appointments = await db.appointments.find({"doctor_id": user.id}, {"_id": 0}).to_list(None)
        
        # Add patient info
        for appointment in appointments:
            patient = await db.users.find_one({"id": appointment["patient_id"]}, {"_id": 0})
            if patient:
                appointment["patient"] = {
                    "name": patient["name"],
                    "picture": patient["picture"]
                }
    else:
        # Get appointments for this patient
        appointments = await db.appointments.find({"patient_id": user.id}, {"_id": 0}).to_list(None)
        
        # Add doctor info
        for appointment in appointments:
            doctor_profile = await db.doctor_profiles.find_one({"id": appointment["doctor_id"]}, {"_id": 0})
            if doctor_profile:
                doctor_user = await db.users.find_one({"id": doctor_profile["user_id"]}, {"_id": 0})
                if doctor_user:
                    appointment["doctor"] = {
                        "name": doctor_user["name"],
                        "picture": doctor_user["picture"],
                        "specialization": doctor_profile["specialization"]
                    }
    
    return {"appointments": appointments}

@api_router.get("/appointments/{appointment_id}/join")
async def join_appointment(appointment_id: str, user: User = Depends(require_auth)):
    """Get appointment details for joining video call"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify user can access this appointment
    if appointment["patient_id"] != user.id and appointment["doctor_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"appointment": appointment}

@api_router.post("/appointments/{appointment_id}/start")
async def start_appointment(appointment_id: str, user: User = Depends(require_auth)):
    """Start appointment video call"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update appointment status
    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {"status": "active"}}
    )
    
    return {"video_room_id": appointment["video_room_id"], "success": True}

# Initialize sample doctors
@api_router.post("/admin/init-sample-doctors")
async def init_sample_doctors():
    """Initialize sample doctors for demo"""
    sample_doctors = [
        {
            "email": "dr.smith@medconnect.com",
            "name": "Dr. Sarah Smith",
            "picture": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150&h=150&fit=crop&crop=face",
            "specialization": "General Medicine",
            "experience_years": 8,
            "license_number": "MD12345",
            "bio": "Experienced family physician specializing in rural healthcare delivery.",
            "consultation_fee": 75.0
        },
        {
            "email": "dr.johnson@medconnect.com",
            "name": "Dr. Michael Johnson",
            "picture": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150&h=150&fit=crop&crop=face",
            "specialization": "Cardiology",
            "experience_years": 12,
            "license_number": "MD67890",
            "bio": "Cardiologist with expertise in remote heart monitoring and consultation.",
            "consultation_fee": 120.0
        },
        {
            "email": "dr.wilson@medconnect.com",
            "name": "Dr. Emily Wilson",
            "picture": "https://images.unsplash.com/photo-1594824804732-ca8db3ac9421?w=150&h=150&fit=crop&crop=face",
            "specialization": "Pediatrics",
            "experience_years": 6,
            "license_number": "MD11122",
            "bio": "Pediatrician dedicated to providing quality healthcare for children in underserved areas.",
            "consultation_fee": 90.0
        }
    ]
    
    for doctor_data in sample_doctors:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": doctor_data["email"]})
        
        if not existing_user:
            # Create user
            user = User(
                email=doctor_data["email"],
                name=doctor_data["name"],
                picture=doctor_data["picture"],
                role="doctor"
            )
            await db.users.insert_one(user.dict())
            
            # Create doctor profile
            profile = DoctorProfile(
                user_id=user.id,
                specialization=doctor_data["specialization"],
                experience_years=doctor_data["experience_years"],
                license_number=doctor_data["license_number"],
                bio=doctor_data["bio"],
                consultation_fee=doctor_data["consultation_fee"]
            )
            await db.doctor_profiles.insert_one(profile.dict())
    
    return {"message": "Sample doctors initialized", "success": True}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()