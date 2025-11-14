import toml
import requests
import json

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