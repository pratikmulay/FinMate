from typing import Literal
from pydantic import BaseModel, Field

Profile = Literal["Conservative", "Moderate", "Aggressive"]

class QuizAnswers(BaseModel):
    age: int = Field(ge=18, le=100)
    horizon: Literal["<1", "1-3", "3-7", "7+"]
    drop_reaction: Literal["sell_all", "sell_some", "hold", "buy_more"]
    income_stability: Literal["unstable", "somewhat", "stable", "very_stable"]
    experience: Literal["none", "beginner", "some", "experienced"]
    emergency_months: int = Field(ge=0, le=60)

class RiskResult(BaseModel):
    score: int
    profile: Profile
    reasons: list[str]