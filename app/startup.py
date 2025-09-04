"""
Startup logic for NFL Trends API.

This module handles initialization tasks that need to run when the application starts,
including pre-populating caches with initial data.
"""

from sqlalchemy.orm import Session
from app.database.connection import get_connection
from app.routers.weekly_trends import WeeklyTrendFilter, get_trends
from app.routers.upcoming_games import get_upcoming_games
from app.cache import (
    generate_cache_key,
    set_weekly_trends_cache,
    set_upcoming_games_cache,
    extract_games_from_upcoming_games
)


async def startup_cache_initialization():
    """
    Initialize caches with default data on application startup.
    
    This function:
    1. Fetches upcoming games and caches the result
    2. Creates the initial weekly trends query with dynamic games_applicable
    3. Caches the initial weekly trends query result
    """
    try:
        # Get database session
        db_session = next(get_connection())
        
        # Cache upcoming games first
        upcoming_games_result = await get_upcoming_games(db_session)
        set_upcoming_games_cache(upcoming_games_result)
        
        # Extract game strings for weekly trends query
        current_games = extract_games_from_upcoming_games(upcoming_games_result)
        
        # Create the initial weekly trends filter with dynamic games
        # Note: We'll create the filter data as a dictionary that matches the WeeklyTrendFilter structure
        initial_filter_data = {
            "category": [
                "home ats",
                "home outright", 
                "away ats",
                "away outright",
                "favorite ats",
                "favorite outright",
                "underdog ats",
                "underdog outright",
                "home favorite ats",
                "home favorite outright",
                "away underdog ats",
                "away underdog outright",
                "away favorite ats",
                "away favorite outright",
                "home underdog ats",
                "home underdog outright",
                "over",
                "under"
            ],
            "month": ["September", "None"],
            "day_of_week": ["Sunday", "Monday", "Thursday", "Friday", "None"],
            "spread": {
                "exact": [
                    "None",
                    "1.5",
                    "2.5", 
                    "3.0",
                    "3.5",
                    "5.5",
                    "6.5",
                    "7.5",
                    "8.5"
                ],
                "or_less": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                "or_more": [1, 2, 3, 4, 5, 6, 7, 8]
            },
            "total": {
                "exact": "None",
                "or_less": [40, 45, 50, 55, 60],
                "or_more": [30, 35, 40, 45, 50]
            },
            "seasons": {
                "exact": [
                    "since 2006-2007",
                    "since 2007-2008",
                    "since 2008-2009",
                    "since 2009-2010",
                    "since 2010-2011",
                    "since 2011-2012",
                    "since 2012-2013",
                    "since 2013-2014",
                    "since 2014-2015",
                    "since 2015-2016",
                    "since 2016-2017",
                    "since 2017-2018",
                    "since 2018-2019",
                    "since 2019-2020",
                    "since 2020-2021",
                    "since 2021-2022",
                    "since 2022-2023",
                    "since 2023-2024",
                    "since 2024-2025"
                ]
            },
            "limit": 5000,
            "offset": 0,
            "sort_by": [
                {"field": "win_percentage", "order": "desc"},
                {"field": "total_games", "order": "desc"}
            ],
            "games_applicable": {
                "games": current_games,
                "match_mode": "contains_any"
            }
        }
        
        # Create the filter object
        initial_filter = WeeklyTrendFilter(**initial_filter_data)
        
        # Generate the actual cache key for this filter
        cache_key = generate_cache_key(initial_filter.dict())
        
        # Execute the initial query and cache the result using the generated key
        initial_result = get_trends(initial_filter, db_session)
        set_weekly_trends_cache(cache_key, initial_result)
        
        print("✅ Cache initialization completed successfully")
        print(f"✅ Cached upcoming games: {len(upcoming_games_result.get('upcoming_games', []))} games")
        print(f"✅ Cached initial weekly trends: {len(initial_result)} trends")
        print(f"✅ Initial weekly trends cache key: {cache_key}")
        
    except Exception as e:
        print(f"❌ Error during cache initialization: {str(e)}")
        # Don't raise the exception to prevent app startup failure
    finally:
        if 'db_session' in locals():
            db_session.close()
