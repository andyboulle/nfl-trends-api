from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Boolean, Numeric
from app.enums.game_enums import MonthEnum, DayOfWeekEnum

Base = declarative_base()

class Trend(Base):
    __tablename__ = 'trends'
    id = Column(String, primary_key=True)
    id_string = Column(String, nullable=False)
    category = Column(String, nullable=False)
    month = Column(Enum(MonthEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    day_of_week = Column(Enum(DayOfWeekEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    divisional = Column(Boolean, nullable=False)
    spread = Column(String, nullable=False)
    total = Column(String, nullable=False)
    seasons = Column(String, nullable=False)
    wins = Column(Integer, nullable=False)
    losses = Column(Integer, nullable=False)
    pushes = Column(Integer, nullable=False)
    total_games = Column(Integer, nullable=False)
    win_percentage = Column(Numeric(precision=4, scale=3), nullable=False)
    trend_string = Column(String, nullable=False)

    def __repr__(self):
        return f'<Trend(id={self.id_string}, record={self.wins}-{self.losses}-{self.pushes}, win_pct={self.win_percentage})>'
