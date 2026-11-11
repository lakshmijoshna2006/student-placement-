import functools
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_db, to_oid

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash('You do not have permission to access that resource.', 'danger')
                if user_role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user_role == 'student':
                    return redirect(url_for('student.dashboard'))
                elif user_role == 'company':
                    return redirect(url_for('company.dashboard'))
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Retrieve full user document and profile info from session."""
    if 'user_id' not in session:
        return None
    db = get_db()
    user = db.users.find_one({'_id': to_oid(session['user_id'])})
    return user

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
        elif role == 'company':
            return redirect(url_for('company.dashboard'))
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role_hint = request.form.get('role', '').strip()

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('login.html', email=email, role=role_hint)

        db = get_db()
        user = db.users.find_one({'email': email})

        if not user or not check_password_hash(user.get('password_hash', ''), password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', email=email, role=role_hint)

        # Check role match if role was selected
        if role_hint and user.get('role') != role_hint:
            flash(f"Account found, but registered as a {user.get('role').capitalize()}, not {role_hint.capitalize()}.", 'warning')

        # Set session
        session.clear()
        session['user_id'] = str(user['_id'])
        session['email'] = user.get('email')
        session['role'] = user.get('role')
        
        # Fetch display name from related profile
        name = user.get('email')
        if user['role'] == 'student':
            st = db.students.find_one({'user_id': user['_id']})
            if st and st.get('name'):
                name = st['name']
                session['student_id'] = str(st['_id'])
        elif user['role'] == 'company':
            cp = db.companies.find_one({'user_id': user['_id']})
            if cp and cp.get('company_name'):
                name = cp['company_name']
                session['company_id'] = str(cp['_id'])
        elif user['role'] == 'admin':
            name = user.get('name', 'Placement Administrator')

        session['name'] = name
        flash(f'Welcome back, {name}!', 'success')

        # Redirect to next URL or role-based dashboard
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        if user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user['role'] == 'student':
            return redirect(url_for('student.dashboard'))
        elif user['role'] == 'company':
            return redirect(url_for('company.dashboard'))
        return redirect(url_for('index'))

    return render_template('login.html', role=request.args.get('role', ''))

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        roll_no = request.form.get('roll_no', '').strip().upper()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()
        passing_year = request.form.get('passing_year', '').strip()
        skills = request.form.get('skills', '').strip()
        
        try:
            cgpa = float(request.form.get('cgpa', 0.0))
        except ValueError:
            cgpa = 0.0

        try:
            backlogs = int(request.form.get('backlogs', 0))
        except ValueError:
            backlogs = 0

        # Validations
        if not name or not email or not password or not roll_no or not department:
            flash('Please fill in all mandatory fields.', 'danger')
            return render_template('register_student.html', form=request.form)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register_student.html', form=request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register_student.html', form=request.form)

        if cgpa < 0.0 or cgpa > 10.0:
            flash('CGPA must be between 0.0 and 10.0.', 'danger')
            return render_template('register_student.html', form=request.form)

        db = get_db()
        # Check existing email
        if db.users.find_one({'email': email}):
            flash('An account with this email address already exists.', 'danger')
            return render_template('register_student.html', form=request.form)

        # Check existing roll no
        if db.students.find_one({'roll_no': roll_no}):
            flash('A student with this Roll Number is already registered.', 'danger')
            return render_template('register_student.html', form=request.form)

        # Create user
        user_doc = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': 'student',
            'status': 'active',
            'created_at': datetime.now(timezone.utc)
        }
        user_res = db.users.insert_one(user_doc)
        user_id = user_res.inserted_id

        # Create student profile
        student_doc = {
            'user_id': user_id,
            'name': name,
            'email': email,
            'roll_no': roll_no,
            'department': department,
            'cgpa': cgpa,
            'backlogs': backlogs,
            'passing_year': passing_year,
            'phone': phone,
            'skills': [s.strip() for s in skills.split(',') if s.strip()] if skills else [],
            'resume_filename': None,
            'status': 'Eligible',
            'created_at': datetime.now(timezone.utc)
        }
        db.students.insert_one(student_doc)

        flash('Registration successful! Please log in to your student portal.', 'success')
        return redirect(url_for('auth.login', role='student'))

    return render_template('register_student.html', form={})

@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        contact_person = request.form.get('contact_person', '').strip()
        phone = request.form.get('phone', '').strip()
        industry = request.form.get('industry', '').strip()
        website = request.form.get('website', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        if not company_name or not email or not password:
            flash('Please fill in company name, email, and password.', 'danger')
            return render_template('register_company.html', form=request.form)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register_company.html', form=request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register_company.html', form=request.form)

        db = get_db()
        if db.users.find_one({'email': email}):
            flash('An account with this email address already exists.', 'danger')
            return render_template('register_company.html', form=request.form)

        # Create user
        user_doc = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': 'company',
            'status': 'active',
            'created_at': datetime.now(timezone.utc)
        }
        user_res = db.users.insert_one(user_doc)
        user_id = user_res.inserted_id

        # Create company profile
        company_doc = {
            'user_id': user_id,
            'company_name': company_name,
            'email': email,
            'contact_person': contact_person,
            'phone': phone,
            'industry': industry,
            'website': website,
            'location': location,
            'description': description,
            'verified': True,
            'created_at': datetime.now(timezone.utc)
        }
        db.companies.insert_one(company_doc)

        flash('Company registration successful! Please log in to post job opportunities.', 'success')
        return redirect(url_for('auth.login', role='company'))

    return render_template('register_company.html', form={})

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
