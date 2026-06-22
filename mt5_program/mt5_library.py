import asyncio
from typing import Any, Protocol

import MetaTrader5 as mt5

from app.redis.model.mt5_program_model import MT5ProgramPositionInfo


class MT5ClientProtocol(Protocol):
    def initialize(
        self,
        path: str | None = None,
        *,
        timeout: int | None = None,
    ) -> bool: ...

    def last_error(self) -> tuple[int, str] | Any: ...
    def login(self, login: int, password: str, server: str) -> bool: ...
    def account_info(self) -> Any | None: ...
    def positions_get(self) -> tuple[Any, ...] | None: ...
    def orders_get(self) -> tuple[Any, ...] | None: ...
    def shutdown(self) -> None: ...
    def symbol_info_tick(self, symbol: str) -> Any | None: ...
    def symbol_info(self, symbol: str) -> Any | None: ...
    def order_send(self, request: dict[str, Any]) -> Any: ...
    def symbol_select(self, symbol: str, enable: bool) -> bool: ...


class MT5Library:
    @staticmethod
    async def symbol_info(mt5_client: MT5ClientProtocol, symbol: str) -> Any:
        symbol_info = mt5_client.symbol_info(symbol)
        if symbol_info is None:
            raise ValueError(f"Symbol {symbol} not found in MT5")
        if not symbol_info.visible:
            symbol_selected = mt5_client.symbol_select(symbol, True)
            if not symbol_selected:
                raise ValueError(f"Symbol {symbol} is not visible in MT5")
            await asyncio.sleep(0.5)  # Wait for symbol to be selected
            symbol_info = mt5_client.symbol_info(symbol)
        return symbol_info

    @staticmethod
    async def normalize_volume(
        mt5_client: MT5ClientProtocol, symbol: str, volume: float
    ) -> float:
        symbol_info = await MT5Library.symbol_info(mt5_client, symbol)
        volume_step = getattr(symbol_info, "volume_step", 0.01)
        volume_min = getattr(symbol_info, "volume_min", 0.01)
        volume_max = getattr(symbol_info, "volume_max", 100.0)

        volume = round(volume / volume_step) * volume_step
        volume = max(min(volume, volume_max), volume_min)
        return volume

    @staticmethod
    async def open_buy(
        mt5_client: MT5ClientProtocol,
        symbol: str,
        volume: float,
        comment: str = "",
    ) -> bool:
        normalized_volume = await MT5Library.normalize_volume(
            mt5_client, symbol, volume
        )
        tick: Any = mt5_client.symbol_info_tick(symbol)
        if tick is None:
            raise ValueError(f"Tick not found for symbol {symbol}")
        request: dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": normalized_volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": tick.ask,
            "deviation": 10,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        result = mt5_client.order_send(request)

        if not result.retcode == mt5.TRADE_RETCODE_DONE:
            print(
                f"Failed to open buy position for {symbol} with volume {volume}: {result}"
            )

        return result

    @staticmethod
    async def open_sell(
        mt5_client: MT5ClientProtocol,
        symbol: str,
        volume: float,
        comment: str = "",
    ) -> bool:
        normalized_volume = await MT5Library.normalize_volume(
            mt5_client, symbol, volume
        )
        tick: Any = mt5_client.symbol_info_tick(symbol)
        if tick is None:
            raise ValueError(f"Tick not found for symbol {symbol}")
        request: dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": normalized_volume,
            "type": mt5.ORDER_TYPE_SELL,
            "price": tick.bid,
            "deviation": 10,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        result = mt5_client.order_send(request)

        if not result.retcode == mt5.TRADE_RETCODE_DONE:
            print(
                f"Failed to open sell position for {symbol} with volume {volume}: {result}"
            )

        return result

    @staticmethod
    async def close(
        mt5_client: MT5ClientProtocol,
        position: MT5ProgramPositionInfo,
        comment: str = "",
    ) -> bool:
        symbol = position.get("symbol", "")
        volume = position.get("volume", 0.0)
        ticket = position.get("ticket", 0)
        if volume <= 0.0:
            raise ValueError(f"Invalid volume {volume} for position {ticket}")
        if not symbol:
            raise ValueError(f"Symbol not found for position {ticket}")
        if not ticket:
            raise ValueError(f"Ticket not found for position with symbol {symbol}")
        await MT5Library.symbol_info(mt5_client, symbol)
        tick: Any = mt5_client.symbol_info_tick(symbol)
        if tick is None:
            raise ValueError(f"Tick not found for symbol {symbol} in position {ticket}")

        if position.get("type") == 0:  # Buy
            close_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:  # Sell
            close_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        request: dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "price": price,
            "deviation": 10,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        result = mt5_client.order_send(request)

        if not result.retcode == mt5.TRADE_RETCODE_DONE:
            print(
                f"Failed to close position with ticket {ticket} for symbol {symbol} and volume {volume}: {result}"
            )

        return result
