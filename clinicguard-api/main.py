from datetime import datetime

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    status,
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlmodel import Session, select

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.extension import _rate_limit_exceeded_handler

from database.session import (
    create_tables,
    get_session,
)

from models.user import (
    User,
    UserCreate,
    UserResponse,
)

from models.patient import (
    Patient,
    PatientCreate,
    PatientUpdate,
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_active_user,
    get_current_admin,
    get_current_doctor,
    get_receptionist_or_above,
)

app = FastAPI(
    title="ClinicGuard API",
    version="1.0.0",
)

create_tables()

# ==========================================================
# RATE LIMITING
# ==========================================================

limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(
    SlowAPIMiddleware
)

# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to ClinicGuard API"
    }

# ==========================================================
# REGISTER
# ==========================================================

@app.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register_user(
    request: Request,
    user_data: UserCreate,
    session: Session = Depends(get_session),
):

    existing = session.exec(
        select(User).where(
            User.username == user_data.username
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    existing = session.exec(
        select(User).where(
            User.email == user_data.email
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already exists",
        )

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(
            user_data.password
        ),
        full_name=user_data.full_name,
        role=user_data.role,
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {
        "message": "User created successfully",
        "user": db_user,
    }

# ==========================================================
# LOGIN
# ==========================================================

@app.post("/login")
@limiter.limit("5/minute")
def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):

    user = session.exec(
        select(User).where(
            User.username == form_data.username
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive account",
        )

    user.last_login = datetime.utcnow()

    session.add(user)
    session.commit()

    token = create_access_token(
        {"sub": user.username}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1800,
        "username": user.username,
        "role": user.role,
    }

# ==========================================================
# CURRENT USER
# ==========================================================

@app.get(
    "/users/me",
    response_model=UserResponse,
)
def current_user(
    user: User = Depends(
        get_current_active_user
    ),
):
    return user

# ==========================================================
# UPDATE PROFILE
# ==========================================================

@app.patch(
    "/users/me",
    response_model=UserResponse,
)
def update_profile(
    full_name: str | None = None,
    current_user: User = Depends(
        get_current_active_user
    ),
    session: Session = Depends(get_session),
):

    if full_name:
        current_user.full_name = full_name

    current_user.updated_at = datetime.utcnow()

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user

# ==========================================================
# PATIENT ENDPOINTS
# ==========================================================

@app.post(
    "/patients",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/hour")
def create_patient(
    request: Request,
    patient_data: PatientCreate,
    current_user: User = Depends(
        get_receptionist_or_above
    ),
    session: Session = Depends(get_session),
):

    if patient_data.doctor_id:

        doctor = session.get(
            User,
            patient_data.doctor_id,
        )

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found",
            )

        if doctor.role not in [
            "admin",
            "doctor",
        ]:
            raise HTTPException(
                status_code=400,
                detail="Assigned user must be a doctor",
            )

    patient = Patient(
        **patient_data.model_dump(),
        created_by=current_user.id,
    )

    session.add(patient)
    session.commit()
    session.refresh(patient)

    return patient
# ==========================================================
# LIST PATIENTS
# ==========================================================

@app.get("/patients")
@limiter.limit("30/minute")
def list_patients(
    request: Request,
    current_user: User = Depends(get_receptionist_or_above),
    session: Session = Depends(get_session),
):
    """
    List patient records.
    Doctors only see patients assigned to them.
    Receptionists and admins see all patients.
    """

    query = select(Patient)

    if current_user.role == "doctor":
        query = query.where(
            Patient.doctor_id == current_user.id
        )

    patients = session.exec(query).all()

    return patients


# ==========================================================
# GET ONE PATIENT
# ==========================================================

@app.get("/patients/{patient_id}")
@limiter.limit("30/minute")
def get_patient(
    request: Request,
    patient_id: int,
    current_user: User = Depends(get_receptionist_or_above),
    session: Session = Depends(get_session),
):
    """
    Retrieve one patient.
    """

    patient = session.get(
        Patient,
        patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    if (
        current_user.role == "doctor"
        and patient.doctor_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this patient",
        )

    return patient


# ==========================================================
# UPDATE PATIENT
# ==========================================================

@app.patch("/patients/{patient_id}")
def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    current_user: User = Depends(get_current_doctor),
    session: Session = Depends(get_session),
):
    """
    Update patient details.
    """

    patient = session.get(
        Patient,
        patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    if (
        current_user.role != "admin"
        and patient.doctor_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only update your own patients",
        )

    update_data = patient_update.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(patient, key, value)

    patient.updated_at = datetime.utcnow()

    session.add(patient)
    session.commit()
    session.refresh(patient)

    return patient


# ==========================================================
# DELETE PATIENT
# ==========================================================

@app.delete("/patients/{patient_id}")
def delete_patient(
    patient_id: int,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Delete patient.
    Admin only.
    """

    patient = session.get(
        Patient,
        patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    session.delete(patient)
    session.commit()

    return {
        "message": "Patient record deleted"
    }


# ==========================================================
# EXERCISE 2
# UNASSIGNED PATIENTS
# ==========================================================

@app.get("/patients/unassigned")
def get_unassigned_patients(
    current_user: User = Depends(get_current_doctor),
    session: Session = Depends(get_session),
):
    """
    Doctors and admins can view
    patients without an assigned doctor.
    """

    patients = session.exec(
        select(Patient).where(
            Patient.doctor_id == None
        )
    ).all()

    return patients


# ==========================================================
# CLAIM PATIENT
# ==========================================================

@app.patch("/patients/{patient_id}/claim")
def claim_patient(
    patient_id: int,
    doctor: User = Depends(get_current_doctor),
    session: Session = Depends(get_session),
):
    """
    Doctor claims an unassigned patient.
    """

    patient = session.get(
        Patient,
        patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    if patient.doctor_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Patient already assigned",
        )

    patient.doctor_id = doctor.id
    patient.updated_at = datetime.utcnow()

    session.add(patient)
    session.commit()
    session.refresh(patient)

    return {
        "message": "Patient assigned successfully",
        "patient": patient,
    }


# ==========================================================
# DOCTOR'S PATIENTS
# ==========================================================

@app.get("/patients/my-patients")
def my_patients(
    doctor: User = Depends(get_current_doctor),
    session: Session = Depends(get_session),
):
    """
    Return patients assigned
    to the logged-in doctor.
    """

    patients = session.exec(
        select(Patient).where(
            Patient.doctor_id == doctor.id
        )
    ).all()

    return patients
# ==========================================================
# ADMIN USER MANAGEMENT
# ==========================================================

@app.get(
    "/users",
    response_model=list[UserResponse],
)
def list_users(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    List all users.
    Admin only.
    """

    return session.exec(
        select(User)
    ).all()


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Retrieve one user.
    """

    user = session.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@app.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Update a user's role.
    """

    allowed_roles = [
        "admin",
        "doctor",
        "receptionist",
    ]

    if new_role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    user = session.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own role",
        )

    user.role = new_role
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "message": f"{user.username} is now a {new_role}"
    }


@app.patch("/users/{user_id}/activate")
def toggle_user_activation(
    user_id: int,
    activate: bool,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Activate or deactivate a user.
    """

    user = session.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate yourself",
        )

    user.is_active = activate
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "message": f"{user.username} activation set to {activate}"
    }


# ==========================================================
# OPTIONAL HEALTH CHECK
# ==========================================================

@app.get("/health")
def health_check():
    """
    API health check.
    """

    return {
        "status": "healthy",
        "service": "ClinicGuard API",
        "timestamp": datetime.utcnow(),
    }

