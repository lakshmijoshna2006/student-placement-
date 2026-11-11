import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_from_directory
from werkzeug.utils import secure_filename
from models.database import get_db, to_oid
from routes.auth import login_required, role_required

student_bp = Blueprint('student', __name__, url_prefix='/student')

def get_current_student():
    """Helper to fetch currently logged in student profile."""
    if 'user_id' not in session:
        return None
    db = get_db()
    return db.students.find_one({'user_id': to_oid(session['user_id'])})

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    db = get_db()
    student = get_current_student()
    if not student:
        flash('Student profile not found. Please contact the administrator.', 'warning')
        return redirect(url_for('auth.logout'))

    st_id = student['_id']

    # Application counts
    total_apps = db.applications.count_documents({'student_id': st_id})
    shortlisted_apps = db.applications.count_documents({'student_id': st_id, 'status': 'Shortlisted'})
    selected_apps = db.applications.count_documents({'student_id': st_id, 'status': 'Selected'})
    rejected_apps = db.applications.count_documents({'student_id': st_id, 'status': 'Rejected'})
    
    # Training counts
    registered_trainings_count = db.training_registrations.count_documents({'student_id': st_id})

    # Recent applications (last 5)
    applications = list(db.applications.find({'student_id': st_id}).sort('applied_date', -1).limit(5))
    for app in applications:
        app['job'] = db.jobs.find_one({'_id': to_oid(app.get('job_id'))}) or {}
        app['company'] = db.companies.find_one({'_id': to_oid(app.get('company_id'))}) or {}

    # Placed record if any
    placement_record = db.placements.find_one({'student_id': st_id})
    if placement_record:
        placement_record['company'] = db.companies.find_one({'_id': to_oid(placement_record.get('company_id'))})
        placement_record['job'] = db.jobs.find_one({'_id': to_oid(placement_record.get('job_id'))})

    # Recommended eligible jobs
    # Student matches if cgpa >= min_cgpa and backlogs <= max_backlogs and department in eligible_departments
    all_active_jobs = list(db.jobs.find({'status': 'Active'}).sort('created_at', -1))
    applied_job_ids = set(app.get('job_id') for app in db.applications.find({'student_id': st_id}, {'job_id': 1}))
    
    recommended_jobs = []
    for job in all_active_jobs:
        # Check eligibility
        min_cgpa = job.get('min_cgpa', 0.0)
        max_backlogs = job.get('max_backlogs', 99)
        dept_eligible = job.get('departments', ['All'])
        
        is_dept_ok = ('All' in dept_eligible) or (student.get('department') in dept_eligible)
        is_cgpa_ok = float(student.get('cgpa', 0.0)) >= float(min_cgpa)
        is_backlog_ok = int(student.get('backlogs', 0)) <= int(max_backlogs)

        job['is_eligible'] = is_dept_ok and is_cgpa_ok and is_backlog_ok
        job['is_applied'] = job['_id'] in applied_job_ids
        
        if job['is_eligible'] and not job['is_applied']:
            recommended_jobs.append(job)

    # Upcoming trainings (last 3)
    upcoming_trainings = list(db.trainings.find({'status': 'Upcoming'}).sort('start_date', 1).limit(3))
    user_registered_trainings = set(tr['training_id'] for tr in db.training_registrations.find({'student_id': st_id}))
    for tr in upcoming_trainings:
        tr['is_registered'] = tr['_id'] in user_registered_trainings

    return render_template(
        'student_dashboard.html',
        student=student,
        total_apps=total_apps,
        shortlisted_apps=shortlisted_apps,
        selected_apps=selected_apps,
        rejected_apps=rejected_apps,
        registered_trainings_count=registered_trainings_count,
        applications=applications,
        placement_record=placement_record,
        recommended_jobs=recommended_jobs[:4],
        upcoming_trainings=upcoming_trainings
    )

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def profile():
    db = get_db()
    student = get_current_student()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        passing_year = request.form.get('passing_year', '').strip()
        skills = request.form.get('skills', '').strip()
        bio = request.form.get('bio', '').strip()
        linkedin = request.form.get('linkedin', '').strip()
        github = request.form.get('github', '').strip()
        
        try:
            cgpa = float(request.form.get('cgpa', student.get('cgpa', 0.0)))
        except ValueError:
            cgpa = student.get('cgpa', 0.0)

        try:
            backlogs = int(request.form.get('backlogs', student.get('backlogs', 0)))
        except ValueError:
            backlogs = student.get('backlogs', 0)

        update_data = {
            'name': name,
            'phone': phone,
            'department': department,
            'cgpa': cgpa,
            'backlogs': backlogs,
            'passing_year': passing_year,
            'skills': [s.strip() for s in skills.split(',') if s.strip()] if skills else [],
            'bio': bio,
            'linkedin': linkedin,
            'github': github
        }

        # Check for resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                filename = file.filename
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext != 'pdf':
                    flash('Resume must be in PDF format (.pdf) only.', 'danger')
                    return render_template('profile.html', student=student)
                
                # Secure unique filename
                clean_roll = student.get('roll_no', 'student').replace('/', '_')
                saved_filename = secure_filename(f"Resume_{clean_roll}_{int(datetime.now(timezone.utc).timestamp())}.pdf")
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, saved_filename))
                update_data['resume_filename'] = saved_filename
                flash('Resume PDF uploaded successfully!', 'success')

        db.students.update_one({'_id': student['_id']}, {'$set': update_data})
        session['name'] = name
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('student.profile'))

    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    return render_template('profile.html', student=student, departments=departments)

@student_bp.route('/applications')
@login_required
@role_required('student')
def applications():
    db = get_db()
    student = get_current_student()
    if not student:
        return redirect(url_for('auth.logout'))

    st_id = student['_id']
    apps = list(db.applications.find({'student_id': st_id}).sort('applied_date', -1))
    for app in apps:
        app['job'] = db.jobs.find_one({'_id': to_oid(app.get('job_id'))}) or {}
        app['company'] = db.companies.find_one({'_id': to_oid(app.get('company_id'))}) or {}

    return render_template('applications.html', applications=apps, role='student', student=student)

@student_bp.route('/trainings')
@login_required
@role_required('student')
def trainings():
    db = get_db()
    student = get_current_student()
    trainings_list = list(db.trainings.find().sort('start_date', 1))
    
    st_id = student['_id']
    user_registered = set(tr['training_id'] for tr in db.training_registrations.find({'student_id': st_id}))
    
    for t in trainings_list:
        t['is_registered'] = t['_id'] in user_registered
        t['reg_count'] = db.training_registrations.count_documents({'training_id': t['_id']})

    return render_template('trainings.html', trainings=trainings_list, role='student', student=student)

@student_bp.route('/trainings/<training_id>/register', methods=['POST'])
@login_required
@role_required('student')
def register_training(training_id):
    db = get_db()
    student = get_current_student()
    oid = to_oid(training_id)
    training = db.trainings.find_one({'_id': oid})
    if not training:
        flash('Training program not found.', 'danger')
        return redirect(url_for('student.trainings'))

    # Check already registered
    existing = db.training_registrations.find_one({'training_id': oid, 'student_id': student['_id']})
    if existing:
        flash('You are already registered for this training program.', 'warning')
        return redirect(url_for('student.trainings'))

    # Check max seats limit
    max_seats = int(training.get('max_seats', 100))
    current_count = db.training_registrations.count_documents({'training_id': oid})
    if current_count >= max_seats:
        flash('Registration is full for this training program.', 'danger')
        return redirect(url_for('student.trainings'))

    db.training_registrations.insert_one({
        'training_id': oid,
        'student_id': student['_id'],
        'student_name': student.get('name'),
        'student_roll': student.get('roll_no'),
        'registered_date': datetime.now(timezone.utc),
        'status': 'Registered'
    })

    flash(f"Successfully registered for '{training.get('title')}'!", 'success')
    return redirect(url_for('student.trainings'))

@student_bp.route('/trainings/<training_id>/cancel', methods=['POST'])
@login_required
@role_required('student')
def cancel_training(training_id):
    db = get_db()
    student = get_current_student()
    oid = to_oid(training_id)
    
    res = db.training_registrations.delete_one({'training_id': oid, 'student_id': student['_id']})
    if res.deleted_count > 0:
        flash('Training registration has been canceled.', 'info')
    else:
        flash('You were not registered for this training.', 'warning')
    return redirect(url_for('student.trainings'))

@student_bp.route('/resume/<filename>')
@login_required
def download_resume(filename):
    """Download/view resume file."""
    upload_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_dir, filename)
