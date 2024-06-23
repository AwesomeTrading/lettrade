from typing import Literal

import pandas as pd
import talib.abstract as ta


def keltner_channel(
    dataframe: pd.DataFrame,
    ma: int = 20,
    ma_mode: Literal["ema", "sma"] = "ema",
    atr: int = 20,
    shift: float = 1.6,
    prefix: str = "kc_",
    inplace: bool = False,
) -> dict[str, pd.Series] | pd.DataFrame:
    """_summary_

    Args:
        dataframe (pd.DataFrame): _description_
        ma (int, optional): _description_. Defaults to 20.
        ma_mode (Literal[&quot;ema&quot;, &quot;sma&quot;], optional): _description_. Defaults to "ema".
        atr (int, optional): _description_. Defaults to 20.
        shift (float, optional): _description_. Defaults to 1.6.
        prefix (str, optional): _description_. Defaults to "kc_".
        inplace (bool, optional): _description_. Defaults to False.

    Returns:
        dict[str, pd.Series] | pd.DataFrame: {kc_upper, kc_middle, kc_lower}
    """
    if __debug__:
        if not isinstance(dataframe, pd.DataFrame):
            raise RuntimeError(
                f"dataframe type '{type(dataframe)}' "
                "is not instance of pandas.DataFrame"
            )

    ma_fn = ta.SMA if ma_mode == "sma" else ta.EMA
    i_atr = ta.ATR(dataframe, timeperiod=atr)

    i_basis = ma_fn(dataframe, timeperiod=ma)
    i_upper = i_basis + shift * i_atr
    i_lower = i_basis - shift * i_atr

    # Result is inplace or new dict
    result = dataframe if inplace else {}
    result[f"{prefix}upper"] = i_upper
    result[f"{prefix}basis"] = i_basis
    result[f"{prefix}lower"] = i_lower
    return result
