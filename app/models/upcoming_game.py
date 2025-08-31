from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Boolean, Numeric
from app.enums.game_enums import MonthEnum, DayOfWeekEnum, FullTeamNameEnum, TeamAbbreviationEnum, DivisionEnum

Base = declarative_base()

class UpcomingGame(Base):
    __tablename__ = 'upcoming_games'
    id = Column(String, primary_key=True)
    id_string = Column(String, nullable=False)
    date = Column(String, nullable=False)
    month = Column(Enum(MonthEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    day = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    season = Column(String, nullable=False)
    day_of_week = Column(Enum(DayOfWeekEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    home_team = Column(Enum(FullTeamNameEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    home_abbreviation = Column(Enum(TeamAbbreviationEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    home_division = Column(Enum(DivisionEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    away_team = Column(Enum(FullTeamNameEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    away_abbreviation = Column(Enum(TeamAbbreviationEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    away_division = Column(Enum(DivisionEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=False)
    divisional = Column(Boolean, nullable=False)
    spread = Column(Numeric(precision=4, scale=1), nullable=False)
    home_spread = Column(Numeric(precision=4, scale=1), nullable=False)
    home_spread_odds = Column(Integer, nullable=False)
    away_spread = Column(Numeric(precision=4, scale=1), nullable=False)
    away_spread_odds = Column(Integer, nullable=False)
    home_moneyline_odds = Column(Integer, nullable=False)
    away_moneyline_odds = Column(Integer, nullable=False)
    total = Column(Numeric(precision=4, scale=1), nullable=False)
    over = Column(Numeric(precision=4, scale=1), nullable=False)
    over_odds = Column(Integer, nullable=False)
    under = Column(Numeric(precision=4, scale=1), nullable=False)
    under_odds = Column(Integer, nullable=False)

    def __repr__(self):
        return f'<UpcomingGame(id={self.id_string}, date={self.date}, season={self.season}, home={self.home_abbreviation}, away={self.away_abbreviation})>'
