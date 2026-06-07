import logging
import os
import subprocess
import sys
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


class MT5ProgramControlProcess:
    async def exe_open(self, path: str) -> int:
        try:
            # psutil.Popen(path)
            process = subprocess.Popen([path])
            return process.pid
        except Exception as e:
            raise Exception(f"Failed to open program {path}: {str(e)}")

    async def exe_close(self, pid: int):
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
        except Exception as e:
            raise Exception(f"Failed to close program with PID {pid}: {str(e)}")

    async def py_start(self, program_name: str, show_terminal: bool = False) -> int:
        try:
            python_executable = sys.executable
            command = [
                python_executable,
                "-m",
                "mt5_program.mt5_program_runner",
                "--program_name",
                program_name,
            ]

            if show_terminal:
                creation_flags = 0
                if os.name == "nt":
                    # Always force a visible console window when requested.
                    creation_flags = (
                        subprocess.CREATE_NEW_CONSOLE
                        | subprocess.CREATE_NEW_PROCESS_GROUP
                    )

                process = subprocess.Popen(
                    command,
                    creationflags=creation_flags,
                    close_fds=os.name != "nt",
                )
                return process.pid

            else:
                startupinfo = None
                creation_flags = 0
                if os.name == "nt":
                    pythonw_executable = Path(sys.executable).with_name("pythonw.exe")
                    if pythonw_executable.exists():
                        command[0] = str(pythonw_executable)

                    creation_flags = (
                        subprocess.DETACHED_PROCESS
                        | subprocess.CREATE_NEW_PROCESS_GROUP
                        | subprocess.CREATE_NO_WINDOW
                    )
                    if hasattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB"):
                        creation_flags |= subprocess.CREATE_BREAKAWAY_FROM_JOB

                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=creation_flags,
                    startupinfo=startupinfo,
                    close_fds=os.name != "nt",
                )
                return process.pid
        except Exception as e:
            raise Exception(f"Failed to start program {program_name}: {str(e)}")

    async def py_stop(self, pid: int):
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
        except Exception as e:
            raise Exception(f"Failed to stop program with PID {pid}: {str(e)}")
