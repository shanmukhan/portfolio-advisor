"""Financial currency and numeric formatters for Indian financial markets."""

from typing import Any, Union
import pandas as pd


def format_inr(
    amount: Any,
    decimals: int = 0,
    include_symbol: bool = True,
    show_plus: bool = False,
) -> str:
    """Format numbers and currencies using the Indian numbering system.

    Formats with Lakhs (1,00,000) and Crores (1,00,00,000) grouping delimiters.

    Examples:
        format_inr(1191318) -> '₹11,91,318'
        format_inr(-141659) -> '-₹1,41,659'
        format_inr(968.3, decimals=2) -> '₹968.30'
        format_inr(50000) -> '₹50,000'
        format_inr(10000000) -> '₹1,00,00,000'

    Args:
        amount: Number, float, int, or numeric string to format.
        decimals: Number of decimal places to preserve.
        include_symbol: Whether to prefix '₹' currency symbol.
        show_plus: Whether to prefix '+' for positive values.

    Returns:
        Formatted currency string, or '-' if input is None or NaN.
    """
    if amount is None or pd.isna(amount):
        return "-"
    try:
        val = float(amount)
    except (ValueError, TypeError):
        return str(amount)

    is_negative = val < 0
    abs_val = abs(val)

    if decimals > 0:
        base = f"{abs_val:.{decimals}f}"
        int_part, dec_part = base.split('.')
        dec_str = '.' + dec_part
    else:
        int_part = str(int(round(abs_val)))
        dec_str = ''

    if len(int_part) <= 3:
        formatted = int_part
    else:
        last3 = int_part[-3:]
        other = int_part[:-3]
        groups = []
        while len(other) > 2:
            groups.insert(0, other[-2:])
            other = other[:-2]
        if other:
            groups.insert(0, other)
        formatted = ','.join(groups) + ',' + last3

    res = formatted + dec_str

    if is_negative:
        sign = "-₹" if include_symbol else "-"
    elif show_plus and val > 0:
        sign = "+₹" if include_symbol else "+"
    else:
        sign = "₹" if include_symbol else ""

    return sign + res
