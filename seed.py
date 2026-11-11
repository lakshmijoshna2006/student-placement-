import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash

def get_utc_now():
    return datetime.now(timezone.utc)

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from models.database import get_db

def create_sample_pdf(filepath, student_name, roll_no, dept, cgpa):
    """Generates a valid standalone PDF resume for demo purposes."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    stream_content = (
        f"BT\n"
        f"/F1 20 Tf\n"
        f"50 730 Td\n"
        f"({student_name} - Resume) Tj\n"
        f"/F1 12 Tf\n"
        f"0 -30 Td\n"
        f"(Roll No: {roll_no} | Department: {dept} | CGPA: {cgpa}) Tj\n"
        f"0 -25 Td\n"
        f"(Education: B.Tech in Engineering (2022-2026)) Tj\n"
        f"0 -20 Td\n"
        f"(Key Skills: Python, Java, Full Stack Development, Cloud Computing, Git) Tj\n"
        f"0 -20 Td\n"
        f"(Projects: Student Placement Portal, Intelligent Chatbot, Distributed Cache) Tj\n"
        f"0 -20 Td\n"
        f"(Certification: AWS Certified Cloud Practitioner, HackerRank 5-Star Coder) Tj\n"
        f"ET\n"
    )
    stream_bytes = stream_content.encode('latin1')
    length = len(stream_bytes)

    pdf_template = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(length).encode('latin1') + b" >>\nstream\n" +
        stream_bytes +
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000227 00000 n \n0000000350 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n450\n%%EOF\n"
    )
    with open(filepath, 'wb') as f:
        f.write(pdf_template)

def seed_database():
    db = get_db()
    print("[Seed] Resetting existing collections in 'placement_management'...")

    # Clear existing collections
    db.users.delete_many({})
    db.students.delete_many({})
    db.companies.delete_many({})
    db.jobs.delete_many({})
    db.applications.delete_many({})
    db.trainings.delete_many({})
    db.training_registrations.delete_many({})
    db.placements.delete_many({})

    resume_dir = os.path.join(BASE_DIR, 'static', 'uploads', 'resumes')
    os.makedirs(resume_dir, exist_ok=True)

    # ---------------- 1. ADMIN ACCOUNT ----------------
    admin_email = "admin@placement.edu"
    admin_user_id = db.users.insert_one({
        'email': admin_email,
        'password_hash': generate_password_hash("Admin@123"),
        'role': 'admin',
        'status': 'active',
        'name': 'Dr. K. S. Sharma (Placement Director)',
        'created_at': get_utc_now()
    }).inserted_id
    print(f" [✓] Created 1 Admin: {admin_email}")

    # ---------------- 2. COMPANIES (5 Accounts) ----------------
    companies_data = [
        {
            'company_name': 'Google',
            'email': 'recruiter@google.com',
            'password': 'Company@123',
            'contact_person': 'Sundararajan V.',
            'phone': '+91 98112 34567',
            'industry': 'Software & Cloud Computing',
            'website': 'https://about.google',
            'location': 'Bangalore / Hyderabad',
            'description': 'Google LLC is an American multinational corporation and technology company focusing on search engine technology, cloud computing, computer software, and artificial intelligence.'
        },
        {
            'company_name': 'Microsoft',
            'email': 'careers@microsoft.com',
            'password': 'Company@123',
            'contact_person': 'Ananya Sengupta',
            'phone': '+91 98223 45678',
            'industry': 'Enterprise Software & Cloud',
            'website': 'https://careers.microsoft.com',
            'location': 'Hyderabad / Bangalore / Noida',
            'description': 'Microsoft Corporation produces computer software, consumer electronics, personal computers, and related cloud services with Azure.'
        },
        {
            'company_name': 'Amazon',
            'email': 'campus@amazon.com',
            'password': 'Company@123',
            'contact_person': 'Rajesh Menon',
            'phone': '+91 98334 56789',
            'industry': 'E-Commerce & Cloud Infrastructure (AWS)',
            'website': 'https://amazon.jobs',
            'location': 'Hyderabad / Chennai / Bangalore',
            'description': 'Amazon focuses on e-commerce, cloud computing, online advertising, digital streaming, and artificial intelligence.'
        },
        {
            'company_name': 'Infosys',
            'email': 'hr@infosys.com',
            'password': 'Company@123',
            'contact_person': 'Deepika Nair',
            'phone': '+91 98445 67890',
            'industry': 'IT Services & Consulting',
            'website': 'https://www.infosys.com/careers',
            'location': 'Pune / Mysore / Chennai',
            'description': 'Infosys Limited is a global leader in next-generation digital services and consulting helping enterprises navigate digital transformation.'
        },
        {
            'company_name': 'Tata Consultancy Services',
            'email': 'recruitment@tcs.com',
            'password': 'Company@123',
            'contact_person': 'Manoj Kulkarni',
            'phone': '+91 98556 78901',
            'industry': 'Information Technology & Solutions',
            'website': 'https://www.tcs.com/careers',
            'location': 'Mumbai / Bangalore / Kolkata',
            'description': 'TCS is a purpose-led organization that brings together the best in people and technology to deliver world-class digital solutions.'
        }
    ]

    company_map = {}
    for c in companies_data:
        uid = db.users.insert_one({
            'email': c['email'],
            'password_hash': generate_password_hash(c['password']),
            'role': 'company',
            'status': 'active',
            'created_at': get_utc_now()
        }).inserted_id

        cid = db.companies.insert_one({
            'user_id': uid,
            'company_name': c['company_name'],
            'email': c['email'],
            'contact_person': c['contact_person'],
            'phone': c['phone'],
            'industry': c['industry'],
            'website': c['website'],
            'location': c['location'],
            'description': c['description'],
            'verified': True,
            'created_at': get_utc_now()
        }).inserted_id
        company_map[c['company_name']] = cid

    print(f" [✓] Created {len(company_map)} Companies.")

    # ---------------- 3. STUDENTS (10 Accounts) ----------------
    students_data = [
        {
            'name': 'Arun Kumar',
            'email': 'arun.kumar@student.edu',
            'password': 'Student@123',
            'roll_no': '21CSE001',
            'department': 'CSE',
            'cgpa': 9.4,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 97111 22334',
            'skills': ['Python', 'React', 'MongoDB', 'Node.js', 'Data Structures', 'Docker'],
            'status': 'Placed'
        },
        {
            'name': 'Priya Sharma',
            'email': 'priya.sharma@student.edu',
            'password': 'Student@123',
            'roll_no': '21IT002',
            'department': 'IT',
            'cgpa': 8.8,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 97222 33445',
            'skills': ['Java', 'Spring Boot', 'SQL', 'AWS', 'Microservices'],
            'status': 'Placed'
        },
        {
            'name': 'Rahul Verma',
            'email': 'rahul.verma@student.edu',
            'password': 'Student@123',
            'roll_no': '21ECE003',
            'department': 'ECE',
            'cgpa': 8.2,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 97333 44556',
            'skills': ['C++', 'Embedded C', 'IoT', 'Python', 'MATLAB'],
            'status': 'Placed'
        },
        {
            'name': 'Ananya Patel',
            'email': 'ananya.patel@student.edu',
            'password': 'Student@123',
            'roll_no': '21CSE004',
            'department': 'CSE',
            'cgpa': 7.9,
            'backlogs': 1,
            'passing_year': '2026',
            'phone': '+91 97444 55667',
            'skills': ['JavaScript', 'HTML5', 'CSS3', 'Express', 'Git'],
            'status': 'Eligible'
        },
        {
            'name': 'Vikram Singh',
            'email': 'vikram.singh@student.edu',
            'password': 'Student@123',
            'roll_no': '21MECH005',
            'department': 'MECH',
            'cgpa': 8.5,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 97555 66778',
            'skills': ['AutoCAD', 'SolidWorks', 'Python', 'MATLAB', 'Ansys'],
            'status': 'Placed'
        },
        {
            'name': 'Sneha Reddy',
            'email': 'sneha.reddy@student.edu',
            'password': 'Student@123',
            'roll_no': '21EEE006',
            'department': 'EEE',
            'cgpa': 7.4,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 97666 77889',
            'skills': ['Power Systems', 'MATLAB', 'C', 'Simulink', 'PLC'],
            'status': 'Eligible'
        },
        {
            'name': 'Karthik N.',
            'email': 'karthik.n@student.edu',
            'password': 'Student@123',
            'roll_no': '21CIVIL007',
            'department': 'CIVIL',
            'cgpa': 7.1,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 97777 88990',
            'skills': ['Revit Architecture', 'STAAD Pro', 'AutoCAD', 'Surveying'],
            'status': 'Eligible'
        },
        {
            'name': 'Divya Menon',
            'email': 'divya.menon@student.edu',
            'password': 'Student@123',
            'roll_no': '21IT008',
            'department': 'IT',
            'cgpa': 8.9,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 97888 99001',
            'skills': ['Data Analytics', 'Python', 'Tableau', 'Machine Learning', 'Pandas', 'PowerBI'],
            'status': 'Placed'
        },
        {
            'name': 'Rohit Gupta',
            'email': 'rohit.gupta@student.edu',
            'password': 'Student@123',
            'roll_no': '21CSE009',
            'department': 'CSE',
            'cgpa': 6.8,
            'backlogs': 2,
            'passing_year': '2026',
            'phone': '+91 97999 00112',
            'skills': ['C++', 'Java', 'Web Development', 'SQL'],
            'status': 'Eligible'
        },
        {
            'name': 'Meera Nair',
            'email': 'meera.nair@student.edu',
            'password': 'Student@123',
            'roll_no': '21ECE010',
            'department': 'ECE',
            'cgpa': 8.6,
            'backlogs': 0,
            'passing_year': '2026',
            'phone': '+91 98000 11223',
            'skills': ['VLSI Design', 'Verilog', 'Python', 'Digital Electronics', 'Cadence'],
            'status': 'Eligible'
        }
    ]

    student_map = {}
    for s in students_data:
        uid = db.users.insert_one({
            'email': s['email'],
            'password_hash': generate_password_hash(s['password']),
            'role': 'student',
            'status': 'active',
            'created_at': get_utc_now()
        }).inserted_id

        # Generate sample resume PDF
        clean_roll = s['roll_no'].replace('/', '_')
        pdf_filename = f"Resume_{clean_roll}_sample.pdf"
        pdf_path = os.path.join(resume_dir, pdf_filename)
        create_sample_pdf(pdf_path, s['name'], s['roll_no'], s['department'], s['cgpa'])

        sid = db.students.insert_one({
            'user_id': uid,
            'name': s['name'],
            'email': s['email'],
            'roll_no': s['roll_no'],
            'department': s['department'],
            'cgpa': s['cgpa'],
            'backlogs': s['backlogs'],
            'passing_year': s['passing_year'],
            'phone': s['phone'],
            'skills': s['skills'],
            'resume_filename': pdf_filename,
            'status': s['status'],
            'created_at': get_utc_now()
        }).inserted_id
        student_map[s['roll_no']] = sid

    print(f" [✓] Created {len(student_map)} Students with sample PDF resumes.")

    # ---------------- 4. JOB OPPORTUNITIES (8 Jobs) ----------------
    jobs_data = [
        {
            'company_name': 'Google',
            'title': 'Software Development Engineer (L3)',
            'location': 'Bangalore, India (Hybrid)',
            'job_type': 'Full-time',
            'salary_package': 18.5,
            'min_cgpa': 8.0,
            'max_backlogs': 0,
            'departments': ['CSE', 'IT'],
            'skills_required': ['Algorithms', 'Data Structures', 'Python/Go/C++', 'System Design'],
            'description': 'As an SDE at Google, you will tackle scalable backend infrastructure, intelligent web interfaces, and distributed cloud computing systems that impact billions of global users.',
            'deadline': '2026-12-15',
            'status': 'Active'
        },
        {
            'company_name': 'Microsoft',
            'title': 'Associate Cloud Solutions Architect',
            'location': 'Hyderabad, India',
            'job_type': 'Full-time',
            'salary_package': 16.0,
            'min_cgpa': 7.5,
            'max_backlogs': 0,
            'departments': ['CSE', 'IT', 'ECE'],
            'skills_required': ['Azure Cloud', 'C# / Java', 'Networking', 'Security Architecture'],
            'description': 'Partner with enterprise customers to design and build cloud native solutions on Microsoft Azure. Involves architectural reviews and prototyping high-availability systems.',
            'deadline': '2026-11-30',
            'status': 'Active'
        },
        {
            'company_name': 'Amazon',
            'title': 'Systems Development Engineer (SysDE)',
            'location': 'Hyderabad / Bangalore',
            'job_type': 'Full-time',
            'salary_package': 15.0,
            'min_cgpa': 7.2,
            'max_backlogs': 1,
            'departments': ['CSE', 'IT', 'ECE', 'EEE'],
            'skills_required': ['Linux Internals', 'Python', 'AWS Services', 'Shell Scripting', 'CI/CD'],
            'description': 'SysDEs at Amazon own the reliability, scalability, and deployment automation for Amazon Web Services internal backbone infrastructure.',
            'deadline': '2026-12-05',
            'status': 'Active'
        },
        {
            'company_name': 'Infosys',
            'title': 'Specialist Programmer (Power Programmer)',
            'location': 'Bangalore / Mysore / Pune',
            'job_type': 'Full-time',
            'salary_package': 9.5,
            'min_cgpa': 7.0,
            'max_backlogs': 0,
            'departments': ['All'],
            'skills_required': ['Full Stack Java', 'Microservices', 'Spring Boot', 'React', 'MongoDB'],
            'description': 'High-performance developer role dedicated to digital core transformation, advanced algorithms, and enterprise scale cloud applications.',
            'deadline': '2026-12-20',
            'status': 'Active'
        },
        {
            'company_name': 'Tata Consultancy Services',
            'title': 'Digital Software Engineer (TCS Digital)',
            'location': 'Mumbai / Bangalore / Chennai',
            'job_type': 'Full-time',
            'salary_package': 7.5,
            'min_cgpa': 6.5,
            'max_backlogs': 1,
            'departments': ['All'],
            'skills_required': ['Python', 'SQL', 'Cloud Basics', 'Web Technologies'],
            'description': 'TCS Digital candidates solve complex digital transformation problems for banking, healthcare, retail, and manufacturing leaders.',
            'deadline': '2026-12-25',
            'status': 'Active'
        },
        {
            'company_name': 'Microsoft',
            'title': 'Data Analytics & AI Intern',
            'location': 'Bangalore, India',
            'job_type': 'Internship',
            'salary_package': 8.5,
            'min_cgpa': 7.5,
            'max_backlogs': 0,
            'departments': ['CSE', 'IT'],
            'skills_required': ['Python', 'SQL', 'Power BI', 'Machine Learning', 'Data Wrangling'],
            'description': 'Analyze large telemetry datasets to derive product usage patterns and build machine learning prediction models for Microsoft 365 services.',
            'deadline': '2026-11-25',
            'status': 'Active'
        },
        {
            'company_name': 'Google',
            'title': 'Technical Solutions Consultant',
            'location': 'Gurugram, India',
            'job_type': 'Full-time',
            'salary_package': 14.0,
            'min_cgpa': 7.8,
            'max_backlogs': 0,
            'departments': ['CSE', 'IT', 'ECE'],
            'skills_required': ['Python / Java', 'APIs & Web Services', 'Client Communication', 'Troubleshooting'],
            'description': 'Bridge the gap between Google engineering and strategic clients by deploying custom technical integrations on Google Cloud and Workspace platforms.',
            'deadline': '2026-12-10',
            'status': 'Active'
        },
        {
            'company_name': 'Infosys',
            'title': 'Systems Engineer',
            'location': 'Pan India',
            'job_type': 'Full-time',
            'salary_package': 4.5,
            'min_cgpa': 6.0,
            'max_backlogs': 2,
            'departments': ['All'],
            'skills_required': ['Programming Fundamentals', 'Database Basics', 'Analytical Skills'],
            'description': 'Entry-level engineering role with foundational training at the world-renowned Infosys Mysore campus.',
            'deadline': '2026-12-30',
            'status': 'Active'
        }
    ]

    job_ids = []
    for j in jobs_data:
        cid = company_map[j['company_name']]
        jid = db.jobs.insert_one({
            'company_id': cid,
            'company_name': j['company_name'],
            'title': j['title'],
            'location': j['location'],
            'job_type': j['job_type'],
            'salary_package': j['salary_package'],
            'min_cgpa': j['min_cgpa'],
            'max_backlogs': j['max_backlogs'],
            'departments': j['departments'],
            'skills_required': j['skills_required'],
            'description': j['description'],
            'deadline': j['deadline'],
            'status': j['status'],
            'created_at': get_utc_now() - timedelta(days=2)
        }).inserted_id
        job_ids.append((j['title'], jid, cid, j['salary_package']))

    print(f" [✓] Created {len(job_ids)} Job Opportunities.")

    # ---------------- 5. TRAINING PROGRAMS (5 Programs) ----------------
    trainings_data = [
        {
            'title': 'Full Stack Web Development Bootcamp (MERN & Flask)',
            'trainer_name': 'Mr. Aditya Saxena (Senior Full Stack Architect)',
            'description': 'Comprehensive hands-on training covering HTML5, CSS3, modern JavaScript, Node.js, Express, Python Flask, and MongoDB integration with production deployment on cloud.',
            'mode': 'Online (Zoom & Classroom Portal)',
            'venue': 'Virtual Live Classroom A',
            'start_date': '2026-11-20',
            'end_date': '2026-12-20',
            'eligibility': 'All Pre-Final & Final Year Students',
            'max_seats': 120,
            'status': 'Upcoming'
        },
        {
            'title': 'Data Structures & Algorithms Mastery Bootcamp',
            'trainer_name': 'Prof. K. V. Sharma (Competitive Programming Lead)',
            'description': 'Intensive problem-solving bootcamp focusing on LeetCode patterns, Trees, Graphs, Dynamic Programming, Heap, and time-space optimization for Tier-1 product interviews.',
            'mode': 'Offline',
            'venue': 'Campus Computer Lab 301 & 302',
            'start_date': '2026-11-18',
            'end_date': '2026-12-15',
            'eligibility': 'CSE, IT & ECE Students',
            'max_seats': 80,
            'status': 'Upcoming'
        },
        {
            'title': 'Cloud Computing with AWS & Docker Architecture',
            'trainer_name': 'Ms. Shalini Das (AWS Certified Solutions Architect)',
            'description': 'Learn cloud foundations, EC2, S3, RDS, VPC networking, Lambda serverless, and containerization with Docker and Kubernetes cluster management.',
            'mode': 'Online',
            'venue': 'Virtual Tech Hub',
            'start_date': '2026-11-25',
            'end_date': '2026-12-10',
            'eligibility': 'All Branches',
            'max_seats': 100,
            'status': 'Upcoming'
        },
        {
            'title': 'Corporate Soft Skills & HR Technical Interview Masterclass',
            'trainer_name': 'Dr. Anita Roy (Executive Corporate HR Coach)',
            'description': 'Mastering resume building, LinkedIn branding, group discussions, aptitude shortcuts, body language, and behavioral STAR technique interview rounds.',
            'mode': 'Offline',
            'venue': 'Auditorium Seminar Hall B',
            'start_date': '2026-11-15',
            'end_date': '2026-11-30',
            'eligibility': 'All Final Year Eligible Students',
            'max_seats': 200,
            'status': 'Upcoming'
        },
        {
            'title': 'Applied Machine Learning & Generative AI Workshop',
            'trainer_name': 'Dr. Sandeep Verma (AI Research Scientist)',
            'description': 'Hands-on practicals with Scikit-Learn, TensorFlow, LLMs, prompt engineering, vector databases, and building RAG pipelines using Python.',
            'mode': 'Hybrid',
            'venue': 'AI Research Lab 404 & Online Stream',
            'start_date': '2026-12-01',
            'end_date': '2026-12-18',
            'eligibility': 'CSE, IT & ECE',
            'max_seats': 90,
            'status': 'Upcoming'
        }
    ]

    training_ids = []
    for t in trainings_data:
        tid = db.trainings.insert_one({
            'title': t['title'],
            'trainer_name': t['trainer_name'],
            'description': t['description'],
            'mode': t['mode'],
            'venue': t['venue'],
            'start_date': t['start_date'],
            'end_date': t['end_date'],
            'eligibility': t['eligibility'],
            'max_seats': t['max_seats'],
            'status': t['status'],
            'created_at': get_utc_now()
        }).inserted_id
        training_ids.append(tid)

    print(f" [✓] Created {len(training_ids)} Training Programs.")

    # ---------------- 6. SAMPLE APPLICATIONS & PLACEMENTS ----------------
    # Let's map specific applications:
    # Arun Kumar (21CSE001) -> Google SDE -> Selected (18.5 LPA)
    # Priya Sharma (21IT002) -> Microsoft Cloud Arch -> Selected (16.0 LPA)
    # Rahul Verma (21ECE003) -> Amazon SysDE -> Selected (15.0 LPA)
    # Vikram Singh (21MECH005) -> Infosys Specialist -> Selected (9.5 LPA)
    # Divya Menon (21IT008) -> Microsoft Data Analytics -> Selected (8.5 LPA)
    # Ananya Patel (21CSE004) -> Infosys Specialist -> Shortlisted
    # Sneha Reddy (21EEE006) -> TCS Digital -> Interview Scheduled
    # Karthik N. (21CIVIL007) -> Infosys Systems Engineer -> Applied
    # Meera Nair (21ECE010) -> Google Technical Solutions -> Applied
    # Rohit Gupta (21CSE009) -> Infosys Systems Engineer -> Applied

    apps_config = [
        # (Roll, Job Title, Status, Remarks)
        ('21CSE001', 'Software Development Engineer (L3)', 'Selected', 'Exceptional performance in algorithm and coding interview rounds. Offered 18.5 LPA.'),
        ('21IT002', 'Associate Cloud Solutions Architect', 'Selected', 'Strong cloud architectural knowledge and system design acumen. Offered 16.0 LPA.'),
        ('21ECE003', 'Systems Development Engineer (SysDE)', 'Selected', 'Demonstrated deep proficiency in Linux systems and C++. Offered 15.0 LPA.'),
        ('21MECH005', 'Specialist Programmer (Power Programmer)', 'Selected', 'Excellent problem solving and full-stack coding capability. Offered 9.5 LPA.'),
        ('21IT008', 'Data Analytics & AI Intern', 'Selected', 'Outstanding statistical modeling and Python visualization skills. Offered 8.5 LPA.'),
        ('21CSE004', 'Specialist Programmer (Power Programmer)', 'Shortlisted', 'Cleared round 1 technical coding assessment. Technical interview scheduled for Nov 24.'),
        ('21EEE006', 'Digital Software Engineer (TCS Digital)', 'Interview Scheduled', 'Selected for technical interview round on Nov 22 at 11:00 AM.'),
        ('21CIVIL007', 'Systems Engineer', 'Applied', 'Application under preliminary screening by recruiter.'),
        ('21ECE010', 'Technical Solutions Consultant', 'Applied', 'Application received and profile forwarded to hiring team.'),
        ('21CSE009', 'Systems Engineer', 'Applied', 'Application received.')
    ]

    # Quick lookup for jobs by title
    job_lookup = {title: (jid, cid, pkg) for title, jid, cid, pkg in job_ids}

    for roll, jtitle, status, remarks in apps_config:
        sid = student_map[roll]
        jid, cid, pkg = job_lookup[jtitle]
        st_doc = db.students.find_one({'_id': sid})
        comp_doc = db.companies.find_one({'_id': cid})

        db.applications.insert_one({
            'job_id': jid,
            'student_id': sid,
            'company_id': cid,
            'applied_date': get_utc_now() - timedelta(days=5),
            'status': status,
            'remarks': remarks,
            'updated_at': get_utc_now()
        })

        if status == 'Selected':
            db.placements.insert_one({
                'student_id': sid,
                'student_name': st_doc['name'],
                'roll_no': st_doc['roll_no'],
                'department': st_doc['department'],
                'company_id': cid,
                'company_name': comp_doc['company_name'],
                'job_id': jid,
                'job_title': jtitle,
                'package': float(pkg),
                'academic_year': '2025-2026',
                'placement_date': get_utc_now() - timedelta(days=2)
            })

    # Sample training registrations
    for idx, (roll, sid) in enumerate(student_map.items()):
        # Register each student in 1 or 2 trainings
        t1 = training_ids[idx % len(training_ids)]
        db.training_registrations.insert_one({
            'training_id': t1,
            'student_id': sid,
            'student_name': db.students.find_one({'_id': sid})['name'],
            'student_roll': roll,
            'registered_date': get_utc_now() - timedelta(days=1),
            'status': 'Registered'
        })

    print(f" [✓] Created {len(apps_config)} Sample Applications and Placements.")
    print("\n[Database Seeding Complete] All records inserted successfully!")

if __name__ == '__main__':
    seed_database()
