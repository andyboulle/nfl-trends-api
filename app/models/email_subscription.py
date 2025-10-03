from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database.connection import Base

class EmailSubscription(Base):
    __tablename__ = 'email_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    subscription_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EmailSubscription(id={self.id}, email='{self.email}', is_active={self.is_active})>"