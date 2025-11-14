import toml
import requests
import json
import os
import zipfile
client_config = toml.load("config.toml")
def check_for_updates():
    try:
        rep = requests.get(client_config["Update_Link"])
    except requests.exceptions as e:
        print(f"Error checking for updates: {e}")
        return False
    remote_version_info = rep.json()
    ver_json = remote_version_info.get("NowVersion", 0)
    if ver_json > client_config["Now_Version"]:
        return True
def download_update():
    update_url = "https://github.com/hexo141/Wnclient/archive/refs/heads/main.zip"
    try:
        os.mkdir("../updates")
    except FileExistsError as e:
        print(f"Directory already exists: {e}")
    try:
        rep = requests.get(update_url)
        with open("../updates/update.zip", "wb") as f:
            f.write(rep.content)
        with zipfile.ZipFile("../updates/update.zip", 'r') as zip_ref:
            zip_ref.extractall("../updates/")
    except requests.exceptions as e:
        print(f"Error downloading update: {e}")
        return False
    except zipfile.BadZipFile as e:
        print(f"Error extracting update: {e}")
        return False

def main(auto=True):
    print("\n")
    if check_for_updates():
        print("\033[033mA new update is available!\033[0m")
        if auto:
            download_update()
            print("\033[032mUpdate downloaded successfully. Please replace the old files with the new ones from the 'updates' folder.\033[0m")
            return True
        elif input("Do you want to download the update? (y/n): ").lower() == 'y':
            download_update()
            print("\033[032mUpdate downloaded successfully. Please replace the old files with the new ones from the 'updates' folder.\033[0m")
            return True
    else:
        print("\033[032mYou are using the latest version.\033[0m")
if __name__ == "__main__":
    main(auto=False)