import os
import sys
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    from extensions import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from views.auth import auth_bp
    from views.admin import admin_bp
    from views.jobs import jobs_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(jobs_bp)

    with app.app_context():
        db.create_all()
        _ensure_admin(app)

    return app


def _ensure_admin(app):
    from models import User
    from extensions import db
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User(
            username='admin',
            email=app.config['ADMIN_EMAIL'],
            is_admin=True,
            is_active=True
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    scheduler = None
    if 'scheduler' in sys.argv:
        from scheduler_service import start_scheduler
        scheduler = start_scheduler(app)
        print(f'Scheduler started with {len(scheduler.get_jobs())} jobs')
    app.run(host='0.0.0.0', port=5000, debug=True)
