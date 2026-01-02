#  /\_/\
# ( o.o )
#  > ^ <

import sys
import json
import subprocess
import platform
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

loaded_mods = []
loaded_mappings = {}
loaded_modules = {}
def load_mods(modlist_path='Modlist.json',mod_name="*",type="Normal"):
    with open(modlist_path, 'r') as f:
        modlist = json.load(f)
    if mod_name == "*":
        mods_to_load = modlist.keys()
    else:
        mods_to_load = [mod_name] if mod_name in modlist else []
        if mod_name not in modlist:
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
                autoload = modlist[mod_name].get('AutoLoad', False)
                if not autoload:
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
    # load mappings file for this mod
    with open(loaded_mappings[mod_name], 'r') as f:
        mod_mappings = json.load(f)
    
    if func.strip() == "":
        func_options = list(mod_mappings.keys())
        selected = 0
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
    except Exception as e:
        lwjgl.error(f"Error calling '{target_func_name}' from mod '{mod_name}': {e}")
        return
    
def main():
    load_mods(type="AutoLoad")
    while True:
        rich.print("[bold blue]Wnclient> [/bold blue]", end="")
        input_command = input("")
        if input_command.lower() in ['exit', 'quit']:
            sys.exit(0)
        else:
            if input_command.strip() == "":
                continue
            if input_command.split()[0].lower() == "use":
                mod_to_use = input_command.split()[1]
                mod_func = input_command.split()[2] if len(input_command.split()) >2 else ""
                mod_parameters = input_command.split()[3:] if len(input_command.split()) > 3 else []
                mod_kwargs = {}
                for mod_param in mod_parameters:
                    if '=' in mod_param:
                        key, value = mod_param.split('=', 1)
                        mod_kwargs[key] = value
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
                lwjgl.error(f"Unknown command: {input_command}")
if __name__ == "__main__":
    main()