from enum import Enum


class SymbolAction(Enum):
    BUY: str = "BUY"
    SELL: str = "SELL"
    HOLD: str = ""


def get_symbol_action(action: str) -> SymbolAction:

    if action == "BUY":
        return SymbolAction.BUY
    if action == "SELL":
        return SymbolAction.SELL

    return SymbolAction.HOLD
