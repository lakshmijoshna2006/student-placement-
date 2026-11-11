import io
import os
import unittest
from datetime import datetime
from app import create_app
from models.database import get_db, to_oid
from seed import seed_database

class PlacementPortalTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        with cls.app.app_context():
            seed_database()

    def setUp(self):
        self.client = self.app.test_client()

    def test_01_home_and_about(self):
        """Test public Home and About pages"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'FIELDWISE', res.data)
        self.assertIn(b'Placement Highlights', res.data)

        res2 = self.client.get('/about')
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b'Training &amp; Placement Cell', res2.data)

    def test_02_admin_login(self):
        """Test 1: Admin login & dashboard"""
        res = self.client.post('/login', data={
            'email': 'admin@placement.edu',
            'password': 'Admin@123',
            'role': 'admin'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Administrative Control Center', res.data)

    def test_03_student_registration_and_login(self):
        """Test 2: Student registration and login"""
        # Register new student
        res_reg = self.client.post('/register/student', data={
            'name': 'Test Candidate',
            'email': 'test.candidate@student.edu',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'roll_no': '21CSE999',
            'department': 'CSE',
            'cgpa': '8.75',
            'backlogs': '0',
            'passing_year': '2026',
            'phone': '+91 99999 88888',
            'skills': 'Python, Flask, MongoDB'
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b'Registration successful', res_reg.data)

        # Login with newly registered student
        res_login = self.client.post('/login', data={
            'email': 'test.candidate@student.edu',
            'password': 'Password@123',
            'role': 'student'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Test Candidate', res_login.data)

    def test_04_company_registration_and_login(self):
        """Test 3: Company registration and login"""
        res_reg = self.client.post('/register/company', data={
            'company_name': 'Netflix Technology',
            'email': 'recruiting@netflix.com',
            'password': 'Netflix@123',
            'confirm_password': 'Netflix@123',
            'contact_person': 'Ted Sarandos',
            'phone': '+91 98888 77777',
            'industry': 'Entertainment & Cloud',
            'website': 'https://jobs.netflix.com',
            'location': 'Mumbai / Remote',
            'description': 'Leading global streaming entertainment platform.'
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b'Company registration successful', res_reg.data)

        # Login
        res_login = self.client.post('/login', data={
            'email': 'recruiting@netflix.com',
            'password': 'Netflix@123',
            'role': 'company'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Netflix Technology', res_login.data)

    def test_05_student_crud_operations(self):
        """Test 4: Admin Student CRUD operations"""
        # Admin login
        self.client.post('/login', data={'email': 'admin@placement.edu', 'password': 'Admin@123'})
        
        # View students
        res_view = self.client.get('/admin/students')
        self.assertEqual(res_view.status_code, 200)
        self.assertIn(b'Registered Students Directory', res_view.data)

        # Add Student via Admin
        res_add = self.client.post('/admin/students', data={
            'name': 'Admin Added Student',
            'email': 'admin.added@student.edu',
            'password': 'Student@123',
            'roll_no': '21IT777',
            'department': 'IT',
            'cgpa': '8.2',
            'backlogs': '0',
            'passing_year': '2026',
            'phone': '+91 98765 43210',
            'skills': 'Java, Spring'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b'Admin Added Student', res_add.data)

        # Edit Student
        db = get_db()
        st = db.students.find_one({'roll_no': '21IT777'})
        self.assertIsNotNone(st)
        res_edit = self.client.post(f'/admin/students/{st["_id"]}/edit', data={
            'name': 'Admin Added Student Updated',
            'department': 'IT',
            'cgpa': '8.5',
            'backlogs': '0',
            'phone': '+91 98765 00000',
            'passing_year': '2026',
            'status': 'Eligible',
            'skills': 'Java, Spring Boot, AWS'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b'updated successfully', res_edit.data)

        # Delete Student
        res_del = self.client.post(f'/admin/students/{st["_id"]}/delete', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIsNone(db.students.find_one({'_id': st['_id']}))

    def test_06_company_crud_operations(self):
        """Test 5: Admin Company CRUD operations"""
        # Admin login
        self.client.post('/login', data={'email': 'admin@placement.edu', 'password': 'Admin@123'})
        
        # View Companies
        res_view = self.client.get('/admin/companies')
        self.assertEqual(res_view.status_code, 200)
        self.assertIn(b'Registered Corporate Recruiters', res_view.data)

        # Add Company
        res_add = self.client.post('/admin/companies', data={
            'company_name': 'Salesforce India',
            'email': 'campus@salesforce.com',
            'password': 'Company@123',
            'contact_person': 'Marc Benioff',
            'phone': '+91 91234 56789',
            'industry': 'CRM & Cloud',
            'website': 'https://salesforce.com',
            'location': 'Hyderabad',
            'description': 'Customer Relationship Management cloud platform.'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b'Salesforce India', res_add.data)

        # Edit Company
        db = get_db()
        cp = db.companies.find_one({'email': 'campus@salesforce.com'})
        self.assertIsNotNone(cp)
        res_edit = self.client.post(f'/admin/companies/{cp["_id"]}/edit', data={
            'company_name': 'Salesforce Global Inc',
            'contact_person': 'Marc Benioff',
            'phone': '+91 91234 99999',
            'industry': 'Cloud & AI CRM',
            'website': 'https://salesforce.com',
            'location': 'Hyderabad / Bangalore',
            'description': 'Global cloud platform.'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b'updated successfully', res_edit.data)

        # Delete Company
        res_del = self.client.post(f'/admin/companies/{cp["_id"]}/delete', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIsNone(db.companies.find_one({'_id': cp['_id']}))

    def test_07_job_posting_searching_filtering(self):
        """Test 6 & 7: Job posting, searching, and filtering"""
        # Company login
        self.client.post('/login', data={'email': 'recruiter@google.com', 'password': 'Company@123'})
        
        # Post new Job
        res_post = self.client.post('/jobs/create', data={
            'title': 'AI Software Engineer (Deep Learning)',
            'job_type': 'Full-time',
            'salary_package': '22.0',
            'location': 'Bangalore, India',
            'deadline': '2026-12-31',
            'min_cgpa': '8.5',
            'max_backlogs': '0',
            'departments': ['CSE', 'IT'],
            'skills_required': 'Python, PyTorch, Transformers, Algorithms',
            'description': 'Research and implement deep learning foundational architectures.'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)

        # Search for the newly posted job
        res_search = self.client.get('/jobs?q=Deep+Learning')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'AI Software Engineer', res_search.data)

        # Filter by department
        res_filter = self.client.get('/jobs?dept=CSE&min_pkg=20')
        self.assertEqual(res_filter.status_code, 200)
        self.assertIn(b'22.0 LPA', res_filter.data)

    def test_08_resume_upload_and_download(self):
        """Test 12: PDF Resume upload and download"""
        # Student login
        self.client.post('/login', data={'email': 'priya.sharma@student.edu', 'password': 'Student@123'})

        # Upload a dummy PDF
        dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        data = {
            'name': 'Priya Sharma',
            'department': 'IT',
            'cgpa': '8.8',
            'backlogs': '0',
            'resume': (io.BytesIO(dummy_pdf_content), 'Priya_Updated_Resume.pdf')
        }
        res_upload = self.client.post('/student/profile', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res_upload.status_code, 200)
        self.assertIn(b'Resume PDF uploaded successfully', res_upload.data)

        # Check that download works
        db = get_db()
        st = db.students.find_one({'email': 'priya.sharma@student.edu'})
        self.assertIsNotNone(st.get('resume_filename'))
        res_dl = self.client.get(f'/student/resume/{st["resume_filename"]}')
        self.assertEqual(res_dl.status_code, 200)

    def test_09_job_application_and_duplicate_prevention(self):
        """Test 8, 9 & 10: Eligibility verification, application, and duplicate prevention"""
        # Student login (Arun Kumar, CGPA: 9.4, CSE, eligible for all drives)
        self.client.post('/login', data={'email': 'arun.kumar@student.edu', 'password': 'Student@123'})

        db = get_db()
        # Find Microsoft Cloud Solutions Architect job
        job = db.jobs.find_one({'title': 'Associate Cloud Solutions Architect'})
        self.assertIsNotNone(job)

        # Check job details page
        res_details = self.client.get(f'/jobs/{job["_id"]}')
        self.assertEqual(res_details.status_code, 200)
        self.assertIn(b'You satisfy all academic', res_details.data)

        # Apply for the job
        res_apply = self.client.post(f'/jobs/{job["_id"]}/apply', follow_redirects=True)
        self.assertEqual(res_apply.status_code, 200)
        self.assertIn(b'Application submitted successfully', res_apply.data)

        # Attempt to apply a second time -> MUST prevent duplicate
        res_dup = self.client.post(f'/jobs/{job["_id"]}/apply', follow_redirects=True)
        self.assertEqual(res_dup.status_code, 200)
        self.assertIn(b'already applied', res_dup.data)

    def test_10_eligibility_enforcement(self):
        """Test 10: Ineligible student rejection on application"""
        # Student login (Rohit Gupta, CGPA: 6.8, 2 backlogs)
        self.client.post('/login', data={'email': 'rohit.gupta@student.edu', 'password': 'Student@123'})

        db = get_db()
        # Find Google SDE job (Requires min CGPA 8.0 and 0 backlogs)
        job = db.jobs.find_one({'title': 'Software Development Engineer (L3)'})
        self.assertIsNotNone(job)

        # Details page should show ineligible alert
        res_details = self.client.get(f'/jobs/{job["_id"]}')
        self.assertEqual(res_details.status_code, 200)
        self.assertIn(b'Application Restricted', res_details.data)

        # Submitting POST apply must be rejected
        res_apply = self.client.post(f'/jobs/{job["_id"]}/apply', follow_redirects=True)
        self.assertEqual(res_apply.status_code, 200)
        self.assertIn(b'Ineligible', res_apply.data)

    def test_11_application_status_update_and_placement_sync(self):
        """Test 11: Application status update to Selected auto-records placement"""
        # Recruiter login (Microsoft)
        self.client.post('/login', data={'email': 'careers@microsoft.com', 'password': 'Company@123'})

        db = get_db()
        job = db.jobs.find_one({'title': 'Associate Cloud Solutions Architect'})
        student = db.students.find_one({'roll_no': '21CSE001'})
        app = db.applications.find_one({'job_id': job['_id'], 'student_id': student['_id']})
        self.assertIsNotNone(app)

        # Update status to 'Selected'
        res_update = self.client.post(f'/company/applications/{app["_id"]}/status', data={
            'status': 'Selected',
            'remarks': 'Outstanding system design round. Offer of 16.0 LPA approved!'
        }, follow_redirects=True)
        self.assertEqual(res_update.status_code, 200)

        # Verify placement collection was automatically updated
        placement = db.placements.find_one({'job_id': job['_id'], 'student_id': student['_id']})
        self.assertIsNotNone(placement)
        self.assertEqual(placement['package'], 16.0)

    def test_12_training_registration_and_cancellation(self):
        """Test 13: Training registration and cancellation"""
        # Student login
        self.client.post('/login', data={'email': 'meera.nair@student.edu', 'password': 'Student@123'})

        db = get_db()
        # Choose training she is not registered for
        training = db.trainings.find_one({'title': 'Cloud Computing with AWS & Docker Architecture'})
        self.assertIsNotNone(training)

        # Register for training
        res_reg = self.client.post(f'/student/trainings/{training["_id"]}/register', follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b'Successfully registered', res_reg.data)

        # Cancel registration
        res_cancel = self.client.post(f'/student/trainings/{training["_id"]}/cancel', follow_redirects=True)
        self.assertEqual(res_cancel.status_code, 200)
        self.assertIn(b'registration has been canceled', res_cancel.data)

    def test_13_placement_reports(self):
        """Test 14: Placement reports and analytics"""
        # Admin login
        self.client.post('/login', data={'email': 'admin@placement.edu', 'password': 'Admin@123'})
        res = self.client.get('/admin/reports')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Placement Analytics', res.data)
        self.assertIn(b'Departmental Academic Year Placement Performance', res.data)

    def test_14_role_based_access_control(self):
        """Test 15: Role-based access control and unauthorized route protection"""
        # Student logs in
        self.client.post('/login', data={'email': 'arun.kumar@student.edu', 'password': 'Student@123'})

        # Student trying to access Admin dashboard -> MUST be redirected
        res_admin = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Student Portal', res_admin.data)  # Redirected back to student dashboard

        # Student trying to access Company dashboard -> MUST be redirected
        res_comp = self.client.get('/company/dashboard', follow_redirects=True)
        self.assertEqual(res_comp.status_code, 200)
        self.assertIn(b'Student Portal', res_comp.data)

        # Logout
        self.client.get('/logout')

        # Unauthenticated access to /admin/students -> Redirects to login
        res_guest = self.client.get('/admin/students', follow_redirects=True)
        self.assertEqual(res_guest.status_code, 200)
        self.assertIn(b'Portal Authentication', res_guest.data)

if __name__ == '__main__':
    unittest.main()
