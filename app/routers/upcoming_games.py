from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from app.models.upcoming_game import UpcomingGame
from app.database.connection import get_connection
from app.cache import (
    get_upcoming_games_from_cache,
    set_upcoming_games_cache
)

router = APIRouter()

@router.get("/upcoming-games", summary="Retrieve all upcoming games", tags=["Upcoming Games"])
async def get_upcoming_games(session: Session = Depends(get_connection)):
    """
    Retrieve all upcoming games from the database.
    
    This endpoint returns all games from the upcoming_games table without any filters.
    Uses caching to improve performance with TTL cache.
    """
    # Try to get from cache first
    cached_data = get_upcoming_games_from_cache()
    if cached_data is not None:
        print("🎯 CACHE HIT - Upcoming games cache hit")
        return cached_data
    
    try:
        # Query all upcoming games from the database
        upcoming_games = session.query(UpcomingGame).all()
        
        # Convert to list of dictionaries for JSON response
        games_list = []
        for game in upcoming_games:
            game_dict = {
                "id": game.id,
                "id_string": game.id_string,
                "date": game.date,
                "month": game.month,
                "day": game.day,
                "year": game.year,
                "season": game.season,
                "day_of_week": game.day_of_week,
                "home_team": game.home_team,
                "home_abbreviation": game.home_abbreviation,
                "home_division": game.home_division,
                "away_team": game.away_team,
                "away_abbreviation": game.away_abbreviation,
                "away_division": game.away_division,
                "divisional": game.divisional,
                "spread": float(game.spread) if game.spread else None,
                "home_spread": float(game.home_spread) if game.home_spread else None,
                "home_spread_odds": game.home_spread_odds,
                "away_spread": float(game.away_spread) if game.away_spread else None,
                "away_spread_odds": game.away_spread_odds,
                "home_moneyline_odds": game.home_moneyline_odds,
                "away_moneyline_odds": game.away_moneyline_odds,
                "total": float(game.total) if game.total else None,
                "over": float(game.over) if game.over else None,
                "over_odds": game.over_odds,
                "under": float(game.under) if game.under else None,
                "under_odds": game.under_odds
            }
            games_list.append(game_dict)
        
        result = {
            "upcoming_games": games_list,
            "total_count": len(games_list)
        }
        
        # Cache the result
        set_upcoming_games_cache(result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving upcoming games: {str(e)}")
