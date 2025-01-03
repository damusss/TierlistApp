import os
import shutil

if os.path.exists("Tierlist.exe"):
    os.remove("Tierlist.exe")

os.system(
    "pyinstaller --onefile --icon=appdata/icon.png --name=Tierlist --windowed main.py"
)

shutil.copyfile("dist/Tierlist.exe", "Tierlist.exe")
os.remove("Tierlist.spec")
shutil.rmtree("dist")
shutil.rmtree("build")
