'''
Minecraft Nickname Generator Core Algorithm
Link: https://github.com/wang-yupu/netease_mc_name_generator/
'''
import random
import hashlib
import time
import os
import json
import rich

def generate_random_nickname(data_dir="Mod/NE_Name/data", structure_key=None):
    # 1. 加载词库数据库
    def load_database():
        """加载所有词库数据"""
        dbs = {}
        db_files = ["前缀.txt", "人名.txt", "人物.txt", "动词.txt", "形容.txt", "物品.txt"]
        
        for filename in db_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as file:
                    key = filename.replace(".txt", "")
                    lines = [line.strip() for line in file if line.strip()]
                    if lines:  # 只添加非空词库
                        dbs[key] = lines
        return dbs
    
    # 2. 加载名称结构配置
    def load_config():
        """加载名称结构配置"""
        config_path = os.path.join(data_dir, "name_strus.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as file:
                name_structures = json.load(file)
        else:
            # 默认配置
            name_structures = {
                "结构1": "前缀+人名+动词",
                "结构2": "前缀+人物+动词", 
                "结构3": "前缀+人物+动词",
                "结构4": "前缀+形容+人名",
                "结构5": "前缀+动词+人物",
                "结构6": "前缀+动词+人名",
                "结构7": "人名+#的+前缀+物品"
            }
        return name_structures, list(name_structures.keys())
    
    # 3. 初始化随机种子
    def init_random_seed():
        """初始化随机种子"""
        seed_str = hashlib.sha512(str(time.time()).encode()).hexdigest()[:8]
        seed = int(seed_str, 16)
        random.seed(seed)
    init_random_seed()
    
    # 加载数据
    dbs = load_database()
    name_structures, structure_keys = load_config()
    
    if not dbs:
        raise ValueError(f"未找到词库文件，请检查目录: {data_dir}")
    
    if not structure_keys:
        raise ValueError("未找到有效的名称结构配置")
    
    # 选择名称结构
    if structure_key and structure_key in name_structures:
        selected_structure = structure_key
    else:
        selected_structure = random.choice(structure_keys)
    
    # 获取结构字符串
    structure_str = name_structures[selected_structure]
    structure_parts = structure_str.split("+")
    
    # 生成各部分
    name_parts = []
    for part in structure_parts:
        if part.startswith("#"):
            # 固定词（如 #的 -> 的）
            name_parts.append(part[1:])
        elif part in dbs:
            # 随机选择词库中的词
            if dbs[part]:  # 确保词库不为空
                name_parts.append(random.choice(dbs[part]))
            else:
                name_parts.append("")
        else:
            # 未知部分，直接使用
            name_parts.append(part)
    
    # 拼接生成最终名称
    generated_name = "".join(name_parts)

    rich.print(f"Generated name: [u]{generated_name}[/u], Selected structure: [u]{selected_structure}[/u], Parts: [u]{name_parts}[/u], Structure string: [u]{structure_str}[/u]")


if __name__ == "__main__":
    generate_random_nickname()