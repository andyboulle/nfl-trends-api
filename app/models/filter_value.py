from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime

Base = declarative_base()

class FilterValue(Base):
    __tablename__ = 'filter_values'
    
    filter_type = Column(String(50), primary_key=True)
    values_json = Column(String, nullable=False)
    last_updated = Column(DateTime, nullable=True)

    def __repr__(self):
        return f'<FilterValue(filter_type={self.filter_type}, last_updated={self.last_updated})>'