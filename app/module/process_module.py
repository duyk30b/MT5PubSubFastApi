import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import NotRequired, Required, TypedDict

import psutil

logger = logging.getLogger(__name__)


class ProcessInfo(TypedDict):
    pid: Required[int]
    name: NotRequired[str]
    exe: NotRequired[str]  # Example: D:\Programs\MetaTrader5\terminal64.exe
    cmdline: NotRequired[list[str]]
    status: NotRequired[str]
    create_time: NotRequired[float]
    cpu_percent: NotRequired[float]
    memory_mb: NotRequired[float]
    memory_percent: NotRequired[float]
    is_running: Required[bool]


class ProcessOpenResult(TypedDict):
    open_new: Required[bool]
    process_info: Required[ProcessInfo]


class ProcessModule:
    async def exe_find_process(self, path: str) -> psutil.Process | None:
        path_resolve = Path(path).resolve()
        for proc in psutil.process_iter(
            ["pid", "name", "exe", "cpu_percent", "memory_info"]
        ):
            try:
                proc_exe = proc.info["exe"]
                if not proc_exe:
                    continue
                proc_name: str = str(proc.info["name"] or "").lower()
                if proc_name not in {"terminal64.exe", "terminal.exe"}:
                    continue
                proc_path = Path(proc_exe).resolve()

                if proc_path == path_resolve:
                    return proc

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    async def exe_open(self, path: str) -> ProcessOpenResult:
        open_new = False

        process_opened = await self.exe_find_process(path)
        if process_opened:
            open_new = False
            process = process_opened
        else:
            open_new = True
            try:
                # process = psutil.Popen(path)
                subprocess_proc = subprocess.Popen([path])
                await asyncio.sleep(2)  # Đợi một chút để mt5 khởi động
                process = psutil.Process(subprocess_proc.pid)
            except Exception as e:
                raise Exception(f"Failed to open program {path}: {str(e)}")

        assert process is not None

        return {
            "open_new": open_new,
            "process_info": ProcessInfo(
                pid=process.pid,
                name=process.name() or "",
                exe=process.exe() or "",
                cmdline=process.cmdline(),
                status=process.status(),
                create_time=process.create_time(),
                cpu_percent=process.cpu_percent(interval=1),
                memory_mb=round(process.memory_full_info().uss / (1024 * 1024), 2),
                memory_percent=process.memory_info().rss
                / psutil.virtual_memory().total
                * 100,
                is_running=process.is_running(),
            ),
        }

    async def exe_cleanup(self, path_parent: str, path_list_keep: list[str]):
        path_resolve_list = [Path(path).resolve() for path in path_list_keep]
        for proc in psutil.process_iter(
            ["pid", "name", "exe", "cpu_percent", "memory_info"]
        ):
            try:
                proc_exe = proc.info["exe"]
                if not proc_exe:
                    continue
                proc_name: str = str(proc.info["name"] or "").lower()
                if proc_name not in {"terminal64.exe"}:
                    continue
                proc_path = Path(proc_exe).resolve()

                # Chỉ đóng các MT5 process có đường dẫn exe và đường dẫn có chứa path_parent, và không nằm trong path_list_keep
                if str(proc_path).find(path_parent) == -1:
                    continue

                if proc_path in path_resolve_list:
                    continue
                else:
                    proc.terminate()
                    proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    async def py_find_process(self, program_name: str) -> psutil.Process | None:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                proc_name: str = str(proc.info["name"] or "").lower()
                # pythonw.exe sẽ tự thoát theo python.exe
                if proc_name not in {"python.exe"}:
                    continue

                proc_cmdline = proc.info["cmdline"]
                if not proc_cmdline:
                    continue

                if (
                    len(proc_cmdline) >= 5
                    and proc_cmdline[0] == sys.executable
                    and proc_cmdline[1] == "-m"
                    and proc_cmdline[2] == "mt5_program.mt5_program_runner"
                    and proc_cmdline[3] == "--program_name"
                    and proc_cmdline[4] == program_name
                ):
                    return proc

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    async def py_start(
        self, program_name: str, show_terminal: bool = False
    ) -> ProcessOpenResult:
        open_new = False
        process_opened = await self.py_find_process(program_name)
        if process_opened:
            open_new = False
            process = process_opened
        else:
            open_new = True
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
                    subprocess_proc = subprocess.Popen(
                        command,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                else:
                    subprocess_proc = subprocess.Popen(
                        command,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                await asyncio.sleep(2)  # Đợi một chút để py khởi động
                process = psutil.Process(subprocess_proc.pid)
            except Exception as e:
                raise Exception(f"Failed to start program {program_name}: {str(e)}")

        return {
            "open_new": open_new,
            "process_info": ProcessInfo(
                pid=process.pid,
                name=process.name() or "",
                exe=process.exe() or "",
                cmdline=process.cmdline(),
                status=process.status(),
                create_time=process.create_time(),
                cpu_percent=process.cpu_percent(interval=1),
                memory_mb=round(process.memory_full_info().uss / (1024 * 1024), 2),
                memory_percent=process.memory_info().rss
                / psutil.virtual_memory().total
                * 100,
                is_running=process.is_running(),
            ),
        }

    async def py_cleanup(self, program_name_list_keep: list[str]):
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                proc_name: str = str(proc.info["name"] or "").lower()
                if proc_name not in {"python.exe"}:
                    continue

                proc_cmdline = proc.info["cmdline"]
                if not proc_cmdline:
                    continue

                if (
                    len(proc_cmdline) >= 5
                    and proc_cmdline[0] == sys.executable
                    and proc_cmdline[1] == "-m"
                    and proc_cmdline[2] == "mt5_program.mt5_program_runner"
                    and proc_cmdline[3] == "--program_name"
                ):
                    program_name = proc_cmdline[4]
                    if program_name in program_name_list_keep:
                        continue
                    else:
                        proc.terminate()
                        proc.wait(timeout=5)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    async def process_stop(self, pid: int):
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
        except Exception as e:
            raise Exception(f"Failed to stop program with PID {pid}: {str(e)}")
