from pydantic import BaseModel, Field

class LLMAllocation(BaseModel):
    asset_id: str
    weight_pct: float = Field(ge=0, le=100)
    rationale: str = Field(max_length=300)

class LLMPortfolio(BaseModel):
    allocations: list[LLMAllocation]
    summary: str = ""