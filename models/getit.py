import subprocess
import os
import pathlib
class getit:
    def __init__(self):
        self.c_path = str(pathlib.Path(os.getcwd()) / "getit.c")
        self.compile_path = str(pathlib.Path(os.getcwd()) / "getit" / "getit.exe")
        if not os.path.exists(self.compile_path):
            try:
                subprocess.run(f"g++ {self.c_path} -o {self.compile_path}")
            except FileNotFoundError as e:
                print(f"FileNotFound: {e}")
    def start(self):
        try:
            subprocess.run(self.compile_path)
        except FileNotFoundError as e :
            print(f"Error: {e}")
        return {"Wnclient": "Single mission"}
    def stop(self):
        return {"Wnclient": "Single mission"}