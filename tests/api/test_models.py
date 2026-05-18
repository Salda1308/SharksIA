from api.database import init_db, SessionLocal
from api.models import User, Company, Design, Asset

def test_init_db_creates_tables():
    init_db()
    db = SessionLocal()
    # Si las tablas no existen esto lanza OperationalError
    db.query(User).first()
    db.query(Company).first()
    db.query(Design).first()
    db.query(Asset).first()
    db.close()
