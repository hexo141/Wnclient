import requests
import json
import os
import zipfile
import hashlib
import shutil

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CLIENT_VER_PATH = SCRIPT_DIR / "version.json"

try:
    client_ver = json.load(open(CLIENT_VER_PATH, "r", encoding="utf-8"))
except Exception:
    client_ver = {"NowVersion": 0}


def check_for_updates():
    """检查远程 version.json 是否有更高的 NowVersion。"""
    url = "https://raw.githubusercontent.com/hexo141/Wnclient/main/version.json"
    try:
        rep = requests.get(url, timeout=10)
        rep.raise_for_status()
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")
        return False
    try:
        remote_version_info = rep.json()
    except Exception as e:
        print(f"Error parsing remote version info: {e}")
        return False
    ver_json = remote_version_info.get("NowVersion", 0)
    if ver_json > client_ver.get("NowVersion", 0):
        return True
    return False


def md5_of_file(path: Path):
    h = hashlib.md5()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None


def download_and_extract(update_url: str, out_dir: Path) -> Path | None:
    """下载 ZIP 并解压到指定目录，返回解压后的根目录（第一个子目录）。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "update.zip"
    try:
        rep = requests.get(update_url, timeout=60)
        rep.raise_for_status()
        with zip_path.open("wb") as f:
            f.write(rep.content)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(out_dir)
    except requests.RequestException as e:
        print(f"Error downloading update: {e}")
        return None
    except zipfile.BadZipFile as e:
        print(f"Error extracting update: {e}")
        return None

    # 找到第一个解压出的目录（通常是 repo-main）
    for child in out_dir.iterdir():
        if child.name == 'update.zip':
            continue
        # 如果是目录，认为这是源码根
        if child.is_dir():
            return child
    return out_dir


def replace_files_by_md5(src_root: Path, dst_root: Path) -> list:
    """遍历 src_root，按相对路径与 dst_root 比较 MD5，不同则覆盖。返回被替换/新增的文件列表。"""
    replaced = []
    src_root = src_root.resolve()
    dst_root = dst_root.resolve()
    for src_path in src_root.rglob("*"):
        if src_path.is_dir():
            continue
        rel = src_path.relative_to(src_root)
        dst_path = dst_root / rel
        src_md5 = md5_of_file(src_path)
        dst_md5 = md5_of_file(dst_path)
        if dst_md5 != src_md5:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            replaced.append(str(rel))
    return replaced


def download_update_and_replace():
    update_url = "https://github.com/hexo141/Wnclient/archive/refs/heads/main.zip"
    updates_dir = SCRIPT_DIR / "updates"
    extracted = download_and_extract(update_url, updates_dir)
    if not extracted:
        return False

    # 计算并替换文件
    replaced = replace_files_by_md5(extracted, SCRIPT_DIR)
    if replaced:
        print(f"Replaced/added {len(replaced)} files:")
        for p in replaced:
            print(f" - {p}")
    else:
        print("No files needed replacement; already up-to-date.")
    return True


def main():
    print("\n")
    if check_for_updates():
        print("\033[033mA new update is available!\033[0m")
        ok = download_update_and_replace()
        if ok:
            print("\033[032mUpdate applied (files replaced where MD5 differed).\033[0m")
            return True
        else:
            print("\033[031mUpdate failed. See messages above.\033[0m")
            return False
    else:
        print("\033[032mYou are using the latest version.\033[0m")
        return True


if __name__ == "__main__":
    main()