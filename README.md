# ClinicGuard-API


Authorization & Rate Limiting: Patient Management API

Lab: 8
Project: ClinicGuard API
Focus: Authentication, Authorization, Role-Based Access Control (RBAC), CRUD Operations, and Rate Limiting

1. Project Overview

ClinicGuard is a secure patient management REST API built with FastAPI.

The system allows healthcare staff to manage patient records while ensuring that users can only perform actions permitted by their roles.

The project builds on concepts from the previous labs and introduces more advanced security through:

User authentication
JWT access tokens
Password hashing
Role-Based Access Control (RBAC)
Protected endpoints
Rate limiting
Role-specific permissions
Database relationships
2. Problem Statement

A clinic needs a centralized API for managing patient information.

Different members of staff require different levels of access.

For example:

Administrators need full system access.
Doctors need to view and update patients assigned to them.
Receptionists need to register and manage patient information but should not have administrative privileges.

The API therefore needs to ensure that:

Users are authenticated.
Passwords are stored securely.
Users can only access permitted resources.
Different roles have different permissions.
Sensitive endpoints are protected from excessive requests.
3. Learning Objectives

By completing Lab 8, the following concepts are practiced:

FastAPI authentication
JWT authentication
Password hashing
OAuth2 password flow
Role-Based Access Control
Protected API endpoints
Dependency injection
PostgreSQL
SQLModel relationships
CRUD operations
Rate limiting with SlowAPI
Environment variables
Database migrations with Alembic
4. Technologies Used
Technology	Purpose
Python	Programming language
FastAPI	API framework
SQLModel	ORM and data validation
PostgreSQL	Relational database
Docker	Database containerization
JWT	Authentication tokens
Passlib	Password hashing
bcrypt	Password hashing algorithm
Python-Jose	JWT creation and validation
OAuth2	Login authentication flow
SlowAPI	Rate limiting
Alembic	Database migrations
5. Project Structure
clinicguard-api/
│
├── main.py
│
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── patient.py
│
├── database/
│   ├── __init__.py
│   └── session.py
│
├── auth.py
├── seeds.py
├── .env
├── docker-compose.yml
└── alembic.ini
6. Directory Structure Explained
main.py

The main FastAPI application.

It contains:

API routes
Authentication endpoints
Patient endpoints
CRUD operations
Rate limiting configuration
Authorization dependencies
models/

Contains the application's database models and schemas.

models/
├── user.py
└── patient.py
user.py

Defines:

User database model
User creation schema
Login schema
User response schema
patient.py

Defines:

Patient database model
Patient creation schema
Patient update schema
Patient response schema
database/

Contains database configuration.

database/
├── __init__.py
└── session.py

session.py handles the database engine and database sessions.

auth.py

Contains reusable authentication and authorization logic.

It handles:

Password hashing
Password verification
JWT creation
JWT decoding
Current user retrieval
Role verification
seeds.py

Used to create initial users and sample data.

.env

Stores configuration and sensitive values such as:

DATABASE_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
docker-compose.yml

Defines the PostgreSQL container.

alembic.ini

Configuration file for Alembic database migrations.

7. PostgreSQL Setup

The project uses PostgreSQL 16 through Docker.

Docker Compose
services:
  db:
    image: postgres:16
    container_name: clinicguard_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: clinicguard_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:

Start PostgreSQL:

docker compose up -d

Check the container:

docker ps
8. Environment Variables

Create a .env file:

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/clinicguard_db

SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
Configuration
Variable	Purpose
DATABASE_URL	PostgreSQL connection
SECRET_KEY	JWT signing key
ALGORITHM	JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES	Token expiration time

The .env file should not be committed to GitHub when it contains real secrets.

9. User Model

The User model represents people who can access the API.

Important fields include:

id
username
email
hashed_password
full_name
role
is_active
created_at
updated_at
last_login
10. User Roles

ClinicGuard uses three roles:

admin
doctor
receptionist
Admin

Administrators have full access to the system.

They can:

Manage users
View patients
Update patients
Delete patients
Perform administrative operations
Doctor

Doctors have access to patients assigned to them.

They can:

View assigned patients
Update patient information where permitted
Receptionist

Receptionists handle patient registration and general patient information.

They can:

Register patients
View patient records
Perform permitted patient-management operations

They do not have administrator privileges.

11. Authentication

ClinicGuard uses JWT-based authentication.

The authentication process is:

Username + Password
        ↓
Password verification
        ↓
JWT generated
        ↓
Client receives token
        ↓
Token sent with protected requests
        ↓
API validates token
        ↓
User identified
12. Password Security

Passwords are never stored as plaintext.

Passlib is used to hash passwords:

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

Password hashing process:

Plain Password
      ↓
bcrypt
      ↓
Password Hash
      ↓
Database

When a user logs in, the submitted password is compared against the stored hash.

13. JWT Authentication

JWT tokens are generated after successful login.

The token contains information such as the username and expiration time.

Example conceptual payload:

{
  "sub": "doctor1",
  "exp": "expiration-time"
}

The token is then used to access protected endpoints.

14. Current User Dependency

The API uses FastAPI dependency injection to identify the authenticated user.

get_current_user()

The dependency:

Receives the JWT token.
Decodes the token.
Gets the username.
Finds the user in the database.
Checks whether the account is active.
Returns the current user.
15. Role-Based Authorization

The application provides role-specific dependencies.

Examples:

get_current_admin()
get_current_doctor()
get_receptionist_or_above()

This allows individual endpoints to specify which roles can access them.

Example:

current_user: User = Depends(get_current_admin)

Only administrators can access that endpoint.

16. Authorization Flow
Request
   ↓
JWT Token
   ↓
Authentication
   ↓
Current User
   ↓
Check Role
   ↓
┌───────────────┐
│ Authorized?   │
└───────┬───────┘
        │
   ┌────┴────┐
   │         │
  YES        NO
   │         │
   ▼         ▼
Allow      403
Request    Forbidden
17. Patient Model

The Patient model represents patients registered in the clinic.

Important fields include:

id
first_name
last_name
date_of_birth
phone
email
address
medical_notes
doctor_id
created_by
created_at
updated_at
18. Database Relationships

ClinicGuard uses relationships between users and patients.

A doctor can be assigned multiple patients.

Conceptually:

Doctor
  │
  ├── Patient 1
  ├── Patient 2
  └── Patient 3

The relationship is represented through:

doctor_id

A patient's creator can also be recorded using:

created_by
19. CRUD Operations

ClinicGuard provides CRUD operations for patient management.

CRUD means:

Create
Read
Update
Delete
Create

Register a new patient:

POST /patients
Read

List patients:

GET /patients

Get one patient:

GET /patients/{patient_id}
Update

Update patient information:

PUT /patients/{patient_id}
Delete

Delete a patient:

DELETE /patients/{patient_id}
20. Patient Access Rules

The API applies authorization to patient records.

For example:

Admin
  ↓
Can access all patients
Doctor
  ↓
Can access assigned patients
Receptionist
  ↓
Can perform permitted patient-management operations

This prevents users from accessing information outside their role.

21. Rate Limiting

Lab 8 introduces rate limiting using SlowAPI.

Rate limiting restricts how many requests a user/client can make within a specific time period.

This helps protect the API from:

Excessive requests
Brute-force login attempts
Abuse
Accidental request floods
22. Rate Limit Configuration

SlowAPI uses a client address to identify requests.

limiter = Limiter(
    key_func=get_remote_address
)

The limiter is attached to the application:

app.state.limiter = limiter
23. Example Rate Limits

Authentication endpoints have stricter limits.

Registration
/register
5 requests/minute
Login
/login
5 requests/minute

Patient endpoints can have higher limits.

/patients
30 requests/minute

Individual patient endpoints can also be limited.

24. API Endpoints
Authentication
Method	Endpoint	Purpose
POST	/register	Create a user
POST	/login	Authenticate user
Patient Management
Method	Endpoint	Purpose
POST	/patients	Create patient
GET	/patients	List patients
GET	/patients/{patient_id}	Get patient
PUT	/patients/{patient_id}	Update patient
DELETE	/patients/{patient_id}	Delete patient
25. API Documentation

FastAPI automatically generates interactive API documentation.

Swagger UI:

http://127.0.0.1:8000/docs

ReDoc:

http://127.0.0.1:8000/redoc

Swagger can be used to:

Test authentication
Obtain JWT tokens
Authorize requests
Test patient endpoints
View request/response schemas
26. Authentication Example Workflow

First register:

POST /register

Example request:

{
  "username": "doctor1",
  "email": "doctor@example.com",
  "password": "password123",
  "full_name": "Dr. Example",
  "role": "doctor"
}

Then login:

POST /login

The API returns an access token.

The token is then included in protected requests:

Authorization: Bearer <access_token>
27. Complete Request Flow
             Client
                │
                ▼
             /login
                │
                ▼
       Username + Password
                │
                ▼
        Verify Password
                │
                ▼
          Create JWT
                │
                ▼
           Access Token
                │
                ▼
       Protected Endpoint
                │
                ▼
       Validate JWT Token
                │
                ▼
        Identify User
                │
                ▼
        Check User Role
                │
          ┌─────┴─────┐
          │           │
      Authorized   Unauthorized
          │           │
          ▼           ▼
       Database      403
        Action
28. Security Features

ClinicGuard includes several security controls.

Password hashing

Passwords are hashed using bcrypt.

JWT authentication

Protected endpoints require valid access tokens.

Role-Based Access Control

Users receive permissions based on their roles.

Active account checking

Inactive users cannot access protected resources.

Rate limiting

Sensitive endpoints are protected against excessive requests.

Environment variables

Secrets and database configuration are stored outside the source code.

29. Exercise 1 — Admin User Management

The first exercise focuses on user management.

Possible functionality includes:

Listing users
Viewing user details
Updating user roles
Activating/deactivating accounts
Protecting user-management endpoints

Only administrators should be able to perform administrative operations.

30. Exercise 2 — Doctor Patient Access

The second exercise focuses on authorization.

A doctor should only be able to access patients assigned to them.

For example:

Doctor A
 ├── Patient 1
 ├── Patient 2
 └── Patient 3

Doctor A should not automatically be able to access:

Doctor B's patients

The API should check:

Current User
     ↓
Current User's Role
     ↓
Patient's Assigned Doctor
     ↓
Allow / Deny
31. Exercise 3 — Rate Limiting

The third exercise focuses on protecting the API from excessive requests.

Different endpoints can have different limits.

For example:

Login
5/minute
Patient listing
30/minute

More sensitive endpoints should generally have stricter limits.

32. Database Migrations

Alembic is included for managing database schema changes.

The configuration is stored in:

alembic.ini

A migration workflow can be used when the models change.

Conceptually:

Model Change
     ↓
Create Migration
     ↓
Review Migration
     ↓
Apply Migration
     ↓
Database Updated
33. Running the Application
1. Start PostgreSQL
docker compose up -d
2. Activate the virtual environment

Windows:

.venv\Scripts\Activate.ps1
3. Install dependencies
pip install fastapi uvicorn sqlmodel psycopg2-binary python-dotenv python-jose passlib bcrypt python-multipart slowapi alembic
4. Start FastAPI
uvicorn main:app --reload

The API runs at:

http://127.0.0.1:8000
34. Testing With Swagger

Open:

http://127.0.0.1:8000/docs

Recommended testing order:

1. Register user
       ↓
2. Login
       ↓
3. Copy access token
       ↓
4. Authorize Swagger
       ↓
5. Create patient
       ↓
6. List patients
       ↓
7. Get patient
       ↓
8. Update patient
       ↓
9. Test role restrictions
       ↓
10. Test rate limits
35. Lab 8 Key Concepts

The major concepts introduced or reinforced in this lab are:

Authentication

Who are you?

Implemented using:

JWT
OAuth2
Password hashing
Authorization

What are you allowed to do?

Implemented using:

Roles
Dependencies
Permission checks
RBAC
Admin
Doctor
Receptionist

Each role receives different permissions.

Rate Limiting

How frequently can you access an endpoint?

Implemented using:

SlowAPI
36. Lab 8 Progression From Previous Labs

The project can be viewed as a progression:

Previous Labs
      │
      ▼
FastAPI Fundamentals
      │
      ▼
Database + SQLModel
      │
      ▼
CRUD Operations
      │
      ▼
Authentication
      │
      ▼
Lab 8
      │
      ├── JWT
      ├── RBAC
      ├── Role permissions
      ├── Protected endpoints
      └── Rate limiting

Lab 8 therefore moves the application from a basic CRUD API toward a more secure, role-aware backend.

37. Lab 8 → Lab 9

Lab 9, SendIt, builds directly on this lab.

The concepts reused include:

FastAPI
PostgreSQL
SQLModel
JWT authentication
Password hashing
RBAC
Dependency injection
Rate limiting
Environment variables
CRUD

Lab 9 then introduces additional concepts:

File uploads
File validation
File storage
External APIs
Weather enrichment
Document status
Document versioning
Webhooks

Therefore:

ClinicGuard
Security + CRUD
       │
       ▼
SendIt
Security + CRUD
       +
File Management
       +
External API Integration
38. Key Takeaways

Lab 8 demonstrates how to build a backend API that is not only functional but also protected by authentication and authorization.

The core architecture is:

FastAPI
   │
   ├── Authentication
   │      └── JWT
   │
   ├── Authorization
   │      └── RBAC
   │
   ├── Database
   │      └── PostgreSQL
   │
   ├── ORM
   │      └── SQLModel
   │
   └── Protection
          └── Rate Limiting

The key lesson is that authentication and authorization are different:

Authentication
= Who are you?

Authorization
= What are you allowed to do?

ClinicGuard combines both concepts to protect patient information and control access based on user roles.

Author

ClinicGuard API — Lab 8

FastAPI Backend Development La
