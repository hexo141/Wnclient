import platform
import psutil
import rich
from rich.table import Table
import os
import socket
import datetime
import screeninfo
import GPUtil
import time
def get_gpu_info_gputil():
    try:
        gpus = GPUtil.getGPUs()
        gpu_list = []
        
        for gpu in gpus:
            gpu_info = {
                'id': gpu.id,
                'name': gpu.name,
                'load': gpu.load * 100,
                'memory_total': gpu.memoryTotal,
                'memory_used': gpu.memoryUsed,
                'memory_free': gpu.memoryFree,
                'temperature': gpu.temperature,
                'uuid': gpu.uuid
            }
            gpu_list.append(gpu_info)
        
        return gpu_list
    except Exception as e:
        print(f"{e}")
        return []


gpus = get_gpu_info_gputil()

def format_bytes_to_gb(bytes_value):
    if bytes_value is None:
        return "N/A"
    return f"{bytes_value / 1024**3:.2f}"

def get_memory_info_psutil():
    virtual_mem = psutil.virtual_memory()
    swap_mem = psutil.swap_memory()
    
    memory_info = {
        'total': format_bytes_to_gb(virtual_mem.total),
        'available': format_bytes_to_gb(virtual_mem.available),
        'used': format_bytes_to_gb(virtual_mem.used),
        'free': format_bytes_to_gb(virtual_mem.free),
        'percent': virtual_mem.percent,
        'swap_total': format_bytes_to_gb(swap_mem.total),
        'swap_used': format_bytes_to_gb(swap_mem.used),
        'swap_free': format_bytes_to_gb(swap_mem.free),
        'swap_percent': swap_mem.percent
    }
    
    return memory_info

def get_network_speed(interval=1.0):
    """
    Get current network upload/download speed.
    Returns: (upload_speed, download_speed) as formatted strings
    """
    # Get initial stats
    net_start = psutil.net_io_counters()
    bytes_sent_start = net_start.bytes_sent
    bytes_recv_start = net_start.bytes_recv
    
    # Wait and measure
    time.sleep(interval)
    
    # Get final stats
    net_end = psutil.net_io_counters()
    bytes_sent_end = net_end.bytes_sent
    bytes_recv_end = net_end.bytes_recv
    
    # Calculate speeds (bytes per second)
    upload_bps = (bytes_sent_end - bytes_sent_start) / interval
    download_bps = (bytes_recv_end - bytes_recv_start) / interval
    
    # Format function
    def format_speed(bps):
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bps < 1024:
                return f"{bps:.1f} {unit}"
            bps /= 1024
        return f"{bps:.1f} TB/s"
    
    return format_speed(upload_bps), format_speed(download_bps)

def get_terminal_and_shell():
    try:
        current = psutil.Process()
        
        ancestors = []
        parent = current.parent()
        while parent:
            ancestors.append(parent)
            parent = parent.parent()
        
        result = {
            'current_process': current.name(),
            'shell': 'unknown',
            'terminal': 'unknown'
        }
        
        for proc in ancestors:
            name = proc.name().lower()
            exe = proc.exe().lower() if proc.exe() else ''
            
            if any(term in name for term in ['gnome-terminal', 'konsole', 'xfce4-terminal', 
                                            'terminator', 'alacritty', 'kitty']):
                result['terminal'] = name
            
            elif any(shell in name for shell in ['bash', 'zsh', 'fish', 'dash', 'sh']):
                result['shell'] = name
            elif 'powershell' in name or 'pwsh' in name:
                result['shell'] = 'powershell'
            elif 'cmd.exe' in name:
                result['shell'] = 'cmd'
            
            elif any(term in exe for term in ['iterm', 'windows terminal', 'terminal.app']):
                result['terminal'] = os.path.basename(exe)
        
        return result
        
    except Exception as e:
        return {'error': str(e)}

def create_progress_bar(percentage, width=20):
    filled = int(width * percentage / 100)
    bar = "[blue]" + "█" * filled + "[/blue]"
    bar += "[grey]" + "█" * (width - filled) + "[/grey]"
    return bar

def main():
    # 创建主面板
    console = rich.get_console()
    
    # 标题
    rich.print(f"[bold red]{os.getlogin()}[/bold red] @ [bold red]{socket.gethostname()}[/bold red]")
    rich.print("[bold cyan]" + "─" * 40 + "[/bold cyan]")
    
    # 基本信息
    info = get_terminal_and_shell()
    rich.print(f"[bold yellow]OS:[/bold yellow] {platform.platform()}")
    rich.print(f"[bold yellow]Kernel:[/bold yellow] {platform.release()}")
    rich.print(f"[bold yellow]Process:[/bold yellow] {len(psutil.pids())}")
    
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
    rich.print(f"[bold yellow]Uptime:[/bold yellow] {uptime}")
    rich.print(f"[bold yellow]Shell:[/bold yellow] {info.get('shell')}")
    rich.print(f"[bold yellow]Terminal:[/bold yellow] {info.get('terminal')}")
    
    # CPU信息
    cpu_percent = psutil.cpu_percent(interval=0.1)
    rich.print(f"[bold yellow]CPU:[/bold yellow] {platform.processor()}")
    rich.print(f"    [green]->[/green] Usage: {create_progress_bar(cpu_percent)} {cpu_percent:.1f}%")
    rich.print(f"    [green]->[/green] Machine: {platform.machine()}")
    
    # 显示器信息
    monitors = screeninfo.get_monitors()
    rich.print(f"[bold yellow]Screen[/bold yellow] ({len(monitors)}):")
    for i, monitor in enumerate(monitors):
        rich.print(f"    [green]->[/green] Display {i}: {monitor.name} ([bold blue]{monitor.width}x{monitor.height}[/bold blue])")

    if gpus:
        rich.print(f"[bold yellow]GPU[/bold yellow] ({len(gpus)}):")
        for gpu in gpus:
            gpu_load = gpu['load']
            vram_percent = (gpu['memory_used'] / gpu['memory_total']) * 100 if gpu['memory_total'] > 0 else 0
            
            # GPU计算负载进度条
            rich.print(f"    [green]->[/green] GPU {gpu['id']}: {gpu['name']}")
            rich.print(f"       Load: {create_progress_bar(gpu_load)} {gpu_load:.1f}%")
            
            # VRAM使用进度条
            rich.print(f"       VRAM: {create_progress_bar(vram_percent)} {gpu['memory_used']:.0f}/{gpu['memory_total']:.0f} MB ({vram_percent:.1f}%)")
            
            # 温度信息
            if gpu['temperature']:
                temp = gpu['temperature']
                temp_color = "green" if temp < 70 else "yellow" if temp < 85 else "red"
                rich.print(f"       Temp: [{temp_color}]{temp:.1f}°C[/{temp_color}]")
    else:
        rich.print("[bold yellow]GPU:[/bold yellow] No GPU detected")

    rich.print("[bold yellow]Memory:[/bold yellow]")
    memory_info = get_memory_info_psutil()

    ram_percent = memory_info['percent']
    ram_bar = create_progress_bar(ram_percent)
    rich.print(f"    [green]->[/green] RAM: {ram_bar} {ram_percent:.1f}%")
    rich.print(f"       Used: {memory_info['used']} GB / Total: {memory_info['total']} GB")
    rich.print(f"       Available: {memory_info['available']} GB | Free: {memory_info['free']} GB")
    

    if float(memory_info['swap_total'].replace('N/A', '0')) > 0:
        swap_percent = memory_info['swap_percent']
        swap_bar = create_progress_bar(swap_percent)
        rich.print(f"    [green]->[/green] Swap: {swap_bar} {swap_percent:.1f}%")
        rich.print(f"       Used: {memory_info['swap_used']} GB / Total: {memory_info['swap_total']} GB")
    
    print("\n")
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            percent = usage.percent
            disk_bar = create_progress_bar(percent, width=15)
            
            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            
            rich.print(
                    f"[bold]{partition.device}[/]  [cyan]{partition.mountpoint}[/]",
                    disk_bar,
                    f"[green]{used_gb:.1f}[/]/[bold]{total_gb:.1f} GB[/]  "
                    f"[{'green' if percent < 70 else 'yellow' if percent < 90 else 'red'}]{percent:.1f}%[/]"
                )
        except:
            continue
    print("\n")
    connections = len(psutil.net_connections())
    rich.print(f"[bold yellow]Network Connections:[/bold yellow] {connections}")

    upload, download = get_network_speed()
    rich.print(f"[bold yellow]Network Speed:[/bold yellow]\n    [green]->[/green] Upload: {upload}\n    [green]->[/green] Download: {download}\n")
if __name__ == "__main__":
    main()