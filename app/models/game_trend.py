from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Boolean, Numeric
from app.enums.game_enums import MonthEnum, DayOfWeekEnum

Base = declarative_base()

def create_game_trend_model(table_name: str):
    """
    Factory function to create a GameTrend model for a specific table.
    
    Args:
        table_name: The name of the table (e.g., 'phidal20250904')
    
    Returns:
        A GameTrend class configured for the specified table
    """
    
    class GameTrend(Base):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
        
        id = Column(String, primary_key=True)
        id_string = Column(String, nullable=False)
        category = Column(String, nullable=False)
        month = Column(Enum(MonthEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=True)
        day_of_week = Column(Enum(DayOfWeekEnum, native_enum=False, values_callable=lambda enum: [e.value for e in enum]), nullable=True)
        divisional = Column(Boolean, nullable=True)
        spread = Column(String, nullable=True)
        total = Column(String, nullable=True)
        seasons = Column(String, nullable=False)
        wins = Column(Integer, nullable=False)
        losses = Column(Integer, nullable=False)
        pushes = Column(Integer, nullable=False)
        total_games = Column(Integer, nullable=False)
        win_percentage = Column(Numeric(precision=4, scale=3), nullable=False)
        trend_string = Column(String, nullable=False)

        def __repr__(self):
            return f'<GameTrend(id={self.id_string}, record={self.wins}-{self.losses}-{self.pushes}, win_pct={self.win_percentage})>'
    
    # Set a unique class name to avoid conflicts
    GameTrend.__name__ = f'GameTrend_{table_name}'
    GameTrend.__qualname__ = f'GameTrend_{table_name}'
    
    return GameTrend
