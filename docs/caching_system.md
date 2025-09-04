# NFL Trends API Caching System

## Overview

The NFL Trends API implements a comprehensive caching system using `cachetools` to improve performance and reduce database load. The system includes three main caches with different strategies and protected entries that ensure critical data is always available.

## Cache Types

### 1. Upcoming Games Cache (TTL Cache)
- **Type**: TTL (Time To Live) Cache
- **Max Size**: 16 entries
- **TTL**: 1 hour (3600 seconds)
- **Purpose**: Caches upcoming games endpoint responses
- **Key**: `"upcoming_games_empty_body"`

### 2. Weekly Trends Cache (LRU Cache)
- **Type**: LRU (Least Recently Used) Cache
- **Max Size**: 100 entries
- **Purpose**: Caches complex weekly trends query results
- **Key Generation**: SHA256 hash of filter parameters

### 3. Weekly Filter Options Cache (TTL Cache)
- **Type**: TTL (Time To Live) Cache
- **Max Size**: 1 entry
- **TTL**: 1 hour (3600 seconds)
- **Purpose**: Caches weekly filter options endpoint responses
- **Key**: `"weekly_filter_options"`

## Protected Cache Entries

The system maintains three protected cache entries that are preserved during cache clearing operations:

### 1. Default Upcoming Games
- **Key**: `"upcoming_games_empty_body"`
- **Content**: Response from upcoming games endpoint with empty body
- **Protection**: Preserved during cache clearing unless explicitly disabled

### 2. Initial Weekly Trends Query
- **Key**: `"0d0aeea50e84aae522b2f54ed54f14cd9f9b651b6cb50dd6aa873441282851e9"`
- **Content**: Comprehensive weekly trends query result with all major filter combinations
- **Protection**: Always preserved during cache clearing operations
- **Dynamic Content**: Games applicable section is dynamically populated from current upcoming games

### 3. Weekly Filter Options
- **Key**: `"weekly_filter_options"`
- **Content**: Available filter options for weekly trends (months, days, spreads, totals, etc.)
- **Protection**: Protected - preserved during cache clearing unless explicitly disabled

## Cache Key Generation

Weekly trends cache keys are generated using SHA256 hashing of the filter parameters:

```python
def generate_cache_key(data: Any) -> str:
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()
```

This ensures:
- Consistent keys for identical filter combinations
- Unique keys for different filter parameters
- Deterministic cache behavior

## Startup Behavior

On API startup, the system automatically:

1. **Fetches and caches upcoming games** with the protected key
2. **Fetches and caches weekly filter options** for immediate availability
3. **Extracts current game strings** from upcoming games
4. **Creates comprehensive initial weekly trends query** with:
   - All major categories (home/away, ats/outright, favorite/underdog, over/under)
   - Current month filters (September, None)
   - Day of week filters (Sunday, Monday, Thursday, Friday, None)
   - Spread and total ranges
   - All available seasons since 2006-2007
   - Dynamic games_applicable section using current games
5. **Executes and caches the initial query** using the generated hash key

## Cache Management Endpoints

### View Cache Statistics
```
GET /api/v1/cache/stats
```
Returns detailed information about both caches including sizes, keys, and configurations.

### Clear Upcoming Games Cache
```
POST /api/v1/cache/clear/upcoming-games?preserve_default=true
```
Clears the upcoming games cache with option to preserve the default entry.

### Clear Weekly Trends Cache
```
POST /api/v1/cache/clear/weekly-trends?preserve_initial=true
```
Clears the weekly trends cache with option to preserve the initial query.

### Clear Weekly Filter Options Cache
```
POST /api/v1/cache/clear/weekly-filter-options
```
Clears the weekly filter options cache to force refresh from database.

### Clear All Caches
```
POST /api/v1/cache/clear/all?preserve_protected=true
```
Clears all caches with option to preserve protected entries. When `preserve_protected=true` (default), upcoming games, initial weekly trends, and weekly filter options are preserved.

### Check Protected Entries
```
GET /api/v1/cache/protected-entries
```
Returns information about whether protected cache entries exist and their basic statistics, including weekly filter options cache status.

## Cache Hit Logging

The system includes debug logging for cache operations:

- **Cache Hits**: `🎯 CACHE HIT - [cache_type] cache hit for key: [key_prefix]...`
- **Upcoming Games**: `🎯 CACHE HIT - Upcoming games cache hit`
- **Weekly Trends**: `🎯 CACHE HIT - Weekly trends cache hit for key: 0d0aeea5...`
- **Weekly Filter Options**: `🎯 CACHE HIT - Weekly filter options cache hit`

## Performance Benefits

### Upcoming Games Cache
- **Before**: Database query on every request
- **After**: Cached response for 1 hour, database query only when cache expires
- **Impact**: Significant reduction in database load for frequent upcoming games requests

### Weekly Filter Options Cache
- **Before**: Database query with multiple DISTINCT operations on every request
- **After**: Cached response for 1 hour, database query only when cache expires
- **Impact**: Dramatic improvement in initial page load performance

### Weekly Trends Cache
- **Before**: Complex database queries with multiple joins and filters on every request
- **After**: Cached results for identical filter combinations
- **Impact**: Dramatic performance improvement for repeated complex queries

## Cache Behavior Examples

### First Request (Cache Miss)
1. Client sends weekly trends request with specific filters
2. System generates cache key from filters
3. Cache lookup returns null (cache miss)
4. Database query executes
5. Result is cached with generated key
6. Response returned to client

### Subsequent Identical Request (Cache Hit)
1. Client sends identical weekly trends request
2. System generates same cache key
3. Cache lookup returns cached result (cache hit)
4. Cached response returned immediately (no database query)

### Different Request (Cache Miss)
1. Client sends request with different filters
2. System generates different cache key
3. Cache lookup returns null (cache miss)
4. Database query executes with new filters
5. New result cached with new key

## Technical Implementation

### Files
- `app/cache.py`: Core caching functionality and configuration
- `app/startup.py`: Cache initialization logic
- `app/routers/cache_management.py`: Cache management endpoints
- `app/routers/upcoming_games.py`: Upcoming games caching integration
- `app/routers/weekly_trends.py`: Weekly trends caching integration

### Dependencies
- `cachetools`: Provides TTL and LRU cache implementations
- `hashlib`: Used for generating consistent cache keys
- `json`: Used for serializing filter data for key generation

## Best Practices

1. **Protected Entries**: Always preserve protected entries during cache clearing to maintain API performance
2. **Cache Statistics**: Monitor cache hit rates and sizes using the statistics endpoint
3. **Key Generation**: Ensure filter data is consistently structured for reliable cache key generation
4. **Startup Initialization**: Allow startup cache initialization to complete for optimal initial performance

## Troubleshooting

### Common Issues

**All requests return the same cached result:**
- Check if cache key generation is working correctly
- Verify filter parameters are being properly received and processed
- Clear cache and monitor cache hit logs

**Cache not hitting when expected:**
- Compare generated cache keys for similar requests
- Check if filter parameters are consistently structured
- Verify cache is not full (LRU eviction) or expired (TTL)

**Startup cache initialization fails:**
- Check upcoming games data availability
- Verify database connectivity during startup
- Review startup logs for error messages
