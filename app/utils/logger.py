# app/utils/logger.py

from app.models import LogEntry, db
from datetime import datetime

def log_event(message):
    try:
        entry = LogEntry(message=message, timestamp=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Error al guardar el log: {str(e)}")
