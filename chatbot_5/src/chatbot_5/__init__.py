import subprocess
args=["uv","run","chainlit","run","src/frontend/app.py","-w"]
subprocess.run(args=args).returncode