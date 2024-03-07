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
                                starting_balance=10000, exchange_ratio_threshold=0.6,
                                commission_fee_rate=0.001) -> pd.DataFrame:
    ideal_position_ratio_df = price_df.apply(
        lambda row: calculate_ideal_position(row.iloc[0], row.iloc[1], ratio_range_bounds), axis=1)
    crypto_1, crypto_2, _ = price_df.columns
    ideal_position_ratio_df.columns = [f"{crypto_1}_percent", f"{crypto_2}_percent"]

    start_position_ratio = ideal_position_ratio_df.iloc[0]
    start_holdings = new_holdings = starting_balance * start_position_ratio.values / price_df.iloc[0, :2]
    cash_unused = starting_balance - start_holdings.dot(price_df.iloc[0, :2])

    regression_result_list = [
        {crypto_1: price_df.iloc[0, 0], crypto_2: price_df.iloc[0, 1], 'snapshot_time': price_df.iloc[0, 2],
         f"{crypto_1}_holdings": start_holdings.iloc[0], f"{crypto_2}_holdings": start_holdings.iloc[1],
         f"{crypto_1}_trade_volume": 0, f"{crypto_2}_trade_volume": 0,
         'Commission Fee': starting_balance * commission_fee_rate,
         'Net Balance': starting_balance}]

    for index, ((_, prices_record), (_, ideal_position_ratios)) in enumerate(
            zip(price_df.iterrows(), ideal_position_ratio_df.iterrows())):
        prices_vector = prices_record.iloc[:2]
        snapshot_time = prices_record.iloc[2]
        if index == 0:  # skip first row as that's our starting position
            continue
        prev_holdings = new_holdings
        new_balance = prices_vector.dot(prev_holdings) + cash_unused
        next_holdings = new_balance * ideal_position_ratios.values / prices_vector
        trade_volume = next_holdings - prev_holdings
        abs_trade_usd = abs(trade_volume).dot(abs(prices_vector))

        regression_result_dict = {crypto_1: prices_vector.iloc[0], crypto_2: prices_vector.iloc[1],
                                  'snapshot_time': snapshot_time,
                                  f"{crypto_1}_holdings": prev_holdings.iloc[0],
                                  f"{crypto_2}_holdings": prev_holdings.iloc[1],
                                  f"{crypto_1}_trade_volume": 0,
                                  f"{crypto_2}_trade_volume": 0,
                                  'Commission Fee': 0,
                                  'Net Balance': new_balance}
        if abs_trade_usd / new_balance > exchange_ratio_threshold:
            # print("trade it!")
            new_holdings = next_holdings
            commission_fee_incurred = abs_trade_usd * commission_fee_rate
            regression_result_dict[f"{crypto_1}_trade_volume"] = trade_volume.iloc[0]
            regression_result_dict[f"{crypto_2}_trade_volume"] = trade_volume.iloc[1]
            regression_result_dict['Commission Fee'] = commission_fee_incurred
            regression_result_dict[f"{crypto_1}_holdings"] = new_holdings.iloc[0]
            regression_result_dict[f"{crypto_2}_holdings"] = new_holdings.iloc[1]
            regression_result_dict['Net Balance'] = new_balance - commission_fee_incurred

        regression_result_list.append(regression_result_dict)

    result_df = pd.DataFrame(regression_result_list)

    result_df[f"All in {crypto_1}"] = (starting_balance / price_df[[crypto_1]].iloc[0]) * price_df[[crypto_1]]
    result_df[f"All in {crypto_2}"] = (starting_balance / price_df[[crypto_2]].iloc[0]) * price_df[[crypto_2]]
    return result_df


def run_regression(crypto_1: str, crypto_2: str, price_range_bounds: pd.Series, regression_start_date,
                   regression_end_date, starting_balance=10000,
                   exchange_ratio_threshold=0.1) -> pd.DataFrame:
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
         where {crypto_1}.snapshot_time >= '{regression_start_date}' 
         and {crypto_1}.snapshot_time <= '{regression_end_date}'
    """
    time_series_df = pd.read_sql_query(query_crypto, con)
    # print(time_series_df)
    regression_result_df = coin_pair_exchange_strategy(time_series_df[[crypto_1, crypto_2, 'snapshot_time']],
                                                       price_range_bounds,
                                                       starting_balance=starting_balance,
                                                       exchange_ratio_threshold=exchange_ratio_threshold)
    return regression_result_df


if __name__ == '__main__':
    op_near_ratio_range = pd.Series([0.6, 1.6])
    regression_result_df = run_regression("OP", "NEAR", op_near_ratio_range, '2022-01-01', '2023-02-02')
    print(regression_result_df)
