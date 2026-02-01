import pathlib
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import psutil
import time
import os
import lwjgl
import threading

def process_single_file(src_file, backup_path, manifest, relative_path):
    try:
        # 创建对应的备份文件路径
        dest_path = backup_path / relative_path
        dest_path.mkdir(parents=True, exist_ok=True)

        dest_file = dest_path / src_file.name
        
        # 复制文件
        with open(src_file, 'rb') as sf, open(dest_file, 'wb') as df:
            df.write(sf.read())
        
        # 计算并记录文件的MD5
        with open(src_file, 'rb') as f:
            file_content = f.read()
            manifest[str(dest_file)] = hashlib.md5(file_content).hexdigest()
        
        print(f"Backed up {src_file} -> {dest_file}")
        return src_file, True
    except Exception as e:
        print(f"Error processing {src_file}: {e}")
        return src_file, False

def copy_file(backup_dirs, file_num=0):
    for dir_path in backup_dirs:
        backup_path = pathlib.Path(dir_path) / "Wnclient_Backups"
        backup_path.mkdir(parents=True, exist_ok=True)
        print(f"Backup directory created at: {backup_path}")
        
        # 创建一份含有md5的清单文件
        manifest_path = backup_path / "backup_manifest.json"
        manifest = {}
        
        # 收集所有需要备份的文件
        files_to_backup = []
        file_relative_paths = {}

        remove_dir = ['.git', '.vscode', '__pycache__', '.idea', 'venv', 'env', 'node_modules']
        for root, dirs, files in os.walk(os.getcwd()):
            if any(dir_name in dirs for dir_name in remove_dir):
                dirs[:] = [d for d in dirs if d not in remove_dir]
            for file in files:
                src_file = pathlib.Path(root) / file
                relative_path = pathlib.Path(root).relative_to(os.getcwd())
                files_to_backup.append(src_file)
                file_relative_paths[src_file] = relative_path
        
        print(f"Found {len(files_to_backup)} files to backup")
        
        # 使用多线程处理文件复制
        with ThreadPoolExecutor(max_workers=min(os.cpu_count() * 2, 32)) as executor:
            # 提交所有文件处理任务
            future_to_file = {}
            for src_file in files_to_backup:
                relative_path = file_relative_paths[src_file]
                future = executor.submit(
                    process_single_file, 
                    src_file, 
                    backup_path, 
                    manifest, 
                    relative_path
                )
                future_to_file[future] = src_file
            
            # 等待所有任务完成并收集结果
            successful = 0
            failed = 0
            
            for future in as_completed(future_to_file):
                src_file = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"Task for {src_file} generated an exception: {e}")
                    failed += 1
        
        # 保存清单文件
        with open(manifest_path, 'w') as mf:
            json.dump(manifest, mf, indent=4)
        
        lwjgl.info(f"Backup completed. Successful: {successful}, Failed: {failed}")
        lwjgl.info(f"Manifest saved to: {manifest_path}")


def restore_files_batch(file_batch, backup_base_path):
    """恢复一批文件（无限循环监听）"""
    while True:
        for backup_file_path_str, expected_md5 in file_batch.items():
            backup_file_path = pathlib.Path(backup_file_path_str)
            
            # 计算目标文件路径（去掉备份目录前缀）
            relative_path = backup_file_path.relative_to(backup_base_path)
            target_file_path = pathlib.Path(os.getcwd()) / relative_path
            
            # 检查备份文件是否存在
            if not backup_file_path.exists():
                print(f"Backup file {backup_file_path} does not exist, skipping.")
                continue
            
            # 检查目标文件是否存在
            if not target_file_path.exists():
                print(f"Restoring missing file: {target_file_path}")
                try:
                    target_file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(backup_file_path, 'rb') as src, open(target_file_path, 'wb') as dst:
                        dst.write(src.read())
                    print(f"Restored: {target_file_path}")
                except Exception as e:
                    print(f"Error restoring {target_file_path}: {e}")
                continue
            
            # 检查目标文件的MD5
            try:
                with open(target_file_path, 'rb') as f:
                    current_md5 = hashlib.md5(f.read()).hexdigest()
                
                if current_md5 != expected_md5:
                    print(f"MD5 mismatch for {target_file_path}, restoring...")
                    with open(backup_file_path, 'rb') as src, open(target_file_path, 'wb') as dst:
                        dst.write(src.read())
                    print(f"Restored: {target_file_path}")
            except Exception as e:
                print(f"Error checking/restoring {target_file_path}: {e}")
        
        # 每次检查完一批文件后等待一段时间
        time.sleep(5)

def AutoRestore():
    """启动自动恢复线程"""
    # 查找可用的备份清单
    backup_dirs = []
    for partition in psutil.disk_partitions():
        if 'rw' in partition.opts:
            backup_dirs.append(partition.mountpoint)
    
    manifest_data = None
    backup_base_path = None
    
    # 加载第一个找到的备份清单
    for backup_dir in backup_dirs:
        manifest_path = pathlib.Path(backup_dir) / "Wnclient_Backups" / "backup_manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
                backup_base_path = manifest_path.parent
                print(f"Loaded backup manifest from: {manifest_path}")
                break
            except Exception as e:
                print(f"Error loading manifest from {manifest_path}: {e}")
                continue
    
    if manifest_data is None:
        print("No backup manifest found in any backup directory.")
        return
    
    # 将文件分配给多个线程
    batch_size = psutil.cpu_count() or 4  # 每个线程处理一批文件
    file_items = list(manifest_data.items())
    threads = []
    
    # 创建线程，每个线程处理一部分文件
    for i in range(0, len(file_items), batch_size):
        file_batch = dict(file_items[i:i + batch_size])
        if file_batch:  # 确保批次不为空
            thread = threading.Thread(
                target=restore_files_batch,
                args=(file_batch, backup_base_path),
                daemon=True  # 设置为守护线程，主程序退出时自动结束
            )
            threads.append(thread)
            thread.start()
            print(f"Started restore thread {len(threads)} handling {len(file_batch)} files")
    
    print(f"Started {len(threads)} restore threads for continuous monitoring.")
    return threads  # 返回线程列表以便后续管理

def toggle_auto_backup(enable: bool):
    config_path = pathlib.Path("Mod/AutoBackup/auto_backup.json")
    if enable:
        with open(config_path, 'w') as f:
            json.dump({"enabled": True}, f)
        
        # 查找可以存储备份的目录
        backup_dirs = []
        for partition in psutil.disk_partitions():
            if 'rw' in partition.opts:
                backup_dirs.append(partition.mountpoint)
        
        print("Available backup directories:", backup_dirs)
        
        # 创建备份文件夹并启动恢复
        if backup_dirs:
            copy_file([backup_dirs[0]], file_num=0)
            # 启动自动恢复（返回线程对象以便管理）
            restore_threads = AutoRestore()
            # 可以将restore_threads保存到全局变量以便后续停止
        else:
            print("No writable backup directories found!")
    else:
        with open(config_path, 'w') as f:
            json.dump({"enabled": False}, f)
        print("Auto backup/restore disabled.")