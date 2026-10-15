from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import routes_health, routes_risk, routes_portfolio
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


app = FastAPI(title=settings.app_name)
app.include_router(routes_health.router, prefix="/api/v1")
app.include_router(routes_risk.router, prefix="/api/v1")
app.include_router(routes_portfolio.router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="frontend"), name="static")
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")