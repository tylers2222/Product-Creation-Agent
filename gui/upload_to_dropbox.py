import dropbox
import os
from dotenv import load_dotenv
import glob
import logging
import requests
from requests.models import PreparedRequest

logging.basicConfig(
    level=logging.INFO,
    format= '%(levelname)s [%(asctime)s] {%(pathname)s:%(lineno)d} - %(message)s',
)

def get_authorization_code():
    load_dotenv()
    url =f"https://www.dropbox.com/oauth2/authorize?client_id={os.getenv("DROPBOX_APP_KEY")}&token_access_type=offline&response_type=code"
    response = requests.get(url=url)

    # visting this in the browser and get your code
    print(url)

def get_oauth_key():
    load_dotenv()
    base_url = "https://api.dropbox.com/oauth2/token"

    response = requests.post(
        url=base_url,
        data={
            "grant_type": "authorization_code",
            "code": os.getenv("AUTH_CODE"),
            "client_id": os.getenv("DROPBOX_APP_KEY"),
            "client_secret": os.getenv("DROPBOX_APP_SECRET")
        }
    )

    logging.debug("Requested URL: %s, Response: %s", base_url, response.json())
    logging.debug("Access Token: %s", response.json().get("access_token"))

def get_access_token():
    load_dotenv()
    base_url = "https://api.dropbox.com/oauth2/token"

    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")

    logging.debug("Refresh Token: %s, App Key: %s, App Secret: %s", refresh_token is not None, app_key is not None, app_secret is not None)

    response = requests.post(
        url=base_url,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": app_key,
            "client_secret": app_secret
        }
    )

    if response.status_code > 299:
        logging.error("Response: %s", response.json())
        raise ValueError("Response is none")

    logging.debug("New Access Token: %s", response.json().get("access_token"))
    return response.json().get("access_token")

def upload_to_dropbox():
    load_dotenv()

    zip_files = glob.glob("*.zip")
    if not zip_files:
        print("No zipped files in dir")
        os._exit(1)

    mac_or_wndows = ""
    app_files = glob.glob("*.app")
    if app_files:
        print("Mac Os found")
        mac_or_wndows = "mac"

    exe_files = glob.glob("*.exe")
    if exe_files:
        print("Windows Os found")
        mac_or_wndows = "windows"

    if mac_or_wndows == "":
        dist_exists = os.path.exists("./dist")
        if not dist_exists:
            raise Exception("No executables found")

        app_file = glob.glob("./dist/*.app")
        exe_file = glob.glob("./dist/*.exe")

        if app_file:
            mac_or_wndows = "mac"
        if exe_file:
            mac_or_wndows = "windows"

    dbx = dropbox.Dropbox(oauth2_access_token=get_access_token())
    with open(zip_files[0], "rb") as f:
        dbx.files_upload(f.read(), f"/Agent Executables/ef-agent-{mac_or_wndows}.zip", mode=dropbox.files.WriteMode.overwrite)

    print("Successfully uploaded to drop box")

if __name__ == "__main__":
    #get_authorization_code()
    #get_oauth_key()
    #get_access_token()
    upload_to_dropbox()