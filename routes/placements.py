from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.database import get_db, to_oid
from routes.auth import login_required, role_required

placements_bp = Blueprint('placements', __name__, url_prefix='/placements')

@placements_bp.route('')
def index():
    db = get_db()
    search_q = request.args.get('q', '').strip()
    dept_filter = request.args.get('dept', '').strip()
    year_filter = request.args.get('year', '').strip()

    query = {}
    if search_q:
        query['$or'] = [
            {'student_name': {'$regex': search_q, '$options': 'i'}},
            {'roll_no': {'$regex': search_q, '$options': 'i'}},
            {'company_name': {'$regex': search_q, '$options': 'i'}},
            {'job_title': {'$regex': search_q, '$options': 'i'}}
        ]
    if dept_filter and dept_filter != 'All':
        query['department'] = dept_filter
    if year_filter and year_filter != 'All':
        query['academic_year'] = year_filter

    placements_list = list(db.placements.find(query).sort('placement_date', -1))

    # Calculate summary metrics
    all_placements = list(db.placements.find({}))
    packages = [p['package'] for p in all_placements if isinstance(p.get('package'), (int, float))]
    highest_pkg = max(packages) if packages else 0.0
    avg_pkg = round(sum(packages) / len(packages), 2) if packages else 0.0
    total_placed = len(all_placements)

    # For admin dropdowns
    students_list = []
    companies_list = []
    if session.get('role') == 'admin':
        students_list = list(db.students.find().sort('name', 1))
        companies_list = list(db.companies.find().sort('company_name', 1))

    departments = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL']
    return render_template(
        'placements.html',
        placements=placements_list,
        total_placed=total_placed,
        highest_pkg=highest_pkg,
        avg_pkg=avg_pkg,
        search_q=search_q,
        dept_filter=dept_filter,
        year_filter=year_filter,
        departments=departments,
        students=students_list,
        companies=companies_list
    )

@placements_bp.route('/create', methods=['POST'])
@login_required
@role_required('admin')
def create():
    db = get_db()
    student_id_val = request.form.get('student_id')
    company_id_val = request.form.get('company_id')
    job_title = request.form.get('job_title', '').strip()
    academic_year = request.form.get('academic_year', '2025-2026').strip()
    
    try:
        package = float(request.form.get('package', 0.0))
    except ValueError:
        package = 0.0

    student = db.students.find_one({'_id': to_oid(student_id_val)})
    company = db.companies.find_one({'_id': to_oid(company_id_val)})

    if not student or not company or not job_title:
        flash('Student, Company, and Job Title are required.', 'danger')
        return redirect(url_for('placements.index'))

    # Insert placement record
    doc = {
        'student_id': student['_id'],
        'student_name': student.get('name'),
        'roll_no': student.get('roll_no'),
        'department': student.get('department'),
        'company_id': company['_id'],
        'company_name': company.get('company_name'),
        'job_title': job_title,
        'package': package,
        'academic_year': academic_year,
        'placement_date': datetime.now(timezone.utc)
    }
    db.placements.insert_one(doc)

    # Mark student as Placed
    db.students.update_one({'_id': student['_id']}, {'$set': {'status': 'Placed'}})

    flash(f"Placement recorded for {student.get('name')} at {company.get('company_name')} ({package} LPA)!", 'success')
    return redirect(url_for('placements.index'))

@placements_bp.route('/<placement_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete(placement_id):
    db = get_db()
    oid = to_oid(placement_id)
    placement = db.placements.find_one({'_id': oid})
    if not placement:
        flash('Placement record not found.', 'danger')
        return redirect(url_for('placements.index'))

    student_id = placement.get('student_id')
    db.placements.delete_one({'_id': oid})

    # If student has no other placement records, revert status to Eligible
    if student_id:
        remaining = db.placements.count_documents({'student_id': to_oid(student_id)})
        if remaining == 0:
            db.students.update_one({'_id': to_oid(student_id)}, {'$set': {'status': 'Eligible'}})

    flash('Placement record removed.', 'info')
    return redirect(url_for('placements.index'))
