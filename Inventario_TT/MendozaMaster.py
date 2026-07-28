import subprocess
import time
import webview
import os
import sys

def arrancar_app():
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless=true", "--global.developmentMode=false"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    webview.create_window("Mendoza Servicios e Herramientas - Sistema Maestro TT", url="http://localhost:8501", width=1200, height=750, resizable=True)
    webview.start()

if __name__ == "__main__":
    arrancar_app()
