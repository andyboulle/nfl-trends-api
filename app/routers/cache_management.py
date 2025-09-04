"""
Cache management router for NFL Trends API.

This module provides endpoints for:
1. Viewing cache statistics
2. Clearing caches while preserving protected entries
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.cache import (
    get_cache_stats,
    clear_upcoming_games_cache,
    clear_weekly_trends_cache,
    get_upcoming_games_from_cache,
    get_initial_weekly_trends_from_cache
)

router = APIRouter()


@router.get("/cache/stats", summary="Get cache statistics", tags=["Cache Management"])
def get_cache_statistics() -> Dict[str, Any]:
    """
    Get detailed statistics about all caches including:
    - Cache types and configurations
    - Current sizes and contents
    - Protected keys that won't be cleared
    - Timestamp of when stats were generated
    
    Returns:
        Dictionary containing comprehensive cache statistics
    """
    try:
        return get_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cache statistics: {str(e)}")


@router.post("/cache/clear/upcoming-games", summary="Clear upcoming games cache", tags=["Cache Management"])
def clear_upcoming_games_cache_endpoint(preserve_default: bool = True) -> Dict[str, str]:
    """
    Clear the upcoming games cache.
    
    Args:
        preserve_default: If True (default), preserves the default upcoming games entry
        
    Returns:
        Success message
    """
    try:
        clear_upcoming_games_cache(preserve_default=preserve_default)
        message = "Upcoming games cache cleared"
        if preserve_default:
            message += " (default entry preserved)"
        else:
            message += " (all entries removed)"
        
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing upcoming games cache: {str(e)}")


@router.post("/cache/clear/weekly-trends", summary="Clear weekly trends cache", tags=["Cache Management"])
def clear_weekly_trends_cache_endpoint(preserve_initial: bool = True) -> Dict[str, str]:
    """
    Clear the weekly trends cache.
    
    Args:
        preserve_initial: If True (default), preserves the initial weekly trends query result
        
    Returns:
        Success message
    """
    try:
        clear_weekly_trends_cache(preserve_initial=preserve_initial)
        message = "Weekly trends cache cleared"
        if preserve_initial:
            message += " (initial query preserved)"
        else:
            message += " (all entries removed)"
            
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing weekly trends cache: {str(e)}")


@router.post("/cache/clear/all", summary="Clear all caches", tags=["Cache Management"])
def clear_all_caches_endpoint(preserve_protected: bool = True) -> Dict[str, str]:
    """
    Clear all caches.
    
    Args:
        preserve_protected: If True (default), preserves protected entries (upcoming games default and initial weekly trends)
        
    Returns:
        Success message
    """
    try:
        clear_upcoming_games_cache(preserve_default=preserve_protected)
        clear_weekly_trends_cache(preserve_initial=preserve_protected)
        
        message = "All caches cleared"
        if preserve_protected:
            message += " (protected entries preserved)"
        else:
            message += " (all entries removed)"
            
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing all caches: {str(e)}")


@router.get("/cache/protected-entries", summary="Check protected cache entries", tags=["Cache Management"])
def get_protected_entries() -> Dict[str, Any]:
    """
    Check if the protected cache entries exist and provide basic info about them.
    
    Returns:
        Information about protected cache entries
    """
    try:
        upcoming_games_cached = get_upcoming_games_from_cache()
        initial_trends_cached = get_initial_weekly_trends_from_cache()
        
        return {
            "upcoming_games_default": {
                "exists": upcoming_games_cached is not None,
                "game_count": len(upcoming_games_cached.get("upcoming_games", [])) if upcoming_games_cached else 0
            },
            "initial_weekly_trends": {
                "exists": initial_trends_cached is not None,
                "trend_count": initial_trends_cached.get("count", 0) if initial_trends_cached else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking protected entries: {str(e)}")
