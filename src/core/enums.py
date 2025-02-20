from enum import Enum


class SortType(str, Enum):
    ASC = 'ASC'
    DESC = 'DESC'


class RatingType(str, Enum):
    gdp = 'gdp'
    capacity = 'capacity'
