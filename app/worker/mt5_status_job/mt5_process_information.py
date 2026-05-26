import subprocess
from pathlib import Path
from typing import Any, List, Optional, Set, TypedDict, cast

import psutil


class Mt5ProcessStatus(TypedDict):
    name: Optional[str]
    pid: Optional[int]
    cpu_percent: float
    memory_mb: float


class Mt5ProcessInformation:
    PROCESS_NAMES: Set[str] = {
        "terminal64.exe",
        "terminal.exe",
        "metatrader5.exe",
    }

    def __init__(
        self,
    ) -> None:
        pass

    def _find_processes(self) -> List[psutil.Process]:
        result: List[psutil.Process] = []

        for proc in psutil.process_iter(
            ["pid", "name", "exe", "cpu_percent", "memory_info"]
        ):
            try:
                name: str = str(proc.info["name"] or "").lower()

                if name in self.PROCESS_NAMES:
                    result.append(proc)
                    continue

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return result

    def is_open(self) -> bool:  # Check MT5 có đang mở không
        processes: List[psutil.Process] = self._find_processes()
        return len(processes) > 0

    def open(self, exe_path: Optional[str]) -> bool:  # Mở MT5
        if self.is_open():
            return True
        if exe_path is None:
            raise ValueError("exe_path is required")

        path = Path(exe_path)
        if not path.exists():
            raise FileNotFoundError(str(path))

        subprocess.Popen(
            [str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        return True

    def close(self) -> bool:  # Đóng MT5
        processes = self._find_processes()
        if not processes:
            return True

        # B1: terminate mềm
        for proc in processes:
            try:
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # B2: chờ process thoát sau khi gửi terminate 5 giây
        gone, alive = psutil.wait_procs(
            processes,
            timeout=5,
        )

        # B3: kill process lì
        for proc in alive:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # B4: chờ lần cuối
        psutil.wait_procs(alive, timeout=3)

        return True

    def is_busy(self) -> bool:
        processes = self._find_processes()

        for proc in processes:
            try:
                cpu = proc.cpu_percent(interval=0.1)
                if cpu > 5.0:  # MT5 đang bận nếu CPU usage > 5%
                    return True
                mem = proc.memory_info().rss / (1024 * 1024)  # Convert to MB
                if mem > 100:  # MT5 đang bận nếu Memory usage > 100MB
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return False

    def get_proc_status(self) -> Mt5ProcessStatus:
        processes = self._find_processes()

        if not processes:
            return {
                "name": None,
                "pid": None,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
            }

        try:
            proc = processes[0]
            # memory_mb = proc.memory_info().rss / (1024 * 1024)  # Convert to MB
            return {
                "name": proc.name(),
                "pid": proc.pid,
                "cpu_percent": round(proc.cpu_percent(interval=1), 2),
                "memory_mb": round(proc.memory_full_info().uss / (1024 * 1024), 2),
            }

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "name": None,
                "pid": None,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
            }


mt5_process_information = Mt5ProcessInformation()
