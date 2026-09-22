import sys
import os
import uvicorn

sys.path.insert(0, os.path.abspath("."))
from src.utils.logger import get_logger

logger = get_logger("run_app")

def main():
    logger.info("==================================================")
    logger.info("STARTING RETAILMIND-X AI COMMAND CENTER WEB SERVER")
    logger.info("==================================================")
    logger.info("Server listening at: http://127.0.0.1:8000")
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
