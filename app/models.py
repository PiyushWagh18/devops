from datetime import datetime, timezone
from app import db


def _utcnow():
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(10), nullable=False, default='medium')
    status = db.Column(db.String(20), nullable=False, default='todo')
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    PRIORITIES = ['low', 'medium', 'high']
    STATUSES = ['todo', 'in-progress', 'done']

    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
