from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.database import get_db, to_oid
from routes.auth import login_required, role_required

jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

def get_logged_student():
    if session.get('role') != 'student':
        return None
    db = get_db()
    return db.students.find_one({'user_id': to_oid(session['user_id'])})

def get_logged_company():
    if session.get('role') != 'company':
        return None
    db = get_db()
    return db.companies.find_one({'user_id': to_oid(session['user_id'])})

@jobs_bp.route('')
def index():
    db = get_db()
    search_q = request.args.get('q', '').strip()
    dept_filter = request.args.get('dept', '').strip()
    type_filter = request.args.get('type', '').strip()
    min_pkg_filter = request.args.get('min_pkg', '').strip()

    query = {}
    
    # Non-admin users only see active jobs by default unless filtering
    if session.get('role') not in ['admin', 'company']:
        query['status'] = 'Active'

    if search_q:
        query['$or'] = [
            {'title': {'$regex': search_q, '$options': 'i'}},
            {'company_name': {'$regex': search_q, '$options': 'i'}},
            {'location': {'$regex': search_q, '$options': 'i'}},
            {'skills_required': {'$regex': search_q, '$options': 'i'}}
        ]
    if dept_filter and dept_filter != 'All':
        query['$or'] = query.get('$or', []) + [{'departments': 'All'}, {'departments': dept_filter}]
    if type_filter and type_filter != 'All':
        query['job_type'] = type_filter
    if min_pkg_filter:
        try:
            query['salary_package'] = {'$gte': float(min_pkg_filter)}
        except ValueError:
            pass

    jobs_list = list(db.jobs.find(query).sort('created_at', -1))

    # Enrich jobs with applicant count and student eligibility
    student = get_logged_student()
    applied_job_ids = set()
    if student:
        applied_job_ids = set(app['job_id'] for app in db.applications.find({'student_id': student['_id']}, {'job_id': 1}))

    for j in jobs_list:
        j['applicant_count'] = db.applications.count_documents({'job_id': j['_id']})
        if student:
            min_cgpa = float(j.get('min_cgpa', 0.0))
            max_backlogs = int(j.get('max_backlogs', 99))
            dept_eligible = j.get('departments', ['All'])
            
            is_dept_ok = ('All' in dept_eligible) or (student.get('department') in dept_eligible)
            is_cgpa_ok = float(student.get('cgpa', 0.0)) >= min_cgpa
            is_backlog_ok = int(student.get('backlogs', 0)) <= max_backlogs
            
            j['is_eligible'] = is_dept_ok and is_cgpa_ok and is_backlog_ok
            j['is_applied'] = j['_id'] in applied_job_ids

    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    return render_template(
        'jobs.html',
        jobs=jobs_list,
        search_q=search_q,
        dept_filter=dept_filter,
        type_filter=type_filter,
        min_pkg_filter=min_pkg_filter,
        departments=departments,
        student=student
    )

@jobs_bp.route('/<job_id>')
def details(job_id):
    db = get_db()
    oid = to_oid(job_id)
    job = db.jobs.find_one({'_id': oid})
    if not job:
        flash('Job posting not found.', 'danger')
        return redirect(url_for('jobs.index'))

    company = db.companies.find_one({'_id': to_oid(job.get('company_id'))}) or {}
    job['applicant_count'] = db.applications.count_documents({'job_id': oid})

    # Student specific evaluation
    student = get_logged_student()
    application = None
    eligibility = {
        'is_eligible': False,
        'cgpa_ok': False,
        'backlogs_ok': False,
        'dept_ok': False,
        'resume_ok': False,
        'reasons': []
    }

    if student:
        application = db.applications.find_one({'job_id': oid, 'student_id': student['_id']})
        
        # CGPA check
        min_cgpa = float(job.get('min_cgpa', 0.0))
        st_cgpa = float(student.get('cgpa', 0.0))
        eligibility['cgpa_ok'] = st_cgpa >= min_cgpa
        if not eligibility['cgpa_ok']:
            eligibility['reasons'].append(f"Minimum CGPA required is {min_cgpa}. Your CGPA is {st_cgpa}.")

        # Backlog check
        max_backlogs = int(job.get('max_backlogs', 99))
        st_backlogs = int(student.get('backlogs', 0))
        eligibility['backlogs_ok'] = st_backlogs <= max_backlogs
        if not eligibility['backlogs_ok']:
            eligibility['reasons'].append(f"Maximum backlogs permitted is {max_backlogs}. You have {st_backlogs} backlogs.")

        # Department check
        dept_eligible = job.get('departments', ['All'])
        st_dept = student.get('department')
        eligibility['dept_ok'] = ('All' in dept_eligible) or (st_dept in dept_eligible)
        if not eligibility['dept_ok']:
            eligibility['reasons'].append(f"Eligible departments are: {', '.join(dept_eligible)}. Your department is {st_dept}.")

        # Resume check
        eligibility['resume_ok'] = bool(student.get('resume_filename'))
        if not eligibility['resume_ok']:
            eligibility['reasons'].append("You must upload your resume (PDF) in your profile before applying.")

        eligibility['is_eligible'] = (
            eligibility['cgpa_ok'] and
            eligibility['backlogs_ok'] and
            eligibility['dept_ok'] and
            eligibility['resume_ok']
        )

    return render_template(
        'job_details.html',
        job=job,
        company=company,
        student=student,
        application=application,
        eligibility=eligibility
    )

@jobs_bp.route('/<job_id>/apply', methods=['POST'])
@login_required
@role_required('student')
def apply(job_id):
    db = get_db()
    oid = to_oid(job_id)
    job = db.jobs.find_one({'_id': oid})
    if not job:
        flash('Job opportunity does not exist.', 'danger')
        return redirect(url_for('jobs.index'))

    if job.get('status') != 'Active':
        flash('Applications for this job are currently closed.', 'warning')
        return redirect(url_for('jobs.details', job_id=job_id))

    student = get_logged_student()
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('jobs.details', job_id=job_id))

    st_id = student['_id']

    # 1. Prevent duplicate applications
    existing_app = db.applications.find_one({'job_id': oid, 'student_id': st_id})
    if existing_app:
        flash('You have already applied for this job position.', 'warning')
        return redirect(url_for('jobs.details', job_id=job_id))

    # 2. Check resume upload
    if not student.get('resume_filename'):
        flash('Please upload your resume in PDF format in your Student Profile before applying.', 'danger')
        return redirect(url_for('student.profile'))

    # 3. Check Eligibility Criteria
    min_cgpa = float(job.get('min_cgpa', 0.0))
    st_cgpa = float(student.get('cgpa', 0.0))
    if st_cgpa < min_cgpa:
        flash(f'Ineligible: Requires minimum CGPA of {min_cgpa}. Your CGPA is {st_cgpa}.', 'danger')
        return redirect(url_for('jobs.details', job_id=job_id))

    max_backlogs = int(job.get('max_backlogs', 99))
    st_backlogs = int(student.get('backlogs', 0))
    if st_backlogs > max_backlogs:
        flash(f'Ineligible: Maximum {max_backlogs} backlogs allowed. You currently have {st_backlogs}.', 'danger')
        return redirect(url_for('jobs.details', job_id=job_id))

    dept_eligible = job.get('departments', ['All'])
    st_dept = student.get('department')
    if ('All' not in dept_eligible) and (st_dept not in dept_eligible):
        flash(f'Ineligible: This drive is open to {", ".join(dept_eligible)} only.', 'danger')
        return redirect(url_for('jobs.details', job_id=job_id))

    # Insert Application
    app_doc = {
        'job_id': oid,
        'student_id': st_id,
        'company_id': job.get('company_id'),
        'applied_date': datetime.now(timezone.utc),
        'status': 'Applied',
        'remarks': 'Application received successfully.',
        'updated_at': datetime.now(timezone.utc)
    }
    db.applications.insert_one(app_doc)

    flash(f"Application submitted successfully for '{job.get('title')}' at {job.get('company_name')}!", 'success')
    return redirect(url_for('jobs.details', job_id=job_id))

@jobs_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'company'])
def create():
    db = get_db()
    role = session.get('role')

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        location = request.form.get('location', '').strip()
        job_type = request.form.get('job_type', 'Full-time').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills_required', '').strip()
        deadline = request.form.get('deadline', '').strip()
        
        # Departments selection
        selected_depts = request.form.getlist('departments')
        if not selected_depts:
            selected_depts = ['All']

        try:
            salary_package = float(request.form.get('salary_package', 0.0))
        except ValueError:
            salary_package = 0.0

        try:
            min_cgpa = float(request.form.get('min_cgpa', 6.0))
        except ValueError:
            min_cgpa = 6.0

        try:
            max_backlogs = int(request.form.get('max_backlogs', 0))
        except ValueError:
            max_backlogs = 0

        # Determine company_id and company_name
        if role == 'company':
            company = get_logged_company()
            if not company:
                flash('Company profile error.', 'danger')
                return redirect(url_for('company.dashboard'))
            company_id = company['_id']
            company_name = company['company_name']
        else: # admin
            company_id_val = request.form.get('company_id')
            company = db.companies.find_one({'_id': to_oid(company_id_val)})
            if not company:
                flash('Please select a valid company.', 'danger')
                return redirect(url_for('jobs.create'))
            company_id = company['_id']
            company_name = company['company_name']

        if not title:
            flash('Job Title is required.', 'danger')
            return redirect(url_for('jobs.create'))

        job_doc = {
            'company_id': company_id,
            'company_name': company_name,
            'title': title,
            'location': location,
            'job_type': job_type,
            'salary_package': salary_package,
            'min_cgpa': min_cgpa,
            'max_backlogs': max_backlogs,
            'departments': selected_depts,
            'skills_required': [s.strip() for s in skills.split(',') if s.strip()] if skills else [],
            'description': description,
            'deadline': deadline,
            'status': 'Active',
            'created_at': datetime.now(timezone.utc)
        }
        db.jobs.insert_one(job_doc)

        flash(f"Job opportunity '{title}' posted successfully!", 'success')
        if role == 'company':
            return redirect(url_for('company.dashboard'))
        return redirect(url_for('jobs.index'))

    # GET
    companies_list = []
    if role == 'admin':
        companies_list = list(db.companies.find().sort('company_name', 1))

    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    return render_template('job_form.html', action='Create', job={}, companies=companies_list, departments=departments)

@jobs_bp.route('/<job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'company'])
def edit(job_id):
    db = get_db()
    oid = to_oid(job_id)
    job = db.jobs.find_one({'_id': oid})
    if not job:
        flash('Job not found.', 'danger')
        return redirect(url_for('jobs.index'))

    # Security check for company
    if session.get('role') == 'company':
        company = get_logged_company()
        if str(job.get('company_id')) != str(company['_id']):
            flash('Unauthorized to modify this job.', 'danger')
            return redirect(url_for('jobs.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        location = request.form.get('location', '').strip()
        job_type = request.form.get('job_type', 'Full-time').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills_required', '').strip()
        deadline = request.form.get('deadline', '').strip()
        status = request.form.get('status', 'Active').strip()
        selected_depts = request.form.getlist('departments')
        if not selected_depts:
            selected_depts = ['All']

        try:
            salary_package = float(request.form.get('salary_package', job.get('salary_package', 0.0)))
        except ValueError:
            salary_package = job.get('salary_package', 0.0)

        try:
            min_cgpa = float(request.form.get('min_cgpa', job.get('min_cgpa', 6.0)))
        except ValueError:
            min_cgpa = job.get('min_cgpa', 6.0)

        try:
            max_backlogs = int(request.form.get('max_backlogs', job.get('max_backlogs', 0)))
        except ValueError:
            max_backlogs = job.get('max_backlogs', 0)

        update_fields = {
            'title': title,
            'location': location,
            'job_type': job_type,
            'salary_package': salary_package,
            'min_cgpa': min_cgpa,
            'max_backlogs': max_backlogs,
            'departments': selected_depts,
            'skills_required': [s.strip() for s in skills.split(',') if s.strip()] if skills else [],
            'description': description,
            'deadline': deadline,
            'status': status
        }

        db.jobs.update_one({'_id': oid}, {'$set': update_fields})
        flash(f"Job posting '{title}' updated successfully.", 'success')
        return redirect(url_for('jobs.details', job_id=job_id))

    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    companies_list = list(db.companies.find().sort('company_name', 1)) if session.get('role') == 'admin' else []
    return render_template('job_form.html', action='Edit', job=job, companies=companies_list, departments=departments)

@jobs_bp.route('/<job_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'company'])
def delete(job_id):
    db = get_db()
    oid = to_oid(job_id)
    job = db.jobs.find_one({'_id': oid})
    if not job:
        flash('Job not found.', 'danger')
        return redirect(url_for('jobs.index'))

    if session.get('role') == 'company':
        company = get_logged_company()
        if str(job.get('company_id')) != str(company['_id']):
            flash('Unauthorized.', 'danger')
            return redirect(url_for('company.dashboard'))

    # Delete applications for this job
    db.applications.delete_many({'job_id': oid})
    db.jobs.delete_one({'_id': oid})

    flash(f"Job posting '{job.get('title')}' deleted.", 'info')
    if session.get('role') == 'company':
        return redirect(url_for('company.dashboard'))
    return redirect(url_for('jobs.index'))
