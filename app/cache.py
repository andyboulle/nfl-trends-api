"""
Cache configuration and management for NFL Trends API.

This module provides caching functionality using cachetools for:
1. upcoming_games endpoint - Small TTL cache for max 16 entries
2. weekly_trends endpoint - Larger LRU cache for complex query results
"""

import json
import hashlib
from typing import Any, Dict, List, Optional
from cachetools import TTLCache, LRUCache
from datetime import datetime


# Cache instances
upcoming_games_cache = TTLCache(maxsize=16, ttl=3600)  # 1 hour TTL, max 16 entries
weekly_trends_cache = LRUCache(maxsize=100)  # LRU cache for 100 entries

# Special keys for protected cache entries
UPCOMING_GAMES_KEY = "upcoming_games_empty_body"
INITIAL_WEEKLY_TRENDS_KEY = "0d0aeea50e84aae522b2f54ed54f14cd9f9b651b6cb50dd6aa873441282851e9"


def generate_cache_key(data: Any) -> str:
    """
    Generate a consistent cache key from any data structure.
    
    Args:
        data: The data to generate a key for (dict, list, string, etc.)
        
    Returns:
        A SHA256 hash string to use as cache key
    """
    # Convert to JSON string with sorted keys for consistency
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


def get_upcoming_games_from_cache() -> Optional[Dict]:
    """
    Get upcoming games from cache.
    
    Returns:
        Cached upcoming games data or None if not found
    """
    return upcoming_games_cache.get(UPCOMING_GAMES_KEY)


def set_upcoming_games_cache(data: Dict) -> None:
    """
    Set upcoming games in cache.
    
    Args:
        data: The upcoming games data to cache
    """
    upcoming_games_cache[UPCOMING_GAMES_KEY] = data


def get_weekly_trends_from_cache(cache_key: str) -> Optional[Dict]:
    """
    Get weekly trends from cache by key.
    
    Args:
        cache_key: The cache key to look up
        
    Returns:
        Cached weekly trends data or None if not found
    """
    return weekly_trends_cache.get(cache_key)


def set_weekly_trends_cache(cache_key: str, data: Dict) -> None:
    """
    Set weekly trends in cache.
    
    Args:
        cache_key: The cache key to use
        data: The weekly trends data to cache
    """
    weekly_trends_cache[cache_key] = data


def set_initial_weekly_trends_cache(data: Dict) -> None:
    """
    Set the initial weekly trends query result in cache.
    This entry should never be removed.
    
    Args:
        data: The initial weekly trends data to cache
    """
    weekly_trends_cache[INITIAL_WEEKLY_TRENDS_KEY] = data


def get_initial_weekly_trends_from_cache() -> Optional[Dict]:
    """
    Get the initial weekly trends query result from cache.
    
    Returns:
        Cached initial weekly trends data or None if not found
    """
    return weekly_trends_cache.get(INITIAL_WEEKLY_TRENDS_KEY)


def clear_upcoming_games_cache(preserve_default: bool = True) -> None:
    """
    Clear upcoming games cache.
    
    Args:
        preserve_default: If True, preserve the default upcoming games entry
    """
    if preserve_default and UPCOMING_GAMES_KEY in upcoming_games_cache:
        default_data = upcoming_games_cache[UPCOMING_GAMES_KEY]
        upcoming_games_cache.clear()
        upcoming_games_cache[UPCOMING_GAMES_KEY] = default_data
    else:
        upcoming_games_cache.clear()


def clear_weekly_trends_cache(preserve_initial: bool = True) -> None:
    """
    Clear weekly trends cache.
    
    Args:
        preserve_initial: If True, preserve the initial weekly trends entry
    """
    if preserve_initial and INITIAL_WEEKLY_TRENDS_KEY in weekly_trends_cache:
        initial_data = weekly_trends_cache[INITIAL_WEEKLY_TRENDS_KEY]
        weekly_trends_cache.clear()
        weekly_trends_cache[INITIAL_WEEKLY_TRENDS_KEY] = initial_data
    else:
        weekly_trends_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about both caches.
    
    Returns:
        Dictionary containing cache statistics
    """
    return {
        "upcoming_games_cache": {
            "type": "TTLCache",
            "maxsize": upcoming_games_cache.maxsize,
            "current_size": len(upcoming_games_cache),
            "ttl_seconds": upcoming_games_cache.ttl,
            "keys": list(upcoming_games_cache.keys())
        },
        "weekly_trends_cache": {
            "type": "LRUCache", 
            "maxsize": weekly_trends_cache.maxsize,
            "current_size": len(weekly_trends_cache),
            "keys": list(weekly_trends_cache.keys())
        },
        "protected_keys": {
            "upcoming_games_default": UPCOMING_GAMES_KEY,
            "initial_weekly_trends": INITIAL_WEEKLY_TRENDS_KEY
        },
        "timestamp": datetime.now().isoformat()
    }


def extract_games_from_upcoming_games(upcoming_games_data: Dict) -> List[str]:
    """
    Extract game strings from upcoming games data for use in weekly trends queries.
    
    Args:
        upcoming_games_data: The upcoming games response data
        
    Returns:
        List of game strings in format "HOMEABBREVvsAWAYABBREV"
    """
    games = []
    if "upcoming_games" in upcoming_games_data:
        for game in upcoming_games_data["upcoming_games"]:
            home_abbrev = game.get("home_abbreviation", "").value
            away_abbrev = game.get("away_abbreviation", "").value
            if home_abbrev and away_abbrev:
                games.append(f"{home_abbrev}vs{away_abbrev}")
    return games
