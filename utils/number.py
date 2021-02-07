from math import ceil

def round_decimals_up(number, decimals=2):
    """
    Returns a value rounded up to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return ceil(number)

    factor = 10 ** decimals
    return ceil(number * factor) / factor