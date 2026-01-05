import dropbox
import os
from dotenv import load_dotenv
import glob

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

    dbx = dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))
    with open(zip_files[0], "rb") as f:
        dbx.files_upload(f.read(), f"/Agent Executables/ef-agent-{mac_or_wndows}.zip", mode=dropbox.files.WriteMode.overwrite)

    print("Successfully uploaded to drop box")

if __name__ == "__main__":
    upload_to_dropbox()