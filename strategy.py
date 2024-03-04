import sqlite3
import pandas as pd
import numpy as np


def calculate_ideal_position(c1_price: float, c2_price: float, ratio_range_bounds: pd.Series) -> pd.Series:
    price_ratio = c1_price / c2_price
    lower_bound, upper_bound = ratio_range_bounds
    percentile = (price_ratio - lower_bound) / abs(upper_bound - lower_bound)
    if percentile < 0:
        percentile = 0
    elif percentile > 1:
        percentile = 1
    c1_position = 1 - percentile
    c2_position = percentile
    return pd.Series([c1_position, c2_position])


def coin_pair_exchange_strategy(price_df: pd.DataFrame, ratio_range_bounds: pd.Series,
                                starting_balance=10000) -> pd.DataFrame:
    ideal_position_ratio_df = price_df.apply(
        lambda row: calculate_ideal_position(row.iloc[0], row.iloc[1], ratio_range_bounds), axis=1)
    crypto_1, crypto_2 = price_df.columns
    ideal_position_ratio_df.columns = [f"{crypto_1}_percent", f"{crypto_2}_percent"]

    start_position_ratio = ideal_position_ratio_df.iloc[0]
    start_holdings = new_holdings = starting_balance * start_position_ratio.values / price_df.iloc[0]

    balances = [starting_balance]
    holdings = [new_holdings]
    for index, ((_, prices), (_, ideal_position_ratios)) in enumerate(
            zip(price_df.iterrows(), ideal_position_ratio_df.iterrows())):
        if index == 0:  # skip first row as that's our starting position
            continue
        new_balance = prices.dot(new_holdings)
        new_holdings = new_balance * ideal_position_ratios.values / prices
        balances.append(new_balance)
        holdings.append(new_holdings)
    holdings_df = pd.DataFrame(holdings)
    holdings_df.columns = [f"{crypto_1}_holdings", f"{crypto_2}_holdings"]
    result_df = pd.concat([price_df,
                           ideal_position_ratio_df,
                           holdings_df,
                           pd.Series(balances, name='Net Balance')], axis=1)

    result_df[f"All in {crypto_1}"] = (starting_balance / price_df[[crypto_1]].iloc[0]) * price_df[[crypto_1]]
    result_df[f"All in {crypto_2}"] = (starting_balance / price_df[[crypto_2]].iloc[0]) * price_df[[crypto_2]]
    return result_df


def run_regression(crypto_1: str, crypto_2: str, price_range_bounds: pd.Series, starting_balance=10000) -> pd.DataFrame:
    crypto_1 = crypto_1.upper()
    crypto_2 = crypto_2.upper()
    con = sqlite3.connect("crypto.db")
    query_crypto = f"""
    with {crypto_1} as (select *
                from Crypto
                where symbol = '{crypto_1}'),
         {crypto_2} as (select *
                  from Crypto
                  where symbol = '{crypto_2}')
         select {crypto_1}.price_usd as {crypto_1},
                {crypto_2}.price_usd as {crypto_2},
                {crypto_1}.snapshot_time as snapshot_time
         from {crypto_1}
            join {crypto_2}
                on {crypto_1}.snapshot_time = {crypto_2}.snapshot_time
         where {crypto_1}.snapshot_time > '2023-01-23'
    """
    time_series_df = pd.read_sql_query(query_crypto, con)
    # print(time_series_df)
    regression_result_df = coin_pair_exchange_strategy(time_series_df[[crypto_1, crypto_2]],
                                                       price_range_bounds,
                                                       starting_balance=starting_balance)
    return pd.concat([regression_result_df, time_series_df['snapshot_time']], axis=1)


if __name__ == '__main__':
    op_near_ratio_range = pd.Series([0.6, 1.6])
    regression_result_df = run_regression("OP", "NEAR", op_near_ratio_range)
    print(regression_result_df)
