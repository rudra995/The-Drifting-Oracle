"""
Pydantic request/response schemas.
All 20 features are numeric — no categorical encoding needed.
"""
from pydantic import BaseModel
from typing import Optional


class PredictRequest(BaseModel):
    AMT_INCOME_TOTAL: Optional[float] = 200000.0
    AMT_CREDIT_x: Optional[float] = 500000.0
    AMT_ANNUITY: Optional[float] = 25000.0
    CNT_CHILDREN: Optional[int] = 0
    CNT_FAM_MEMBERS: Optional[float] = 2.0
    DAYS_EMPLOYED: Optional[float] = -1500.0
    EXT_SOURCE_1: Optional[float] = 0.5
    EXT_SOURCE_2: Optional[float] = 0.5
    EXT_SOURCE_3: Optional[float] = 0.5
    REGION_POPULATION_RELATIVE: Optional[float] = 0.03
    REGION_RATING_CLIENT: Optional[int] = 2
    FLAG_EMP_PHONE: Optional[int] = 1
    FLAG_WORK_PHONE: Optional[int] = 0
    age: Optional[float] = 35.0
    income_credit_ratio: Optional[float] = 0.4
    annuity_ratio: Optional[float] = 0.05
    CODE_GENDER_M: Optional[int] = 1
    CODE_GENDER_XNA: Optional[int] = 0
    FLAG_OWN_CAR_Y: Optional[int] = 0
    FLAG_OWN_REALTY_Y: Optional[int] = 1
