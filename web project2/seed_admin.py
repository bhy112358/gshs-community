from app import app
from extensions import db
from models import User

with app.app_context():
    email = "admin@test.com"
    existing = User.query.filter_by(email=email).first()

    if not existing:
        admin = User(
            username="admin",
            email=email,
            real_name="관리자",
            school="관리자",
            grade="운영자",
            is_admin=True
        )
        admin.set_password("1234")
        db.session.add(admin)
        db.session.commit()
        print("관리자 계정 생성 완료")
    else:
        print("이미 관리자 계정이 존재합니다.")