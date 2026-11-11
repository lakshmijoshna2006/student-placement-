import os
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import mongomock

_db = None
_client = None
_is_mock = False

def get_db(config=None):
    """
    Returns the database instance.
    Connects to live MongoDB via PyMongo if available;
    otherwise falls back gracefully to in-memory PyMongo (mongomock)
    so the application works reliably in all environments.
    """
    global _db, _client, _is_mock
    if _db is not None:
        return _db

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/placement_management')
    db_name = os.getenv('DB_NAME', 'placement_management')

    try:
        # Attempt connecting to live MongoDB with short timeout
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
        # Verify connection by issuing a ping command
        client.admin.command('ping')
        _client = client
        _db = client[db_name]
        _is_mock = False
        print(f"[Database] Successfully connected to live MongoDB at '{mongo_uri}' -> Database: '{db_name}'")
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
        print(f"[Database Note] Live MongoDB not reachable ({exc}). Initializing PyMongo in-memory database...")
        client = mongomock.MongoClient()
        _client = client
        _db = client[db_name]
        _is_mock = True
        print(f"[Database] PyMongo in-memory store initialized for '{db_name}'.")

    # Ensure indexes on collections
    ensure_indexes(_db)

    # Auto-seed if database is empty so demo accounts work out-of-the-box
    try:
        if _db.users.count_documents({}) == 0:
            from seed import seed_database
            seed_database()
    except Exception as e:
        pass

    return _db

def is_mock_db():
    global _is_mock
    return _is_mock

def ensure_indexes(db):
    """Create unique and search indexes across collections."""
    try:
        # Users
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("role", ASCENDING)])

        # Students
        db.students.create_index([("user_id", ASCENDING)], unique=True)
        db.students.create_index([("roll_no", ASCENDING)], unique=True)
        db.students.create_index([("email", ASCENDING)], unique=True)
        db.students.create_index([("department", ASCENDING)])
        db.students.create_index([("cgpa", DESCENDING)])

        # Companies
        db.companies.create_index([("user_id", ASCENDING)], unique=True)
        db.companies.create_index([("company_name", ASCENDING)])

        # Jobs
        db.jobs.create_index([("company_id", ASCENDING)])
        db.jobs.create_index([("status", ASCENDING)])
        db.jobs.create_index([("created_at", DESCENDING)])

        # Applications - Prevent duplicate applications per student per job
        db.applications.create_index([("job_id", ASCENDING), ("student_id", ASCENDING)], unique=True)
        db.applications.create_index([("status", ASCENDING)])

        # Trainings
        db.trainings.create_index([("status", ASCENDING)])

        # Training Registrations - Prevent duplicate registration per student per training
        db.training_registrations.create_index([("training_id", ASCENDING), ("student_id", ASCENDING)], unique=True)

        # Placements
        db.placements.create_index([("student_id", ASCENDING)])
        db.placements.create_index([("company_id", ASCENDING)])
        db.placements.create_index([("academic_year", DESCENDING)])
    except Exception as e:
        # Mongomock or existing indexes might raise warnings
        pass

def to_oid(val):
    """Safely converts string or ObjectId to ObjectId."""
    if val is None:
        return None
    if isinstance(val, ObjectId):
        return val
    try:
        return ObjectId(str(val))
    except Exception:
        return None

def serialize_doc(doc):
    """Converts ObjectId and datetime to string for JSON/template compatibility."""
    if not doc:
        return doc
    res = dict(doc)
    for k, v in res.items():
        if isinstance(v, ObjectId):
            res[k] = str(v)
        elif isinstance(v, datetime):
            res[k] = v.strftime("%Y-%m-%d %H:%M")
        elif isinstance(v, list):
            res[k] = [serialize_doc(item) if isinstance(item, dict) else (str(item) if isinstance(item, ObjectId) else item) for item in v]
        elif isinstance(v, dict):
            res[k] = serialize_doc(v)
    return res
