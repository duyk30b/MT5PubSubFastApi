import argparse
import asyncio
import logging
import time
import traceback
from typing import cast

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
TIME_SLEEP_SECONDS = 0.25


async def main(program_name: str):
    signal_time_1 = time.perf_counter()
    await RedisConnection.connect()
    await MT5ProgramCache.program_log_push(
        program_name, "Connected to Redis successfully !"
    )
    signal_time_2 = time.perf_counter()
    print(
        f"{program_name}: Connected to Redis successfully in {(signal_time_2 - signal_time_1) * 1000:.4f} milliseconds!"
    )

    path = await MT5ProgramCache.program_information_get_path(program_name)
    if not path:
        await MT5ProgramCache.program_error_push(
            program_name, "MT5 program path not found"
        )
        print(f"{program_name}: MT5 program path not found")
        return

    if not mt5_client.initialize(path):
        await MT5ProgramCache.program_error_push(
            program_name,
            f"MT5 initialize failed: {mt5_client.last_error()}",
        )
        print(f"{program_name}: MT5 initialize failed: {mt5_client.last_error()}")
        return

    await MT5ProgramCache.program_log_push(program_name, f"MT5 open with path: {path}")
    print(f"{program_name}: MT5 open with path: {path}")

    try:
        while True:
            refresh_time = time.strftime("%Y-%m-%d %H:%M:%S")

            account_info_follower_raw = mt5_client.account_info()
            if not account_info_follower_raw:
                last_error = mt5_client.last_error()
                await MT5ProgramCache.program_error_push(
                    program_name,
                    f"MT5 account_info failed: {last_error}",
                )
                print(f"{program_name}: MT5 account_info failed: {last_error}")
                await MT5ProgramCache.program_information_set_runtime_snapshot(
                    program_name=program_name,
                    refresh_time=refresh_time,
                    account_info={},
                    position_list=[],
                )
                await asyncio.sleep(5)
                continue

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
                print(f"{program_name}: MT5 positions_get failed: {last_error}")
                await MT5ProgramCache.program_information_set_runtime_snapshot(
                    program_name=program_name,
                    refresh_time=refresh_time,
                    account_info=account_info_follower,
                    position_list=[],
                )
                await asyncio.sleep(5)
                continue

            position_list_follower: list[MT5ProgramPositionInfo] = [
                position._asdict() for position in position_list_raw
            ]

            await MT5ProgramCache.program_information_set_runtime_snapshot(
                program_name=program_name,
                refresh_time=refresh_time,
                account_info=account_info_follower,
                position_list=position_list_follower,
            )

            copy_enabled = await MT5ProgramCache.program_information_get_copy_status(
                program_name
            )
            ### === Xử lý copy trading nếu có thiết lập === ###
            if copy_enabled:
                id_login_follower = account_info_follower.get("login", 0)
                mt5_account_follower = (
                    await MT5ProgramCache.account_setting_get_mt5_account(
                        id_login_follower
                    )
                )
                if not mt5_account_follower:
                    await MT5ProgramCache.program_error_push(
                        program_name,
                        f"Follower account with login {id_login_follower} not found in account settings, skipping copy trading",
                    )
                    print(
                        f"{program_name}: Follower account with login {id_login_follower} not found in account settings, skipping copy trading"
                    )
                    await asyncio.sleep(5)
                    continue

                id_login_master = mt5_account_follower.get("copyMasterLogin", 0)

                account_setting_master = await MT5ProgramCache.account_setting_get_all(
                    id_login_master
                )
                mt5_account_master = account_setting_master.get("mt5_account", {})
                program_name_master = account_setting_master.get("program_name", "")

                if not mt5_account_master:
                    await MT5ProgramCache.program_error_push(
                        program_name,
                        f"Master account with login {id_login_master} not found in account settings, skipping copy trading",
                    )
                    print(
                        f"{program_name}: Master account with login {id_login_master} not found in account settings, skipping copy trading"
                    )
                    await asyncio.sleep(5)
                    continue

                program_information_master = (
                    await MT5ProgramCache.program_information_get_all(
                        program_name_master
                    )
                )
                py_process_master = program_information_master.get("py_process", {})
                position_list_master = program_information_master.get(
                    "position_list", []
                )

                if not py_process_master.get("is_running", False):
                    await MT5ProgramCache.program_error_push(
                        program_name,
                        f"Master program {program_name_master} is not running, skipping copy trading",
                    )
                    print(
                        f"{program_name}: Master program {program_name_master} is not running, skipping copy trading"
                    )
                    await asyncio.sleep(5)
                    continue

                tickets_master = {
                    position.get("ticket", 0) for position in position_list_master
                }
                tickets_followed: set[int] = set()
                PREFIX = f"{mt5_account_master.get('id', 0)}_"

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
                            print(
                                f"{program_name}: Cannot find follower position with ticketMasterId {ticket} in follower account, skipping close"
                            )
                            continue
                        symbol = position_follower.get("symbol", "")
                        volume = position_follower.get("volume", 0.0)
                        if not symbol:
                            await MT5ProgramCache.program_error_push(
                                program_name,
                                f"Cannot find symbol for ticketMasterId {ticket} in follower account, skipping close",
                            )
                            print(
                                f"{program_name}: Cannot find symbol for ticketMasterId {ticket} in follower account, skipping close"
                            )
                            continue
                        MT5Library.close(
                            mt5_client=mt5_client,
                            position=position_follower,
                            comment=f"{PREFIX}{ticket}",
                        )
                        await MT5ProgramCache.program_log_push(
                            program_name,
                            f"Close Position - Symbol:{symbol}, volume:{volume}. Closed from master position {ticket}",
                        )
                        print(
                            f"{program_name}: Close Position - Symbol:{symbol}, volume:{volume}. Closed from master position {ticket}"
                        )

                if tickets_to_open:
                    tick = mt5_client.symbol_info_tick("EURUSD")
                    time_msc = tick.time_msc if tick else 0
                    account_info_master = (
                        await MT5ProgramCache.program_information_get_account_info(
                            program_name_master
                        )
                    )
                    if not account_info_master:
                        await MT5ProgramCache.program_error_push(
                            program_name,
                            f"Cannot get account info for master account {id_login_master}, skipping copy positions",
                        )
                        print(
                            f"{program_name}: Cannot get account info for master account {id_login_master}, skipping copy positions"
                        )
                        continue
                    if not account_info_master.get("balance", 0.0) > 0:
                        await MT5ProgramCache.program_error_push(
                            program_name,
                            f"Master account {id_login_master} has non-positive balance, skipping copy positions",
                        )
                        print(
                            f"{program_name}: Master account {id_login_master} has non-positive balance, skipping copy positions"
                        )
                        continue

                    for ticket in tickets_to_open:
                        position_master = position_master_map_ticket.get(ticket)
                        if not position_master or not position_master.get("symbol"):
                            await MT5ProgramCache.program_error_push(
                                program_name,
                                f"Cannot find symbol for ticket {ticket} in master account, skipping copy",
                            )
                            print(
                                f"{program_name}: Cannot find symbol for ticket {ticket} in master account, skipping copy"
                            )
                            continue

                        time_update = position_master.get("time_update_msc", 0)

                        if (
                            time_msc - time_update > 5 * 60 * 1000
                        ):  # Nếu lệnh đã cũ hơn 5 phút, bỏ qua không copy
                            continue

                        symbol = position_master.get("symbol", "")
                        volume_master = position_master.get("volume", 0.0)
                        volume_follower = (
                            volume_master
                            * account_info_follower.get("balance", 0.0)
                            / account_info_master.get("balance", 0.0)
                        )

                        if position_master.get("type") == 0:  # Buy
                            MT5Library.open_buy(
                                mt5_client=mt5_client,
                                symbol=symbol,
                                volume=volume_follower,
                                comment=f"{PREFIX}{ticket}",
                            )
                        elif position_master.get("type") == 1:  # Sell
                            MT5Library.open_sell(
                                mt5_client=mt5_client,
                                symbol=symbol,
                                volume=volume_follower,
                                comment=f"{PREFIX}{ticket}",
                            )
                        else:
                            await MT5ProgramCache.program_error_push(
                                program_name,
                                f"Unknown position type {position_master.get('type')} for ticket {ticket} in master account, skipping copy",
                            )
                            print(
                                f"{program_name}: Unknown position type {position_master.get('type')} for ticket {ticket} in master account, skipping copy"
                            )
                            continue

                        await MT5ProgramCache.program_log_push(
                            program_name,
                            f"Open Position - Symbol:{symbol}, volume:{volume_follower}. Copied from master position {ticket}",
                        )
                        print(
                            f"{program_name}: Open Position - Symbol:{symbol}, volume:{volume_follower}. Copied from master position {ticket}"
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
        await RedisConnection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_name", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.program_name))
