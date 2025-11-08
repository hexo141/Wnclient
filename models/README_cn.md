## models文件夹内的所有模块都必须包含一个类（类名与模块名相同），并保存一个启动和结束的调用方法，主程序会分别调用
## 必须创建一个与py脚本名同名的json文件
```python
class example:
    def __init__(self):
        pass
    def start(self):
        pass
    def stop(self):
        pass
```
# 每个程序务必使用多线程，不得堵塞主线程
# 以_为开头的模块不会被执行导入
## JSON配置文件要求如下
```json
{
    "dependence": ["pyside6","example"]
}
```