import logging_config
import logging
import structlog
import uvicorn
from dotenv import load_dotenv
import os

from api.main import create_app

load_dotenv()

logger = structlog.get_logger(__name__)

def main():
    logger.info("Creating app from root")
    api = create_app()
    uvicorn.run(app=api, host="0.0.0.0", port=3000, log_config=None)

if __name__ == "__main__":
    main()
