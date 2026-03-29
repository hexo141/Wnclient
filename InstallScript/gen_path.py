import platform
import subprocess
import pathlib
import os

try:
    os.makedirs("../Env_Bin", exist_ok=True)
except Exception as e:
    print(f"\033[0;31mFailed to create Env_Bin directory: {e}\033[0m")
def gen_path_on_windows():
    # 获取项目根目录
    root_dir = pathlib.Path(__file__).parent.parent.absolute() / "Env_Bin"
    bat_path = root_dir / "wncli.bat"

    # 创建批处理文件，用于在命令行中运行
    bat_content = f"""@echo off
cd /d {root_dir.parent}
python main.py
"""
    with open(bat_path, "w") as f:
        f.write(bat_content)

    # 使用 PowerShell 修改用户环境变量 PATH
    ps_script = f'''
$targetDir = "{root_dir}"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$paths = $userPath -split ';' | Where-Object {{ $_ -and $_ -ne "" }}
$filteredPaths = $paths | Where-Object {{ $_ -notlike "*wnclient*" }}
$normTarget = [System.IO.Path]::GetFullPath($targetDir)
$alreadyExists = $filteredPaths | Where-Object {{ [System.IO.Path]::GetFullPath($_) -eq $normTarget }}
if (-not $alreadyExists) {{
    $newPaths = $filteredPaths + $normTarget
    $newPathString = $newPaths -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPathString, "User")
    Write-Host "Added {root_dir} to user PATH."
}} else {{
    Write-Host "Path already exists in user PATH."
}}
'''
    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True,
                       capture_output=True, text=True)
        print("\033[0;32mEnvironment variable updated. "
              "You may need to restart your terminal or run 'refreshenv' "
              "(if using choco) to apply changes.\033[0m")
    except subprocess.CalledProcessError as e:
        print(f"\033[0;31mFailed to set environment variable: {e}\033[0m")
        if e.stderr:
            print(e.stderr)
    else:
        print("\033[0;32mYou can now run the program using 'wncli' "
              "command in the terminal (after restarting terminal).\033[0m")

def gen_path_on_linux():
    # 获取项目根目录
    root_dir = pathlib.Path(__file__).parent.parent.absolute()
    # 创建用户本地 bin 目录
    local_bin = pathlib.Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    script_path = local_bin / "wncli"

    # 生成 shell 脚本
    script_content = f"""#!/bin/bash
cd {root_dir}
python3 main.py
"""
    with open(script_path, "w") as f:
        f.write(script_content)
    # 添加可执行权限
    os.chmod(script_path, 0o755)

    # 检测当前使用的 shell 并配置 PATH
    home = pathlib.Path.home()
    shell = os.environ.get('SHELL', '')
    if 'zsh' in shell:
        config_file = home / ".zshrc"
    else:
        config_file = home / ".bashrc"  # 默认 bash

    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
        # 检查是否已将 ~/.local/bin 加入 PATH
        if 'export PATH="$HOME/.local/bin:$PATH"' not in content and \
           'export PATH=~/.local/bin:$PATH' not in content:
            with open(config_file, 'a') as f:
                f.write('\n# Added by wncli installer\n'
                        'export PATH="$HOME/.local/bin:$PATH"\n')
            print(f"\033[0;32mAdded ~/.local/bin to PATH in {config_file}. "
                  f"Please run 'source {config_file}' or restart your terminal.\033[0m")
        else:
            print(f"\033[0;32m~/.local/bin already in PATH in {config_file}.\033[0m")
    else:
        print(f"\033[0;33m{config_file} not found. "
              "Please ensure ~/.local/bin is in your PATH manually.\033[0m")

    # 检查是否存在其他位置的 wncli 脚本
    try:
        result = subprocess.run(['which', 'wncli'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            existing = result.stdout.strip()
            if existing != str(script_path):
                print(f"\033[0;33mWarning: Another 'wncli' found at {existing}. "
                      f"The new one at {script_path} may not be used unless "
                      f"{local_bin} appears earlier in PATH.\033[0m")
    except:
        pass

    print("\033[0;32mYou can now run the program using 'wncli' "
          "command in the terminal (after adding PATH if needed).\033[0m")

if __name__ == "__main__":
    system = platform.system()
    if system == 'Windows':
        gen_path_on_windows()
    elif system == 'Linux':
        gen_path_on_linux()
    else:
        print(f"\033[0;31mUnsupported platform: {system}\033[0m")
