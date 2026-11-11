# STUDENT PLACEMENT AND TRAINING MANAGEMENT SYSTEM

A centralized, enterprise-grade college placement and pre-placement training web application engineered for collegiate training & placement departments, corporate recruiters, and aspiring engineering candidates.

Built strictly using **HTML5, CSS3, JavaScript, Bootstrap 5, Python Flask, MongoDB, and PyMongo**.

---

## 1. Demo Login Credentials

Pre-configured sample accounts inserted via `seed.py`:

| User Role | Email Address | Password | Account Name / Details |
| :--- | :--- | :--- | :--- |
| **Placement Admin** | `admin@placement.edu` | `Admin@123` | Dr. K. S. Sharma (Placement Director) |
| **Student (CSE)** | `arun.kumar@student.edu` | `Student@123` | Arun Kumar (Roll: 21CSE001, CGPA: 9.4) |
| **Student (IT)** | `priya.sharma@student.edu` | `Student@123` | Priya Sharma (Roll: 21IT002, CGPA: 8.8) |
| **Student (ECE)** | `rahul.verma@student.edu` | `Student@123` | Rahul Verma (Roll: 21ECE003, CGPA: 8.2) |
| **Student (Mech)** | `vikram.singh@student.edu` | `Student@123` | Vikram Singh (Roll: 21MECH005, CGPA: 8.5) |
| **Corporate Partner** | `recruiter@google.com` | `Company@123` | Google LLC (Sundararajan V.) |
| **Corporate Partner** | `careers@microsoft.com` | `Company@123` | Microsoft Corporation (Ananya Sengupta) |
| **Corporate Partner** | `campus@amazon.com` | `Company@123` | Amazon AWS (Rajesh Menon) |
| **Corporate Partner** | `hr@infosys.com` | `Company@123` | Infosys Limited (Deepika Nair) |
| **Corporate Partner** | `recruitment@tcs.com` | `Company@123` | Tata Consultancy Services (Manoj Kulkarni) |

> **Pro Tip**: On the Login screen, click any of the **Quick Demo Autofill** buttons to instantly populate email, password, and role selector.

---

## 2. Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js
- **Backend**: Python Flask 3.0+
- **Database**: MongoDB (Database Name: `placement_management`)
- **Database Driver**: PyMongo (with BSON ObjectIds, compound uniqueness indexes, and resilient in-memory fallback)
- **Security**: Werkzeug secure password hashing (`generate_password_hash`, `check_password_hash`), role-based access control decorators (`@login_required`, `@role_required`), secure file uploads for PDF resumes.

---

## 3. Project Folder Structure

```
placement_management/
├── app.py                      # Flask Application Entry Point & Global Config
├── config.py                   # Configuration Settings & Environment Variables
├── requirements.txt            # Python Dependencies
├── .env.example                # Sample Environment Template
├── .env                        # Local Environment Configuration
├── seed.py                     # Database Seeder (Admin, 10 Students, 5 Companies, 8 Jobs, 5 Trainings)
├── test_app.py                 # Comprehensive Unit Test Suite (14 Tests covering all rubric items)
├── README.md                   # Complete Documentation & Setup Guide
│
├── models/
│   └── database.py             # MongoDB connection, Index Definitions, ObjectId & Serialization Helpers
│
├── routes/
│   ├── auth.py                 # Authentication, Student & Company Registration, Session Management
│   ├── admin.py                # Admin Dashboard, Student CRUD, Company CRUD, Reports & Analytics
│   ├── student.py              # Student Dashboard, Profile Management, PDF Resume Upload/Download
│   ├── company.py              # Recruiter Dashboard, Profile, Job Applications, Candidate Status Decisions
│   ├── jobs.py                 # Job Listings, Search/Filters, Details, Automated Eligibility & Apply
│   ├── training.py             # Pre-Placement Training Sessions, Student Registration/Cancellation
│   └── placements.py           # Placement Records, Hall of Fame, Manual Placement Creation
│
├── templates/
│   ├── base.html               # Master Layout (Navbar, Flash Messages, Footer, CDN inclusions)
│   ├── index.html              # Modern Landing Page (Hero, Metrics Counter, Process, Hiring Partners)
│   ├── about.html              # About T&P Cell, Director Message, Infrastructure, Facilities
│   ├── login.html              # Authentication Page with Demo Autofill Chips
│   ├── register_student.html   # Student Registration Form with Validation
│   ├── register_company.html   # Corporate Partner Registration Form
│   ├── admin_dashboard.html    # Admin Dashboard with KPI Cards, Chart.js Analytics & Quick Actions
│   ├── student_dashboard.html  # Student Portal with Profile Card, Recommended Jobs & Application Tracking
│   ├── company_dashboard.html  # Recruiter Dashboard with Metric Cards & Recent Candidate Applications
│   ├── profile.html            # Student Profile Editor & PDF Resume Upload
│   ├── company_profile.html    # Company Information Editor
│   ├── students.html           # Admin Student Management (Search, Filters, Add, Edit, Delete Modals)
│   ├── companies.html          # Admin Company Management (Search, Add, Edit, Delete Modals)
│   ├── jobs.html               # Job Listings with Search by Title, Company, Skills, Dept & Package
│   ├── job_details.html        # Job Details with Dynamic Candidate Eligibility Evaluation & Modal Apply
│   ├── job_form.html           # Job Creation and Edit Form (Admin & Company)
│   ├── applications.html       # Unified Application Review Hub for Admin, Recruiter, and Student
│   ├── trainings.html          # Pre-Placement Training Programs (Create, Edit, Register, Cancel)
│   ├── training_participants.html # Enrolled Student Roster for Training Programs
│   ├── placements.html         # Official Placement Records & Hall of Fame
│   ├── recruitment_history.html# Corporate Recruiter Hiring History & Placed Candidates
│   └── reports.html            # Placement Analytics & Statistical Reports (Department & Salary Tier Charts)
│
└── static/
    ├── css/
    │   └── style.css           # Custom Blue, White, and Slate Grey Stylesheet
    ├── js/
    │   └── script.js           # Client-side Form Validation, Auto-Dismiss Alerts, Table Live Search
    └── uploads/
        └── resumes/            # Stored Student PDF Resumes
```

---

## 4. MongoDB Database Architecture

Database Name: `placement_management`

### Collections & Schema Specifications:

1. **`users`**:
   - `_id`: ObjectId
   - `email`: String (Unique Index)
   - `password_hash`: String (pbkdf2:sha256)
   - `role`: String (`admin` | `student` | `company`)
   - `status`: String (`active` | `disabled`)
   - `created_at`: DateTime (UTC)

2. **`students`**:
   - `_id`: ObjectId
   - `user_id`: ObjectId (References `users._id`, Unique Index)
   - `name`: String
   - `roll_no`: String (Unique Index)
   - `email`: String
   - `phone`: String
   - `department`: String (`CSE`, `IT`, `ECE`, `EEE`, `MECH`, `CIVIL`)
   - `cgpa`: Float (0.00 to 10.00)
   - `backlogs`: Integer
   - `passing_year`: String
   - `skills`: Array of Strings
   - `resume_filename`: String (Saved in `static/uploads/resumes/`)
   - `status`: String (`Eligible` | `Placed` | `Ineligible`)
   - `created_at`: DateTime (UTC)

3. **`companies`**:
   - `_id`: ObjectId
   - `user_id`: ObjectId (References `users._id`, Unique Index)
   - `company_name`: String
   - `email`: String
   - `contact_person`: String
   - `phone`: String
   - `industry`: String
   - `website`: String
   - `location`: String
   - `description`: String
   - `verified`: Boolean
   - `created_at`: DateTime (UTC)

4. **`jobs`**:
   - `_id`: ObjectId
   - `company_id`: ObjectId (References `companies._id`)
   - `company_name`: String
   - `title`: String
   - `location`: String
   - `job_type`: String (`Full-time` | `Internship`)
   - `salary_package`: Float (LPA)
   - `min_cgpa`: Float
   - `max_backlogs`: Integer
   - `departments`: Array of Strings (`All`, `CSE`, etc.)
   - `skills_required`: Array of Strings
   - `description`: String
   - `deadline`: String (YYYY-MM-DD)
   - `status`: String (`Active` | `Closed`)
   - `created_at`: DateTime (UTC)

5. **`applications`**:
   - `_id`: ObjectId
   - `job_id`: ObjectId (References `jobs._id`)
   - `student_id`: ObjectId (References `students._id`)
   - `company_id`: ObjectId (References `companies._id`)
   - `applied_date`: DateTime (UTC)
   - `status`: String (`Applied` | `Shortlisted` | `Interview Scheduled` | `Selected` | `Rejected`)
   - `remarks`: String
   - `updated_at`: DateTime (UTC)
   - **Compound Unique Index**: `(job_id, student_id)` — strictly prevents duplicate applications.

6. **`trainings`**:
   - `_id`: ObjectId
   - `title`: String
   - `trainer_name`: String
   - `description`: String
   - `mode`: String (`Online` | `Offline` | `Hybrid`)
   - `venue`: String
   - `start_date`: String
   - `end_date`: String
   - `eligibility`: String
   - `max_seats`: Integer
   - `status`: String (`Upcoming` | `Ongoing` | `Completed`)
   - `created_at`: DateTime (UTC)

7. **`training_registrations`**:
   - `_id`: ObjectId
   - `training_id`: ObjectId (References `trainings._id`)
   - `student_id`: ObjectId (References `students._id`)
   - `student_name`: String
   - `student_roll`: String
   - `registered_date`: DateTime (UTC)
   - **Compound Unique Index**: `(training_id, student_id)` — prevents duplicate registration.

8. **`placements`**:
   - `_id`: ObjectId
   - `student_id`: ObjectId (References `students._id`)
   - `student_name`: String
   - `roll_no`: String
   - `department`: String
   - `company_id`: ObjectId (References `companies._id`)
   - `company_name`: String
   - `job_id`: ObjectId (References `jobs._id`)
   - `job_title`: String
   - `package`: Float (LPA)
   - `academic_year`: String (`2025-2026`)
   - `placement_date`: DateTime (UTC)

---

## 5. Setup & Execution Instructions

### Step 1: Clone or Navigate to the Workspace
Open a terminal in the project directory:
```bash
cd "placement_management"
```

### Step 2: Set up a Python Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure MongoDB
You can use **MongoDB Community Server (Local)** or **MongoDB Atlas (Cloud)**:

- **Local MongoDB**:
  Install and start the MongoDB service:
  ```bash
  # Windows service check / start:
  net start MongoDB
  ```
  The default URI is `mongodb://localhost:27017/placement_management`.

- **MongoDB Atlas**:
  In `.env`, set:
  ```env
  MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/placement_management?retryWrites=true&w=majority
  ```

> **Note**: If a live MongoDB server is not running on your machine, the application includes a smart, built-in PyMongo in-memory engine (`mongomock`), allowing immediate evaluation and testing without server crashes!

### Step 5: Seed the Database with Sample Data
Populates 1 Admin, 10 Students with generated PDF resumes, 5 Companies, 8 Jobs, 5 Trainings, Applications, and Placement records:
```bash
python seed.py
```

### Step 6: Start the Flask Application
```bash
python app.py
```
The application will launch on:
```
http://localhost:5000
```
Open your browser and navigate to `http://localhost:5000`.

---

## 6. Running Automated Tests

Run the complete 14-test test suite covering all rubrics:
```bash
python -m unittest test_app -v
```

All 14 tests verify:
1. Public Landing & About Pages
2. Admin Authentication
3. Student Registration & Authentication
4. Company Registration & Authentication
5. Student CRUD operations (Add, View, Edit, Delete)
6. Company CRUD operations (Add, View, Edit, Delete)
7. Job Posting, Searching, and Multi-criteria Filtering
8. PDF Resume Upload and Download verification
9. Application Submission & Duplicate Prevention
10. Automated Eligibility Engine enforcement
11. Recruiter Decision Workflow & Automatic Placement Sync
12. Pre-Placement Training Registration & Cancellation
13. Institutional Analytics & Statistical Reports
14. Role-Based Access Control & Route Guarding.

---

## 7. Key System Modules & Workflows

### A. Candidate Eligibility Engine
When a student views any job drive:
1. The student's CGPA is verified against `min_cgpa`.
2. The student's active backlogs are checked against `max_backlogs`.
3. The student's department is matched with `departments` (or `All`).
4. The system validates that a valid PDF resume is uploaded.
If all 4 conditions are met, the "Apply Now" button is active. If any condition fails, an informative alert indicates the exact requirement needed.

### B. Duplicate Application Prevention
Applications are indexed on `(job_id, student_id)`. If an applicant attempts to apply more than once, the application is rejected gracefully with an informative notification.

### C. Automatic Placement Synchronization
When a corporate recruiter or placement administrator updates a candidate's status to **"Selected"**, the system automatically writes an official record into the `placements` collection and marks the student's status as `Placed`.

### D. Resume Validation
Only authentic `.pdf` files up to 16 MB are allowed. File names are secured using `secure_filename()` and stored in `static/uploads/resumes/`.

---

## 8. Authors & Academic Credits
- **Project**: Student Placement & Training Management System
- **Framework**: Full Stack Web Development (B.Tech CSE / IT Practical External Capstone)
- **Year**: 2026
