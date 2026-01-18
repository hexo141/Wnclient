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
from PIL import Image
import requests
from io import BytesIO
import numpy as np

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

def image_to_ascii_colored(image_url_or_path, max_width=40):
    """
    Convert an image to colored ASCII art using Unicode block characters
    with proper aspect ratio correction for terminal characters
    Returns a list of colored strings for each line
    """
    try:
        # Load image from URL or local path
        if image_url_or_path.startswith(('http://', 'https://')):
            response = requests.get(image_url_or_path)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(image_url_or_path)
        
        # Convert to RGB if needed
        img = img.convert('RGB')
        
        # Get original dimensions
        original_width, original_height = img.size
        
        # Terminal characters are about 2 times taller than wide
        # To maintain aspect ratio, we need to adjust height by factor 0.5
        terminal_char_aspect_ratio = 2.0  # Character height/width ratio
        
        # Calculate new dimensions preserving aspect ratio
        aspect_ratio = original_height / original_width
        
        # Adjust for terminal character aspect ratio
        new_width = max_width
        # Formula: new_height = (original_height / original_width) * new_width / terminal_char_aspect_ratio
        new_height = int(aspect_ratio * new_width / terminal_char_aspect_ratio)
        
        # Ensure minimum height
        if new_height < 10:
            new_height = 10
            
        # Ensure maximum height (can adjust based on your needs)
        max_height = 40
        if new_height > max_height:
            new_height = max_height
            # Recalculate width to maintain aspect ratio
            new_width = int(new_height * terminal_char_aspect_ratio / aspect_ratio)
        
        # Resize image with high-quality resampling
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Define Unicode block characters with different fill levels
        # Using full block characters for better density
        chars = ["█", "▓", "▒", "░", " "]
        
        # Convert to ASCII art with colors
        ascii_lines = []
        pixels = np.array(img)
        
        for row in pixels:
            line_parts = []
            for pixel in row:
                r, g, b = pixel
                # Calculate brightness and select character
                brightness = 0.299 * r + 0.587 * g + 0.114 * b  # Human perception formula
                
                # Map brightness to character index (0-4)
                char_index = int(brightness / 51)  # 51 = 255/5
                char_index = min(4, max(0, char_index))
                
                # Reverse so brighter pixels get more filled characters
                char_index = 4 - char_index
                char = chars[char_index]
                
                # Convert to hex color
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Create colored character
                line_parts.append(f"[{hex_color}]{char}[/{hex_color}]")
            
            ascii_lines.append("".join(line_parts))
        
        return ascii_lines
    
    except Exception as e:
        print(f"Error loading image: {e}")
        # Return a placeholder ASCII art
        return [
            "[#FF0000]█[/#FF0000][#FF6600]█[/#FF6600][#FFCC00]█[/#FFCC00][#00FF00]█[/#00FF00][#0066FF]█[/#0066FF][#6600FF]█[/#6600FF]",
            "[#FF0000]No Image[/#FF0000][#FF6600] Loaded[/#FF6600]",
            "[#00FF00]Use:[/#00FF00] python script.py --image path/to/image.jpg"
        ]

def display_system_info_with_image(info_lines, image_lines, image_width=40):
    """Display system info with ASCII image on the left"""
    console = rich.get_console()
    
    # Calculate maximum height needed
    max_height = max(len(info_lines), len(image_lines))
    
    # Pad both lists to the same height
    image_lines_padded = list(image_lines) + [""] * (max_height - len(image_lines))
    info_lines_padded = list(info_lines) + [""] * (max_height - len(info_lines))
    
    # Display side by side
    for i, (img_line, info_line) in enumerate(zip(image_lines_padded, info_lines_padded)):
        # Print image on left (with fixed width), then system info
        console.print(f"{img_line:<{image_width}}  {info_line}")

def get_system_info_lines():
    """Get all system information as a list of formatted lines"""
    info_lines = []
    
    # Title
    info_lines.append(f"[bold red]{os.getlogin()}[/bold red] @ [bold red]{socket.gethostname()}[/bold red]")
    info_lines.append("[bold cyan]" + "─" * 40 + "[/bold cyan]")
    
    # Basic information
    info = get_terminal_and_shell()
    info_lines.append(f"[bold yellow]OS:[/bold yellow] {platform.platform()}")
    info_lines.append(f"[bold yellow]Kernel:[/bold yellow] {platform.release()}")
    info_lines.append(f"[bold yellow]Process:[/bold yellow] {len(psutil.pids())}")
    
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    info_lines.append(f"[bold yellow]Uptime:[/bold yellow] {uptime_str}")
    info_lines.append(f"[bold yellow]Shell:[/bold yellow] {info.get('shell')}")
    info_lines.append(f"[bold yellow]Terminal:[/bold yellow] {info.get('terminal')}")
    
    # CPU information
    cpu_percent = psutil.cpu_percent(interval=0.1)
    info_lines.append(f"[bold yellow]CPU:[/bold yellow] {platform.processor()}")
    info_lines.append(f"    [green]->[/green] Usage: {create_progress_bar(cpu_percent)} {cpu_percent:.1f}%")
    info_lines.append(f"    [green]->[/green] Machine: {platform.machine()}")
    
    # Display information
    monitors = screeninfo.get_monitors()
    info_lines.append(f"[bold yellow]Screen[/bold yellow] ({len(monitors)}):")
    for i, monitor in enumerate(monitors):
        info_lines.append(f"    [green]->[/green] Display {i}: {monitor.name} ([bold blue]{monitor.width}x{monitor.height}[/bold blue])")

    # GPU information
    if gpus:
        info_lines.append(f"[bold yellow]GPU[/bold yellow] ({len(gpus)}):")
        for gpu in gpus:
            gpu_load = gpu['load']
            vram_percent = (gpu['memory_used'] / gpu['memory_total']) * 100 if gpu['memory_total'] > 0 else 0
            
            # GPU compute load progress bar
            info_lines.append(f"    [green]->[/green] GPU {gpu['id']}: {gpu['name']}")
            info_lines.append(f"       Load: {create_progress_bar(gpu_load)} {gpu_load:.1f}%")
            
            # VRAM usage progress bar
            info_lines.append(f"       VRAM: {create_progress_bar(vram_percent)} {gpu['memory_used']:.0f}/{gpu['memory_total']:.0f} MB ({vram_percent:.1f}%)")
            
            # Temperature information
            if gpu['temperature']:
                temp = gpu['temperature']
                temp_color = "green" if temp < 70 else "yellow" if temp < 85 else "red"
                info_lines.append(f"       Temp: [{temp_color}]{temp:.1f}°C[/{temp_color}]")
    else:
        info_lines.append("[bold yellow]GPU:[/bold yellow] No GPU detected")

    # Memory information
    info_lines.append("[bold yellow]Memory:[/bold yellow]")
    memory_info = get_memory_info_psutil()

    ram_percent = memory_info['percent']
    ram_bar = create_progress_bar(ram_percent)
    info_lines.append(f"    [green]->[/green] RAM: {ram_bar} {ram_percent:.1f}%")
    info_lines.append(f"       Used: {memory_info['used']} GB / Total: {memory_info['total']} GB")
    info_lines.append(f"       Available: {memory_info['available']} GB | Free: {memory_info['free']} GB")
    
    # Swap memory
    if float(memory_info['swap_total'].replace('N/A', '0')) > 0:
        swap_percent = memory_info['swap_percent']
        swap_bar = create_progress_bar(swap_percent)
        info_lines.append(f"    [green]->[/green] Swap: {swap_bar} {swap_percent:.1f}%")
        info_lines.append(f"       Used: {memory_info['swap_used']} GB / Total: {memory_info['swap_total']} GB")
    
    info_lines.append("")  # Empty line
    
    # Disk information
    disk_count = 0
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            percent = usage.percent
            disk_bar = create_progress_bar(percent, width=15)
            
            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            
            info_lines.append(
                f"[bold]{partition.device}[/]  [cyan]{partition.mountpoint}[/]  "
                f"{disk_bar}  "
                f"[green]{used_gb:.1f}[/]/[bold]{total_gb:.1f} GB[/]  "
                f"[{'green' if percent < 70 else 'yellow' if percent < 90 else 'red'}]{percent:.1f}%[/]"
            )
            disk_count += 1
        except:
            continue
    
    if disk_count == 0:
        info_lines.append("[yellow]No disk information available[/yellow]")
    
    info_lines.append("")  # Empty line
    
    # Network information
    connections = len(psutil.net_connections())
    info_lines.append(f"[bold yellow]Network Connections:[/bold yellow] {connections}")

    upload, download = get_network_speed()
    info_lines.append(f"[bold yellow]Network Speed:[/bold yellow]")
    info_lines.append(f"    [green]->[/green] Upload: {upload}")
    info_lines.append(f"    [green]->[/green] Download: {download}")
    
    return info_lines

def main(image_url_or_path=None):
    # Create main panel
    console = rich.get_console()
    
    # Get terminal size for better layout
    terminal_size = console.size
    terminal_width = terminal_size.width
    
    # Calculate image width based on terminal size
    # Use about 1/3 of terminal width for image, maximum 40 characters
    image_width = min(40, terminal_width // 3)
    
    # Generate ASCII image if provided
    image_lines = []
    if image_url_or_path:
        image_lines = image_to_ascii_colored(image_url_or_path, max_width=image_width)
    
    # Get system information lines
    info_lines = get_system_info_lines()
    
    # Display with image if provided, otherwise just system info
    if image_url_or_path and image_lines:
        display_system_info_with_image(info_lines, image_lines, image_width)
    else:
        for line in info_lines:
            console.print(line)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Display system information with optional image')
    parser.add_argument('--image', '-i', help='Path or URL to an image file')
    
    args = parser.parse_args()
    
    if args.image:
        main(args.image)
    else:
        # Run without image
        main()