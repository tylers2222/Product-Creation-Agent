import logging
import uvicorn
from api.main import create_app

def main():
    # set up URL for api and run from main
    print("="*60)
    print("API STARTED RE-ROUTING VIA REVERSE PROXY")
    api = create_app()
    uvicorn.run(app=api, host="0.0.0.0", port=3000)
    logging.info("Api successfully started")

if __name__ == "__main__":
    main()