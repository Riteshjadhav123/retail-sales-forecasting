import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.api.routes import router as api_router
from app.core.logging import get_logger

logger = get_logger("fastapi_app")

app = FastAPI(
    title="RetailMind-X AI Command Center",
    description="Self-Adaptive, Uncertainty-Aware Retail Demand Forecasting & Intelligent Inventory Decision System",
    version="1.0.0"
)

# Mount API router
app.include_router(api_router)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serves RetailMind-X AI Command Center Web Interface."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>RetailMind-X AI Command Center Server Running!</h1>"

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    is_dev = os.environ.get("ENVIRONMENT", "development").lower() != "production"
    uvicorn.run("app.main:app", host=host, port=port, reload=is_dev)

