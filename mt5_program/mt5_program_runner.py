import argparse
import asyncio
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Literal, cast

import MetaTrader5 as mt5

from app.redis.cache.mt5_program_cache import MT5ProgramCache
from app.redis.model.mt5_program_model import (
    MT5ProgramAccountInfo,
    MT5ProgramPositionInfo,
)
from app.redis.redis_connection import RedisConnection
from mt5_program.mt5_library import MT5ClientProtocol, MT5Library

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)

logger = logging.getLogger(__name__)

mt5_client = cast(MT5ClientProtocol, mt5)
TIME_SLEEP_SECONDS = 0.1


async def main(program_name: str):
    signal_time_1 = time.perf_counter()
    await RedisConnection.connect()
    signal_time_2 = time.perf_counter()
    await MT5ProgramCache.program_log_push(
        program_name,
        f"Connected to Redis successfully in {(signal_time_2 - signal_time_1) * 1000:.4f} milliseconds!",
    )

    path = await MT5ProgramCache.program_data_get_path(program_name)
    if not path:
        await MT5ProgramCache.program_error_push(
            program_name, "MT5 program path not found"
        )
        return

    if not mt5_client.initialize(path):
        await MT5ProgramCache.program_error_push(
            program_name,
            f"MT5 initialize failed: {mt5_client.last_error()}",
        )
        return

    await MT5ProgramCache.program_log_push(program_name, f"MT5 open with path: {path}")

    try:
        while True:
            refresh_time = (
                datetime.now(timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )

            account_info_follower_raw = mt5_client.account_info()
            if not account_info_follower_raw:
                last_error = mt5_client.last_error()
                await MT5ProgramCache.program_error_push(
                    program_name,
                    f"MT5 account_info failed: {last_error}",
                )
                await MT5ProgramCache.program_data_set_runtime_snapshot(
                    program_name=program_name,
                    refresh_time=refresh_time,
                    account_info={"login": 0},
                    position_list=[],
                )
                break

            account_info_follower: MT5ProgramAccountInfo = (
                account_info_follower_raw._asdict()
            )

            position_list_raw = mt5_client.positions_get()
            if position_list_raw is None:
                last_error = mt5_client.last_error()
                await MT5ProgramCache.program_error_push(
                    program_name,
                    f"MT5 positions_get failed: {last_error}",
                )
                await MT5ProgramCache.program_data_set_runtime_snapshot(
                    program_name=program_name,
                    refresh_time=refresh_time,
                    account_info=account_info_follower,
                    position_list=[],
                )
                break

            position_list_follower: list[MT5ProgramPositionInfo] = [
                position._asdict() for position in position_list_raw
            ]

            await MT5ProgramCache.program_data_set_runtime_snapshot(
                program_name=program_name,
                refresh_time=refresh_time,
                account_info=account_info_follower,
                position_list=position_list_follower,
            )

            login_key_follower = account_info_follower.get("login", 0)
            mt5_account_follower = await MT5ProgramCache.mt5_account_get_by_login_key(
                login_key_follower
            )
            if not mt5_account_follower:
                await MT5ProgramCache.program_error_push(
                    program_name,
                    f"Follower account with login {login_key_follower} not found in account settings, skipping copy trading",
                )
                await asyncio.sleep(5)
                continue

            if account_info_follower.get("currency") == "USC":
                continue  # Nếu là tài khoản cent, bỏ qua copy trading vì không hỗ trợ

            ### === Xử lý copy trading nếu có thiết lập === ###
            if mt5_account_follower["isCopying"]:
                login_key_master = mt5_account_follower["copyMasterLogin"]
                mt5_account_master = await MT5ProgramCache.mt5_account_get_by_login_key(
                    login_key_master
                )
                program_name_master = mt5_account_master["programName"]

                if not mt5_account_master["id"] or not program_name_master:
                    await MT5ProgramCache.program_error_push(
                        program_name,
                        f"Master account with login {login_key_master} not found in account settings, skipping copy trading",
                    )
                    await asyncio.sleep(5)
                    continue

                program_data_master = await MT5ProgramCache.program_data_get_all(
                    program_name_master
                )
                py_process_master = program_data_master.get("py_process", {})
                position_list_master = program_data_master.get("position_list", [])

                if not py_process_master.get("is_running", False):
                    await MT5ProgramCache.program_error_push(
                        program_name,
                        f"Master program {program_name_master} is not running, skipping copy trading",
                    )
                    await asyncio.sleep(5)
                    continue

                tickets_master = {
                    position.get("ticket", 0) for position in position_list_master
                }
                tickets_followed: set[int] = set()
                PREFIX = f"{mt5_account_master['id']}_"

                def _ticket_from_comment(comment: str) -> int | None:
                    if not comment.startswith(PREFIX):
                        return None
                    ticket_suffix = comment[len(PREFIX) :].lstrip("_")
                    if not ticket_suffix.isdigit():
                        return None
                    return int(ticket_suffix)

                position_map_follower: dict[int, MT5ProgramPositionInfo] = {}
                for position in position_list_follower:
                    comment = position.get("comment", "")
                    ticket_id_cur = _ticket_from_comment(comment)
                    if ticket_id_cur is not None:
                        tickets_followed.add(ticket_id_cur)
                        position_map_follower[ticket_id_cur] = position

                tickets_to_open = tickets_master - tickets_followed
                tickets_to_close = tickets_followed - tickets_master

                position_master_map_ticket = {
                    position.get("ticket", 0): position
                    for position in position_list_master
                }

                if tickets_to_close:
                    for ticket in tickets_to_close:
                        position_follower = position_map_follower.get(ticket)
                        if not position_follower:
                            await MT5ProgramCache.program_error_push(
                                program_name,
                                f"Cannot find follower position with ticketMasterId {ticket} in follower account, skipping close",
                            )
                            continue
                        symbol = position_follower.get("symbol", "")
                        volume = position_follower.get("volume", 0.0)
                        if not symbol:
                            await MT5ProgramCache.program_error_push(
                                program_name,
                                f"Cannot find symbol for ticketMasterId {ticket} in follower account, skipping close",
                            )
                            continue
                        await MT5Library.close(
                            mt5_client=mt5_client,
                            position=position_follower,
                            comment=f"{PREFIX}{ticket}",
                        )
                        await MT5ProgramCache.program_log_push(
                            program_name,
                            f"Close Position - {symbol}, volume:{volume}. Closed from master position {ticket}",
                        )

                if tickets_to_open:
                    account_info_master = (
                        await MT5ProgramCache.program_data_get_account_info(
                            program_name_master
                        )
                    )

                    if not account_info_master:
                        await MT5ProgramCache.program_error_push(
                            program_name,
                            f"Cannot get account info for master account {login_key_master}, skipping copy positions",
                        )
                        continue
                    if not account_info_master.get("balance", 0.0) > 0:
                        await MT5ProgramCache.program_error_push(
                            program_name,
                            f"Master account {login_key_master} has non-positive balance, skipping copy positions",
                        )
                        continue

                    for ticket in tickets_to_open:
                        position_master = position_master_map_ticket.get(ticket)
                        if not position_master or not position_master.get("symbol"):
                            await MT5ProgramCache.program_error_push(
                                program_name,
                                f"Cannot find symbol for ticket {ticket} in master account, skipping copy",
                            )
                            continue

                        time_position = (
                            position_master.get("time_update_msc", 0)
                            + mt5_account_master["timeCorrectionSeconds"] * 1000
                        )
                        time_now = int(time.time() * 1000)

                        # Nếu lệnh đã cũ hơn 5 phút, bỏ qua không copy
                        if time_now - time_position > 5 * 60 * 1000:
                            continue

                        symbol_master = position_master.get("symbol", "")
                        symbol_suffix_master = mt5_account_master["symbolSuffix"]
                        symbol_normalized = symbol_master
                        if symbol_suffix_master and symbol_master.endswith(
                            symbol_suffix_master
                        ):
                            symbol_normalized = symbol_master[
                                : -len(symbol_suffix_master)
                            ]
                        symbol_suffix_follower = mt5_account_follower["symbolSuffix"]
                        symbol_follower = symbol_normalized + symbol_suffix_follower

                        volume_master = position_master.get("volume", 0.0)
                        volume_follower = await MT5Library.normalize_volume(
                            mt5_client,
                            symbol_follower,
                            (
                                volume_master
                                * account_info_follower.get("equity", 0.0)
                                / account_info_master.get("equity", 0.0)
                            ),
                        )
                        position_type: Literal["Buy", "Sell"] = (
                            "Buy" if position_master.get("type", 0) == 0 else "Sell"
                        )

                        if position_type == "Buy":
                            await MT5Library.open_buy(
                                mt5_client=mt5_client,
                                symbol=symbol_follower,
                                volume=volume_follower,
                                comment=f"{PREFIX}{ticket}",
                            )
                        elif position_type == "Sell":
                            await MT5Library.open_sell(
                                mt5_client=mt5_client,
                                symbol=symbol_follower,
                                volume=volume_follower,
                                comment=f"{PREFIX}{ticket}",
                            )

                        await MT5ProgramCache.program_log_push(
                            program_name,
                            f"Open {position_type} - {symbol_follower}, volume:{volume_follower}. Copied from master position {ticket}",
                        )

            await asyncio.sleep(TIME_SLEEP_SECONDS)

    except Exception as e:
        error_detail = traceback.format_exc()
        await MT5ProgramCache.program_error_push(
            program_name,
            f"MT5 program runner encountered an error:  {str(e)}\n{error_detail}",
        )

    finally:
        mt5_client.shutdown()
        await MT5ProgramCache.program_error_push(
            program_name,
            f"Exit PY Runner at {time.strftime('%Y-%m-%d %H:%M:%S')}",
        )
        await MT5ProgramCache.program_data_set_py_process(
            program_name, {"pid": 0, "is_running": False}
        )
        await RedisConnection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_name", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.program_name))
