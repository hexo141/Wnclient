import subprocess
import sys

def Setup():
    # 安装uv管理包
    subprocess.run(['pip', 'install', 'uv'])
    try:
        subprocess.run(['uv','-V'])
    except Exception as e:
        print("[Error] uv management package installation failed:", e)
        exit(1)
    print("[Info] uv management package installed successfully.")
    # 继续执行其他安装步骤
    try:
        subprocess.run(['uv','pip', 'install', '-r', 'requirements.txt', '--python',sys.executable], check=True)
    except Exception as e:
        print("[Error] Failed to install dependencies from requirements.txt:", e)
        exit(1)

if __name__ == "__main__":
    Setup()