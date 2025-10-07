import subprocess
args=["uv","run","chainlit","run","src/chatbot/app.py","-w"]

def main():
    return subprocess.run(args).returncode #During execution if error occurs returncode will show the proper error message in terminal.