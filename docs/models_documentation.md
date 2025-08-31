# NFL Trends API Database Models Documentation

This document provides comprehensive documentation for the SQLAlchemy database models used by the NFL Trends FastAPI application. These models define the structure and relationships of data retrieved from the PostgreSQL database.

## Overview

The API uses SQLAlchemy ORM models to interact with the database, providing type-safe access to NFL game data, trends, and betting information. All models use enum types for consistent data validation and improved query performance.

---

## Database Models

### 1. Game Model

**File**: `app/models/game.py`  
**Table**: `games`  
**Purpose**: Represents completed NFL games with final scores, outcomes, and calculated betting results.

#### Schema Definition

```python
from sqlalchemy import Column, Integer, String, Enum, Boolean, Numeric
from app.enums.game_enums import MonthEnum, DayOfWeekEnum, FullTeamNameEnum, TeamAbbreviationEnum, DivisionEnum

class Game(Base):
    __tablename__ = 'games'
```

#### Attributes

##### Primary Identification
- **`id`** (`String`, Primary Key): Unique SHA-256 hash identifier
- **`id_string`** (`String`, Required): Human-readable game identifier (e.g., "BUFMIA20240915")

##### Game Information
- **`date`** (`String`, Required): Game date in YYYY-MM-DD format
- **`month`** (`MonthEnum`, Required): Month of the game (January-December)
- **`day`** (`Integer`, Required): Day of the month (1-31)
- **`year`** (`Integer`, Required): Four-digit year
- **`season`** (`String`, Required): Season identifier (e.g., "2024-2025")
- **`day_of_week`** (`DayOfWeekEnum`, Required): Day name (Monday-Sunday)

##### Team Information
- **`home_team`** (`FullTeamNameEnum`, Required): Full home team name
- **`home_abbreviation`** (`TeamAbbreviationEnum`, Required): Three-letter home team code
- **`home_division`** (`DivisionEnum`, Required): Home team's division
- **`away_team`** (`FullTeamNameEnum`, Required): Full away team name
- **`away_abbreviation`** (`TeamAbbreviationEnum`, Required): Three-letter away team code
- **`away_division`** (`DivisionEnum`, Required): Away team's division
- **`divisional`** (`Boolean`, Required): True if teams are in same division

##### Score Information
- **`home_score`** (`Integer`, Required): Final home team score
- **`away_score`** (`Integer`, Required): Final away team score
- **`combined_score`** (`Integer`, Required): Total points scored
- **`tie`** (`Boolean`, Required): True if game ended in tie
- **`winner`** (`FullTeamNameEnum`, Required): Winning team name
- **`loser`** (`FullTeamNameEnum`, Required): Losing team name

##### Betting Information
- **`spread`** (`Numeric(4,1)`, Required): Absolute spread value
- **`home_spread`** (`Numeric(4,1)`, Required): Home team spread (negative if favored)
- **`home_spread_result`** (`Integer`, Required): Actual margin (away_score - home_score)
- **`away_spread`** (`Numeric(4,1)`, Required): Away team spread (negative if favored)
- **`away_spread_result`** (`Integer`, Required): Actual margin (home_score - away_score)
- **`spread_push`** (`Boolean`, Required): True if spread was exact
- **`pk`** (`Boolean`, Required): True if spread was zero (pick'em)
- **`total`** (`Numeric(4,1)`, Required): Over/under betting total
- **`total_push`** (`Boolean`, Required): True if total was exact

##### Team Roles
- **`home_favorite`** (`Boolean`, Required): True if home team was favored
- **`away_underdog`** (`Boolean`, Required): True if away team was underdog
- **`away_favorite`** (`Boolean`, Required): True if away team was favored
- **`home_underdog`** (`Boolean`, Required): True if home team was underdog

##### Win Results
- **`home_win`** (`Boolean`, Required): True if home team won outright
- **`away_win`** (`Boolean`, Required): True if away team won outright
- **`favorite_win`** (`Boolean`, Required): True if favorite won outright
- **`underdog_win`** (`Boolean`, Required): True if underdog won outright
- **`home_favorite_win`** (`Boolean`, Required): True if home favorite won
- **`away_underdog_win`** (`Boolean`, Required): True if away underdog won
- **`away_favorite_win`** (`Boolean`, Required): True if away favorite won
- **`home_underdog_win`** (`Boolean`, Required): True if home underdog won

##### Cover Results (Against the Spread)
- **`home_cover`** (`Boolean`, Required): True if home team covered spread
- **`away_cover`** (`Boolean`, Required): True if away team covered spread
- **`favorite_cover`** (`Boolean`, Required): True if favorite covered spread
- **`underdog_cover`** (`Boolean`, Required): True if underdog covered spread
- **`home_favorite_cover`** (`Boolean`, Required): True if home favorite covered
- **`away_underdog_cover`** (`Boolean`, Required): True if away underdog covered
- **`away_favorite_cover`** (`Boolean`, Required): True if away favorite covered
- **`home_underdog_cover`** (`Boolean`, Required): True if home underdog covered

##### Total Results
- **`over_hit`** (`Boolean`, Required): True if total score exceeded betting line
- **`under_hit`** (`Boolean`, Required): True if total score was below betting line

#### API Usage
- **GET /games**: Retrieve paginated list of completed games
- **GET /games/{game_id}**: Retrieve specific game details
- Used for historical analysis and trend validation

---

### 2. UpcomingGame Model

**File**: `app/models/upcoming_game.py`  
**Table**: `upcoming_games`  
**Purpose**: Represents future NFL games with current betting lines, odds, and predictions.

#### Schema Definition

```python
class UpcomingGame(Base):
    __tablename__ = 'upcoming_games'
```

#### Attributes

##### Primary Identification
- **`id`** (`String`, Primary Key): Unique SHA-256 hash identifier
- **`id_string`** (`String`, Required): Human-readable game identifier

##### Game Information
- **`date`** (`String`, Required): Scheduled game date
- **`month`** (`MonthEnum`, Required): Month of the game
- **`day`** (`Integer`, Required): Day of the month
- **`year`** (`Integer`, Required): Four-digit year
- **`season`** (`String`, Required): Season identifier
- **`day_of_week`** (`DayOfWeekEnum`, Required): Day name

##### Team Information
- **`home_team`** (`FullTeamNameEnum`, Required): Full home team name
- **`home_abbreviation`** (`TeamAbbreviationEnum`, Required): Home team code
- **`home_division`** (`DivisionEnum`, Required): Home team's division
- **`away_team`** (`FullTeamNameEnum`, Required): Full away team name
- **`away_abbreviation`** (`TeamAbbreviationEnum`, Required): Away team code
- **`away_division`** (`DivisionEnum`, Required): Away team's division
- **`divisional`** (`Boolean`, Required): True if same division matchup

##### Spread Information
- **`spread`** (`Numeric(4,1)`, Required): Absolute spread value
- **`home_spread`** (`Numeric(4,1)`, Required): Home team spread
- **`home_spread_odds`** (`Integer`, Required): Odds for home spread bet
- **`away_spread`** (`Numeric(4,1)`, Required): Away team spread
- **`away_spread_odds`** (`Integer`, Required): Odds for away spread bet

##### Moneyline Information
- **`home_moneyline_odds`** (`Integer`, Required): Odds for home team to win outright
- **`away_moneyline_odds`** (`Integer`, Required): Odds for away team to win outright

##### Total Information
- **`total`** (`Numeric(4,1)`, Required): Over/under betting total
- **`over`** (`Numeric(4,1)`, Required): Over value (same as total)
- **`over_odds`** (`Integer`, Required): Odds for over bet
- **`under`** (`Numeric(4,1)`, Required): Under value (same as total)
- **`under_odds`** (`Integer`, Required): Odds for under bet

#### API Usage
- **GET /upcoming-games**: Retrieve all upcoming games for the week
- **GET /upcoming-games/{game_id}**: Retrieve specific upcoming game
- Used for displaying current week's games and betting information

---

### 3. Trend Model

**File**: `app/models/trend.py`  
**Table**: `trends`  
**Purpose**: Represents historical betting trends with accumulated statistics across all NFL history.

#### Schema Definition

```python
class Trend(Base):
    __tablename__ = 'trends'
```

#### Attributes

##### Primary Identification
- **`id`** (`String`, Primary Key): Unique SHA-256 hash of trend parameters
- **`id_string`** (`String`, Required): Comma-separated trend components

##### Trend Parameters
- **`category`** (`String`, Required): Trend type (e.g., 'home ats', 'favorite outright')
- **`month`** (`MonthEnum`, Required): Month filter (or None for all months)
- **`day_of_week`** (`DayOfWeekEnum`, Required): Day filter (or None for all days)
- **`divisional`** (`Boolean`, Required): Divisional game filter (True/False/None)
- **`spread`** (`String`, Required): Spread condition (e.g., '3.5', '7 or more')
- **`total`** (`String`, Required): Total condition (e.g., '45', '50 or less')
- **`seasons`** (`String`, Required): Season range (e.g., 'since 2020-2021')

##### Statistics
- **`wins`** (`Integer`, Required): Number of successful outcomes
- **`losses`** (`Integer`, Required): Number of unsuccessful outcomes
- **`pushes`** (`Integer`, Required): Number of tie/push outcomes
- **`total_games`** (`Integer`, Required): Total games analyzed
- **`win_percentage`** (`Numeric(4,3)`, Required): Win percentage (0.000-100.000)

##### Display
- **`trend_string`** (`String`, Required): Human-readable trend description

#### API Usage
- **GET /trends**: Retrieve paginated historical trends with filtering
- **GET /trends/{trend_id}**: Retrieve specific trend details
- Used for all-time trend analysis and historical pattern discovery

---

### 4. WeeklyTrend Model

**File**: `app/models/weekly_trend.py`  
**Table**: `weekly_trends`  
**Purpose**: Represents trends applicable to the current week's games with game-specific context.

#### Schema Definition

```python
class WeeklyTrend(Base):
    __tablename__ = 'weekly_trends'
```

#### Attributes

##### Primary Identification
- **`id`** (`String`, Primary Key): Unique trend identifier
- **`id_string`** (`String`, Required): Comma-separated trend components

##### Trend Parameters
- **`category`** (`String`, Required): Trend type
- **`month`** (`MonthEnum`, Required): Month filter
- **`day_of_week`** (`DayOfWeekEnum`, Required): Day filter
- **`divisional`** (`Boolean`, Required): Divisional game filter
- **`spread`** (`String`, Required): Spread condition
- **`total`** (`String`, Required): Total condition
- **`seasons`** (`String`, Required): Season range

##### Statistics
- **`wins`** (`Integer`, Required): Number of successful outcomes
- **`losses`** (`Integer`, Required): Number of unsuccessful outcomes
- **`pushes`** (`Integer`, Required): Number of tie/push outcomes
- **`total_games`** (`Integer`, Required): Total games analyzed
- **`win_percentage`** (`Numeric(4,3)`, Required): Win percentage

##### Display and Context
- **`trend_string`** (`String`, Required): Human-readable description
- **`games_applicable`** (`String`, Required): Comma-separated list of game IDs that match this trend

#### API Usage
- **GET /weekly-trends**: Retrieve trends for current week's games
- **GET /weekly-trends/filter-options**: Get dynamic filter options for weekly view
- Used for "This Week" filtering and game-specific trend analysis

---

### 5. GameTrend Model (Dynamic)

**File**: `app/models/game_trend.py`  
**Purpose**: Factory function that creates individual trend models for specific games.

#### Dynamic Model Creation

```python
def create_game_trend_model(table_name: str):
    """
    Factory function to create a GameTrend model for a specific table.
    
    Args:
        table_name: The name of the table (e.g., 'phidal20250904')
    
    Returns:
        A GameTrend class configured for the specified table
    """
```

#### Schema Definition

Each dynamic GameTrend model has the following structure:

##### Primary Identification
- **`id`** (`String`, Primary Key): Unique trend identifier
- **`id_string`** (`String`, Required): Trend components string

##### Trend Parameters (Nullable for Flexibility)
- **`category`** (`String`, Required): Trend type
- **`month`** (`MonthEnum`, Nullable): Month filter
- **`day_of_week`** (`DayOfWeekEnum`, Nullable): Day filter
- **`divisional`** (`Boolean`, Nullable): Divisional filter
- **`spread`** (`String`, Nullable): Spread condition
- **`total`** (`String`, Nullable): Total condition
- **`seasons`** (`String`, Required): Season range

##### Statistics
- **`wins`** (`Integer`, Required): Number of wins
- **`losses`** (`Integer`, Required): Number of losses
- **`pushes`** (`Integer`, Required): Number of pushes
- **`total_games`** (`Integer`, Required): Total games
- **`win_percentage`** (`Numeric(4,3)`, Required): Win percentage

##### Display
- **`trend_string`** (`String`, Required): Human-readable description

#### Dynamic Table Naming

Tables are named using the format: `{home_abbrev}{away_abbrev}{YYYYMMDD}`

**Examples**:
- `phidal20250904` (Philadelphia Eagles vs Dallas Cowboys on 2025-09-04)
- `bufmia20250915` (Buffalo Bills vs Miami Dolphins on 2025-09-15)

#### API Usage
- **GET /game-trends/{game_id}**: Retrieve all trends for a specific game
- **GET /game-trends/{game_id}/filter-options**: Get filter options for specific game
- Used for individual game analysis and game-specific trend filtering

---

## Enum Types

All models use enum types for data validation and consistency:

### MonthEnum
Valid values: `January`, `February`, `March`, `April`, `May`, `June`, `July`, `August`, `September`, `October`, `November`, `December`

### DayOfWeekEnum  
Valid values: `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, `Sunday`

### FullTeamNameEnum
Full NFL team names (e.g., `Buffalo Bills`, `Miami Dolphins`)

### TeamAbbreviationEnum
Three-letter team codes (e.g., `BUF`, `MIA`, `PHI`, `DAL`)

### DivisionEnum
NFL divisions: `AFC East`, `AFC North`, `AFC South`, `AFC West`, `NFC East`, `NFC North`, `NFC South`, `NFC West`

---

## Database Relationships and Data Flow

### 1. Historical Data Pipeline
```
games table → trends table → weekly_trends table
```

1. **Completed Games**: Stored in `games` table with final outcomes
2. **Trend Calculation**: Historical trends calculated from all games
3. **Weekly Filtering**: Applicable trends filtered for current week

### 2. Upcoming Games Pipeline
```
upcoming_games table → individual game tables → game-specific analysis
```

1. **Weekly Updates**: `upcoming_games` refreshed with current betting lines
2. **Game Tables**: Individual tables created for each upcoming game
3. **Trend Matching**: Applicable historical trends populated per game

### 3. API Data Sources

| Endpoint Pattern | Primary Model | Secondary Models | Use Case |
|------------------|---------------|------------------|----------|
| `/trends` | `Trend` | - | Historical analysis |
| `/weekly-trends` | `WeeklyTrend` | `UpcomingGame` | Current week analysis |
| `/game-trends/{id}` | `GameTrend` (dynamic) | `UpcomingGame` | Individual game analysis |
| `/games` | `Game` | - | Historical game data |
| `/upcoming-games` | `UpcomingGame` | - | Current week games |

---

## Query Performance Considerations

### Indexing Strategy
- **Primary Keys**: SHA-256 hashes for unique identification
- **Enum Columns**: Indexed for fast filtering (month, day_of_week, team names)
- **Boolean Columns**: Indexed for divisional and outcome filtering
- **Composite Indexes**: On frequently filtered combinations

### Data Types
- **Numeric(4,1)**: Precise decimal storage for betting lines (e.g., -3.5, 47.5)
- **Numeric(4,3)**: High precision for win percentages (e.g., 65.432%)
- **Enums**: Memory-efficient storage with fast comparison
- **Boolean**: Optimized for true/false filtering

### Pagination Support
All main endpoints support pagination with:
- **limit**: Results per page
- **offset**: Starting position
- **total_count**: Total available records

---

## API Response Format

### Standard Response Structure
```json
{
  "limit": 50,
  "offset": 0,
  "count": 25,
  "total_count": 1234,
  "results": [...]
}
```

### Individual Record Format
Each model serializes to JSON with all attributes included, using enum string values for readability.

### Error Handling
- **404**: Record not found
- **422**: Validation error (invalid enum values, etc.)
- **500**: Database connection or query errors

This documentation provides complete reference for all database models used by the NFL Trends API, including their structure, relationships, and usage patterns.
