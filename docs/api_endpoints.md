# NFL Trends API Endpoints Documentation

This document provides comprehensive documentation for all endpoints in the NFL Trends FastAPI application, including inputs, restrictions, values, and outputs.

## Table of Contents

1. [Overview](#overview)
2. [Common Data Types](#common-data-types)
3. [Response Format](#response-format)
4. [Trends Endpoints](#trends-endpoints)
5. [Weekly Trends Endpoints](#weekly-trends-endpoints)
6. [Game Trends Endpoints](#game-trends-endpoints)
7. [Games Endpoints](#games-endpoints)
8. [Upcoming Games Endpoints](#upcoming-games-endpoints)
9. [Error Handling](#error-handling)

---

## Overview

The NFL Trends API provides access to historical NFL betting trends, game data, and upcoming game information. All endpoints support various filtering options and return JSON responses with consistent structure.

**Base URL**: `/api/v1` (assumed based on typical FastAPI structure)

**Authentication**: None currently required

**Content-Type**: `application/json`

---

## Common Data Types

### Enum Values

#### CategoryEnum
**Valid Values:**
- `"home outright"` - Home team to win straight up
- `"away outright"` - Away team to win straight up
- `"favorite outright"` - Favorite to win straight up
- `"underdog outright"` - Underdog to win straight up
- `"home favorite outright"` - Home team when favored to win straight up
- `"away underdog outright"` - Away team when underdog to win straight up
- `"away favorite outright"` - Away team when favored to win straight up
- `"home underdog outright"` - Home team when underdog to win straight up
- `"home ats"` - Home team against the spread
- `"away ats"` - Away team against the spread
- `"favorite ats"` - Favorite against the spread
- `"underdog ats"` - Underdog against the spread
- `"home favorite ats"` - Home team when favored against the spread
- `"away underdog ats"` - Away team when underdog against the spread
- `"away favorite ats"` - Away team when favored against the spread
- `"home underdog ats"` - Home team when underdog against the spread
- `"over"` - Over total points
- `"under"` - Under total points

#### MonthEnum
**Valid Values:**
`"January"`, `"February"`, `"March"`, `"April"`, `"May"`, `"June"`, `"July"`, `"August"`, `"September"`, `"October"`, `"November"`, `"December"`

#### DayOfWeekEnum
**Valid Values:**
`"Sunday"`, `"Monday"`, `"Tuesday"`, `"Wednesday"`, `"Thursday"`, `"Friday"`, `"Saturday"`

#### TeamAbbreviationEnum
**Valid Values:**
`"NYJ"`, `"NE"`, `"BUF"`, `"MIA"`, `"PIT"`, `"BAL"`, `"CIN"`, `"CLE"`, `"TEN"`, `"IND"`, `"JAX"`, `"HOU"`, `"KC"`, `"LAC"`, `"LV"`, `"DEN"`, `"DAL"`, `"PHI"`, `"NYG"`, `"WAS"`, `"CHI"`, `"MIN"`, `"GB"`, `"DET"`, `"ATL"`, `"NO"`, `"CAR"`, `"TB"`, `"ARI"`, `"SEA"`, `"SF"`, `"LAR"`

#### FullTeamNameEnum
**Valid Values:**
`"New York Jets"`, `"New England Patriots"`, `"Buffalo Bills"`, `"Miami Dolphins"`, `"Pittsburgh Steelers"`, `"Baltimore Ravens"`, `"Cincinnati Bengals"`, `"Cleveland Browns"`, `"Tennessee Titans"`, `"Indianapolis Colts"`, `"Jacksonville Jaguars"`, `"Houston Texans"`, `"Kansas City Chiefs"`, `"Los Angeles Chargers"`, `"Las Vegas Raiders"`, `"Denver Broncos"`, `"Dallas Cowboys"`, `"Philadelphia Eagles"`, `"New York Giants"`, `"Washington Commanders"`, `"Chicago Bears"`, `"Minnesota Vikings"`, `"Green Bay Packers"`, `"Detroit Lions"`, `"Atlanta Falcons"`, `"New Orleans Saints"`, `"Carolina Panthers"`, `"Tampa Bay Buccaneers"`, `"Arizona Cardinals"`, `"Seattle Seahawks"`, `"San Francisco 49ers"`, `"Los Angeles Rams"`

#### DivisionEnum
**Valid Values:**
`"AFC East"`, `"AFC North"`, `"AFC South"`, `"AFC West"`, `"NFC East"`, `"NFC North"`, `"NFC South"`, `"NFC West"`

### Complex Filter Objects

#### SpreadFilter
```json
{
  "exact": ["3.0", "7.5"] | "3.0",           // Exact spread values
  "or_less": [3, 7] | 3,                     // X or less values (1-20)
  "or_more": [7, 10] | 7                     // X or more values (1-20)
}
```

#### TotalFilter
```json
{
  "exact": ["45 or more", "50 or less"] | "45 or more",  // Exact total strings
  "or_less": [45, 50] | 45,                              // X or less (30-60, steps of 5)
  "or_more": [35, 40] | 35                               // X or more (30-60, steps of 5)
}
```

#### SeasonFilter
```json
{
  "exact": ["since 2015-2016"] | "since 2015-2016",     // Exact season strings
  "since_or_later": "since 2012-2013",                   // This season and later
  "since_or_earlier": "since 2020-2021"                  // This season and earlier
}
```

#### SortField
```json
{
  "field": "win_percentage",     // Field name to sort by
  "order": "desc"               // "asc" or "desc" (default: "asc")
}
```

---

## Response Format

### Standard Paginated Response
```json
{
  "limit": 50,
  "offset": 0,
  "count": 25,
  "total_count": 1234,
  "results": [...]
}
```

**Response Fields:**
- **`limit`** (`integer`): Maximum results per page
- **`offset`** (`integer`): Starting position in result set
- **`count`** (`integer`): Number of results in current response
- **`total_count`** (`integer`): Total number of matching records
- **`results`** (`array`): Array of result objects

### Error Response
```json
{
  "detail": "Error message describing the issue"
}
```

---

## Trends Endpoints

### POST /trends
**Summary**: Retrieve historical trends with advanced filtering  
**URL**: `POST http://your-api-domain.com/api/v1/trends`

**Description**: Get historical betting trends from the main trends table with comprehensive filtering options.

#### Request Body (TrendFilter)

##### Pagination
- **`limit`** (`integer`, optional, default: `5000`)
  - **Description**: Maximum number of results to return
  - **Range**: 1-5000
  - **Example**: `100`

- **`offset`** (`integer`, optional, default: `0`)
  - **Description**: Number of results to skip
  - **Range**: ≥ 0
  - **Example**: `50`

##### Identification Filters
- **`trend_id`** (`string | string[]`, optional)
  - **Description**: Filter by trend ID(s) in comma-separated format
  - **Format**: `category,month,day_of_week,divisional,spread,total,seasons`
  - **Example**: `"home ats,October,Thursday,False,8 or less,40 or less,since 2008-2009"`
  - **Example Array**: `["home ats,October,Thursday,False,8 or less,40 or less,since 2008-2009"]`

##### Category Filters
- **`category`** (`string | string[]`, optional)
  - **Description**: Filter by betting category
  - **Valid Values**: See [CategoryEnum](#categoryenum)
  - **Example**: `"home ats"`
  - **Example Array**: `["home outright", "away outright"]`

##### Date/Time Filters
- **`month`** (`string | string[]`, optional)
  - **Description**: Filter by month(s) or null values
  - **Valid Values**: See [MonthEnum](#monthenum) or `"None"` for null values
  - **Example**: `"January"`
  - **Example Array**: `["January", "February"]`
  - **Example Array with None**: `["January", "February", "None"]`
  - **Example Null**: `"None"`

- **`start_month`** (`string`, optional)
  - **Description**: Starting month for range filtering
  - **Valid Values**: See [MonthEnum](#monthenum)
  - **Example**: `"January"`

- **`end_month`** (`string`, optional)
  - **Description**: Ending month for range filtering
  - **Valid Values**: See [MonthEnum](#monthenum)
  - **Example**: `"December"`

- **`day_of_week`** (`string | string[]`, optional)
  - **Description**: Filter by day(s) of week or null values
  - **Valid Values**: See [DayOfWeekEnum](#dayofweekenum) or `"None"` for null values
  - **Example**: `"Monday"`
  - **Example Array**: `["Monday", "Tuesday"]`
  - **Example Array with None**: `["Monday", "Tuesday", "None"]`
  - **Example Null**: `"None"`

##### Game Type Filters
- **`divisional`** (`boolean | "None"`, optional)
  - **Description**: Filter for divisional games
  - **Valid Values**: `true`, `false`, `"None"` (for null values)
  - **Example**: `true`

##### Betting Line Filters
- **`spread`** (`SpreadFilter | "None"`, optional)
  - **Description**: Filter by spread conditions or null values
  - **Type**: [SpreadFilter](#spreadfilter) object or `"None"` for null values
  - **Example Object**: `{"exact": "3.0"}`
  - **Example Complex**: `{"or_more": 6, "or_less": [10, 11, 12]}`
  - **Example Null**: `"None"`

- **`total`** (`TotalFilter | "None"`, optional)
  - **Description**: Filter by total points conditions or null values
  - **Type**: [TotalFilter](#totalfilter) object or `"None"` for null values
  - **Example Object**: `{"exact": "45 or more"}`
  - **Example Complex**: `{"or_less": 50, "or_more": [35, 40]}`
  - **Example Null**: `"None"`

##### Season Filters
- **`seasons`** (`SeasonFilter`, optional)
  - **Description**: Filter by season ranges
  - **Type**: [SeasonFilter](#seasonfilter) object
  - **Example**: `{"exact": "since 2015-2016"}`
  - **Example Range**: `{"since_or_later": "since 2012-2013"}`

##### Statistics Filters
- **`wins`** (`integer | integer[]`, optional)
  - **Description**: Exact win count(s)
  - **Range**: 1-5000
  - **Example**: `20`
  - **Example Array**: `[5, 10, 25]`

- **`min_wins`** (`integer`, optional)
  - **Description**: Minimum number of wins (inclusive)
  - **Range**: 1-5000
  - **Example**: `10`

- **`max_wins`** (`integer`, optional)
  - **Description**: Maximum number of wins (inclusive)
  - **Range**: 1-5000
  - **Example**: `100`

- **`losses`** (`integer | integer[]`, optional)
  - **Description**: Exact loss count(s)
  - **Range**: 1-5000
  - **Example**: `20`
  - **Example Array**: `[5, 10, 25]`

- **`min_losses`** (`integer`, optional)
  - **Description**: Minimum number of losses (inclusive)
  - **Range**: 1-5000
  - **Example**: `10`

- **`max_losses`** (`integer`, optional)
  - **Description**: Maximum number of losses (inclusive)
  - **Range**: 1-5000
  - **Example**: `100`

- **`pushes`** (`integer | integer[]`, optional)
  - **Description**: Exact push count(s)
  - **Range**: 1-5000
  - **Example**: `5`
  - **Example Array**: `[1, 2, 3]`

- **`min_pushes`** (`integer`, optional)
  - **Description**: Minimum number of pushes (inclusive)
  - **Range**: 1-5000
  - **Example**: `0`

- **`max_pushes`** (`integer`, optional)
  - **Description**: Maximum number of pushes (inclusive)
  - **Range**: 1-5000
  - **Example**: `10`

- **`total_games`** (`integer | integer[]`, optional)
  - **Description**: Exact total games count(s)
  - **Range**: 1-10000
  - **Example**: `50`
  - **Example Array**: `[25, 50, 100]`

- **`min_total_games`** (`integer`, optional)
  - **Description**: Minimum number of total games (inclusive)
  - **Range**: 1-10000
  - **Example**: `20`

- **`max_total_games`** (`integer`, optional)
  - **Description**: Maximum number of total games (inclusive)
  - **Range**: 1-10000
  - **Example**: `500`

- **`win_percentage`** (`number | number[]`, optional)
  - **Description**: Exact win percentage(s)
  - **Range**: 0-100
  - **Example**: `75.5`
  - **Example Array**: `[50.3, 62.12, 100]`

- **`min_win_percentage`** (`number`, optional)
  - **Description**: Minimum win percentage (inclusive)
  - **Range**: 0-100
  - **Example**: `60.0`

- **`max_win_percentage`** (`number`, optional)
  - **Description**: Maximum win percentage (inclusive)
  - **Range**: 0-100
  - **Example**: `90.0`

##### Sorting
- **`sort_by`** (`string | SortField | (string | SortField)[]`, optional)
  - **Description**: Sort results by field(s)
  - **Examples**:
    - Simple: `"win_percentage"`
    - Object: `{"field": "win_percentage", "order": "desc"}`
    - Array: `["wins", "total_games"]`
    - Complex: `[{"field": "win_percentage", "order": "desc"}, {"field": "total_games", "order": "asc"}]`

#### Response

**Success Response (200)**:
```json
{
  "limit": 50,
  "offset": 0,
  "count": 25,
  "total_count": 1234,
  "results": [
    {
      "id": "abc123...",
      "id_string": "home ats,October,Thursday,False,8 or less,40 or less,since 2008-2009",
      "category": "home ats",
      "month": "October",
      "day_of_week": "Thursday",
      "divisional": false,
      "spread": "8 or less",
      "total": "40 or less",
      "seasons": "since 2008-2009",
      "wins": 15,
      "losses": 12,
      "pushes": 1,
      "total_games": 28,
      "win_percentage": 53.571,
      "trend_string": "Home teams against the spread on Thursdays in October Thursday when the spread is 8 or less and total is 40 or less since 2008-2009."
    }
  ]
}
```

**Error Responses**:
- **422**: Validation error (invalid enum values, out of range numbers)
- **500**: Database connection or query error

---

## Weekly Trends Endpoints

### POST /weekly-trends
**Summary**: Retrieve trends applicable to current week's games  
**URL**: `POST http://your-api-domain.com/api/v1/weekly-trends`

**Description**: Get betting trends filtered for the current week's games with game-specific context.

#### Request Body (WeeklyTrendFilter)

Includes all filters from [TrendFilter](#trends-endpoints) plus:

##### Games Applicable Filter
- **`games_applicable`** (`GamesApplicableFilter`, optional)
  - **Description**: Filter trends by applicable games
  - **Structure**:
    ```json
    {
      "games": "PHIvsDAL" | ["PHIvsDAL", "CLEvsCIN"],
      "match_mode": "contains_all" | "contains_any" | "exact" | "excludes_any"
    }
    ```
  - **Game Format**: `{HomeAbbrev}vs{AwayAbbrev}` (e.g., `"PHIvsDAL"`, `"CLEvsCIN"`)
  - **Match Modes**:
    - `"contains_all"` (default): Match if all specified games are in trend's games list
    - `"contains_any"`: Match if any specified games are in trend's games list
    - `"exact"`: Exact match of entire games list
    - `"excludes_any"`: Match trends that do NOT contain any of the specified games
  - **Examples**:
    - Single game: `{"games": "PHIvsDAL", "match_mode": "contains_all"}`
    - Multiple games: `{"games": ["PHIvsDAL", "CLEvsCIN"], "match_mode": "contains_any"}`
    - Exclusion: `{"games": ["PHIvsDAL"], "match_mode": "excludes_any"}`

#### Response

**Success Response (200)**:
```json
{
  "limit": 50,
  "offset": 0,
  "count": 25,
  "total_count": 1234,
  "results": [
    {
      "id": "def456...",
      "id_string": "home ats,October,Thursday,False,8 or less,40 or less,since 2008-2009",
      "category": "home ats",
      "month": "October",
      "day_of_week": "Thursday",
      "divisional": false,
      "spread": "8 or less",
      "total": "40 or less",
      "seasons": "since 2008-2009",
      "wins": 15,
      "losses": 12,
      "pushes": 1,
      "total_games": 28,
      "win_percentage": 53.571,
      "trend_string": "Home teams against the spread on Thursdays in October Thursday when the spread is 8 or less and total is 40 or less since 2008-2009.",
      "games_applicable": "PHIvsDAL, CLEvsCIN, NYGvsWAS"
    }
  ]
}
```

### GET /weekly-filter-options
**Summary**: Get available filter options for weekly trends  
**URL**: `GET http://your-api-domain.com/api/v1/weekly-filter-options`

**Description**: Returns distinct values available in the weekly trends table for dynamic filter generation.

#### Request Parameters
None

#### Response

**Success Response (200)**:
```json
{
  "categories": [
    "home outright",
    "away outright",
    "favorite outright",
    "underdog outright",
    "home ats",
    "away ats",
    "over",
    "under"
  ],
  "months": [
    "September",
    "October",
    "November",
    "December",
    "January"
  ],
  "day_of_weeks": [
    "Sunday",
    "Monday",
    "Thursday"
  ],
  "divisionals": [
    true,
    false
  ],
  "spreads": [
    "1.0",
    "2.5",
    "3.0",
    "3 or less",
    "7 or more",
    "10 or more"
  ],
  "totals": [
    "35 or less",
    "40 or less",
    "45 or more",
    "50 or more"
  ],
  "seasons": [
    "since 2015-2016",
    "since 2020-2021"
  ]
}
```

---

## Game Trends Endpoints

### POST /{table_name}
**Summary**: Retrieve trends for specific game  
**URL**: `POST http://your-api-domain.com/api/v1/game-trends/{table_name}`  
**Example URL**: `POST http://your-api-domain.com/api/v1/game-trends/phidal20250904`

**Description**: Get trends applicable to a specific upcoming game from dynamically created game trend tables.

#### Path Parameters
- **`table_name`** (`string`, required)
  - **Description**: Name of the game trend table
  - **Format**: `{home_abbrev}{away_abbrev}{YYYYMMDD}`
  - **Pattern**: `^[a-z]{2,3}[a-z]{2,3}\d{8}$`
  - **Examples**: `"phidal20250904"`, `"bufmia20250915"`

#### Request Body (TrendFilter)
Uses the same [TrendFilter](#trends-endpoints) structure as the main trends endpoint.

#### Response

**Success Response (200)**:
Uses the same response format as trends endpoint but for game-specific data.

**Error Responses**:
- **400**: Invalid table name format
- **404**: Table not found
- **422**: Validation error
- **500**: Database error

### GET /
**Summary**: List available game trend tables  
**URL**: `GET http://your-api-domain.com/api/v1/game-trends/`

**Description**: Returns list of all available game trend tables (dynamically created for upcoming games).

#### Request Parameters
None

#### Response

**Success Response (200)**:
```json
{
  "available_tables": [
    "phidal20250904",
    "bufmia20250915",
    "kclac20250916",
    "nygwas20250917"
  ],
  "total_count": 4
}
```

### GET /{table_name}/filter-options
**Summary**: Get filter options for specific game  
**URL**: `GET http://your-api-domain.com/api/v1/game-trends/{table_name}/filter-options`  
**Example URL**: `GET http://your-api-domain.com/api/v1/game-trends/phidal20250904/filter-options`

**Description**: Returns available filter values for the specified game trend table.

#### Path Parameters
- **`table_name`** (`string`, required)
  - **Description**: Name of the game trend table
  - **Format**: Same as POST endpoint

#### Response

**Success Response (200)**:
```json
{
  "categories": [
    "home ats",
    "away ats",
    "over",
    "under"
  ],
  "months": [
    "September",
    "October"
  ],
  "day_of_weeks": [
    "Sunday",
    "Monday"
  ],
  "divisionals": [
    true,
    false
  ],
  "spreads": [
    "3.0",
    "7.5",
    "3 or less"
  ],
  "totals": [
    "45 or more",
    "50 or less"
  ],
  "seasons": [
    "since 2020-2021"
  ]
}
```

---

## Games Endpoints

### POST /games
**Summary**: Retrieve historical games with filtering  
**URL**: `POST http://your-api-domain.com/api/v1/games`

**Description**: Get completed NFL games with comprehensive filtering options for historical analysis.

#### Request Body (GameFilter)

##### Pagination
- **`limit`** (`integer`, optional, default: `5000`)
  - **Range**: 1-5000
- **`offset`** (`integer`, optional, default: `0`)
  - **Range**: ≥ 0

##### Game Identification
- **`game_id`** (`string | string[]`, optional)
  - **Description**: Filter by game ID(s)
  - **Format**: `{home_abbrev}{away_abbrev}{YYYYMMDD}`
  - **Case**: Case-insensitive
  - **Example**: `"NYJNE20240910"`
  - **Example Array**: `["NYJNE20240910", "BUFMIA20240911"]`

##### Date Filters
- **`date`** (`string | string[]`, optional)
  - **Description**: Filter by specific date(s)
  - **Format**: `YYYY-MM-DD`
  - **Example**: `"2024-09-10"`
  - **Example Array**: `["2024-09-10", "2024-09-11"]`

- **`start_date`** (`string`, optional)
  - **Description**: Start date for range filtering
  - **Format**: `YYYY-MM-DD`
  - **Example**: `"2020-11-21"`

- **`end_date`** (`string`, optional)
  - **Description**: End date for range filtering
  - **Format**: `YYYY-MM-DD`
  - **Example**: `"2020-12-21"`

- **`month`** (`string | string[]`, optional)
  - **Valid Values**: See [MonthEnum](#monthenum)
  - **Example**: `"January"`
  - **Example Array**: `["January", "February"]`

- **`start_month`** / **`end_month`** (`string`, optional)
  - **Valid Values**: See [MonthEnum](#monthenum)

- **`day`** (`integer | integer[]`, optional)
  - **Description**: Day(s) of the month
  - **Range**: 1-31
  - **Example**: `15`
  - **Example Array**: `[1, 15, 31]`

- **`start_day`** / **`end_day`** (`integer`, optional)
  - **Range**: 1-31

- **`year`** (`integer | integer[]`, optional)
  - **Range**: 2006-2025
  - **Example**: `2024`
  - **Example Array**: `[2020, 2021, 2022]`

- **`start_year`** / **`end_year`** (`integer`, optional)
  - **Range**: 2006-2025

- **`season`** (`string | string[]`, optional)
  - **Format**: `YYYY-YYYY`
  - **Range**: `2006-2007` to `2024-2025`
  - **Example**: `"2022-2023"`
  - **Example Array**: `["2020-2021", "2021-2022"]`

- **`start_season`** / **`end_season`** (`string`, optional)
  - **Format**: `YYYY-YYYY`

- **`day_of_week`** (`string | string[]`, optional)
  - **Valid Values**: See [DayOfWeekEnum](#dayofweekenum)
  - **Example**: `"Monday"`
  - **Example Array**: `["Monday", "Tuesday"]`

##### Team Filters
- **`home_team`** / **`away_team`** (`string | string[]`, optional)
  - **Valid Values**: See [FullTeamNameEnum](#fullteamnameenum)
  - **Example**: `"New York Jets"`
  - **Example Array**: `["New York Jets", "New England Patriots"]`

- **`home_abbreviation`** / **`away_abbreviation`** (`string | string[]`, optional)
  - **Valid Values**: See [TeamAbbreviationEnum](#teamabbreviationenum)
  - **Example**: `"NYJ"`
  - **Example Array**: `["NYJ", "NE"]`

- **`home_division`** / **`away_division`** (`string | string[]`, optional)
  - **Valid Values**: See [DivisionEnum](#divisionenum)
  - **Example**: `"AFC East"`
  - **Example Array**: `["AFC East", "NFC North"]`

- **`divisional`** (`boolean`, optional)
  - **Description**: Filter for divisional matchups
  - **Example**: `true`

##### Score Filters
- **`home_score`** (`integer | integer[]`, optional)
  - **Range**: 0-100
  - **Example**: `24`
  - **Example Array**: `[21, 24, 30]`

- **`min_home_score`** / **`max_home_score`** (`integer`, optional)
  - **Range**: 0-100

- **`away_score`** (`integer | integer[]`, optional)
  - **Range**: 0-100
  - **Example**: `24`
  - **Example Array**: `[21, 24, 30]`

- **`min_away_score`** / **`max_away_score`** (`integer`, optional)
  - **Range**: 0-100

- **`combined_score`** (`integer | integer[]`, optional)
  - **Range**: 0-200
  - **Example**: `48`
  - **Example Array**: `[45, 48, 50]`

- **`min_combined_score`** / **`max_combined_score`** (`integer`, optional)
  - **Range**: 0-200

- **`tie`** (`boolean`, optional)
  - **Description**: Filter for tie games
  - **Example**: `false`

- **`winner`** (`string | string[]`, optional)
  - **Valid Values**: See [FullTeamNameEnum](#fullteamnameenum)
  - **Example**: `"New York Jets"`

##### Sorting
- **`sort_by`** - Same as trends endpoints

#### Response

**Success Response (200)**:
```json
{
  "limit": 50,
  "offset": 0,
  "count": 25,
  "total_count": 1234,
  "results": [
    {
      "id": "ghi789...",
      "id_string": "NYJNE20240910",
      "date": "2024-09-10",
      "month": "September",
      "day": 10,
      "year": 2024,
      "season": "2024-2025",
      "day_of_week": "Tuesday",
      "home_team": "New York Jets",
      "home_abbreviation": "NYJ",
      "home_division": "AFC East",
      "away_team": "New England Patriots",
      "away_abbreviation": "NE",
      "away_division": "AFC East",
      "divisional": true,
      "home_score": 24,
      "away_score": 17,
      "combined_score": 41,
      "tie": false,
      "winner": "New York Jets",
      "loser": "New England Patriots",
      "spread": 3.0,
      "home_spread": -3.0,
      "home_spread_result": 7,
      "away_spread": 3.0,
      "away_spread_result": -7,
      "spread_push": false,
      "pk": false,
      "total": 47.5,
      "total_push": false,
      "home_favorite": true,
      "away_underdog": true,
      "away_favorite": false,
      "home_underdog": false,
      "home_win": true,
      "away_win": false,
      "favorite_win": true,
      "underdog_win": false,
      "home_favorite_win": true,
      "away_underdog_win": false,
      "away_favorite_win": false,
      "home_underdog_win": false,
      "home_cover": true,
      "away_cover": false,
      "favorite_cover": true,
      "underdog_cover": false,
      "home_favorite_cover": true,
      "away_underdog_cover": false,
      "away_favorite_cover": false,
      "home_underdog_cover": false,
      "over_hit": false,
      "under_hit": true
    }
  ]
}
```

---

## Upcoming Games Endpoints

### GET /upcoming-games
**Summary**: Retrieve all upcoming games  
**URL**: `GET http://your-api-domain.com/api/v1/upcoming-games`

**Description**: Get all games from the current week with betting lines and odds information.

#### Request Parameters
None

#### Response

**Success Response (200)**:
```json
{
  "upcoming_games": [
    {
      "id": "jkl012...",
      "id_string": "PHIDAL20250904",
      "date": "2025-09-04",
      "month": "September",
      "day": 4,
      "year": 2025,
      "season": "2025-2026",
      "day_of_week": "Thursday",
      "home_team": "Philadelphia Eagles",
      "home_abbreviation": "PHI",
      "home_division": "NFC East",
      "away_team": "Dallas Cowboys",
      "away_abbreviation": "DAL",
      "away_division": "NFC East",
      "divisional": true,
      "spread": 3.5,
      "home_spread": -3.5,
      "home_spread_odds": -110,
      "away_spread": 3.5,
      "away_spread_odds": -110,
      "home_moneyline_odds": -175,
      "away_moneyline_odds": 145,
      "total": 47.5,
      "over": 47.5,
      "over_odds": -110,
      "under": 47.5,
      "under_odds": -110
    }
  ],
  "total_count": 16
}
```

---

## Error Handling

### HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters, malformed data)
- **404**: Not Found (table doesn't exist, endpoint not found)
- **422**: Unprocessable Entity (validation errors)
- **500**: Internal Server Error (database errors, unexpected errors)

### Common Error Scenarios

#### 400 Bad Request
```json
{
  "detail": "Invalid table name format. Expected format: {home_team}{away_team}{date}"
}
```

#### 404 Not Found
```json
{
  "detail": "Table 'phidal20250904' not found"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "limit"],
      "msg": "ensure this value is less than or equal to 5000",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 5000}
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "An error occurred while retrieving data: Database connection failed"
}
```

### Validation Rules Summary

- **Numbers**: All numeric filters have range restrictions as specified
- **Enums**: String values must match exact enum values (case-sensitive)
- **Dates**: Must follow YYYY-MM-DD format
- **Game IDs**: Must follow team abbreviation + date format
- **Table Names**: Must follow {home}{away}{YYYYMMDD} pattern
- **Seasons**: Must follow YYYY-YYYY format within valid range
- **Arrays**: Can be provided as arrays or comma-separated strings where noted

---

## Usage Examples

### Get High Win Percentage Trends
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "min_win_percentage": 65.0,
    "min_total_games": 20,
    "sort_by": [
      {"field": "win_percentage", "order": "desc"},
      {"field": "total_games", "order": "desc"}
    ],
    "limit": 10
  }'
```

### Get This Week's Home ATS Trends
```bash
curl -X POST "http://your-api-domain.com/api/v1/weekly-trends" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "home ats",
    "games_applicable": {
      "games": ["PHIvsDAL", "BUFvsMIA"],
      "match_mode": "contains_any"
    },
    "min_total_games": 10
  }'
```

### Get October Monday Games
```bash
curl -X POST "http://your-api-domain.com/api/v1/games" \
  -H "Content-Type: application/json" \
  -d '{
    "month": "October",
    "day_of_week": "Monday",
    "start_year": 2020,
    "end_year": 2024
  }'
```

### Get Available Game Trend Tables
```bash
curl -X GET "http://your-api-domain.com/api/v1/game-trends/" \
  -H "Content-Type: application/json"
```

### Get Filter Options for Specific Game
```bash
curl -X GET "http://your-api-domain.com/api/v1/game-trends/phidal20250904/filter-options" \
  -H "Content-Type: application/json"
```

### Get All Upcoming Games
```bash
curl -X GET "http://your-api-domain.com/api/v1/upcoming-games" \
  -H "Content-Type: application/json"
```

### Get Trends for Specific Game (Eagles vs Cowboys)
```bash
curl -X POST "http://your-api-domain.com/api/v1/game-trends/phidal20250904" \
  -H "Content-Type: application/json" \
  -d '{
    "category": ["home ats", "away ats"],
    "min_win_percentage": 55.0,
    "min_total_games": 15,
    "sort_by": {"field": "win_percentage", "order": "desc"}
  }'
```

### Filter Trends by Multiple Months Including None Values
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "month": ["September", "October", "None"],
    "category": "home ats",
    "min_total_games": 25,
    "limit": 20
  }'
```

### Get Weekly Filter Options
```bash
curl -X GET "http://your-api-domain.com/api/v1/weekly-filter-options" \
  -H "Content-Type: application/json"
```

### Complex Spread and Total Filtering
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "spread": {
      "or_less": [3, 7],
      "exact": ["10.5"]
    },
    "total": {
      "or_more": [45, 50],
      "exact": ["35 or less"]
    },
    "category": "favorite ats",
    "divisional": false
  }'
```

### Get Trends for Multiple Teams
```bash
curl -X POST "http://your-api-domain.com/api/v1/games" \
  -H "Content-Type: application/json" \
  -d '{
    "home_abbreviation": ["PHI", "DAL", "NYG", "WAS"],
    "divisional": true,
    "min_combined_score": 35,
    "season": ["2023-2024", "2024-2025"],
    "sort_by": [
      {"field": "date", "order": "desc"},
      {"field": "combined_score", "order": "desc"}
    ]
  }'
```

### Get Over/Under Trends for High-Scoring Games
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "category": ["over", "under"],
    "total": {
      "or_more": [50, 55]
    },
    "seasons": {
      "since_or_later": "since 2020-2021"
    },
    "min_win_percentage": 60.0,
    "sort_by": {"field": "win_percentage", "order": "desc"}
  }'
```

### Filter Games by Score Range
```bash
curl -X POST "http://your-api-domain.com/api/v1/games" \
  -H "Content-Type: application/json" \
  -d '{
    "min_combined_score": 45,
    "max_combined_score": 55,
    "divisional": false,
    "day_of_week": ["Sunday", "Monday"],
    "start_date": "2023-09-01",
    "end_date": "2024-02-15"
  }'
```

### Get Weekly Trends for Specific Games with Exclusion
```bash
curl -X POST "http://your-api-domain.com/api/v1/weekly-trends" \
  -H "Content-Type: application/json" \
  -d '{
    "games_applicable": {
      "games": ["NYJvsNE", "MIAvsBUF"],
      "match_mode": "excludes_any"
    },
    "category": "underdog ats",
    "divisional": true,
    "min_total_games": 20
  }'
```

### Get Trends with Complex Season Filtering
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "seasons": {
      "since_or_earlier": "since 2018-2019",
      "exact": ["since 2015-2016", "since 2010-2011"]
    },
    "day_of_week": ["Thursday", "Monday"],
    "spread": {
      "or_more": [7, 10, 14]
    },
    "min_wins": 15,
    "max_losses": 10
  }'
```

### Get Playoff Season Games (January/February)
```bash
curl -X POST "http://your-api-domain.com/api/v1/games" \
  -H "Content-Type: application/json" \
  -d '{
    "month": ["January", "February"],
    "start_year": 2020,
    "min_combined_score": 40,
    "sort_by": [
      {"field": "year", "order": "desc"},
      {"field": "combined_score", "order": "desc"}
    ],
    "limit": 50
  }'
```

### Get Prime Time Game Trends (Monday/Thursday)
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": ["Monday", "Thursday"],
    "category": ["home favorite ats", "away underdog ats"],
    "total": {
      "or_less": [42, 45]
    },
    "min_total_games": 30,
    "sort_by": [
      {"field": "day_of_week", "order": "asc"},
      {"field": "win_percentage", "order": "desc"}
    ]
  }'
```

### Search for Specific Trend by ID
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "trend_id": "home ats,October,Sunday,False,3 or less,45 or more,since 2015-2016"
  }'
```

### Get High-Volume Trends with Pagination
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "min_total_games": 100,
    "min_win_percentage": 55.0,
    "limit": 25,
    "offset": 50,
    "sort_by": [
      {"field": "total_games", "order": "desc"},
      {"field": "win_percentage", "order": "desc"}
    ]
  }'
```

### Get Division Rivalry Games
```bash
curl -X POST "http://your-api-domain.com/api/v1/games" \
  -H "Content-Type: application/json" \
  -d '{
    "divisional": true,
    "home_division": ["AFC East", "NFC East"],
    "season": "2024-2025",
    "sort_by": {"field": "date", "order": "desc"}
  }'
```

### Find Trends with Null Values
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "month": "None",
    "spread": "None",
    "category": "over",
    "min_total_games": 50
  }'
```

### Get Trends by Exact Win/Loss Records
```bash
curl -X POST "http://your-api-domain.com/api/v1/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "wins": [15, 20, 25],
    "losses": [8, 10, 12],
    "pushes": [1, 2],
    "category": ["home ats", "away ats"],
    "sort_by": {"field": "wins", "order": "desc"}
  }'
```

This comprehensive documentation covers all endpoints, their inputs, restrictions, and expected outputs. The API provides extensive filtering capabilities for analyzing NFL betting trends and game data.
