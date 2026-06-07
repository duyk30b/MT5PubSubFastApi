from typing import TypedDict

from app.postgres.entities.mt5_account_entity import MT5AccountDict


class MT5ProgramProcessInfo(TypedDict, total=False):
    pid: int
    name: str
    exe: str  # Example: D:\Programs\MetaTrader5\terminal64.exe
    cmdline: list[str]
    status: str
    create_time: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    is_running: bool


class MT5ProgramAccountInfo(TypedDict, total=False):
    login: int
    balance: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    name: str
    server: str
    currency: str
    company: str


class MT5ProgramPositionInfo(TypedDict, total=True):
    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    magic: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    profit: float
    symbol: str
    comment: str


class MT5ProgramInformation(TypedDict, total=True):
    refresh_time: str
    path: str
    copy_enabled: bool
    exe_process: MT5ProgramProcessInfo
    py_process: MT5ProgramProcessInfo
    account_info: MT5ProgramAccountInfo
    position_list: list[MT5ProgramPositionInfo]


class MT5ProgramAccountSetting(TypedDict, total=True):
    mt5_account: MT5AccountDict
    program_name: str


class MT5ProgramData(TypedDict, total=True):
    program_name: str
    information: MT5ProgramInformation
    account_setting: MT5ProgramAccountSetting
    error_list: list[str]
    log_list: list[str]
