# /\_/\
# ( -.-)
# / >📄


import sys
import json
import subprocess
import wnc
import platform
import shutil
import os
import argparse
try:
    import toml
    import importlib
    import lwjgl
    import rich
    import readchar
except ImportError as e:
    import setup
    setup.Setup()
    print("[Info] Required packages installed. Please re-run the program.")
    sys.exit(0)


parser = argparse.ArgumentParser(description='A special client made by python!')

# 添加参数
parser.add_argument('-command', help='Quick use Command')
cmd_args = parser.parse_args()



func_dict = {
             "reload": wnc.reload_client,
             "modlist": wnc.modlist,
             "help": wnc.help,
             "rcmd": wnc.rcmd
            }




loaded_mods = []
loaded_mappings = {}
loaded_modules = {}

def load_mods(modlist_path='Modlist.json',mod_name="*",type="Normal"):
    with open(modlist_path, 'r') as f:
        modlist = json.load(f)
    
    # 只在 enable_ignorecase 为 True 时忽略大小写
    if enable_ignorecase:
        # 创建忽略大小写的mod名称映射
        modlist_lower = {k.lower(): k for k in modlist.keys()}
    
    if mod_name == "*":
        mods_to_load = modlist.keys()
    else:
        # 根据 enable_ignorecase 决定查找方式
        if enable_ignorecase:
            # 使用小写查找
            mod_name_lower = mod_name.lower()
            if mod_name_lower in modlist_lower:
                original_name = modlist_lower[mod_name_lower]
                mods_to_load = [original_name]
            else:
                lwjgl.error(f"Mod {mod_name} not found in modlist.")
                return
        else:
            # 区分大小写查找
            if mod_name in modlist:
                mods_to_load = [mod_name]
            else:
                lwjgl.error(f"Mod {mod_name} not found in modlist.")
                return
    
    for mod_name in mods_to_load:
        mod_path = modlist[mod_name]['path']
        mod_mappings_path = modlist[mod_name]['mappings']
        loaded_mappings[mod_name] = mod_mappings_path
        mod_toml_path = modlist[mod_name]['toml']
        enabled = modlist[mod_name].get('Enabled', False)
        if enabled:
            if platform.system() not in toml.load(open(mod_toml_path)).get('platforms', [platform.system()]):
                lwjgl.warning(f"Mod {mod_name} is not supported on {platform.system()} platform. Skipping load.")
                continue
            if type == "AutoLoad":
                # 设置自动加载
                autoload = modlist[mod_name].get('AutoLoad', False)
                enable_threads = toml.load(open(mod_toml_path)).get('Run_in_the_background', False)
                if (autoload is False) or (enable_threads is False):
                    continue
            lwjgl.info(f"Loading mod: {mod_name} | Version: {toml.load(open(mod_toml_path)).get('Version', 'N/A')} | Author: {toml.load(open(mod_toml_path)).get('Author', 'Unknown')}")
            try:
                # import module and keep reference for later use
                module = importlib.import_module(mod_path.replace('/', '.').removesuffix('.py'))
                loaded_modules[mod_name] = module
            except Exception as e:
                lwjgl.warning(f"Failed to load mod {mod_name}: {e}")
                for need_dep in toml.load(open(mod_toml_path))["Dependence"]:
                    lwjgl.info(f"Installing dependency: {need_dep}")
                    try:
                        import setup # 安装依赖库
                        setup.Setup()

                        subprocess.run(['uv','pip', 'install', need_dep,'--python',sys.executable], check=True)
                        lwjgl.info(f"Dependency {need_dep} installed successfully.")
                    except subprocess.CalledProcessError as ce:
                        lwjgl.error(f"Failed to install dependency {need_dep}: {ce}")
                    else:
                        lwjgl.info(f"Mod {mod_name} loaded successfully.")
                        loaded_mods.append(mod_name)
                        # ensure module reference is present if dependency install allowed import
                        try:
                            module = importlib.import_module(mod_path.replace('/', '.').rstrip('.py'))
                            loaded_modules[mod_name] = module
                        except Exception:
                            pass
            else:
                lwjgl.info(f"Mod {mod_name} loaded successfully.")
                loaded_mods.append(mod_name)

def _convert_type(value, to_type):
    try:
        if to_type == 'int':
            return int(value)
        if to_type == 'float':
            return float(value)
        if to_type == 'bool':
            return value.lower() in ('1', 'true', 'yes', 'on')
    except Exception:
        pass
    return value


def UseMod(mod_name, func="", args=None, **kwargs):
    # avoid mutable default
    args = args or []
    
    # 只在 enable_ignorecase 为 True 时忽略大小写
    if enable_ignorecase:
        # 创建忽略大小写的已加载mod映射
        loaded_mods_lower = {m.lower(): m for m in loaded_mods}
        
        # 查找正确的mod名称（忽略大小写）
        mod_name_lower = mod_name.lower()
        if mod_name_lower in loaded_mods_lower:
            correct_mod_name = loaded_mods_lower[mod_name_lower]
        else:
            lwjgl.error(f"Mod {mod_name} is not loaded or does not exist.")
            return
        
        # 使用正确的mod名称
        mod_name = correct_mod_name
    else:
        # 区分大小写查找
        if mod_name not in loaded_mods:
            lwjgl.error(f"Mod {mod_name} is not loaded or does not exist.")
            return
    
    # load mappings file for this mod
    with open(loaded_mappings[mod_name], 'r') as f:
        mod_mappings = json.load(f)
    
    if func.strip() == "":
        func_options = list(mod_mappings.keys())
        selected = 0
        if len(func_options) == 0:
            lwjgl.error(f"No functions available in mappings for mod '{mod_name}'")
            return
        if len(func_options) != 1:
            while True:
                rich.print(f"\n[bold]Please select a func ({mod_name}): [/bold]")
                for idx, option in enumerate(func_options):
                    if idx == selected:
                        rich.print(f"> [bold green]{option}[/bold green]")
                    else:
                        rich.print(f"  {option}")
                key = readchar.readkey()
                if key in (readchar.key.UP, 'w'):
                    selected = (selected - 1) % len(func_options)
                elif key in (readchar.key.DOWN, 's'):
                    selected = (selected + 1) % len(func_options)
                elif key in ('\r', '\n', readchar.key.ENTER):
                    func = func_options[selected]
                    break
                # 清屏重绘
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
        else:
            func = func_options[0]
    if func not in mod_mappings:
        lwjgl.error(f"Function '{func}' not found in mappings for mod '{mod_name}'")
        return
    # 判断是否用户没有传入参数，否则让用户输入
    if not args and not kwargs:
        params_meta = mod_mappings[func].get('Parameters', {})
        for param_name, param_info in params_meta.items():
            if param_info.get('isRequired', False):
                while True:
                    user_input = input(f"Enter value for parameter '{param_name}' (type: {param_info.get('type', 'str')}): ")
                    if user_input.strip() != "":
                        kwargs[param_name] = user_input
                        break
            else:
                user_input = input(f"Enter value for parameter '{param_name}' (type: {param_info.get('type', 'str')}, press Enter to skip): ")
                if user_input.strip() != "":
                    kwargs[param_name] = user_input
    mapping = mod_mappings[func]
    target_func_name = mapping.get('func')
    params_meta = mapping.get('Parameters', {})

    # prepare kwargs: convert types based on mapping
    final_kwargs = {}
    for k, v in kwargs.items():
        expected = params_meta.get(k, {}).get('type')
        final_kwargs[k] = _convert_type(v, expected) if expected else v

    # prepare positional args: if kwargs provided, prefer keyword calling
    final_args = []
    if not final_kwargs and args:
        # use parameter order from mapping if available
        param_order = list(params_meta.keys())
        for i, val in enumerate(args):
            if i < len(param_order):
                expected = params_meta.get(param_order[i], {}).get('type')
                final_args.append(_convert_type(val, expected) if expected else val)
            else:
                final_args.append(val)

    # resolve callable
    func_callable = None
    module = loaded_modules.get(mod_name)
    if module and hasattr(module, target_func_name):
        func_callable = getattr(module, target_func_name)
    else:
        # attempt to import module again if needed
        try:
            # try to find module path via loaded_mappings file path (not ideal but fallback)
            # caller should normally have module loaded already
            # as last resort, try importing mod by name
            if mod_name in loaded_modules:
                module = loaded_modules[mod_name]
            func_callable = getattr(module, target_func_name)
        except Exception:
            lwjgl.error(f"Unable to resolve function '{target_func_name}' for mod '{mod_name}'")
            return

    # call
    try:
        return func_callable(*final_args, **final_kwargs)
    except ImportError as ie:
        with open("Modlist.json", 'r') as f:
            modlist = json.load(f)
        toml_path = modlist[mod_name]['toml']
        dependencies = toml.load(open(toml_path)).get('Dependence', [])
        for dep in dependencies:
            lwjgl.warning(ie)
            lwjgl.info(f"Installing dependency: {dep}")
            try:
                import setup # 安装依赖库
                setup.Setup()

                subprocess.run(['uv','pip', 'install', dep,'--python',sys.executable], check=True)
                lwjgl.info(f"Dependency {dep} installed successfully.")
            except subprocess.CalledProcessError as ce:
                lwjgl.error(f"Failed to install dependency {dep}: {ce}")
            else:
                wnc.reload_client(para="-c",para1=f"use {mod_name} {func} " + ' '.join([str(arg) for arg in args]) + ' ' + ' '.join([f"{k}={v}" for k,v in kwargs.items()]))
    except Exception as e:
        lwjgl.error(f"Error calling '{target_func_name}' from mod '{mod_name}': {e}")
        return

def load_auto_use():
    try:
        with open("AutoStart.json", "r") as f:
            auto_use_data = json.load(f)
        for mod_name, funcs in auto_use_data.items():
            if mod_name not in loaded_mods:
                load_mods(mod_name=mod_name)
            for func, param in funcs.items():
                if param is not None and param != "":
                    # 参数不为空且不是空字符串
                    if isinstance(param, dict):
                        UseMod(mod_name, func, **param)
                    elif isinstance(param, list):
                        UseMod(mod_name, func, param)
                    else:
                        UseMod(mod_name, func, [param])
                else:
                    # 参数为空或空字符串，不传递参数
                    UseMod(mod_name, func)
                    
    except Exception as e:
        lwjgl.warning(f"Error in load_auto_use: {e}")

Used_cmd = False
def main():
    load_auto_use()
    load_mods(type="AutoLoad")
    global enable_ignorecase
    enable_ignorecase = Client_config.get("ignorecase", False)
    global Used_cmd
    while True:
        rich.print("[bold blue]Wnclient> [/bold blue]", end="")
        if not Used_cmd:
            if cmd_args.command is not None:
                input_command = cmd_args.command
            else:
                if enable_ignorecase:
                    input_command = input("").lower()
                else:
                    input_command = input("")
            Used_cmd = True
        else:
            input_command = input("")
        if input_command.lower() in ['exit', 'quit']:
            isExiting = True
            sys.exit(0)
        else:
            if input_command.strip() == "":
                continue
            if input_command.split()[0].lower() == "use":
                if len(input_command.split()) < 2:
                    lwjgl.error("Please specify a mod to use. Usage: use <mod_name> [function_name] [param1 param2 ...]")
                    continue
                mod_to_use = input_command.split()[1]
                mod_func = input_command.split()[2] if len(input_command.split()) >2 else ""
                mod_parameters = input_command.split()[3:] if len(input_command.split()) > 3 else []
                mod_kwargs = {}
                for mod_param in mod_parameters:
                    if '=' in mod_param:
                        key, value = mod_param.split('=', 1)
                        mod_kwargs[key] = value
                
                if enable_ignorecase:
                    # 创建忽略大小写的已加载mod映射
                    loaded_mods_lower = {m.lower(): m for m in loaded_mods}
                    
                    # 查找mod（忽略大小写）
                    mod_to_use_lower = mod_to_use.lower()
                    if mod_to_use_lower in loaded_mods_lower:
                        # 找到已加载的mod（忽略大小写）
                        mod_to_use = loaded_mods_lower[mod_to_use_lower]
                        lwjgl.info(f"Using mod: {mod_to_use}")
                        UseMod(mod_to_use, mod_func, mod_parameters,**mod_kwargs)
                    else:
                        lwjgl.warning(f"Mod {mod_to_use} is not loaded or does not exist.Please wait for loading.")
                        load_mods(mod_name=mod_to_use)
                        
                        # 重新检查是否加载成功（忽略大小写）
                        loaded_mods_lower = {m.lower(): m for m in loaded_mods}
                        if mod_to_use_lower in loaded_mods_lower:
                            mod_to_use = loaded_mods_lower[mod_to_use_lower]
                            lwjgl.info(f"Using mod: {mod_to_use}")
                            UseMod(mod_to_use, mod_func, mod_parameters,**mod_kwargs)
                        else:
                            lwjgl.error(f"Mod {mod_to_use} not found or failed to load.")
                else:
                    # 区分大小写查找
                    if mod_to_use in loaded_mods:
                        lwjgl.info(f"Using mod: {mod_to_use}")
                        UseMod(mod_to_use, mod_func, mod_parameters,**mod_kwargs)
                    else:
                        lwjgl.warning(f"Mod {mod_to_use} is not loaded or does not exist.Please wait for loading.")
                        load_mods(mod_name=mod_to_use)
                        if mod_to_use in loaded_mods:
                            lwjgl.info(f"Using mod: {mod_to_use}")
                            UseMod(mod_to_use, mod_func, mod_parameters,**mod_kwargs)
                        else:
                            lwjgl.error(f"Mod {mod_to_use} not found or failed to load.")
            elif input_command in func_dict:
                func_dict[input_command]()
            else:
                lwjgl.error(f"Unknown command: {input_command}")
            
if __name__ == "__main__":
    lwjgl.info(f"Loading Configuration")
    global Client_config
    Client_config = json.load(open("Client.json", 'r'))

    global enable_ignorecase
    enable_ignorecase = Client_config.get("ignorecase", False)
    if Client_config.get("custom_boot_txt", False):
        with open(Client_config.get("boot_ascii_path", "Boot.txt"), 'r', encoding='utf-8') as f:
            boot_text = f.read()
            print(boot_text)
    try:
        if os.path.exists("./Temp"):
            lwjgl.info("Del temp")
            shutil.rmtree("./Temp")
        os.makedirs("./Temp")
    except Exception as e:
        lwjgl.warning(f"Can not delete some file: {e}")
    isExiting = False
    while isExiting is False:
        try:
            main()
        except KeyboardInterrupt:
            print("\nPlease use 'exit' or 'quit' command to exit the program.")