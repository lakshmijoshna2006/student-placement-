from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.database import get_db, to_oid
from routes.auth import login_required, role_required

training_bp = Blueprint('training', __name__, url_prefix='/trainings')

@training_bp.route('')
def index():
    db = get_db()
    status_filter = request.args.get('status', '').strip()
    query = {}
    if status_filter and status_filter != 'All':
        query['status'] = status_filter

    trainings_list = list(db.trainings.find(query).sort('start_date', 1))

    # Check student registrations
    user_registered = set()
    student = None
    if session.get('role') == 'student' and 'user_id' in session:
        student = db.students.find_one({'user_id': to_oid(session['user_id'])})
        if student:
            user_registered = set(tr['training_id'] for tr in db.training_registrations.find({'student_id': student['_id']}))

    for t in trainings_list:
        t['is_registered'] = t['_id'] in user_registered
        t['reg_count'] = db.training_registrations.count_documents({'training_id': t['_id']})

    return render_template(
        'trainings.html',
        trainings=trainings_list,
        status_filter=status_filter,
        student=student
    )

@training_bp.route('/create', methods=['POST'])
@login_required
@role_required('admin')
def create():
    db = get_db()
    title = request.form.get('title', '').strip()
    trainer_name = request.form.get('trainer_name', '').strip()
    description = request.form.get('description', '').strip()
    mode = request.form.get('mode', 'Offline').strip()
    venue = request.form.get('venue', '').strip()
    start_date = request.form.get('start_date', '').strip()
    end_date = request.form.get('end_date', '').strip()
    eligibility = request.form.get('eligibility', 'All Students').strip()
    status = request.form.get('status', 'Upcoming').strip()
    
    try:
        max_seats = int(request.form.get('max_seats', 60))
    except ValueError:
        max_seats = 60

    if not title or not trainer_name:
        flash('Training title and trainer name are required.', 'danger')
        return redirect(url_for('training.index'))

    doc = {
        'title': title,
        'trainer_name': trainer_name,
        'description': description,
        'mode': mode,
        'venue': venue,
        'start_date': start_date,
        'end_date': end_date,
        'eligibility': eligibility,
        'max_seats': max_seats,
        'status': status,
        'created_at': datetime.now(timezone.utc)
    }
    db.trainings.insert_one(doc)

    flash(f"Training program '{title}' scheduled successfully.", 'success')
    return redirect(url_for('training.index'))

@training_bp.route('/<training_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit(training_id):
    db = get_db()
    oid = to_oid(training_id)
    training = db.trainings.find_one({'_id': oid})
    if not training:
        flash('Training not found.', 'danger')
        return redirect(url_for('training.index'))

    title = request.form.get('title', '').strip()
    trainer_name = request.form.get('trainer_name', '').strip()
    description = request.form.get('description', '').strip()
    mode = request.form.get('mode', 'Offline').strip()
    venue = request.form.get('venue', '').strip()
    start_date = request.form.get('start_date', '').strip()
    end_date = request.form.get('end_date', '').strip()
    eligibility = request.form.get('eligibility', 'All Students').strip()
    status = request.form.get('status', 'Upcoming').strip()

    try:
        max_seats = int(request.form.get('max_seats', training.get('max_seats', 60)))
    except ValueError:
        max_seats = training.get('max_seats', 60)

    db.trainings.update_one({'_id': oid}, {'$set': {
        'title': title,
        'trainer_name': trainer_name,
        'description': description,
        'mode': mode,
        'venue': venue,
        'start_date': start_date,
        'end_date': end_date,
        'eligibility': eligibility,
        'max_seats': max_seats,
        'status': status
    }})

    flash(f"Training '{title}' updated successfully.", 'success')
    return redirect(url_for('training.index'))

@training_bp.route('/<training_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete(training_id):
    db = get_db()
    oid = to_oid(training_id)
    training = db.trainings.find_one({'_id': oid})
    if not training:
        flash('Training not found.', 'danger')
        return redirect(url_for('training.index'))

    db.training_registrations.delete_many({'training_id': oid})
    db.trainings.delete_one({'_id': oid})

    flash(f"Training '{training.get('title')}' deleted.", 'info')
    return redirect(url_for('training.index'))

@training_bp.route('/<training_id>/participants')
@login_required
@role_required('admin')
def participants(training_id):
    db = get_db()
    oid = to_oid(training_id)
    training = db.trainings.find_one({'_id': oid})
    if not training:
        flash('Training not found.', 'danger')
        return redirect(url_for('training.index'))

    registrations = list(db.training_registrations.find({'training_id': oid}).sort('registered_date', -1))
    for reg in registrations:
        reg['student'] = db.students.find_one({'_id': to_oid(reg.get('student_id'))}) or {}

    return render_template('training_participants.html', training=training, registrations=registrations)
