import logging
import re
from pathlib import Path
from typing import TypedDict

import psutil
from sqlalchemy.orm import Session

from app.redis.cache.mt5_program_cache import MT5ProgramCache
from app.redis.model.mt5_program_model import MT5ProgramProcessInfo
from app.setting import settings

logger = logging.getLogger(__name__)


class MT5ProgramDiscover(TypedDict):
    program_name: str
    path: str
    exe_pid: int


class MT5ProgramRefresh:
    async def discover_program_list(self, db: Session) -> list[MT5ProgramDiscover]:
        path_root = Path(settings.mt5_program_root_dir)
        if not path_root.exists() or not path_root.is_dir():
            return []

        discover_list: list[MT5ProgramDiscover] = []
        used_names: set[str] = set()
        for folder in sorted([item for item in path_root.iterdir() if item.is_dir()]):
            terminal_path = folder / settings.mt5_terminal_filename
            if not terminal_path.exists():
                continue

            normalized = re.sub(r"[^a-zA-Z0-9]+", "_", folder.name.strip()).strip("_")
            base_name = normalized.lower() or "unknown"
            candidate = base_name
            idx = 2
            while candidate in used_names:
                candidate = f"{base_name}_{idx}"
                idx += 1
            used_names.add(candidate)
            discover_list.append(
                {
                    "program_name": candidate,
                    "path": str(terminal_path),
                    "exe_pid": 0,
                }
            )
        return discover_list

    async def refresh_exe_process(self, discover_list: list[MT5ProgramDiscover]):
        process_info_map: dict[str, MT5ProgramProcessInfo] = {}
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

                number_find = 0

                for discover in discover_list:
                    discover_path = Path(discover["path"]).resolve()

                    if discover_path == proc_path:
                        number_find += 1
                        discover["exe_pid"] = proc.info["pid"]
                        process_info_map[discover["program_name"]] = (
                            MT5ProgramProcessInfo(
                                pid=proc.info["pid"],
                                name=proc.info["name"] or "",
                                exe=proc_exe or "",
                                cmdline=proc.cmdline(),
                                status=proc.status(),
                                create_time=proc.create_time(),
                                cpu_percent=proc.cpu_percent(interval=1),
                                memory_mb=round(
                                    proc.memory_full_info().uss / (1024 * 1024), 2
                                ),
                                memory_percent=proc.memory_info().rss
                                / psutil.virtual_memory().total
                                * 100,
                                is_running=proc.is_running(),
                            )
                        )
                        break

                if number_find == len(discover_list):
                    break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for item in discover_list:
            await MT5ProgramCache.program_information_set_exe_process(
                item["program_name"],
                process_info_map.get(item["program_name"], MT5ProgramProcessInfo()),
            )

    async def refresh_py_process(
        self, discover_list: list[MT5ProgramDiscover], terminate_others: bool = False
    ):
        process_info_map: dict[str, MT5ProgramProcessInfo] = {}
        program_name_list = {
            item["program_name"] for item in discover_list if item.get("exe_pid", 0) > 0
        }

        for proc in psutil.process_iter(
            ["pid", "name", "exe", "cpu_percent", "memory_info"]
        ):
            try:
                proc_exe = proc.info["exe"]
                if not proc_exe:
                    continue

                proc_name: str = str(proc.info["name"] or "").lower()
                # pythonw.exe sẽ tự thoát theo python.exe
                if proc_name not in {"python.exe"}:
                    continue

                cmdline = proc.cmdline()
                if (
                    "-m" not in cmdline
                    or "mt5_program.mt5_program_runner" not in cmdline
                    or "--program_name" not in cmdline
                ):
                    continue

                program_name_process = cmdline[-1]
                if program_name_process in program_name_list:
                    process_info_map[program_name_process] = MT5ProgramProcessInfo(
                        pid=proc.info["pid"],
                        name=proc.info["name"] or "",
                        exe=proc_exe or "",
                        cmdline=proc.cmdline(),
                        status=proc.status(),
                        create_time=proc.create_time(),
                        cpu_percent=proc.cpu_percent(interval=1),
                        memory_mb=round(proc.memory_full_info().uss / (1024 * 1024), 2),
                        memory_percent=proc.memory_info().rss
                        / psutil.virtual_memory().total
                        * 100,
                        is_running=proc.is_running(),
                    )
                else:
                    if terminate_others:
                        proc.terminate()
                        proc.wait(timeout=5)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for item in discover_list:
            await MT5ProgramCache.program_information_set_py_process(
                item["program_name"],
                process_info_map.get(item["program_name"], MT5ProgramProcessInfo()),
            )
