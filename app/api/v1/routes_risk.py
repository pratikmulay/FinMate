from fastapi import APIRouter
from app.schemas.risk import QuizAnswers, RiskResult
from app.services.risk_engine import compute_risk

router = APIRouter(prefix="/risk", tags=["risk"])

@router.post("/profile", response_model=RiskResult)
def risk_profile(answers: QuizAnswers):
    return compute_risk(answers)