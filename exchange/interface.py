from abc import abstractmethod, ABC
from sqlite3 import Connection
from typing import Any, Tuple
from decimal import Decimal
from common.data_types import SymbolAction


class Exchange(ABC):

    @abstractmethod
    def get_klines(self, symbol_name: str, interval: str, limit: int, start_time: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_market_depth(self, limit: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def determine_my_asset(self) -> Tuple[Decimal, SymbolAction]:
        raise NotImplementedError

    @abstractmethod
    def show_current_limits(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def buy_target_asset(self, quantity: Decimal, price: Decimal, db_connection: Connection) -> None:
        raise NotImplementedError
