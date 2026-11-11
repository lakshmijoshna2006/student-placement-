from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.database import get_db, to_oid
from routes.auth import login_required, role_required

company_bp = Blueprint('company', __name__, url_prefix='/company')

def get_current_company():
    """Helper to fetch currently logged in company document."""
    if 'user_id' not in session:
        return None
    db = get_db()
    return db.companies.find_one({'user_id': to_oid(session['user_id'])})

@company_bp.route('/dashboard')
@login_required
@role_required('company')
def dashboard():
    db = get_db()
    company = get_current_company()
    if not company:
        flash('Company profile not found. Please log in again.', 'warning')
        return redirect(url_for('auth.logout'))

    comp_id = company['_id']

    # Jobs posted by company
    company_jobs = list(db.jobs.find({'company_id': comp_id}).sort('created_at', -1))
    job_ids = [j['_id'] for j in company_jobs]

    # Application metrics
    total_jobs = len(company_jobs)
    total_apps = db.applications.count_documents({'job_id': {'$in': job_ids}})
    shortlisted_apps = db.applications.count_documents({'job_id': {'$in': job_ids}, 'status': 'Shortlisted'})
    selected_apps = db.applications.count_documents({'job_id': {'$in': job_ids}, 'status': 'Selected'})
    rejected_apps = db.applications.count_documents({'job_id': {'$in': job_ids}, 'status': 'Rejected'})

    # Attach applicant count to each job
    for job in company_jobs:
        job['applicant_count'] = db.applications.count_documents({'job_id': job['_id']})
        job['selected_count'] = db.applications.count_documents({'job_id': job['_id'], 'status': 'Selected'})

    # Recent applications (last 6)
    recent_apps = list(db.applications.find({'job_id': {'$in': job_ids}}).sort('applied_date', -1).limit(6))
    for app in recent_apps:
        app['student'] = db.students.find_one({'_id': to_oid(app.get('student_id'))}) or {}
        app['job'] = db.jobs.find_one({'_id': to_oid(app.get('job_id'))}) or {}

    return render_template(
        'company_dashboard.html',
        company=company,
        total_jobs=total_jobs,
        total_apps=total_apps,
        shortlisted_apps=shortlisted_apps,
        selected_apps=selected_apps,
        rejected_apps=rejected_apps,
        company_jobs=company_jobs,
        recent_apps=recent_apps
    )

@company_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('company')
def profile():
    db = get_db()
    company = get_current_company()
    if not company:
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        phone = request.form.get('phone', '').strip()
        industry = request.form.get('industry', '').strip()
        website = request.form.get('website', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        if not company_name:
            flash('Company name cannot be empty.', 'danger')
            return render_template('company_profile.html', company=company)

        db.companies.update_one({'_id': company['_id']}, {'$set': {
            'company_name': company_name,
            'contact_person': contact_person,
            'phone': phone,
            'industry': industry,
            'website': website,
            'location': location,
            'description': description
        }})

        # Keep company_name consistent across jobs
        db.jobs.update_many({'company_id': company['_id']}, {'$set': {'company_name': company_name}})
        session['name'] = company_name
        flash('Company profile updated successfully.', 'success')
        return redirect(url_for('company.profile'))

    return render_template('company_profile.html', company=company)

@company_bp.route('/applications')
@login_required
@role_required('company')
def applications():
    db = get_db()
    company = get_current_company()
    if not company:
        return redirect(url_for('auth.logout'))

    comp_id = company['_id']
    company_jobs = list(db.jobs.find({'company_id': comp_id}))
    job_ids = [j['_id'] for j in company_jobs]

    # Filters
    job_filter = request.args.get('job_id', '').strip()
    status_filter = request.args.get('status', '').strip()
    dept_filter = request.args.get('dept', '').strip()

    query = {'job_id': {'$in': job_ids}}
    if job_filter and job_filter != 'All':
        query['job_id'] = to_oid(job_filter)
    if status_filter and status_filter != 'All':
        query['status'] = status_filter

    raw_apps = list(db.applications.find(query).sort('applied_date', -1))
    
    app_list = []
    for app in raw_apps:
        app['student'] = db.students.find_one({'_id': to_oid(app.get('student_id'))}) or {}
        app['job'] = db.jobs.find_one({'_id': to_oid(app.get('job_id'))}) or {}
        
        # Apply department filter on student if requested
        if dept_filter and dept_filter != 'All':
            if app['student'].get('department') != dept_filter:
                continue
        app_list.append(app)

    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    return render_template(
        'applications.html',
        applications=app_list,
        role='company',
        company=company,
        company_jobs=company_jobs,
        job_filter=job_filter,
        status_filter=status_filter,
        dept_filter=dept_filter,
        departments=departments
    )

@company_bp.route('/applications/<app_id>/status', methods=['POST'])
@login_required
@role_required(['company', 'admin'])
def update_application_status(app_id):
    db = get_db()
    oid = to_oid(app_id)
    application = db.applications.find_one({'_id': oid})
    if not application:
        flash('Application not found.', 'danger')
        return redirect(request.referrer or url_for('company.dashboard'))

    # Check permission for company
    if session.get('role') == 'company':
        company = get_current_company()
        if str(application.get('company_id')) != str(company['_id']):
            flash('Unauthorized access to application.', 'danger')
            return redirect(url_for('company.dashboard'))

    new_status = request.form.get('status', '').strip()
    remarks = request.form.get('remarks', '').strip()

    valid_statuses = ['Applied', 'Shortlisted', 'Interview Scheduled', 'Selected', 'Rejected']
    if new_status not in valid_statuses:
        flash('Invalid status provided.', 'danger')
        return redirect(request.referrer or url_for('company.applications'))

    db.applications.update_one({'_id': oid}, {'$set': {
        'status': new_status,
        'remarks': remarks,
        'updated_at': datetime.now(timezone.utc)
    }})

    # If status is "Selected", automatically record placement in placements collection
    student_id = application.get('student_id')
    job_id = application.get('job_id')
    company_id = application.get('company_id')
    
    if new_status == 'Selected':
        job = db.jobs.find_one({'_id': to_oid(job_id)}) or {}
        student = db.students.find_one({'_id': to_oid(student_id)}) or {}
        company = db.companies.find_one({'_id': to_oid(company_id)}) or {}

        # Check if placement already exists
        existing_placement = db.placements.find_one({
            'student_id': student_id,
            'job_id': job_id
        })
        if not existing_placement:
            db.placements.insert_one({
                'student_id': student_id,
                'student_name': student.get('name'),
                'roll_no': student.get('roll_no'),
                'department': student.get('department'),
                'company_id': company_id,
                'company_name': company.get('company_name', job.get('company_name')),
                'job_id': job_id,
                'job_title': job.get('title'),
                'package': float(job.get('salary_package', 0.0)),
                'academic_year': student.get('passing_year', '2025-2026'),
                'placement_date': datetime.now(timezone.utc)
            })
            # Update student status to Placed
            db.students.update_one({'_id': to_oid(student_id)}, {'$set': {'status': 'Placed'}})

    flash(f"Application status updated to '{new_status}'.", 'success')
    return redirect(request.referrer or url_for('company.applications'))

@company_bp.route('/history')
@login_required
@role_required('company')
def history():
    db = get_db()
    company = get_current_company()
    if not company:
        return redirect(url_for('auth.logout'))

    comp_id = company['_id']
    hires = list(db.placements.find({'company_id': comp_id}).sort('placement_date', -1))
    
    # Enrich hire details
    for h in hires:
        h['student'] = db.students.find_one({'_id': to_oid(h.get('student_id'))}) or {}
        h['job'] = db.jobs.find_one({'_id': to_oid(h.get('job_id'))}) or {}

    return render_template('recruitment_history.html', company=company, hires=hires)
