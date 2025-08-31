from sqlalchemy.orm import Session
from sqlalchemy import case, and_, or_
from sqlalchemy.inspection import inspect
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Literal
from fastapi import APIRouter, HTTPException, Depends
from app.models.trend import Trend
from app.database.connection import get_connection
from app.enums.trend_enums import CategoryEnum, MonthEnum, DayOfWeekEnum

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

##################################
######## FILTER OBJECTS ##########
##################################

class SortField(BaseModel):
    field: str
    order: Literal["asc", "desc"] = "asc"

class SpreadFilter(BaseModel):
    exact: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="List of exact spread strings to match, e.g. ['7.0', '10.5']"
    )
    or_less: Optional[Union[int, List[int]]] = Field(
        default=None,
        description="Filter for 'X or less' spread values, e.g. 3 → '3 or less' or [10, 11, 12] → ['10 or less', '11 or less', '12 or less']"
    )
    or_more: Optional[Union[int, List[int]]] = Field(
        default=None,
        description="Filter for 'X or more' spread values, e.g. 10 → '10 or more' or [7, 8, 9] → ['7 or more', '8 or more', '9 or more']"
    )

class TotalFilter(BaseModel):
    exact: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="List of exact total strings to match, e.g. ['45 or less', '50 or more']"
    )
    or_less: Optional[Union[int, List[int]]] = Field(
        default=None,
        description="Filter for 'X or less' total values, must be 30–60 in steps of 5, e.g. 50 → '50 or less' or [35, 40, 45] → ['35 or less', '40 or less', '45 or less']"
    )
    or_more: Optional[Union[int, List[int]]] = Field(
        default=None,
        description="Filter for 'X or more' total values, must be 30–60 in steps of 5, e.g. 40 → '40 or more' or [35, 40, 45] → ['35 or more', '40 or more', '45 or more']"
    )

class SeasonFilter(BaseModel):
    exact: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Exact seasons string(s), e.g. 'since 2015-2016'"
    )
    since_or_later: Optional[str] = Field(
        default=None,
        description="Return trends from this seasons and later"
    )
    since_or_earlier: Optional[str] = Field(
        default=None,
        description="Return trends from this seasons and earlier"
    )

class TrendFilter(BaseModel):

    ##################################
    ###### PAGINATION FILTERS ########
    ##################################

    limit: Optional[int] = Field(
        5000,
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

    # VALIDATE LIMIT is between 1 and 5000000
    @validator("limit", pre=True)
    def validate_limit(cls, value):
        if not isinstance(value, int) or not (1 <= value <= 5000000):
            raise ValueError("Limit must be an integer between 1 and 5000000")
        return value
    # VALIDATE OFFSET is greater than 0
    @validator("offset", pre=True)
    def validate_offset(cls, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("Offset must be an integer greater than or equal to 0")
        return value
    
    ##################################
    ######## TREND ID FILTERS ########
    ##################################

    trend_id: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by trend ID(s). The format is either a list of strings or a single string of comma separated values of filters for trends in the following order:" \
            "category,month,day of week,divisional,spread,total,seasons since."
            "Example: 'home ats,October,Thursday,False,8 or less,40 or less,since 2008-2009'."
        )
    )

    # VALIDATE TREND IDs are in a comma separated list of filters
    @validator("trend_id", pre=True)
    def validate_trend_id(cls, value):
        if value is None:
            return value

        if isinstance(value, str):
            values = [v.strip() for v in value.split(",")]
            if len(values) != 7:
                raise ValueError(
                    "If trend_id is a string, it must have exactly 7 comma-separated values."
                )
            print("TREND ID is a single string.")
            return value

        elif isinstance(value, list):
            for v in value:
                if not isinstance(v, str):
                    raise ValueError("All items in trend_id list must be strings.")
                values = [x.strip() for x in v.split(",")]
                if len(values) != 7:
                    raise ValueError(
                        f"Each trend_id in the list must have exactly 7 comma-separated values. Got: {values}"
                    )
            print("TREND ID is a list of strings.")
            return value

        raise ValueError("trend_id must be either a string or a list of strings.")
    

    ####################################
    ####### CATEGORY FILTERS ###########
    ####################################

    category: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by category. Can be a single category or a list of categories from the following options:" \
            "home outright, away outright, favorite outright, underdog outright, home favorite outright, away underdog outright, away favorite outright, home underdog outright, home ats, away ats, favorite ats, underdog ats, home favorite ats, away underdog ats, away favorite ats, home underdog ats, over, under." \
            "Example: 'home ats' or ['home outright, away outright']."
        )
    )

    # VALIDATE CATEGORY is in the CategoryEnum format
    @validator("category", pre=True)
    def validate_category(cls, value):
        if value is None:
            return value

        if isinstance(value, str):
            # Validate a single category
            value = value.lower()
            if value not in CategoryEnum._value2member_map_:
                raise ValueError(
                    f"Invalid category: {value}. Must be one of {list(CategoryEnum._value2member_map_.keys())}."
                )
        if isinstance(value, list):
            # Validate a list of categories
            for v in value:
                v = v.lower()
                if v not in CategoryEnum._value2member_map_:
                    raise ValueError(
                        f"Invalid category: {v}. Must be one of {list(CategoryEnum._value2member_map_.keys())}."
                    )
        return value
    

    ############################
    ####### MONTH FILTERS ######
    ############################

    month: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by month. Can be a single month, a list of months, or 'None' (as a string to filter for NULL values). "
            "Example: 'January' or ['January', 'February'] or 'None'."
        )
    )
    start_month: Optional[str] = Field(
        None,
        description="Start month for filtering trends. Example: 'January'."
    )
    end_month: Optional[str] = Field(
        None,
        description="End month for filtering trends. Example: 'December'."
    )

    # VALIDATES MONTHS are in the MonthEnum format
    @validator("month", pre=True)
    def validate_month(cls, value):
        if value == "None":
            return "None"
        if isinstance(value, str):
            value = value.capitalize()
            if value not in MonthEnum._value2member_map_:
                raise ValueError(f"{value} must be one of {list(MonthEnum._value2member_map_.keys())} or 'None'")
            return value
        if isinstance(value, list):
            normalized = []
            for v in value:
                v_cap = v.capitalize() if isinstance(v, str) else v
                if v_cap != "None" and v_cap not in MonthEnum._value2member_map_:
                    raise ValueError(f"Each month in {value} must be one of {list(MonthEnum._value2member_map_.keys())} or 'None'")
                normalized.append(v_cap)
            return normalized
        return value
    
    @validator("start_month", "end_month", pre=True)
    def validate_start_end_month(cls, value):
        if value == "None":
            raise ValueError(f"{value} cannot be 'None'")
        if isinstance(value, str):
            value = value.capitalize()
            if value not in MonthEnum._value2member_map_:
                raise ValueError(f"{value} must be one of {list(MonthEnum._value2member_map_.keys())}")
            return value
        return value
    

    ###############################
    ##### DAY OF WEEK FILTERS #####
    ###############################

    day_of_week: Optional[Union[str, List[str]]] = Field(
        None,
        description=(
            "Filter by day of the week. Can be a single day, a list of days, or 'None' (as a string to filter for NULL values). "
            "Example: 'Monday' or ['Monday', 'Tuesday'] or 'None'."
        )
    )
    
    # VALIDATE DAY OF WEEK are in the DayOfWeekEnum format
    @validator("day_of_week", pre=True)
    def validate_day_of_week(cls, value):
        valid_days = set(DayOfWeekEnum._value2member_map_.keys())

        def is_valid_day(day):
            return day in valid_days or day == "None"

        if isinstance(value, str):
            value = value.capitalize()
            if not is_valid_day(value):
                raise ValueError(f"{value} must be one of {list(valid_days)} or 'None'")
            return value

        if isinstance(value, list):
            value = [str(day).capitalize() if isinstance(day, str) else day for day in value]
            for day in value:
                if not is_valid_day(day):
                    raise ValueError(f"Each day in {value} must be one of {list(valid_days)} or 'None'")
            return value

        return value
    

    ###########################
    ### DIVISIONAL FILTERS ####
    ###########################

    divisional: Optional[Union[bool, Literal["None"]]] = Field(
        None,
        description="Filter for divisional trends. Can be True, False, or 'None' (as a string to filter for NULL values)."
    )

    # VALIDATE DIVISIONAL is a boolean or "None"
    @validator("divisional", pre=True)
    def validate_divisional(cls, value):
        if value == "None":
            return "None"
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        raise ValueError("Divisional must be True, False, or 'None' (as a string)")
    

    #################################
    ####### SPREAD FILTERS ##########
    #################################

    spread: Optional[Union[SpreadFilter, str]] = Field(
        None,
        description=(
            "Filter by spread. Can be 'None' to get rows where spread is null, or a structured filter like "
            "{'exact': '3.0'} or {'or_more': 6} or {'or_less': 10} or {'or_more': [7, 8, 9]} or {'or_less': [10, 11, 12]} or "
            "{'exact': ['7.5', '1.5'], 'or_more': 12} or "
            "{'exact': ['7.0', '10.5'], 'or_less': [3, 4], 'or_more': [10, 11]}"
        )
    )

    # VALIDATE SPREAD is in the SPREAD_VALUES format
    @validator("spread")
    def validate_spread(cls, spread):
        if spread:
            SPREAD_VALUES = {f"{x:.1f}" for x in [i * 0.5 for i in range(0, 55)]}
            SPREAD_VALUES.update({f"{i} or less" for i in range(1, 15)})
            SPREAD_VALUES.update({f"{i} or more" for i in range(1, 15)})
            SPREAD_VALUES.add("None")

            if isinstance(spread, str):
                if spread == "None":
                    return "None"
                raise ValueError(
                    f"Invalid spread value: '{spread}'. Allowed values are structured objects or the string 'None'."
                )

            elif isinstance(spread, SpreadFilter):
                # exact values
                if spread.exact:
                    exact_list = [spread.exact] if isinstance(spread.exact, str) else spread.exact
                    for val in exact_list:
                        if val not in SPREAD_VALUES:
                            raise ValueError(
                                f"Invalid spread value in 'exact': '{val}'. Allowed: '0.0'-'27.0' by 0.5, 'X or less/more' (1-14), or 'None'."
                            )

                # or_less values - can be int or list of ints
                if spread.or_less is not None:
                    or_less_list = [spread.or_less] if isinstance(spread.or_less, int) else spread.or_less
                    for val in or_less_list:
                        if not (1 <= val <= 14):
                            raise ValueError(f"'or_less' value {val} must be between 1 and 14")

                # or_more values - can be int or list of ints
                if spread.or_more is not None:
                    or_more_list = [spread.or_more] if isinstance(spread.or_more, int) else spread.or_more
                    for val in or_more_list:
                        if not (1 <= val <= 14):
                            raise ValueError(f"'or_more' value {val} must be between 1 and 14")

        return spread
    

    #################################
    ####### TOTAL FILTERS ###########
    #################################

    total: Optional[Union[TotalFilter, str]] = Field(
        None,
        description=(
            "Filter by total. Can be 'None' for null totals, or a filter like "
            "{'exact': '45 or more'} or {'or_less': 50} or {'or_more': [35, 40]} or {'or_less': [45, 50]} or "
            "{'exact': ['30 or more', '40 or less'], 'or_more': 55}, etc."
        )
    )

    @validator("total")
    def validate_total(cls, total):
        if total:
            TOTAL_VALUES = {f"{i} or less" for i in range(30, 65, 5)}
            TOTAL_VALUES.update({f"{i} or more" for i in range(30, 65, 5)})
            TOTAL_VALUES.add("None")

            if isinstance(total, str):
                if total == "None":
                    return "None"
                raise ValueError(
                    f"Invalid total value: '{total}'. Allowed values are structured filters or 'None'."
                )

            elif isinstance(total, TotalFilter):
                if total.exact:
                    exact_list = [total.exact] if isinstance(total.exact, str) else total.exact
                    for val in exact_list:
                        if val not in TOTAL_VALUES:
                            raise ValueError(
                                f"Invalid total value in 'exact': '{val}'. Allowed values: 30–60 in steps of 5 for 'X or less'/'X or more', or 'None'."
                            )

                # or_less values - can be int or list of ints
                if total.or_less is not None:
                    or_less_list = [total.or_less] if isinstance(total.or_less, int) else total.or_less
                    for val in or_less_list:
                        if val not in range(30, 65, 5):
                            raise ValueError(f"'or_less' value {val} must be one of: 30, 35, 40, 45, 50, 55, 60")

                # or_more values - can be int or list of ints
                if total.or_more is not None:
                    or_more_list = [total.or_more] if isinstance(total.or_more, int) else total.or_more
                    for val in or_more_list:
                        if val not in range(30, 65, 5):
                            raise ValueError(f"'or_more' value {val} must be one of: 30, 35, 40, 45, 50, 55, 60")

        return total

        return total
    

    #################################
    ####### SEASONS FILTERS #########
    #################################

    seasons: Optional[SeasonFilter] = Field(
        None,
        description=(
            "Filter by seasons. Can be exact seasons(s), or a range like "
            "{'since_or_later': 'since 2012-2013'}, "
            "{'since_or_earlier': 'since 2020-2021'}, etc."
        )
    )

    @validator("seasons")
    def validate_season(cls, seasons):
        if seasons:
            VALID_SEASONS = [f"since {year}-{year + 1}" for year in range(2006, 2026)]

            # Validate exact
            if seasons.exact:
                exact_list = [seasons.exact] if isinstance(seasons.exact, str) else seasons.exact
                for s in exact_list:
                    if s not in VALID_SEASONS:
                        raise ValueError(f"Invalid seasons in 'exact': '{s}'. Must be one of {VALID_SEASONS}.")
                seasons.exact = exact_list

            # Validate since_or_later / since_or_earlier
            if seasons.since_or_later and seasons.since_or_later not in VALID_SEASONS:
                raise ValueError(f"'since_or_later' value '{seasons.since_or_later}' is not valid. Must be one of {VALID_SEASONS}.")
            if seasons.since_or_earlier and seasons.since_or_earlier not in VALID_SEASONS:
                raise ValueError(f"'since_or_earlier' value '{seasons.since_or_earlier}' is not valid. Must be one of {VALID_SEASONS}.")

        return seasons


    ##################################
    ######## WINS FILTERS ############
    ##################################

    wins: Optional[Union[int, List[int]]] = Field(
        None,
        description="Exact win count or list of win counts. Example: 20 or [5, 10, 25]."
    )
    min_wins: Optional[int] = Field(
        None,
        description="Minimum number of wins (inclusive), between 1 and 5000."
    )
    max_wins: Optional[int] = Field(
        None,
        description="Maximum number of wins (inclusive), between 1 and 5000."
    )

    # VALIDATE WINS is between 1 and 5000
    @validator("wins", "min_wins", "max_wins", pre=True)
    def validate_wins(cls, value):
        def is_valid(val):
            return isinstance(val, int) and 1 <= val <= 5000

        if isinstance(value, int):
            if not is_valid(value):
                raise ValueError("Wins must be an integer between 1 and 5000")
        elif isinstance(value, list):
            for v in value:
                if not is_valid(v):
                    raise ValueError("Each value in wins list must be an integer between 1 and 5000")
        elif value is not None:
            raise ValueError("Wins must be an int or a list of ints between 1 and 5000")
        return value
    

    ###################################
    ######### LOSSES FILTERS ##########
    ###################################

    losses: Optional[Union[int, List[int]]] = Field(
        None,
        description="Exact loss count or list of loss counts. Example: 20 or [5, 10, 25]."
    )
    min_losses: Optional[int] = Field(
        None,
        description="Minimum number of losses (inclusive), between 1 and 5000."
    )
    max_losses: Optional[int] = Field(
        None,
        description="Maximum number of losses (inclusive), between 1 and 5000."
    )

    # VALIDATE LOSSES is between 1 and 5000
    @validator("losses", "min_losses", "max_losses", pre=True)
    def validate_losses(cls, value):
        def is_valid(val):
            return isinstance(val, int) and 1 <= val <= 5000

        if isinstance(value, int):
            if not is_valid(value):
                raise ValueError("Losses must be an integer between 1 and 5000")
        elif isinstance(value, list):
            for v in value:
                if not is_valid(v):
                    raise ValueError("Each value in losses list must be an integer between 1 and 5000")
        elif value is not None:
            raise ValueError("Losses must be an int or a list of ints between 1 and 5000")
        return value
    

    ################################
    ###### PUSHES FILTERS ##########
    ################################

    pushes: Optional[Union[int, List[int]]] = Field(
        None,
        description="Exact push count or list of push counts. Example: 20 or [5, 10, 25]."
    )
    min_pushes: Optional[int] = Field(
        None,
        description="Minimum number of pushes (inclusive), between 1 and 5000."
    )
    max_pushes: Optional[int] = Field(
        None,
        description="Maximum number of pushes (inclusive), between 1 and 5000."
    )

    # VALIDATE PUSHES is between 1 and 5000
    @validator("pushes", "min_pushes", "max_pushes", pre=True)
    def validate_pushes(cls, value):
        def is_valid(val):
            return isinstance(val, int) and 1 <= val <= 5000

        if isinstance(value, int):
            if not is_valid(value):
                raise ValueError("Pushes must be an integer between 1 and 5000")
        elif isinstance(value, list):
            for v in value:
                if not is_valid(v):
                    raise ValueError("Each value in pushes list must be an integer between 1 and 5000")
        elif value is not None:
            raise ValueError("Pushes must be an int or a list of ints between 1 and 5000")
        return value
    
    ################################
    ### TOTAL GAMES FILTERS ########
    ################################

    total_games: Optional[Union[int, List[int]]] = Field(
        None,
        description="Exact total games count or list of total games counts. Example: 20 or [5, 10, 25]."
    )
    min_total_games: Optional[int] = Field(
        None,
        description="Minimum number of total games (inclusive), between 1 and 10000."
    )
    max_total_games: Optional[int] = Field(
        None,
        description="Maximum number of total games (inclusive), between 1 and 10000."
    )

    # VALIDATE TOTAL GAMES is between 1 and 10000
    @validator("total_games", "min_total_games", "max_total_games", pre=True)
    def validate_total_games(cls, value):
        def is_valid(val):
            return isinstance(val, int) and 1 <= val <= 10000

        if isinstance(value, int):
            if not is_valid(value):
                raise ValueError("Total games must be an integer between 1 and 10000")
        elif isinstance(value, list):
            for v in value:
                if not is_valid(v):
                    raise ValueError("Each value in total games list must be an integer between 1 and 10000")
        elif value is not None:
            raise ValueError("Total games must be an int or a list of ints between 1 and 10000")
        return value
    

    ##################################
    ##### WIN PERCENTAGE FILTERS #####
    ##################################

    win_percentage: Optional[Union[float, List[float]]] = Field(
        None,
        description="Exact win percentage or list of win percentages. Example: 75 or [50.3, 62.12, 100]."
    )
    min_win_percentage: Optional[float] = Field(
        None,
        description="Minimum win percentage (inclusive), between 0 and 100."
    )
    max_win_percentage: Optional[float] = Field(
        None,
        description="Maximum win percentage (inclusive), between 0 and 100."
    )

    # VALIDATE WIN PERCENTAGE is between 0 and 100
    @validator("win_percentage", "min_win_percentage", "max_win_percentage", pre=True)
    def validate_win_percentage(cls, value):
        def is_valid(val):
            return isinstance(val, (int, float)) and 0 <= val <= 100

        if isinstance(value, (int, float)):
            if not is_valid(value):
                raise ValueError("Win percentage must be a number between 0 and 100")
        elif isinstance(value, list):
            for v in value:
                if not is_valid(v):
                    raise ValueError("Each value in win percentage list must be a number between 0 and 100")
        elif value is not None:
            raise ValueError("Win percentage must be a number or a list of numbers between 0 and 100")
        return value
    

    ##################################
    ####### SORTING FILTERS ##########
    ##################################
    sort_by: Optional[List[SortField]] = Field(
        [
            SortField(field="win_percentage", order="desc"),
            SortField(field="total_games", order="desc"),
        ],
        description=(
            "Sort the results by one or more fields. Can be a single field as a string or dictionary (default is ascending), or a list of fields and directions as dictionaries. "
            "Example: 'month', ['wins', 'total_games'], {'field': 'win_percentage', 'order': 'desc'}, [{'field': 'win_percentage', 'order': 'desc'}, {'field': 'total_games', 'order': 'desc'}]."
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
            "Invalid format for 'sort_by'. Expected a string (e.g. 'wins'), "
            "a list of strings (e.g. ['month', 'season']), an object with 'field' and optional 'order' (e.g. {'field': 'wins', 'order': 'asc'}), "
            "or a list of objects with 'field' and optional 'order' (e.g. [{'field': 'year', 'order': 'desc'}])."
        )

    

@router.post("/trends", summary="Retrieve trends with filters", tags=["Trends"])
def get_trends(filters: TrendFilter, db: Session = Depends(get_connection)):
    """
    Retrieve trends from the database based on the provided filters.

    - **trend_id**: Filter by trend ID(s). The format is a comma separated list of filters for trends in the following order: category,month,day of week,divisional,spread,total,seasons since (Ex: 'home ats,October,Thursday,False,8 or less,40 or less,since 2008-2009').
    - **category**: Filter by category. Can be a single category or a list of categories from the following options: home outright, away outright, favorite outright, underdog outright, home favorite outright, away underdog outright, away favorite outright, home underdog outright, home ats, away ats, favorite ats, underdog ats, home favorite ats, away underdog ats, away favorite ats, home underdog ats, over, under (Ex: 'home ats' or ['home outright', 'away outright']).
    - **month**: Filter by month. Can be a single month, a list of months, or 'None' (as a string to filter for NULL values) (Ex: 'January' or ['January', 'February'] or 'None').
    - **start_month**: Start month for filtering trends (Ex: January).
    - **end_month**: End month for filtering trends (Ex: December).
    - **day_of_week**: Filter by day of the week. Can be a single day, a list of days, or 'None' (as a string to filter for NULL values) (Ex: 'Monday' or ['Monday', 'Tuesday'] or 'None').
    - **divisional**: Filter for divisional trends. Can be True, False, or 'None' (as a string to filter for NULL values) (Ex: True or False or 'None').
    - **spread**: Filter by spread. Can be 'None' to get rows where spread is null, or a structured filter like {'exact': '3.0'} or {'or_more': 6} or {'or_less': 10} or {'or_more': [7, 8, 9]} or {'or_less': [10, 11, 12]} or {'exact': ['7.5', '1.5'], 'or_more': 12} or {'exact': ['7.0', '10.5'], 'or_less': [3, 4], 'or_more': [10, 11]}.
    - **total**: Filter by total. Can be 'None' for null totals, or a filter like {'exact': '45 or more'} or {'or_less': 50} or {'or_more': [35, 40]} or {'or_less': [45, 50]} or {'exact': ['30 or more', '40 or less'], 'or_more': 55}, etc.
    - **seasons**: Filter by seasons. Can be exact seasons(s), or a range like {'since_or_later': 'since 2012-2013'}, {'since_or_earlier': 'since 2020-2021'}, etc or a combination of both.
    - **wins**: Exact win count or list of win counts (Ex: 20 or [5, 10, 25]).
    - **min_wins**: Minimum number of wins (inclusive), between 1 and 5000 (Ex: 10).
    - **max_wins**: Maximum number of wins (inclusive), between 1 and 5000 (Ex: 100).
    - **losses**: Exact loss count or list of loss counts (Ex: 20 or [5, 10, 25]).
    - **min_losses**: Minimum number of losses (inclusive), between 1 and 5000 (Ex: 10).
    - **max_losses**: Maximum number of losses (inclusive), between 1 and 5000 (Ex: 100).
    - **pushes**: Exact push count or list of push counts (Ex: 20 or [5, 10, 25]).
    - **min_pushes**: Minimum number of pushes (inclusive), between 1 and 5000 (Ex: 10).
    - **max_pushes**: Maximum number of pushes (inclusive), between 1 and 5000 (Ex: 100).
    - **total_games**: Exact total games count or list of total games counts (Ex: 20 or [5, 10, 25]).
    - **min_total_games**: Minimum number of total games (inclusive), between 1 and 10000 (Ex: 10).
    - **max_total_games**: Maximum number of total games (inclusive), between 1 and 10000 (Ex: 100).
    - **win_percentage**: Exact win percentage or list of win percentages (Ex: 75 or [50.3, 62.12, 100]).
    - **min_win_percentage**: Minimum win percentage (inclusive), between 0 and 100 (Ex: 10).
    - **max_win_percentage**: Maximum win percentage (inclusive), between 0 and 100 (Ex: 100).
    - **limit**: Limit the number of results returned (Ex: 100).
    - **offset**: Offset the results returned (Ex: 0).
    - **sort_by**: Sort the results by one or more fields. Can be a single field as a string or dictionary (default is ascending), or a list of fields and directions as dictionaries (Ex: 'month', ['wins', 'total_games'], {'field': 'win_percentage', 'order': 'desc'}, [{'field': 'win_percentage', 'order': 'desc'}, {'field': 'total_games', 'order': 'desc'}]).
    """

    query = db.query(Trend)
    filters_list = []

    # Filter by TREND ID
    if filters.trend_id:
        if isinstance(filters.trend_id, str):
            filters_list.append(Trend.id_string == filters.trend_id)
        else:
            print(filters.trend_id)
            filters_list.append(Trend.id_string.in_(filters.trend_id))

    # Filter by CATEGORY
    if filters.category:
        if isinstance(filters.category, str):
            filters_list.append(Trend.category == filters.category)
        else:
            filters_list.append(Trend.category.in_(filters.category))

    # Filter by MONTH
    month_case = case(
        (Trend.month == "January", 1),
        (Trend.month == "February", 2),
        (Trend.month == "March", 3),
        (Trend.month == "April", 4),
        (Trend.month == "May", 5),
        (Trend.month == "June", 6),
        (Trend.month == "July", 7),
        (Trend.month == "August", 8),
        (Trend.month == "September", 9),
        (Trend.month == "October", 10),
        (Trend.month == "November", 11),
        (Trend.month == "December", 12),
        else_=0
    )

    # Handle month value or list (including "None")
    month_conditions = []
    if filters.month:
        if isinstance(filters.month, str):
            if filters.month == "None":
                month_conditions.append(Trend.month == None)
            else:
                month_conditions.append(Trend.month == filters.month)
        else:  # list
            values = [v for v in filters.month if v != "None"]
            if values:
                month_conditions.append(Trend.month.in_(values))
            if "None" in filters.month:
                month_conditions.append(Trend.month == None)

    # Handle start_month/end_month range
    range_condition = None
    if filters.start_month and filters.end_month:
        start = MONTH_MAPPING[filters.start_month]
        end = MONTH_MAPPING[filters.end_month]
        range_condition = and_(Trend.month != None, month_case.between(start, end))
    elif filters.start_month:
        start = MONTH_MAPPING[filters.start_month]
        range_condition = and_(Trend.month != None, month_case >= start)
    elif filters.end_month:
        end = MONTH_MAPPING[filters.end_month]
        range_condition = and_(Trend.month != None, month_case <= end)

    # Combine logic: OR between month filter and range
    if month_conditions and range_condition is not None:
        print("Combining month conditions with range condition")
        filters_list.append(or_(or_(*month_conditions), range_condition))
    elif month_conditions:
        print("Adding month conditions")
        filters_list.append(or_(*month_conditions))
    elif range_condition is not None:
        print("Adding range condition")
        filters_list.append(range_condition)

    # Filter by DAY OF WEEK
    if filters.day_of_week:
        if isinstance(filters.day_of_week, str):
            if filters.day_of_week == 'None':
                filters_list.append(Trend.day_of_week.is_(None))
            else:
                filters_list.append(Trend.day_of_week == filters.day_of_week)
        else:
            days = []
            include_null = False
            for day in filters.day_of_week:
                if day == 'None':
                    include_null = True
                else:
                    days.append(day)
            conditions = []
            if days:
                conditions.append(Trend.day_of_week.in_(days))
            if include_null:
                conditions.append(Trend.day_of_week.is_(None))
            filters_list.append(or_(*conditions))

    # Filter by DIVISIONAL
    if filters.divisional == "None":
        filters_list.append(Trend.divisional.is_(None))
    elif filters.divisional in (True, False):
        filters_list.append(Trend.divisional == filters.divisional)

    # Filter by SPREAD
    if filters.spread:
        spread_clauses = []

        if isinstance(filters.spread, str):
            if filters.spread == "None":
                spread_clauses.append(Trend.spread.is_(None))

        elif isinstance(filters.spread, SpreadFilter):
            if filters.spread.exact:
                exact_list = [filters.spread.exact] if isinstance(filters.spread.exact, str) else filters.spread.exact
                non_null_spreads = [s for s in exact_list if s != "None"]
                if non_null_spreads:
                    spread_clauses.append(Trend.spread.in_(non_null_spreads))
                if "None" in exact_list:
                    spread_clauses.append(Trend.spread.is_(None))

            if filters.spread.or_less is not None:
                or_less_list = [filters.spread.or_less] if isinstance(filters.spread.or_less, int) else filters.spread.or_less
                or_less_values = [f"{val} or less" for val in or_less_list]
                spread_clauses.append(Trend.spread.in_(or_less_values))

            if filters.spread.or_more is not None:
                or_more_list = [filters.spread.or_more] if isinstance(filters.spread.or_more, int) else filters.spread.or_more
                or_more_values = [f"{val} or more" for val in or_more_list]
                spread_clauses.append(Trend.spread.in_(or_more_values))

        if spread_clauses:
            filters_list.append(or_(*spread_clauses))

    # Filter by TOTAL
    if filters.total:
        total_clauses = []

        if isinstance(filters.total, str):
            if filters.total == "None":
                total_clauses.append(Trend.total.is_(None))

        elif isinstance(filters.total, TotalFilter):
            if filters.total.exact:
                exact_list = [filters.total.exact] if isinstance(filters.total.exact, str) else filters.total.exact
                non_null_totals = [t for t in exact_list if t != "None"]
                if non_null_totals:
                    total_clauses.append(Trend.total.in_(non_null_totals))
                if "None" in exact_list:
                    total_clauses.append(Trend.total.is_(None))

            if filters.total.or_less is not None:
                or_less_list = [filters.total.or_less] if isinstance(filters.total.or_less, int) else filters.total.or_less
                or_less_values = [f"{val} or less" for val in or_less_list]
                total_clauses.append(Trend.total.in_(or_less_values))

            if filters.total.or_more is not None:
                or_more_list = [filters.total.or_more] if isinstance(filters.total.or_more, int) else filters.total.or_more
                or_more_values = [f"{val} or more" for val in or_more_list]
                total_clauses.append(Trend.total.in_(or_more_values))

        if total_clauses:
            filters_list.append(or_(*total_clauses))

    # Filter by SEASONS
    if filters.seasons:
        season_clauses = []
        VALID_SEASONS = [f"since {year}-{year + 1}" for year in range(2006, 2026)]

        if filters.seasons.exact:
            season_clauses.append(Trend.seasons.in_(filters.seasons.exact))

        if filters.seasons.since_or_later:
            index = VALID_SEASONS.index(filters.seasons.since_or_later)
            season_clauses.append(Trend.seasons.in_(VALID_SEASONS[index:]))

        if filters.seasons.since_or_earlier:
            index = VALID_SEASONS.index(filters.seasons.since_or_earlier)
            season_clauses.append(Trend.seasons.in_(VALID_SEASONS[: index + 1]))

        if season_clauses:
            filters_list.append(or_(*season_clauses))

    # Filter by WINS
    if filters.wins:
        if isinstance(filters.wins, int):
            filters_list.append(Trend.wins == filters.wins)
        else:
            filters_list.append(Trend.wins.in_(filters.wins))

    if filters.min_wins is not None and filters.max_wins is not None:
        filters_list.append(Trend.wins.between(filters.min_wins, filters.max_wins))
    elif filters.min_wins is not None:
        filters_list.append(Trend.wins >= filters.min_wins)
    elif filters.max_wins is not None:
        filters_list.append(Trend.wins <= filters.max_wins)

    # Filter by LOSSES
    if filters.losses:
        if isinstance(filters.losses, int):
            filters_list.append(Trend.losses == filters.losses)
        else:
            filters_list.append(Trend.losses.in_(filters.losses))

    if filters.min_losses is not None and filters.max_losses is not None:
        filters_list.append(Trend.losses.between(filters.min_losses, filters.max_losses))
    elif filters.min_losses is not None:
        filters_list.append(Trend.losses >= filters.min_losses)
    elif filters.max_losses is not None:
        filters_list.append(Trend.losses <= filters.max_losses)

    # Filter by PUSHES
    if filters.pushes:
        if isinstance(filters.pushes, int):
            filters_list.append(Trend.pushes == filters.pushes)
        else:
            filters_list.append(Trend.pushes.in_(filters.pushes))

    if filters.min_pushes is not None and filters.max_pushes is not None:
        filters_list.append(Trend.pushes.between(filters.min_pushes, filters.max_pushes))
    elif filters.min_pushes is not None:
        filters_list.append(Trend.pushes >= filters.min_pushes)
    elif filters.max_pushes is not None:
        filters_list.append(Trend.pushes <= filters.max_pushes)

    # Filter by TOTAL GAMES
    if filters.total_games:
        if isinstance(filters.total_games, int):
            filters_list.append(Trend.total_games == filters.total_games)
        else:
            filters_list.append(Trend.total_games.in_(filters.total_games))

    if filters.min_total_games is not None and filters.max_total_games is not None:
        filters_list.append(Trend.total_games.between(filters.min_total_games, filters.max_total_games))
    elif filters.min_total_games is not None:
        filters_list.append(Trend.total_games >= filters.min_total_games)
    elif filters.max_total_games is not None:
        filters_list.append(Trend.total_games <= filters.max_total_games)

    # Filter by WIN PERCENTAGE
    if filters.win_percentage:
        if isinstance(filters.win_percentage, float):
            filters_list.append(Trend.win_percentage == filters.win_percentage)
        else:
            filters_list.append(Trend.win_percentage.in_(filters.win_percentage))

    if filters.min_win_percentage is not None and filters.max_win_percentage is not None:
        filters_list.append(Trend.win_percentage.between(filters.min_win_percentage, filters.max_win_percentage))
    elif filters.min_win_percentage is not None:
        filters_list.append(Trend.win_percentage >= filters.min_win_percentage)
    elif filters.max_win_percentage is not None:
        filters_list.append(Trend.win_percentage <= filters.max_win_percentage)

    # Apply filters to the query
    if filters_list:
        query = query.filter(*filters_list)

    total_count = query.order_by(None).count()

    # Sorting
    valid_sort_fields = {c_attr.key for c_attr in inspect(Trend).mapper.column_attrs}
    if filters.sort_by:
        sort_columns = []
        for sort in filters.sort_by:
            if sort.field not in valid_sort_fields:
                raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort.field}")

            if sort.field == "month":
                month_case = case(
                    (Trend.month == "January", 1),
                    (Trend.month == "February", 2),
                    (Trend.month == "March", 3),
                    (Trend.month == "April", 4),
                    (Trend.month == "May", 5),
                    (Trend.month == "June", 6),
                    (Trend.month == "July", 7),
                    (Trend.month == "August", 8),
                    (Trend.month == "September", 9),
                    (Trend.month == "October", 10),
                    (Trend.month == "November", 11),
                    (Trend.month == "December", 12),
                    (Trend.month == None, 13),
                    else_=14
                )
                sort_columns.append(month_case.desc() if sort.order == "desc" else month_case.asc())
            elif sort.field == 'day_of_week':
                day_case = case(
                    (Trend.day_of_week == "Sunday", 1),
                    (Trend.day_of_week == "Monday", 2),
                    (Trend.day_of_week == "Tuesday", 3),
                    (Trend.day_of_week == "Wednesday", 4),
                    (Trend.day_of_week == "Thursday", 5),
                    (Trend.day_of_week == "Friday", 6),
                    (Trend.day_of_week == "Saturday", 7),
                    (Trend.day_of_week == None, 8),
                    else_=9
                )
                sort_columns.append(day_case.desc() if sort.order == "desc" else day_case.asc())
            else:
                col = getattr(Trend, sort.field)
                sort_columns.append(col.desc() if sort.order == "desc" else col.asc())

        if sort_columns:
            query = query.order_by(*sort_columns)

    # Pagination
    if filters.limit:
        query = query.limit(filters.limit)
    if filters.offset:
        query = query.offset(filters.offset)

    trends = query.all()

    if not trends:
        return []
    return {
        "limit": filters.limit,
        "offset": filters.offset,
        "count": len(trends),
        "total_count": total_count,
        "results": trends,
    }