import os
from datetime import datetime, timezone
from flask import Flask, render_template, session, send_from_directory, redirect, url_for
from config import Config
from models.database import get_db, is_mock_db, to_oid
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.student import student_bp
from routes.company import company_bp
from routes.jobs import jobs_bp
from routes.training import training_bp
from routes.placements import placements_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize Database connection
    with app.app_context():
        get_db()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(placements_bp)

    # Global template context processor
    @app.context_processor
    def inject_globals():
        role = session.get('role')
        name = session.get('name', '')
        email = session.get('email', '')
        return {
            'session_role': role,
            'session_name': name,
            'session_email': email,
            'is_mock_database': is_mock_db(),
            'current_year': datetime.now(timezone.utc).year
        }

    # Public Routes
    @app.route('/')
    def index():
        db = get_db()
        # Statistics for Landing Page
        total_students = db.students.count_documents({})
        total_companies = db.companies.count_documents({})
        total_jobs = db.jobs.count_documents({'status': 'Active'})
        total_placed = db.placements.count_documents({})
        
        placements = list(db.placements.find({}))
        packages = [p['package'] for p in placements if isinstance(p.get('package'), (int, float))]
        highest_pkg = max(packages) if packages else 0.0
        avg_pkg = round(sum(packages) / len(packages), 2) if packages else 0.0
        placement_rate = round((total_placed / total_students * 100), 1) if total_students > 0 else 92.5

        # Featured Jobs (up to 4 active)
        featured_jobs = list(db.jobs.find({'status': 'Active'}).sort('created_at', -1).limit(4))
        
        # Hiring Partners (Companies)
        partner_companies = list(db.companies.find().sort('company_name', 1).limit(8))

        # Recent Placements
        recent_placements = list(db.placements.find().sort('placement_date', -1).limit(6))

        return render_template(
            'index.html',
            total_students=total_students,
            total_companies=total_companies,
            total_jobs=total_jobs,
            total_placed=total_placed,
            highest_pkg=highest_pkg,
            avg_pkg=avg_pkg,
            placement_rate=placement_rate,
            featured_jobs=featured_jobs,
            partner_companies=partner_companies,
            recent_placements=recent_placements
        )

    @app.route('/about')
    def about():
        db = get_db()
        total_placed = db.placements.count_documents({})
        total_companies = db.companies.count_documents({})
        placements = list(db.placements.find({}))
        packages = [p['package'] for p in placements if isinstance(p.get('package'), (int, float))]
        highest_pkg = max(packages) if packages else 18.5
        avg_pkg = round(sum(packages) / len(packages), 2) if packages else 9.2

        return render_template(
            'about.html',
            total_placed=total_placed,
            total_companies=total_companies,
            highest_pkg=highest_pkg,
            avg_pkg=avg_pkg
        )

    @app.route('/uploads/resumes/<filename>')
    def uploaded_resume(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', custom_body='<div class="container py-5 text-center"><h2>404 - Page Not Found</h2><p class="text-muted">The requested page does not exist.</p><a href="/" class="btn btn-primary">Return Home</a></div>'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('base.html', custom_body='<div class="container py-5 text-center"><h2>403 - Access Forbidden</h2><p class="text-muted">You do not have permission to view this resource.</p><a href="/" class="btn btn-primary">Return Home</a></div>'), 403

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('base.html', custom_body='<div class="container py-5 text-center"><h2>500 - Server Error</h2><p class="text-muted">An unexpected server error occurred.</p><a href="/" class="btn btn-primary">Return Home</a></div>'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
