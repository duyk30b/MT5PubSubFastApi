from typing import NotRequired, Required, TypedDict

from app.module.process_module import ProcessInfo
from app.postgres.entities.mt5_account_entity import MT5AccountDict


class MT5ProgramAccountInfo(TypedDict):
    login: Required[int]
    balance: NotRequired[float]
    profit: NotRequired[float]
    equity: NotRequired[float]
    margin: NotRequired[float]
    margin_free: NotRequired[float]
    margin_level: NotRequired[float]
    name: NotRequired[str]
    server: NotRequired[str]
    currency: NotRequired[str]
    company: NotRequired[str]


class MT5ProgramPositionInfo(TypedDict):
    ticket: Required[int]
    time: Required[int]
    time_msc: Required[int]
    time_update: Required[int]
    time_update_msc: Required[int]
    magic: Required[int]
    volume: Required[float]
    price_open: Required[float]
    sl: Required[float]
    tp: Required[float]
    price_current: Required[float]
    profit: Required[float]
    symbol: Required[str]
    comment: Required[str]


class MT5ProgramData(TypedDict):
    refresh_time: Required[str]
    path: Required[str]
    exe_process: Required[ProcessInfo]
    py_process: Required[ProcessInfo]
    account_info: Required[MT5ProgramAccountInfo]
    position_list: Required[list[MT5ProgramPositionInfo]]


class MT5ProgramInfo(TypedDict):
    program_name: Required[str]
    data: Required[MT5ProgramData]
    mt5_account: Required[MT5AccountDict]
    error_list: Required[list[str]]
    log_list: Required[list[str]]
