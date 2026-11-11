from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash
from models.database import get_db, to_oid, serialize_doc
from routes.auth import login_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    db = get_db()
    
    total_students = db.students.count_documents({})
    total_companies = db.companies.count_documents({})
    total_jobs = db.jobs.count_documents({})
    total_applications = db.applications.count_documents({})
    placed_students = db.placements.count_documents({})
    total_trainings = db.trainings.count_documents({})

    # Calculate average package
    placements = list(db.placements.find({}))
    avg_package = 0.0
    max_package = 0.0
    if placements:
        packages = [p.get('package', 0.0) for p in placements if isinstance(p.get('package'), (int, float))]
        if packages:
            avg_package = round(sum(packages) / len(packages), 2)
            max_package = max(packages)

    # Recent applications (last 6)
    recent_apps = list(db.applications.find().sort('applied_date', -1).limit(6))
    for app in recent_apps:
        app['student'] = db.students.find_one({'_id': to_oid(app.get('student_id'))}) or {}
        app['job'] = db.jobs.find_one({'_id': to_oid(app.get('job_id'))}) or {}
        app['company'] = db.companies.find_one({'_id': to_oid(app.get('company_id'))}) or {}

    # Recent jobs (last 5)
    recent_jobs = list(db.jobs.find().sort('created_at', -1).limit(5))

    # Department placement counts for chart
    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    dept_counts = {}
    for d in departments:
        # Find placed students from this department
        st_ids = [s['_id'] for s in db.students.find({'department': d}, {'_id': 1})]
        placed_in_dept = db.placements.count_documents({'student_id': {'$in': st_ids}})
        dept_counts[d] = placed_in_dept

    # Application status distribution
    status_counts = {
        'Applied': db.applications.count_documents({'status': 'Applied'}),
        'Shortlisted': db.applications.count_documents({'status': 'Shortlisted'}),
        'Interview Scheduled': db.applications.count_documents({'status': 'Interview Scheduled'}),
        'Selected': db.applications.count_documents({'status': 'Selected'}),
        'Rejected': db.applications.count_documents({'status': 'Rejected'})
    }

    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,
        placed_students=placed_students,
        total_trainings=total_trainings,
        avg_package=avg_package,
        max_package=max_package,
        recent_apps=recent_apps,
        recent_jobs=recent_jobs,
        dept_counts=dept_counts,
        status_counts=status_counts
    )

# ----------------- Student Management -----------------

@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def students():
    db = get_db()
    
    # Handle Add Student
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', 'Student@123')
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

        if not name or not email or not roll_no or not department:
            flash('Name, email, roll number, and department are required.', 'danger')
            return redirect(url_for('admin.students'))

        if db.users.find_one({'email': email}):
            flash('A user with this email already exists.', 'danger')
            return redirect(url_for('admin.students'))

        if db.students.find_one({'roll_no': roll_no}):
            flash('A student with this Roll Number already exists.', 'danger')
            return redirect(url_for('admin.students'))

        # Create user & student
        user_id = db.users.insert_one({
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': 'student',
            'status': 'active',
            'created_at': datetime.now(timezone.utc)
        }).inserted_id

        db.students.insert_one({
            'user_id': user_id,
            'name': name,
            'email': email,
            'roll_no': roll_no,
            'department': department,
            'cgpa': cgpa,
            'backlogs': backlogs,
            'phone': phone,
            'passing_year': passing_year,
            'skills': [s.strip() for s in skills.split(',') if s.strip()] if skills else [],
            'resume_filename': None,
            'status': 'Eligible',
            'created_at': datetime.now(timezone.utc)
        })

        flash(f'Student {name} ({roll_no}) added successfully.', 'success')
        return redirect(url_for('admin.students'))

    # Search & filters
    search_q = request.args.get('q', '').strip()
    dept_filter = request.args.get('dept', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = {}
    if search_q:
        query['$or'] = [
            {'name': {'$regex': search_q, '$options': 'i'}},
            {'email': {'$regex': search_q, '$options': 'i'}},
            {'roll_no': {'$regex': search_q, '$options': 'i'}}
        ]
    if dept_filter and dept_filter != 'All':
        query['department'] = dept_filter
    if status_filter and status_filter != 'All':
        query['status'] = status_filter

    student_list = list(db.students.find(query).sort('roll_no', 1))
    
    # Annotate with placement status
    for st in student_list:
        placement = db.placements.find_one({'student_id': st['_id']})
        st['placement'] = placement
        st['app_count'] = db.applications.count_documents({'student_id': st['_id']})

    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    return render_template(
        'students.html',
        students=student_list,
        search_q=search_q,
        dept_filter=dept_filter,
        status_filter=status_filter,
        departments=departments
    )

@admin_bp.route('/students/<student_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_student(student_id):
    db = get_db()
    oid = to_oid(student_id)
    student = db.students.find_one({'_id': oid})
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))

    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    phone = request.form.get('phone', '').strip()
    passing_year = request.form.get('passing_year', '').strip()
    skills = request.form.get('skills', '').strip()
    status = request.form.get('status', 'Eligible').strip()
    
    try:
        cgpa = float(request.form.get('cgpa', student.get('cgpa', 0.0)))
    except ValueError:
        cgpa = student.get('cgpa', 0.0)

    try:
        backlogs = int(request.form.get('backlogs', student.get('backlogs', 0)))
    except ValueError:
        backlogs = student.get('backlogs', 0)

    update_fields = {
        'name': name,
        'department': department,
        'cgpa': cgpa,
        'backlogs': backlogs,
        'phone': phone,
        'passing_year': passing_year,
        'status': status,
        'skills': [s.strip() for s in skills.split(',') if s.strip()] if skills else []
    }

    db.students.update_one({'_id': oid}, {'$set': update_fields})
    flash(f"Student details for {name} updated successfully.", 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/<student_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_student(student_id):
    db = get_db()
    oid = to_oid(student_id)
    student = db.students.find_one({'_id': oid})
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))

    # Delete linked user account
    if student.get('user_id'):
        db.users.delete_one({'_id': to_oid(student['user_id'])})

    # Delete student's applications, training registrations, placements
    db.applications.delete_many({'student_id': oid})
    db.training_registrations.delete_many({'student_id': oid})
    db.placements.delete_many({'student_id': oid})
    db.students.delete_one({'_id': oid})

    flash(f"Student {student.get('name')} and all associated records deleted.", 'info')
    return redirect(url_for('admin.students'))

# ----------------- Company Management -----------------

@admin_bp.route('/companies', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def companies():
    db = get_db()
    
    # Handle Add Company
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', 'Company@123')
        contact_person = request.form.get('contact_person', '').strip()
        phone = request.form.get('phone', '').strip()
        industry = request.form.get('industry', '').strip()
        website = request.form.get('website', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        if not company_name or not email:
            flash('Company name and email are required.', 'danger')
            return redirect(url_for('admin.companies'))

        if db.users.find_one({'email': email}):
            flash('A user with this email already exists.', 'danger')
            return redirect(url_for('admin.companies'))

        # Create user & company
        user_id = db.users.insert_one({
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': 'company',
            'status': 'active',
            'created_at': datetime.now(timezone.utc)
        }).inserted_id

        db.companies.insert_one({
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
        })

        flash(f'Company {company_name} registered successfully.', 'success')
        return redirect(url_for('admin.companies'))

    search_q = request.args.get('q', '').strip()
    query = {}
    if search_q:
        query['$or'] = [
            {'company_name': {'$regex': search_q, '$options': 'i'}},
            {'email': {'$regex': search_q, '$options': 'i'}},
            {'industry': {'$regex': search_q, '$options': 'i'}},
            {'location': {'$regex': search_q, '$options': 'i'}}
        ]

    company_list = list(db.companies.find(query).sort('company_name', 1))
    for comp in company_list:
        comp['jobs_count'] = db.jobs.count_documents({'company_id': comp['_id']})
        comp['hires_count'] = db.placements.count_documents({'company_id': comp['_id']})

    return render_template('companies.html', companies=company_list, search_q=search_q)

@admin_bp.route('/companies/<company_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_company(company_id):
    db = get_db()
    oid = to_oid(company_id)
    company = db.companies.find_one({'_id': oid})
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.companies'))

    company_name = request.form.get('company_name', '').strip()
    contact_person = request.form.get('contact_person', '').strip()
    phone = request.form.get('phone', '').strip()
    industry = request.form.get('industry', '').strip()
    website = request.form.get('website', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()

    update_fields = {
        'company_name': company_name,
        'contact_person': contact_person,
        'phone': phone,
        'industry': industry,
        'website': website,
        'location': location,
        'description': description
    }

    db.companies.update_one({'_id': oid}, {'$set': update_fields})
    # Also update company_name in any jobs posted by this company
    db.jobs.update_many({'company_id': oid}, {'$set': {'company_name': company_name}})
    
    flash(f"Company {company_name} updated successfully.", 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/companies/<company_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_company(company_id):
    db = get_db()
    oid = to_oid(company_id)
    company = db.companies.find_one({'_id': oid})
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.companies'))

    if company.get('user_id'):
        db.users.delete_one({'_id': to_oid(company['user_id'])})

    # Delete company's jobs, applications, and placement references
    job_ids = [j['_id'] for j in db.jobs.find({'company_id': oid}, {'_id': 1})]
    db.applications.delete_many({'job_id': {'$in': job_ids}})
    db.jobs.delete_many({'company_id': oid})
    db.companies.delete_one({'_id': oid})

    flash(f"Company {company.get('company_name')} and associated jobs removed.", 'info')
    return redirect(url_for('admin.companies'))

# ----------------- Application Management -----------------

@admin_bp.route('/applications')
@login_required
@role_required('admin')
def applications():
    db = get_db()
    
    # Filters
    company_filter = request.args.get('company_id', '').strip()
    status_filter = request.args.get('status', '').strip()
    dept_filter = request.args.get('dept', '').strip()

    query = {}
    if company_filter and company_filter != 'All':
        query['company_id'] = to_oid(company_filter)
    if status_filter and status_filter != 'All':
        query['status'] = status_filter

    raw_apps = list(db.applications.find(query).sort('applied_date', -1))
    
    companies_list = list(db.companies.find().sort('company_name', 1))
    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']

    app_list = []
    for app in raw_apps:
        app['student'] = db.students.find_one({'_id': to_oid(app.get('student_id'))}) or {}
        app['job'] = db.jobs.find_one({'_id': to_oid(app.get('job_id'))}) or {}
        app['company'] = db.companies.find_one({'_id': to_oid(app.get('company_id'))}) or {}

        if dept_filter and dept_filter != 'All':
            if app['student'].get('department') != dept_filter:
                continue
        app_list.append(app)

    return render_template(
        'applications.html',
        applications=app_list,
        role='admin',
        companies=companies_list,
        departments=departments,
        company_filter=company_filter,
        status_filter=status_filter,
        dept_filter=dept_filter
    )

# ----------------- Reports & Analytics -----------------

@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
    db = get_db()
    
    total_students = db.students.count_documents({})
    total_placed = db.placements.count_documents({})
    placement_rate = round((total_placed / total_students * 100), 1) if total_students > 0 else 0.0

    placements = list(db.placements.find({}))
    packages = [p['package'] for p in placements if isinstance(p.get('package'), (int, float))]
    
    highest_package = max(packages) if packages else 0.0
    avg_package = round(sum(packages) / len(packages), 2) if packages else 0.0
    median_package = 0.0
    if packages:
        sorted_pkg = sorted(packages)
        n = len(sorted_pkg)
        median_package = sorted_pkg[n // 2] if n % 2 != 0 else round((sorted_pkg[n // 2 - 1] + sorted_pkg[n // 2]) / 2, 2)

    # Department statistics breakdown
    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    dept_stats = []
    for dept in departments:
        total_dept_students = db.students.count_documents({'department': dept})
        dept_st_ids = [s['_id'] for s in db.students.find({'department': dept}, {'_id': 1})]
        dept_placed = db.placements.count_documents({'student_id': {'$in': dept_st_ids}})
        rate = round((dept_placed / total_dept_students * 100), 1) if total_dept_students > 0 else 0.0
        
        # Dept average package
        dept_placements = list(db.placements.find({'student_id': {'$in': dept_st_ids}}))
        dept_pkgs = [p['package'] for p in dept_placements if isinstance(p.get('package'), (int, float))]
        dept_avg_pkg = round(sum(dept_pkgs) / len(dept_pkgs), 2) if dept_pkgs else 0.0

        dept_stats.append({
            'department': dept,
            'total': total_dept_students,
            'placed': dept_placed,
            'unplaced': total_dept_students - dept_placed,
            'rate': rate,
            'avg_package': dept_avg_pkg
        })

    # Company recruit stats (Top hiring companies)
    companies = list(db.companies.find({}))
    company_stats = []
    for c in companies:
        count = db.placements.count_documents({'company_id': c['_id']})
        if count > 0:
            c_placements = list(db.placements.find({'company_id': c['_id']}))
            c_pkgs = [p['package'] for p in c_placements if isinstance(p.get('package'), (int, float))]
            c_avg = round(sum(c_pkgs) / len(c_pkgs), 2) if c_pkgs else 0.0
            company_stats.append({
                'company_name': c['company_name'],
                'hires': count,
                'avg_package': c_avg
            })
    company_stats.sort(key=lambda x: x['hires'], reverse=True)

    # Salary bracket distribution
    tier_super_dream = len([p for p in packages if p >= 12.0])
    tier_dream = len([p for p in packages if 6.0 <= p < 12.0])
    tier_regular = len([p for p in packages if p < 6.0])

    return render_template(
        'reports.html',
        total_students=total_students,
        total_placed=total_placed,
        placement_rate=placement_rate,
        highest_package=highest_package,
        avg_package=avg_package,
        median_package=median_package,
        dept_stats=dept_stats,
        company_stats=company_stats,
        tier_super_dream=tier_super_dream,
        tier_dream=tier_dream,
        tier_regular=tier_regular
    )
