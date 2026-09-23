import sys
import os
import uvicorn

sys.path.insert(0, os.path.abspath("."))
from src.utils.logger import get_logger

logger = get_logger("run_app")

def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    logger.info("==================================================")
    logger.info("STARTING RETAILMIND-X AI COMMAND CENTER WEB SERVER")
    logger.info("==================================================")
    logger.info(f"Server listening at: http://{host}:{port}")
    
    reload_flag = os.environ.get("RELOAD", "false").lower() in ("true", "1") or os.environ.get("ENVIRONMENT", "").lower() == "development"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_flag)

if __name__ == "__main__":
    main()


