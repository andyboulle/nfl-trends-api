import re
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Literal
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import case, Integer, cast, and_, or_
from app.models.game import Game
from app.database.connection import get_connection
from app.enums.game_enums import MonthEnum, DayOfWeekEnum, FullTeamNameEnum, TeamAbbreviationEnum, DivisionEnum

router = APIRouter()

MONTH_MAPPING = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

class SortField(BaseModel):
    field: str
    order: Literal["asc", "desc"] = "asc"

class GameFilter(BaseModel):
    ############################
    ###### GAME ID FILTERS #####
    ############################

    game_id: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by game ID(s). The format is: home team abbreviation + away team abbreviation + yyyymmdd. "
            "Abbreviations can be lowercase or uppercase. Can be a single game ID or a list of game IDs. "
            "Example: 'NYJNE20240910' or ['NYJNE20240910', 'BUF20240911']."
        )
    )

    # VALIDATE GAME_IDS are in the format home team abbreviation + away team abbreviation + yyyymmdd
    @validator("game_id", pre=True)
    def validate_game_id_format(cls, value):
        game_id_pattern = r"^[A-Za-z]{2,3}[A-Za-z]{2,3}\d{8}$"
        if isinstance(value, str):
            if not re.match(game_id_pattern, value):
                raise ValueError(
                    "Game ID must follow the format: home team abbreviation + away team abbreviation + yyyymmdd. "
                    "Example: 'NYJNE20240910'."
                )
            return value.upper()  # Capitalize the game ID
        elif isinstance(value, list):
            for game_id in value:
                if not isinstance(game_id, str) or not re.match(game_id_pattern, game_id):
                    raise ValueError(
                        "Each Game ID in the list must follow the format: home team abbreviation + away team abbreviation + yyyymmdd. "
                        "Example: 'NYJNE20240910'."
                    )
            return [game_id.upper() for game_id in value]  # Capitalize all game IDs in the list
        return value
    

    ############################
    ####### DATE FILTERS #######
    ############################

    date: Optional[Union[str, List[str]]] = Field(
        None,
        description="Filter by date in the format yyyy-mm-dd. Can be a single date or a list of dates."
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date for filtering games in the format yyyy-mm-dd."
    )
    end_date: Optional[str] = Field(
        None,
        description="End date for filtering games in the format yyyy-mm-dd."
    )

    # VALIDATE DATES are in the format yyyy-mm-dd
    @validator("date", "start_date", "end_date", pre=True)
    def validate_date_format(cls, value):
        if isinstance(value, str):
            # Validate a single date
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                raise ValueError("Date must be in the format yyyy-mm-dd")
        elif isinstance(value, list):
            # Validate a list of dates
            for date in value:
                if not isinstance(date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                    raise ValueError("Each date in the list must be in the format yyyy-mm-dd")
        return value
    

    ############################
    ####### MONTH FILTERS ######
    ############################

    month: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by month. Can be a single month or a list of months. "
            "Example: 'January' or ['January', 'February']."
        )
    )
    start_month: Optional[str] = Field(
        None,
        description="Start month for filtering games. Example: 'January'."
    )
    end_month: Optional[str] = Field(
        None,
        description="End month for filtering games. Example: 'December'."
    )

    # VALIDATES MONTHS are in the MonthEnum format
    @validator("month", "start_month", "end_month", pre=True)
    def validate_month(cls, value):
        if isinstance(value, str):
            # Validate a single month
            value = value.capitalize()  # Capitalize the first letter
            if value not in MonthEnum._value2member_map_:
                raise ValueError(f"{value} must be one of {list(MonthEnum._value2member_map_.keys())}")
        if isinstance(value, list):
            # Validate list of months
            value = [month.capitalize() for month in value]  # Capitalize each string in the list
            for month in value:
                if month not in MonthEnum._value2member_map_:
                    raise ValueError(f"Each month in {value} must be one of {list(MonthEnum._value2member_map_.keys())}")
        return value
    

    ############################
    ######## DAY FILTERS #######
    ############################

    day: Optional[Union[int, List[int]]] = Field(
        None,
        description=(
            "Filter by day(s) of the month. Can be a single day (1-31) or a list of days. "
            "Example: 15 or [1, 15, 31]."
        )
    )
    start_day: Optional[int] = Field(
        None,
        description="Start day for filtering games (1-31). Example: 1."
    )
    end_day: Optional[int] = Field(
        None,
        description="End day for filtering games (1-31). Example: 31."
    )

    # VALIDATE DAYS are between 1 and 31
    @validator("day", "start_day", "end_day", pre=True)
    def validate_day(cls, value):
        if isinstance(value, int):
            if not (1 <= value <= 31):
                raise ValueError("Day must be between 1 and 31")
        elif isinstance(value, list):
            for day in value:
                if not isinstance(day, int) or not (1 <= day <= 31):
                    raise ValueError("Each day in the list must be an integer between 1 and 31")
        return value
    
    ############################
    ####### YEAR FILTERS #######
    ############################
    year: Optional[Union[int, List[int]]] = Field(
        None,
        description=(
            "Filter by year(s). Can be a single year (2006-2025) or a list of years. "
            "Example: 2024 or [2020, 2021, 2022]."
        )
    )
    start_year: Optional[int] = Field(
        None,
        description="Start year for filtering games (2006-2025). Example: 2020."
    )
    end_year: Optional[int] = Field(
        None,
        description="End year for filtering games (2006-2025). Example: 2025."
    )

    # VALIDATE YEARS are between 2006 and 2025
    @validator("year", "start_year", "end_year", pre=True)
    def validate_year(cls, value):
        if isinstance(value, int):
            if not (2006 <= value <= 2025):
                raise ValueError("Year must be between 2006 and 2025")
        elif isinstance(value, list):
            for year in value:
                if not isinstance(year, int) or not (2006 <= year <= 2025):
                    raise ValueError("Each year in the list must be an integer between 2006 and 2025")
        return value
    

    ##########################
    ##### SEASON FILTERS #####
    ##########################

    season: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by season. Can be a single season ('2006-2007' - '2024-2025') or a list of seasons. "
            "Example: '2022-2023' or ['2020-2021', '2021-2022']."
        )
    )
    start_season: Optional[str] = Field(
        None,
        description="Start season for filtering games. Example: '2020-2021'."
    )
    end_season: Optional[str] = Field(
        None,
        description="End season for filtering games. Example: '2025-2026'."
    )

    # VALIDATE SEASONS are in the format yyyy-yyyy
    @validator("season", "start_season", "end_season", pre=True)
    def validate_season_format(cls, value):
        if isinstance(value, str):
            # Validate a single season
            if not re.match(r"^\d{4}-\d{4}$", value):
                raise ValueError("Season must be in the format yyyy-yyyy")
            # Split the season into start and end years
            start_year, end_year = map(int, value.split("-"))
            # Validate that the second year is 1 more than the first
            if end_year != start_year + 1:
                raise ValueError(f"Invalid season range: {value}. The second year must be 1 more than the first year.")
            # Validate that the season is within the allowed range
            if not (2006 <= start_year <= 2024 and 2007 <= end_year <= 2025):
                raise ValueError(f"Season {value} must be between 2006-2007 and 2024-2025")
            return value

        elif isinstance(value, list):
            # Validate a list of seasons
            for season in value:
                if not isinstance(season, str) or not re.match(r"^\d{4}-\d{4}$", season):
                    raise ValueError("Each season in the list must be in the format yyyy-yyyy")
                # Split the season into start and end years
                start_year, end_year = map(int, season.split("-"))
                # Validate that the second year is 1 more than the first
                if end_year != start_year + 1:
                    raise ValueError(f"Invalid season range: {season}. The second year must be 1 more than the first year.")
                # Validate that the season is within the allowed range
                if not (2006 <= start_year <= 2024 and 2007 <= end_year <= 2025):
                    raise ValueError(f"Season {season} must be between 2006-2007 and 2024-2025")
            
            return value
        

    ###############################
    ##### DAY OF WEEK FILTERS #####
    ###############################

    day_of_week: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by day of the week. Can be a single day or a list of days. "
            "Example: 'Monday' or ['Monday', 'Tuesday']."
        )
    )
    
    # VALIDATE DAY OF WEEK are in the DayOfWeekEnum format
    @validator("day_of_week", pre=True)
    def validate_day_of_week(cls, value):
        if isinstance(value, str):
            # Validate a single day of the week
            value = value.capitalize()
            if value not in DayOfWeekEnum._value2member_map_:
                raise ValueError(f"{value} must be one of {list(DayOfWeekEnum._value2member_map_.keys())}")
        if isinstance(value, list):
            # Validate list of days of the week
            value = [day.capitalize() for day in value]
            for day in value:
                if day not in DayOfWeekEnum._value2member_map_:
                    raise ValueError(f"Each day in {value} must be one of {list(DayOfWeekEnum._value2member_map_.keys())}")
        return value
    

    # TODO: Add week filters


    #############################
    ####### TEAM FILTERS ########
    #############################

    home_team: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by home team. Can be a single team or a list of teams. "
            "Example: 'New York Jets' or ['New York Jets', 'New England Patriots']."
        )
    )
    away_team: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by away team. Can be a single team or a list of teams. "
            "Example: 'New York Jets' or ['New York Jets', 'New England Patriots']."
        )
    )

    # VALIDATE TEAMS are in the FullTeamNameEnum format
    @validator("home_team", "away_team", pre=True)
    def validate_team(cls, value):
        def normalize(v: str) -> str:
            # Match case-insensitively against the enum values
            for team_name in FullTeamNameEnum._value2member_map_:
                if v.strip().lower() == team_name.lower():
                    return team_name
            raise ValueError(f"{v} must be one of {list(FullTeamNameEnum._value2member_map_.keys())}")

        if isinstance(value, str):
            return normalize(value)

        elif isinstance(value, list):
            return [normalize(v) for v in value]

        return value
    

    ##################################
    #### TEAM ABBREVIATION FILTERS ###
    ##################################

    home_abbreviation: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by home team abbreviation. Can be a single abbreviation or a list of abbreviations. "
            "Example: 'NYJ' or ['NYJ', 'NE']."
        )
    )
    away_abbreviation: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by away team abbreviation. Can be a single abbreviation or a list of abbreviations. "
            "Example: 'NYJ' or ['NYJ', 'NE']."
        )
    )

    # VALIDATE TEAM ABBREVIATIONS are in the TeamAbbreviationEnum format
    @validator("home_abbreviation", "away_abbreviation", pre=True)
    def validate_team_abbreviation(cls, value):
        if isinstance(value, str):
            # Validate a single abbreviation
            value = value.upper()
            if value not in TeamAbbreviationEnum._value2member_map_:
                raise ValueError(f"{value} must be one of {list(TeamAbbreviationEnum._value2member_map_.keys())}")
        if isinstance(value, list):
            # Validate list of abbreviations
            value = [abbreviation.upper() for abbreviation in value]
            for abbreviation in value:
                if abbreviation not in TeamAbbreviationEnum._value2member_map_:
                    raise ValueError(f"Each abbreviation in {value} must be one of {list(TeamAbbreviationEnum._value2member_map_.keys())}")
        return value
    

    ##################################
    ##### TEAM DIVISION FILTERS ######
    ##################################

    home_division: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by home team division. Can be a single division or a list of divisions. "
            "Example: 'AFC East' or ['AFC East', 'AFC North']."
        )
    )
    away_division: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by away team division. Can be a single division or a list of divisions. "
            "Example: 'AFC East' or ['AFC East', 'AFC North']."
        )
    )

    # VALIDATE TEAM DIVISIONS are in the DivisionEnum format
    @validator("home_division", "away_division", pre=True)
    def validate_team_division(cls, value):
        if isinstance(value, str):
            # Validate a single division
            value = value.upper()
            if value not in DivisionEnum._value2member_map_:
                raise ValueError(f"{value} must be one of {list(DivisionEnum._value2member_map_.keys())}")
        if isinstance(value, list):
            # Validate list of divisions
            value = [division.upper() for division in value]
            for division in value:
                if division not in DivisionEnum._value2member_map_:
                    raise ValueError(f"Each division in {value} must be one of {list(DivisionEnum._value2member_map_.keys())}")
        return value
    
    #################################
    #### DIVISIONAL GAME FILTERS ####
    #################################

    divisional: Optional[bool] = Field(
        None,
        description=(
            "Filter by divisional games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE DIVISIONAL is a boolean
    @validator("divisional", pre=True)
    def validate_divisional(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Divisional must be a boolean value (True or False)")
        return value
    
    ##################################
    ####### HOME SCORE FILTERS #######
    ##################################

    home_score: Optional[Union[int, List[int]]] = Field(
        None,
        description=(
            "Filter by home score. Can be a single score or a list of scores. "
            "Example: 24 or [21, 24, 30]."
        )
    )
    min_home_score: Optional[int] = Field(
        None,
        description="Minimum home score for filtering games. Example: 21."
    )
    max_home_score: Optional[int] = Field(
        None,
        description="Maximum home score for filtering games. Example: 30."
    )

    # VALIDATE HOME SCORE is between 0 and 100
    @validator("home_score", "min_home_score", "max_home_score", pre=True)
    def validate_home_score(cls, value):
        if isinstance(value, int):
            if not (0 <= value <= 100):
                raise ValueError("Home score must be between 0 and 100")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, int) or not (0 <= score <= 100):
                    raise ValueError("Each home score in the list must be an integer between 0 and 100")
        return value
    
    ##################################
    ####### AWAY SCORE FILTERS #######
    ##################################

    away_score: Optional[Union[int, List[int]]] = Field(
        None,
        description=(
            "Filter by away score. Can be a single score or a list of scores. "
            "Example: 24 or [21, 24, 30]."
        )
    )
    min_away_score: Optional[int] = Field(
        None,
        description="Minimum away score for filtering games. Example: 21."
    )
    max_away_score: Optional[int] = Field(
        None,
        description="Maximum away score for filtering games. Example: 30."
    )

    # VALIDATE AWAY SCORE is between 0 and 100
    @validator("away_score", "min_away_score", "max_away_score", pre=True)
    def validate_away_score(cls, value):
        if isinstance(value, int):
            if not (0 <= value <= 100):
                raise ValueError("Away score must be between 0 and 100")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, int) or not (0 <= score <= 100):
                    raise ValueError("Each away score in the list must be an integer between 0 and 100")
        return value
    
    ##################################
    ##### COMBINED SCORE FILTERS #####
    ##################################

    combined_score: Optional[Union[int, List[int]]] = Field(
        None,
        description=(
            "Filter by combined score. Can be a single score or a list of scores. "
            "Example: 48 or [45, 48, 50]."
        )
    )
    min_combined_score: Optional[int] = Field(
        None,
        description="Minimum combined score for filtering games. Example: 45."
    )
    max_combined_score: Optional[int] = Field(
        None,
        description="Maximum combined score for filtering games. Example: 50."
    )

    # VALIDATE COMBINED SCORE is between 0 and 200
    @validator("combined_score", "min_combined_score", "max_combined_score", pre=True)
    def validate_combined_score(cls, value):
        if isinstance(value, int):
            if not (0 <= value <= 200):
                raise ValueError("Combined score must be between 0 and 200")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, int) or not (0 <= score <= 200):
                    raise ValueError("Each combined score in the list must be an integer between 0 and 200")
        return value
    
    ##################################
    ########## TIE FILTERS ###########
    ##################################

    tie: Optional[bool] = Field(
        None,
        description=(
            "Filter by tie games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE TIE is a boolean
    @validator("tie", pre=True)
    def validate_tie(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Tie must be a boolean value (True or False)")
        return value
        
    
    ###################################
    ###### WINNER/LOSER FILTERS #######
    ###################################

    winner: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by winner. Can be a single team or a list of teams. "
            "Example: 'New York Jets' or ['New York Jets', 'New England Patriots']."
        )
    )
    loser: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by loser. Can be a single team or a list of teams. "
            "Example: 'New York Jets' or ['New York Jets', 'New England Patriots']."
        )
    )

    # VALIDATE WINNER/LOSER are in the FullTeamNameEnum format
    @validator("winner", "loser", pre=True)
    def validate_winner_loser(cls, value):
        def normalize(v: str) -> str:
            # Match case-insensitively against the enum values
            for team_name in FullTeamNameEnum._value2member_map_:
                if v.strip().lower() == team_name.lower():
                    return team_name
            raise ValueError(f"{v} must be one of {list(FullTeamNameEnum._value2member_map_.keys())}")

        if isinstance(value, str):
            return normalize(value)

        elif isinstance(value, list):
            return [normalize(v) for v in value]

        return value
    

    ##################################
    ######## SPREAD FILTERS ##########
    ##################################

    spread: Optional[Union[float, List[float]]] = Field(
        None,
        description=(
            "Filter by spread. Can be a single spread or a list of spreads. "
            "Example: 3.5 or [2.5, 3.5, 4.5]."
        )
    )
    min_spread: Optional[float] = Field(
        None,
        description="Minimum spread for filtering games. Example: 2.5."
    )
    max_spread: Optional[float] = Field(
        None,
        description="Maximum spread for filtering games. Example: 4.5."
    )

    # VALIDATE SPREAD is between 0 and 27. And ends with .0 or .5
    @validator("spread", "min_spread", "max_spread", pre=True)
    def validate_spread(cls, value):
        if isinstance(value, float):
            if not (0 <= value <= 27) or (value * 10) % 5 != 0:
                raise ValueError("Spread must be between 0 and 27 and end with .0 or .5")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, float) or not (0 <= score <= 27) or (score * 10) % 5 != 0:
                    raise ValueError("Each spread in the list must be a float between 0 and 27 and end with .0 or .5")
        return value
    
    ##################################
    ###### HOME SPREAD FILTERS #######
    ##################################

    home_spread: Optional[Union[float, List[float]]] = Field(
        None,
        description=(
            "Filter by home spread. Can be a single spread or a list of spreads. "
            "Example: 3.5 or [2.5, 3.5, 4.5]."
        )
    )
    min_home_spread: Optional[float] = Field(
        None,
        description="Minimum home spread for filtering games. Example: 2.5."
    )
    max_home_spread: Optional[float] = Field(
        None,
        description="Maximum home spread for filtering games. Example: 4.5."
    )

    # VALIDATE HOME SPREAD is between -27 and 27. And ends with .0 or .5
    @validator("home_spread", "min_home_spread", "max_home_spread", pre=True)
    def validate_home_spread(cls, value):
        if isinstance(value, float):
            if not (-27 <= value <= 27) or (value * 10) % 5 != 0:
                raise ValueError("Home spread must be between -27 and 27 and end with .0 or .5")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, float) or not (-27 <= score <= 27) or (score * 10) % 5 != 0:
                    raise ValueError("Each home spread in the list must be a float between -27 and 27 and end with .0 or .5")
        return value
    
    ##################################
    ### HOME SPREAD RESULT FILTERS ###
    ##################################

    home_spread_result: Optional[Union[int, List[int]]] = Field(
        None,
        description=(
            "Filter by home spread result. Can be a single spread result or a list of spreads. "
            "Example: 3 or [2, 3, 4]."
        )
    )
    min_home_spread_result: Optional[int] = Field(
        None,
        description="Minimum home spread result for filtering games. Example: 2."
    )
    max_home_spread_result: Optional[int] = Field(
        None,
        description="Maximum home spread result for filtering games. Example: 4."
    )

    # VALIDATE HOME SPREAD RESULT is between -100 and 100
    @validator("home_spread_result", "min_home_spread_result", "max_home_spread_result", pre=True)
    def validate_home_spread_result(cls, value):
        if isinstance(value, int):
            if not (-100 <= value <= 100):
                raise ValueError("Home spread result must be between -100 and 100")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, int) or not (-100 <= score <= 100):
                    raise ValueError("Each home spread result in the list must be an integer between -100 and 100")
        return value
        

    ##################################
    ###### AWAY SPREAD FILTERS #######
    ##################################

    away_spread: Optional[Union[float, List[float]]] = Field(
        None,
        description=(
            "Filter by away spread. Can be a single spread or a list of spreads. "
            "Example: 3.5 or [2.5, 3.5, 4.5]."
        )
    )
    min_away_spread: Optional[float] = Field(
        None,
        description="Minimum away spread for filtering games. Example: 2.5."
    )
    max_away_spread: Optional[float] = Field(
        None,
        description="Maximum away spread for filtering games. Example: 4.5."
    )

    # VALIDATE AWAY SPREAD is between -27 and 27. And ends with .0 or .5
    @validator("away_spread", "min_away_spread", "max_away_spread", pre=True)
    def validate_away_spread(cls, value):
        if isinstance(value, float):
            if not (-27 <= value <= 27) or (value * 10) % 5 != 0:
                raise ValueError("Away spread must be between -27 and 27 and end with .0 or .5")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, float) or not (-27 <= score <= 27) or (score * 10) % 5 != 0:
                    raise ValueError("Each away spread in the list must be a float between -27 and 27 and end with .0 or .5")
        return value
    

    ##################################
    ### AWAY SPREAD RESULT FILTERS ###
    ##################################

    away_spread_result: Optional[Union[int, List[int]]] = Field(
        None,
        description=(
            "Filter by away spread result. Can be a single spread result or a list of spreads. "
            "Example: 3 or [2, 3, 4]."
        )
    )
    min_away_spread_result: Optional[int] = Field(
        None,
        description="Minimum away spread result for filtering games. Example: 2."
    )
    max_away_spread_result: Optional[int] = Field(
        None,
        description="Maximum away spread result for filtering games. Example: 4."
    )

    # VALIDATE AWAY SPREAD RESULT is between -100 and 100
    @validator("away_spread_result", "min_away_spread_result", "max_away_spread_result", pre=True)
    def validate_away_spread_result(cls, value):
        if isinstance(value, int):
            if not (-100 <= value <= 100):
                raise ValueError("Away spread result must be between -100 and 100")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, int) or not (-100 <= score <= 100):
                    raise ValueError("Each away spread result in the list must be an integer between -100 and 100")
        return value
    

    ##################################
    ###### SPREAD PUSH FILTERS #######
    ##################################

    spread_push: Optional[bool] = Field(
        None,
        description=(
            "Filter by spread push games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE SPREAD PUSH is a boolean
    @validator("spread_push", pre=True)
    def validate_spread_push(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Spread push must be a boolean value (True or False)")
        return value
    

    ##################################
    ######## PICKEM FILTERS ##########
    ##################################
    pk: Optional[bool] = Field(
        None,
        description=(
            "Filter by pickem games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE PK is a boolean
    @validator("pk", pre=True)
    def validate_pk(cls, value):
        if not isinstance(value, bool):
            raise ValueError("pk must be a boolean value (True or False)")
        return value
    

    ##################################
    ######### TOTAL FILTERS ##########
    ##################################

    total: Optional[Union[float, List[float]]] = Field(
        None,
        description=(
            "Filter by total. Can be a single total or a list of totals. "
            "Example: 48 or [52.5, 53.5, 54.5]."
        )
    )
    min_total: Optional[float] = Field(
        None,
        description="Minimum total for filtering games. Example: 32.5."
    )
    max_total: Optional[float] = Field(
        None,
        description="Maximum total for filtering games. Example: 54.5."
    )

    # VALIDATE TOTAL is between 0 and 100. And ends with .0 or .5
    @validator("total", "min_total", "max_total", pre=True)
    def validate_total(cls, value):
        if isinstance(value, float):
            if not (0 <= value <= 100) or (value * 10) % 5 != 0:
                raise ValueError("Total must be between 0 and 100 and end with .0 or .5")
        elif isinstance(value, list):
            for score in value:
                if not isinstance(score, float) or not (0 <= score <= 100) or (score * 10) % 5 != 0:
                    raise ValueError("Each total in the list must be a float between 0 and 100 and end with .0 or .5")
        return value
    
    ##################################
    ####### TOTAL PUSH FILTERS #######
    ##################################

    total_push: Optional[bool] = Field(
        None,
        description=(
            "Filter by total push games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE TOTAL PUSH is a boolean
    @validator("total_push", pre=True)
    def validate_total_push(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Total push must be a boolean value (True or False)")
        return value
    
    ##############################################
    #### HOME/AWAY FAVORITE/UNDERDOG FILTERS ####
    #############################################

    home_favorite: Optional[bool] = Field(
        None,
        description=(
            "Filter by home favorite games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_favorite: Optional[bool] = Field(
        None,
        description=(
            "Filter by away favorite games. Can be True or False. "
            "Example: True or False."
        )
    )
    home_underdog: Optional[bool] = Field(
        None,
        description=(
            "Filter by home underdog games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_underdog: Optional[bool] = Field(
        None,
        description=(
            "Filter by away underdog games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE HOME/AWAY FAVORITE/UNDERDOG is a boolean
    @validator("home_favorite", "away_favorite", "home_underdog", "away_underdog", pre=True)
    def validate_favorite_underdog(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Favorite/underdog must be a boolean value (True or False)")
        return value
    
    ###############################################
    ### HOME/AWAY FAVORITE/UNDERDOG WIN FILTERS ###
    ###############################################

    home_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by home win games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by away win games. Can be True or False. "
            "Example: True or False."
        )
    )
    favorite_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by favorite win games. Can be True or False. "
            "Example: True or False."
        )
    )
    underdog_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by underdog win games. Can be True or False. "
            "Example: True or False."
        )
    )
    home_favorite_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by home favorite win games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_favorite_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by away favorite win games. Can be True or False. "
            "Example: True or False."
        )
    )
    home_underdog_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by home underdog win games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_underdog_win: Optional[bool] = Field(
        None,
        description=(
            "Filter by away underdog win games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE HOME/AWAY FAVORITE/UNDERDOG WIN is a boolean
    @validator("home_win", "away_win", "favorite_win", "underdog_win", "home_favorite_win", "away_favorite_win", "home_underdog_win", "away_underdog_win", pre=True)
    def validate_favorite_underdog_win(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Favorite/underdog win must be a boolean value (True or False)")
        return value
    
    #################################################
    ### HOME/AWAY FAVORITE/UNDERDOG COVER FILTERS ###
    #################################################

    home_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by home cover games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by away cover games. Can be True or False. "
            "Example: True or False."
        )
    )
    favorite_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by favorite cover games. Can be True or False. "
            "Example: True or False."
        )
    )
    underdog_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by underdog cover games. Can be True or False. "
            "Example: True or False."
        )
    )
    home_favorite_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by home favorite cover games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_favorite_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by away favorite cover games. Can be True or False. "
            "Example: True or False."
        )
    )
    home_underdog_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by home underdog cover games. Can be True or False. "
            "Example: True or False."
        )
    )
    away_underdog_cover: Optional[bool] = Field(
        None,
        description=(
            "Filter by away underdog cover games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE HOME/AWAY FAVORITE/UNDERDOG COVER is a boolean
    @validator("home_cover", "away_cover", "favorite_cover", "underdog_cover", "home_favorite_cover", "away_favorite_cover", "home_underdog_cover", "away_underdog_cover", pre=True)
    def validate_favorite_underdog_cover(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Favorite/underdog cover must be a boolean value (True or False)")
        return value
    
    ##################################
    ##### OVER/UNDER HIT FILTERS #####
    ##################################

    over_hit: Optional[bool] = Field(
        None,
        description=(
            "Filter by over hit games. Can be True or False. "
            "Example: True or False."
        )
    )
    under_hit: Optional[bool] = Field(
        None,
        description=(
            "Filter by under hit games. Can be True or False. "
            "Example: True or False."
        )
    )

    # VALIDATE OVER/UNDER HIT is a boolean
    @validator("over_hit", "under_hit", pre=True)
    def validate_over_under_hit(cls, value):
        if not isinstance(value, bool):
            raise ValueError("Over/under hit must be a boolean value (True or False)")
        return value
    
    ##################################
    ###### PAGINATION FILTERS ########
    ##################################

    limit: Optional[int] = Field(
        100,
        description=(
            "Limit the number of results returned. "
            "Example: 100."
        )
    )
    offset: Optional[int] = Field(
        0,
        description=(
            "Offset the results returned. "
            "Example: 0."
        )
    )

    # VALIDATE LIMIT is between 1 and 1000
    @validator("limit", pre=True)
    def validate_limit(cls, value):
        if not isinstance(value, int) or not (1 <= value <= 1000):
            raise ValueError("Limit must be an integer between 1 and 1000")
        return value
    # VALIDATE OFFSET is greater than 0
    @validator("offset", pre=True)
    def validate_offset(cls, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("Offset must be an integer greater than or equal to 0")
        return value
    

    ##################################
    ####### SORTING FILTERS ##########
    ##################################
    sort_by: Optional[List[SortField]] = Field(
        [
            SortField(field="date", order="asc"),
            SortField(field="id_string", order="asc"),
        ],
        description=(
            "Sort the results by one or more fields. "
            "Example: [{'field': 'date', 'order': 'asc'}, {'field': 'home_team', 'order': 'desc'}]."
        )
    )

    # VALIDATE SORTING is a list of SortField objects or strings
    @validator("sort_by", pre=True)
    def validate_sort_by(cls, value):
        if not value:
            return None

        if isinstance(value, str):
            # Single field as string (defaults to asc)
            return [SortField(field=value, order="asc")]
        
        if isinstance(value, dict):
            if "field" not in value:
                raise ValueError("Sort field must be specified in the dictionary")
            elif "order" not in value:
                value["order"] = "asc"
            return [SortField(**value)]

        if isinstance(value, list):
            result = []
            for v in value:
                if isinstance(v, dict):
                    # Fill in default order if not specified
                    if "field" not in v:
                        raise ValueError("Sort field must be specified in the dictionary")
                    if "order" not in v:
                        v["order"] = "asc"
                    result.append(SortField(**v))
                elif isinstance(v, str):
                    result.append(SortField(field=v, order="asc"))
                else:
                    raise ValueError(f"Invalid item in sort_by list: {v}")
            return result

        raise ValueError(
            "Invalid format for 'sort_by'. Expected a string (e.g. 'year'), "
            "a list of strings (e.g. ['year', 'season']), or a list of objects "
            "with 'field' and optional 'order' (e.g. [{'field': 'year', 'order': 'desc'}])."
        )
    
@router.post("/games", summary="Retrieve games with filters", tags=["Games"])
def get_games(filters: GameFilter, db: Session = Depends(get_connection)):
    """
    Retrieve games from the database based on the provided filters.

    - **game_id**: Filter by game ID(s) in the format home team abbreviation + away team abbreviation + yyyymmdd. (Ex: NYJBUF20240910 or ['NYJBUF20240910', 'NE20240911']).
    - **date**: Filter by specific date(s) in the format yyyy-mm-dd. (Ex: 2024-09-10 or ['2024-09-10', '2006-10-11']).
    - **start_date**: Start date for filtering games in the format yyyy-mm-dd. (Ex: 2020-11-21).
    - **end_date**: End date for filtering games in the format yyyy-mm-dd. (Ex: 2020-12-21).
    - **month**: Filter by month(s) (Ex: January or ['January', 'February']).
    - **start_month**: Start month for filtering games (Ex: January).
    - **end_month**: End month for filtering games (Ex: December).
    - **day**: Filter by day(s) of the month (1-31). (Ex: 15 or [1, 15, 31]).
    - **start_day**: Start day for filtering games (1-31). (Ex: 1).
    - **end_day**: End day for filtering games (1-31). (Ex: 31).
    - **year**: Filter by year(s) (2006-2025). (Ex: 2024 or [2020, 2021, 2022]).
    - **start_year**: Start year for filtering games (2006-2025). (Ex: 2020).
    - **end_year**: End year for filtering games (2006-2025). (Ex: 2025).
    - **season**: Filter by season(s) (2006-2007 - 2024-2025). (Ex: 2022-2023 or ['2020-2021', '2021-2022']).
    - **start_season**: Start season for filtering games (Ex: 2020-2021).
    - **end_season**: End season for filtering games (Ex: 2025-2026).
    - **day_of_week**: Filter by day of the week(s) (Ex: Monday or ['Monday', 'Tuesday']).
    - **home_team**: Filter by home team(s) (Ex: 'New York Jets' or ['New York Jets', 'New England Patriots']).
    - **away_team**: Filter by away team(s) (Ex: 'New York Jets' or ['New York Jets', 'New England Patriots']).
    - **home_abbreviation**: Filter by home team abbreviation(s) (Ex: 'NYJ' or ['NYJ', 'NE']).
    - **away_abbreviation**: Filter by away team abbreviation(s) (Ex: 'NYJ' or ['NYJ', 'NE']).
    - **home_division**: Filter by home team division(s) (Ex: 'AFC East' or ['AFC East', 'NFC North']).
    - **away_division**: Filter by away team division(s) (Ex: 'AFC East' or ['AFC East', 'NFC North']).
    - **divisional**: Filter by divisional games (Ex: True or False).
    - **home_score**: Filter by home score(s) (Ex: 24 or [21, 24, 30]).
    - **min_home_score**: Minimum home score for filtering games (Ex: 21).
    - **max_home_score**: Maximum home score for filtering games (Ex: 30).
    - **away_score**: Filter by away score(s) (Ex: 24 or [21, 24, 30]).
    - **min_away_score**: Minimum away score for filtering games (Ex: 21).
    - **max_away_score**: Maximum away score for filtering games (Ex: 30).
    - **combined_score**: Filter by combined score(s) (Ex: 48 or [45, 48, 50]).
    - **min_combined_score**: Minimum combined score for filtering games (Ex: 45).
    - **max_combined_score**: Maximum combined score for filtering games (Ex: 50).
    - **tie**: Filter by tie games (Ex: True or False).
    - **winner**: Filter by winner(s) (Ex: 'New York Jets' or ['New York Jets', 'New England Patriots']).
    - **loser**: Filter by loser(s) (Ex: 'New York Jets' or ['New York Jets', 'New England Patriots']).
    - **spread**: Filter by spread(s) (Ex: 3.5 or [2.5, 3.5, 4.5]).
    - **min_spread**: Minimum spread for filtering games (Ex: 2.5).
    - **max_spread**: Maximum spread for filtering games (Ex: 4.5).
    - **home_spread**: Filter by home spread(s) (Ex: 3.5 or [2.5, 3.5, 4.5]).
    - **min_home_spread**: Minimum home spread for filtering games (Ex: 2.5).
    - **max_home_spread**: Maximum home spread for filtering games (Ex: 4.5).
    - **home_spread_result**: Filter by home spread result(s). This is home score - away score. (Ex: 3 or [2, 3, 4]).
    - **min_home_spread_result**: Minimum home spread result for filtering games (Ex: 2).
    - **max_home_spread_result**: Maximum home spread result for filtering games (Ex: 4).
    - **away_spread**: Filter by away spread(s) (Ex: 3.5 or [2.5, 3.5, 4.5]).
    - **min_away_spread**: Minimum away spread for filtering games (Ex: 2.5).
    - **max_away_spread**: Maximum away spread for filtering games (Ex: 4.5).
    - **away_spread_result**: Filter by away spread result(s). This is away score - home score. (Ex: 3 or [2, 3, 4]).
    - **min_away_spread_result**: Minimum away spread result for filtering games (Ex: 2).
    - **max_away_spread_result**: Maximum away spread result for filtering games (Ex: 4).
    - **spread_push**: Filter by games where the spread pushed (Ex: True or False).
    - **pk**: Filter by games where the spread was a pickem (Ex: True or False).
    - **total**: Filter by total(s) (Ex: 48 or [52.5, 53.5, 54.5]).
    - **min_total**: Minimum total for filtering games (Ex: 32.5).
    - **max_total**: Maximum total for filtering games (Ex: 54.5).
    - **total_push**: Filter by games where the total pushed (Ex: True or False).
    - **home_favorite**: Filter by games where the home team was the favorite (Ex: True or False).
    - **away_favorite**: Filter by games where the away team was the favorite (Ex: True or False).
    - **home_underdog**: Filter by games where the home team was the underdog (Ex: True or False).
    - **away_underdog**: Filter by games where the away team was the underdog (Ex: True or False).
    - **home_win**: Filter by games where the home team won (Ex: True or False).
    - **away_win**: Filter by games where the away team won (Ex: True or False).
    - **favorite_win**: Filter by games where the favorite team won (Ex: True or False).
    - **underdog_win**: Filter by games where the underdog team won (Ex: True or False).
    - **home_favorite_win**: Filter by games where the home favorite team won (Ex: True or False).
    - **away_favorite_win**: Filter by games where the away favorite team won (Ex: True or False).
    - **home_underdog_win**: Filter by games where the home underdog team won (Ex: True or False).
    - **away_underdog_win**: Filter by games where the away underdog team won (Ex: True or False).
    - **home_cover**: Filter by games where the home team covered the spread (Ex: True or False).
    - **away_cover**: Filter by games where the away team covered the spread (Ex: True or False).
    - **favorite_cover**: Filter by games where the favorite team covered the spread (Ex: True or False).
    - **underdog_cover**: Filter by games where the underdog team covered the spread (Ex: True or False).
    - **home_favorite_cover**: Filter by games where the home favorite team covered the spread (Ex: True or False).
    - **away_favorite_cover**: Filter by games where the away favorite team covered the spread (Ex: True or False).
    - **home_underdog_cover**: Filter by games where the home underdog team covered the spread (Ex: True or False).
    - **away_underdog_cover**: Filter by games where the away underdog team covered the spread (Ex: True or False).
    - **over_hit**: Filter by games where the over hit (Ex: True or False).
    - **under_hit**: Filter by games where the under hit (Ex: True or False).
    - **limit**: Limit the number of results returned (Ex: 100).
    - **offset**: Offset the results returned (Ex: 0).
    - **sort_by**: Sort the results by one or more fields. (Ex: 'date' or ['month', 'year'] or {'season': 'desc'} or [{'field': 'date', 'order': 'asc'}, {'field': 'home_team', 'order': 'desc'}]).
    """

    query = db.query(Game)
    filters_list = []

    # Filter by GAME ID
    if filters.game_id:
        if isinstance(filters.game_id, str):
            filters_list.append(Game.id_string == filters.game_id)
        else:
            filters_list.append(Game.id_string.in_(filters.game_id))

    # Filter by DATE
    if filters.date:
        if isinstance(filters.date, str):
            filters_list.append(Game.date == filters.date)
        else:
            filters_list.append(Game.date.in_(filters.date))

    # Filter by a DATE RANGE
    if filters.start_date and filters.end_date:
        filters_list.append(Game.date.between(filters.start_date, filters.end_date))
    elif filters.start_date:
        filters_list.append(Game.date >= filters.start_date)
    elif filters.end_date:
        filters_list.append(Game.date <= filters.end_date)

    # Filter by MONTH
    if filters.month:
        if isinstance(filters.month, str):
            filters_list.append(Game.month == filters.month)
        else:
            filters_list.append(Game.month.in_(filters.month))
    
    # Filter by a MONTH RANGE
    # Map database month strings to their numeric equivalents
    month_case = case(
        (Game.month == "January", 1),
        (Game.month == "February", 2),
        (Game.month == "March", 3),
        (Game.month == "April", 4),
        (Game.month == "May", 5),
        (Game.month == "June", 6),
        (Game.month == "July", 7),
        (Game.month == "August", 8),
        (Game.month == "September", 9),
        (Game.month == "October", 10),
        (Game.month == "November", 11),
        (Game.month == "December", 12),
        else_=0
    )

    if filters.start_month and filters.end_month:
        start_month_num = MONTH_MAPPING[filters.start_month]
        end_month_num = MONTH_MAPPING[filters.end_month]
        filters_list.append(month_case.between(start_month_num, end_month_num))
    elif filters.start_month:
        start_month_num = MONTH_MAPPING[filters.start_month]
        filters_list.append(month_case >= start_month_num)
    elif filters.end_month:
        end_month_num = MONTH_MAPPING[filters.end_month]
        filters_list.append(month_case <= end_month_num)

    # Filter by DAY
    if filters.day:
        if isinstance(filters.day, int):
            filters_list.append(Game.day == filters.day)
        else:
            filters_list.append(Game.day.in_(filters.day))

    # Filter by a DAY RANGE
    if filters.start_day and filters.end_day:
        filters_list.append(Game.day.between(filters.start_day, filters.end_day))
    elif filters.start_day:
        filters_list.append(Game.day >= filters.start_day)
    elif filters.end_day:
        filters_list.append(Game.day <= filters.end_day)

    # Filter by YEAR
    if filters.year:
        if isinstance(filters.year, int):
            filters_list.append(Game.year == filters.year)
        else:
            filters_list.append(Game.year.in_(filters.year))

    # Filter by a YEAR RANGE
    if filters.start_year and filters.end_year:
        filters_list.append(Game.year.between(filters.start_year, filters.end_year))
    elif filters.start_year:
        filters_list.append(Game.year >= filters.start_year)
    elif filters.end_year:
        filters_list.append(Game.year <= filters.end_year)

    # Filter by SEASON
    if filters.season:
        if isinstance(filters.season, str):
            filters_list.append(Game.season == filters.season)
        else:
            filters_list.append(Game.season.in_(filters.season))

    # Filter by a SEASON RANGE
    start_season_year = cast(func.substr(Game.season, 1, 4), Integer)

    if filters.start_season and filters.end_season:
        start = int(filters.start_season[:4])
        end = int(filters.end_season[:4])
        filters_list.append(start_season_year.between(start, end))
    elif filters.start_season:
        start = int(filters.start_season[:4])
        filters_list.append(start_season_year >= start)
    elif filters.end_season:
        end = int(filters.end_season[:4])
        filters_list.append(start_season_year <= end)

    # Filter by DAY OF WEEK
    if filters.day_of_week:
        if isinstance(filters.day_of_week, str):
            filters_list.append(Game.day_of_week == filters.day_of_week)
        else:
            filters_list.append(Game.day_of_week.in_(filters.day_of_week))

    # Filter by HOME TEAM and AWAY TEAM
    # Ex: if you want to see all Chicago Bears games, you would use {"home_team": "Chicago Bears", "away_team": "Chicago Bears"}
    # Ex: if you want to see all games between the Chicago Bears and the New York Jets, where the Bears were home and the Jets 
    #     were away you would use {"home_team": "Chicago Bears", "away_team": "New York Jets"}
    # Ex: If you want to see all the games between the Chicago Bears and the New York Jets, regardless of who was home and who 
    #     was away, you would use {"home_team": ["Chicago Bears", "New York Jets"], "away_team": ["Chicago Bears", "New York Jets"]}
    def normalize_to_list(value):
        if isinstance(value, list):
            return value
        elif value:
            return [value]
        return []

    home_teams = normalize_to_list(filters.home_team)
    away_teams = normalize_to_list(filters.away_team)

    # Case: Both home_team and away_team are provided
    if home_teams and away_teams:
        if len(set(home_teams)) == 1 and len(set(away_teams)) == 1 and set(home_teams) == set(away_teams):
            # Scenario 1: All games involving any of the teams
            filters_list.append(
                or_(
                    Game.home_team.in_(home_teams),
                    Game.away_team.in_(away_teams)
                )
            )
        elif len(home_teams) == 1 and len(away_teams) == 1:
            # Scenario 2: Specific home vs away matchup
            filters_list.append(
                and_(
                    Game.home_team == home_teams[0],
                    Game.away_team == away_teams[0]
                )
            )
        else:
            # Scenario 3: All matchups between these two teams, any home/away
            filters_list.append(
                or_(
                    and_(
                        Game.home_team.in_(home_teams),
                        Game.away_team.in_(away_teams)
                    ),
                    and_(
                        Game.home_team.in_(away_teams),
                        Game.away_team.in_(home_teams)
                    )
                )
            )
    elif home_teams:
        # Case: Only home_team(s) provided
        filters_list.append(Game.home_team.in_(home_teams))
    elif away_teams:
        # Case: Only away_team(s) provided
        filters_list.append(Game.away_team.in_(away_teams))

    # Filter by HOME TEAM ABBREVIATION and AWAY TEAM ABBREVIATION
    home_abbreviations = normalize_to_list(filters.home_abbreviation)
    away_abbreviations = normalize_to_list(filters.away_abbreviation)

    # Case: Both home_abbreviation and away_abbreviation are provided
    if home_abbreviations and away_abbreviations:
        if len(set(home_abbreviations)) == 1 and len(set(away_abbreviations)) == 1 and set(home_abbreviations) == set(away_abbreviations):
            # Scenario 1: All games involving any of the teams
            filters_list.append(
                or_(
                    Game.home_abbreviation.in_(home_abbreviations),
                    Game.away_abbreviation.in_(away_abbreviations)
                )
            )
        elif len(home_abbreviations) == 1 and len(away_abbreviations) == 1:
            # Scenario 2: Specific home vs away matchup
            filters_list.append(
                and_(
                    Game.home_abbreviation == home_abbreviations[0],
                    Game.away_abbreviation == away_abbreviations[0]
                )
            )
        else:
            # Scenario 3: All matchups between these two teams, any home/away
            filters_list.append(
                or_(
                    and_(
                        Game.home_abbreviation.in_(home_abbreviations),
                        Game.away_abbreviation.in_(away_abbreviations)
                    ),
                    and_(
                        Game.home_abbreviation.in_(away_abbreviations),
                        Game.away_abbreviation.in_(home_abbreviations)
                    )
                )
            )
    elif home_abbreviations:
        # Case: Only home_abbreviation(s) provided
        filters_list.append(Game.home_abbreviation.in_(home_abbreviations))
    elif away_abbreviations:
        # Case: Only away_abbreviation(s) provided
        filters_list.append(Game.away_abbreviation.in_(away_abbreviations))

    # Filter by HOME TEAM DIVISION and AWAY TEAM DIVISION
    home_divisions = normalize_to_list(filters.home_division)
    away_divisions = normalize_to_list(filters.away_division)

    if home_divisions and away_divisions:
        filters_list.append(
            and_(
                Game.home_division.in_(home_divisions),
                Game.away_division.in_(away_divisions)
            )
        )
    elif home_divisions:
        filters_list.append(Game.home_division.in_(home_divisions))
    elif away_divisions:
        filters_list.append(Game.away_division.in_(away_divisions))

    # Filter by DIVISIONAL
    if filters.divisional is not None:
        filters_list.append(Game.divisional == filters.divisional)

    # Filter by HOME SCORE
    if filters.home_score:
        if isinstance(filters.home_score, int):
            filters_list.append(Game.home_score == filters.home_score)
        else:
            filters_list.append(Game.home_score.in_(filters.home_score))

    # Filter by a HOME SCORE RANGE
    if filters.min_home_score and filters.max_home_score:
        filters_list.append(Game.home_score.between(filters.min_home_score, filters.max_home_score))
    elif filters.min_home_score:
        filters_list.append(Game.home_score >= filters.min_home_score)
    elif filters.max_home_score:
        filters_list.append(Game.home_score <= filters.max_home_score)

    # Filter by AWAY SCORE
    if filters.away_score:
        if isinstance(filters.away_score, int):
            filters_list.append(Game.away_score == filters.away_score)
        else:
            filters_list.append(Game.away_score.in_(filters.away_score))

    # Filter by a AWAY SCORE RANGE
    if filters.min_away_score and filters.max_away_score:
        filters_list.append(Game.away_score.between(filters.min_away_score, filters.max_away_score))
    elif filters.min_away_score:
        filters_list.append(Game.away_score >= filters.min_away_score)
    elif filters.max_away_score:
        filters_list.append(Game.away_score <= filters.max_away_score)

    # Filter by COMBINED SCORE
    if filters.combined_score:
        if isinstance(filters.combined_score, int):
            filters_list.append(Game.combined_score == filters.combined_score)
        else:
            filters_list.append(Game.combined_score.in_(filters.combined_score))
    
    # Filter by a COMBINED SCORE RANGE
    if filters.min_combined_score and filters.max_combined_score:
        filters_list.append(Game.combined_score.between(filters.min_combined_score, filters.max_combined_score))
    elif filters.min_combined_score:
        filters_list.append(Game.combined_score >= filters.min_combined_score)
    elif filters.max_combined_score:
        filters_list.append(Game.combined_score <= filters.max_combined_score)

    # Filter by TIE
    if filters.tie is not None:
        filters_list.append(Game.tie == filters.tie)

    # Filter by WINNER
    if filters.winner:
        if isinstance(filters.winner, str):
            filters_list.append(Game.winner == filters.winner)
        else:
            filters_list.append(Game.winner.in_(filters.winner))

    # Filter by LOSER
    if filters.loser:
        if isinstance(filters.loser, str):
            filters_list.append(Game.loser == filters.loser)
        else:
            filters_list.append(Game.loser.in_(filters.loser))

    # Filter by SPREAD
    if filters.spread:
        if isinstance(filters.spread, float):
            filters_list.append(Game.spread == filters.spread)
        else:
            filters_list.append(Game.spread.in_(filters.spread))

    # Filter by a SPREAD RANGE
    if filters.min_spread and filters.max_spread:
        filters_list.append(Game.spread.between(filters.min_spread, filters.max_spread))
    elif filters.min_spread:
        filters_list.append(Game.spread >= filters.min_spread)
    elif filters.max_spread:
        filters_list.append(Game.spread <= filters.max_spread)

    # Filter by HOME SPREAD
    if filters.home_spread:
        if isinstance(filters.home_spread, float):
            filters_list.append(Game.home_spread == filters.home_spread)
        else:
            filters_list.append(Game.home_spread.in_(filters.home_spread))

    # Filter by a HOME SPREAD RANGE
    if filters.min_home_spread and filters.max_home_spread:
        filters_list.append(Game.home_spread.between(filters.min_home_spread, filters.max_home_spread))
    elif filters.min_home_spread:
        filters_list.append(Game.home_spread >= filters.min_home_spread)
    elif filters.max_home_spread:
        filters_list.append(Game.home_spread <= filters.max_home_spread)

    # Filter by HOME SPREAD RESULT
    if filters.home_spread_result:
        if isinstance(filters.home_spread_result, int):
            filters_list.append(Game.home_spread_result == filters.home_spread_result)
        else:
            filters_list.append(Game.home_spread_result.in_(filters.home_spread_result))

    # Filter by a HOME SPREAD RESULT RANGE
    if filters.min_home_spread_result and filters.max_home_spread_result:
        filters_list.append(Game.home_spread_result.between(filters.min_home_spread_result, filters.max_home_spread_result))
    elif filters.min_home_spread_result:
        filters_list.append(Game.home_spread_result >= filters.min_home_spread_result)
    elif filters.max_home_spread_result:
        filters_list.append(Game.home_spread_result <= filters.max_home_spread_result)

    # Filter by AWAY SPREAD
    if filters.away_spread:
        if isinstance(filters.away_spread, float):
            filters_list.append(Game.away_spread == filters.away_spread)
        else:
            filters_list.append(Game.away_spread.in_(filters.away_spread))

    # Filter by a AWAY SPREAD RANGE
    if filters.min_away_spread and filters.max_away_spread:
        filters_list.append(Game.away_spread.between(filters.min_away_spread, filters.max_away_spread))
    elif filters.min_away_spread:
        filters_list.append(Game.away_spread >= filters.min_away_spread)
    elif filters.max_away_spread:
        filters_list.append(Game.away_spread <= filters.max_away_spread)

    # Filter by AWAY SPREAD RESULT
    if filters.away_spread_result:
        if isinstance(filters.away_spread_result, int):
            filters_list.append(Game.away_spread_result == filters.away_spread_result)
        else:
            filters_list.append(Game.away_spread_result.in_(filters.away_spread_result))

    # Filter by a AWAY SPREAD RESULT RANGE
    if filters.min_away_spread_result and filters.max_away_spread_result:
        filters_list.append(Game.away_spread_result.between(filters.min_away_spread_result, filters.max_away_spread_result))
    elif filters.min_away_spread_result:
        filters_list.append(Game.away_spread_result >= filters.min_away_spread_result)
    elif filters.max_away_spread_result:
        filters_list.append(Game.away_spread_result <= filters.max_away_spread_result)

    # Filter by SPREAD PUSH
    if filters.spread_push is not None:
        filters_list.append(Game.spread_push == filters.spread_push)

    # Filter by PICKEM
    if filters.pk is not None:
        filters_list.append(Game.pk == filters.pk)

    # Filter by TOTAL
    if filters.total:
        if isinstance(filters.total, float):
            filters_list.append(Game.total == filters.total)
        else:
            filters_list.append(Game.total.in_(filters.total))

    # Filter by a TOTAL RANGE
    if filters.min_total and filters.max_total:
        filters_list.append(Game.total.between(filters.min_total, filters.max_total))
    elif filters.min_total:
        filters_list.append(Game.total >= filters.min_total)
    elif filters.max_total:
        filters_list.append(Game.total <= filters.max_total)

    # Filter by TOTAL PUSH
    if filters.total_push is not None:
        filters_list.append(Game.total_push == filters.total_push)

    # Filter by HOME FAVORITE
    if filters.home_favorite is not None:
        filters_list.append(Game.home_favorite == filters.home_favorite)
    # Filter by AWAY FAVORITE
    if filters.away_favorite is not None:
        filters_list.append(Game.away_favorite == filters.away_favorite)
    # Filter by HOME UNDERDOG
    if filters.home_underdog is not None:
        filters_list.append(Game.home_underdog == filters.home_underdog)
    # Filter by AWAY UNDERDOG
    if filters.away_underdog is not None:
        filters_list.append(Game.away_underdog == filters.away_underdog)

    # Filter by HOME WIN
    if filters.home_win is not None:
        filters_list.append(Game.home_win == filters.home_win)
    # Filter by AWAY WIN
    if filters.away_win is not None:
        filters_list.append(Game.away_win == filters.away_win)
    # Filter by FAVORITE WIN
    if filters.favorite_win is not None:
        filters_list.append(Game.favorite_win == filters.favorite_win)
    # Filter by UNDERDOG WIN
    if filters.underdog_win is not None:
        filters_list.append(Game.underdog_win == filters.underdog_win)
    # Filter by HOME FAVORITE WIN
    if filters.home_favorite_win is not None:
        filters_list.append(Game.home_favorite_win == filters.home_favorite_win)
    # Filter by AWAY FAVORITE WIN
    if filters.away_favorite_win is not None:
        filters_list.append(Game.away_favorite_win == filters.away_favorite_win)
    # Filter by HOME UNDERDOG WIN
    if filters.home_underdog_win is not None:
        filters_list.append(Game.home_underdog_win == filters.home_underdog_win)
    # Filter by AWAY UNDERDOG WIN
    if filters.away_underdog_win is not None:
        filters_list.append(Game.away_underdog_win == filters.away_underdog_win)

    # Filter by HOME COVER
    if filters.home_cover is not None:
        filters_list.append(Game.home_cover == filters.home_cover)
    # Filter by AWAY COVER
    if filters.away_cover is not None:
        filters_list.append(Game.away_cover == filters.away_cover)
    # Filter by FAVORITE COVER
    if filters.favorite_cover is not None:
        filters_list.append(Game.favorite_cover == filters.favorite_cover)
    # Filter by UNDERDOG COVER
    if filters.underdog_cover is not None:
        filters_list.append(Game.underdog_cover == filters.underdog_cover)
    # Filter by HOME FAVORITE COVER
    if filters.home_favorite_cover is not None:
        filters_list.append(Game.home_favorite_cover == filters.home_favorite_cover)
    # Filter by AWAY FAVORITE COVER
    if filters.away_favorite_cover is not None:
        filters_list.append(Game.away_favorite_cover == filters.away_favorite_cover)
    # Filter by HOME UNDERDOG COVER
    if filters.home_underdog_cover is not None:
        filters_list.append(Game.home_underdog_cover == filters.home_underdog_cover)
    # Filter by AWAY UNDERDOG COVER
    if filters.away_underdog_cover is not None:
        filters_list.append(Game.away_underdog_cover == filters.away_underdog_cover)

    # Filter by OVER HIT
    if filters.over_hit is not None:
        filters_list.append(Game.over_hit == filters.over_hit)
    # Filter by UNDER HIT
    if filters.under_hit is not None:
        filters_list.append(Game.under_hit == filters.under_hit)

    # Apply filters to the query
    if filters_list:
        query = query.filter(*filters_list)

    total_count = query.order_by(None).count()

    # Sorting
    valid_sort_fields = {c_attr.key for c_attr in inspect(Game).mapper.column_attrs}
    if filters.sort_by:
        sort_columns = []
        for sort in filters.sort_by:
            if sort.field not in valid_sort_fields:
                raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort.field}")

            if sort.field == "month":
                month_case = case(
                    (Game.month == "January", 1),
                    (Game.month == "February", 2),
                    (Game.month == "March", 3),
                    (Game.month == "April", 4),
                    (Game.month == "May", 5),
                    (Game.month == "June", 6),
                    (Game.month == "July", 7),
                    (Game.month == "August", 8),
                    (Game.month == "September", 9),
                    (Game.month == "October", 10),
                    (Game.month == "November", 11),
                    (Game.month == "December", 12),
                    (Game.month == None, 13),
                    else_=14
                )
                sort_columns.append(month_case.desc() if sort.order == "desc" else month_case.asc())
            elif sort.field == 'day_of_week':
                day_case = case(
                    (Game.day_of_week == "Monday", 1),
                    (Game.day_of_week == "Tuesday", 2),
                    (Game.day_of_week == "Wednesday", 3),
                    (Game.day_of_week == "Thursday", 4),
                    (Game.day_of_week == "Friday", 5),
                    (Game.day_of_week == "Saturday", 6),
                    (Game.day_of_week == "Sunday", 7),
                    (Game.day_of_week == None, 8),
                    else_=9
                )
                sort_columns.append(day_case.desc() if sort.order == "desc" else day_case.asc())
            else:
                col = getattr(Game, sort.field)
                sort_columns.append(col.desc() if sort.order == "desc" else col.asc())

        if sort_columns:
            query = query.order_by(*sort_columns)

    # Pagination
    if filters.limit:
        query = query.limit(filters.limit)
    if filters.offset:
        query = query.offset(filters.offset)

    games = query.all()

    if not games:
        return []
    return {
        "limit": filters.limit,
        "offset": filters.offset,
        "count": len(games),
        "total_count": total_count,
        "results": games,
    }