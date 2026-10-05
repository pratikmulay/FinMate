from typing import Literal
from pydantic import BaseModel, Field, model_validator
from app.schemas.risk import QuizAnswers, RiskResult

class PortfolioRequest(BaseModel):
    monthly_income: float = Field(gt=0)
    monthly_savings: float = Field(gt=0)
    quiz: QuizAnswers

    @model_validator(mode="after")
    def savings_within_income(self):
        if self.monthly_savings > self.monthly_income:
            raise ValueError("monthly_savings cannot exceed monthly_income")
        return self

class Allocation(BaseModel):
    asset_id: str
    name: str
    asset_class: str
    weight_pct: float
    monthly_amount: int
    rationale: str

class ProjectionPoint(BaseModel):
    years: int
    invested: int
    pessimistic: int
    expected: int
    optimistic: int

class PortfolioResponse(BaseModel):
    risk: RiskResult
    savings_rate_pct: float
    allocations: list[Allocation]
    projections: list[ProjectionPoint]
    source: Literal["llm", "fallback", "baseline"]
    disclaimer: str = "Educational purposes only. Projections are assumptions, not guarantees."
    summary: str = ""