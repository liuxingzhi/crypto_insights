import okx.Funding as Funding
import okx.MarketData as MarketData
import okx.Account as Account
import okx.PublicData as PublicData
import okx.Trade as Trade
from strategy import calculate_ideal_position
import pandas as pd
import time
import argparse

# 创建 ArgumentParser 对象
parser = argparse.ArgumentParser(description='Process API credentials and account type.')

# 添加参数
parser.add_argument('--api_key', required=True, help='Your API key.')
parser.add_argument('--secret_key', required=True, help='Your secret API key.')
parser.add_argument('--passphrase', required=True, help='Your API passphrase.')
parser.add_argument('--account_type', choices=['prod', 'demo'], required=True, help='Account type (demo or live).')

# 解析命令行参数
args = parser.parse_args()

trading_account = {
    "api_key": args.api_key,
    "secret_key": args.secret_key,
    "passphrase": args.passphrase,
    "account_type": "0" if args.account_type == "prod" else "1"
}


def place_market_order(crypto, stable_coin, side, sz, account):
    trade_api = Trade.TradeAPI(account['api_key'], account['secret_key'], account['passphrase'], False,
                               account['account_type'], debug=True)
    result = trade_api.place_order(
        instId=f"{crypto}-{stable_coin}",
        tdMode="cash",
        side=side,
        ordType="market",
        sz=sz,
    )
    if result["code"] == "0":
        print("Successful order request，order_id = ", result["data"][0]["ordId"])
    else:
        print("Unsuccessful order request，error_code = ", result["data"][0]["sCode"], ", Error_message = ",
              result["data"][0]["sMsg"])


def sell_crypto(crypto, stable_coin, count, account):
    count = abs(count)
    place_market_order(crypto, stable_coin, "sell", count, account)


def buy_crypto(crypto, stable_coin, usd_amount, account):
    place_market_order(crypto, stable_coin, "buy", usd_amount, account)


def rebalance(crypto_1, crypto_2, stable_coin, price_ratio_bounds, account: dict, threshold=0.12):
    account_api = Account.AccountAPI(account['api_key'], account['secret_key'], account['passphrase'], False,
                                     account['account_type'], debug=False)

    coin_balance = account_api.get_account_balance(f'{crypto_1},{crypto_2},{stable_coin}')['data']

    crypto_1_count = 0.0
    crypto_2_count = 0.0
    stable_coin_count = 0.0
    for balance_info in coin_balance[0]['details']:
        if balance_info['ccy'] == crypto_1:
            crypto_1_count = float(balance_info['availBal'])
        elif balance_info['ccy'] == crypto_2:
            crypto_2_count = float(balance_info['availBal'])
        elif balance_info['ccy'] == stable_coin:
            stable_coin_count = float(balance_info['availBal'])

    print(
        f"{crypto_1}_count: {crypto_1_count}, {crypto_2}_count: {crypto_2_count}, {stable_coin_count}_count: {stable_coin_count}")

    public_data_api = PublicData.PublicAPI(flag=account['account_type'], debug=False)
    crypto_1_price = float(public_data_api.get_mark_price(
        'SWAP',
        instId=f"{crypto_1}-USDT-SWAP",  # USDC data often not available, so always use USDT
    )['data'][0]['markPx'])
    crypto_2_price = float(public_data_api.get_mark_price(
        'SWAP',
        instId=f"{crypto_2}-USDT-SWAP",
    )['data'][0]['markPx'])

    print(f"{crypto_1}_price: {crypto_1_price}, {crypto_2}_price: {crypto_2_price}")

    ideal_position = calculate_ideal_position(crypto_1_price, crypto_2_price, price_ratio_bounds)
    print("Ideal position: ", ideal_position.values)

    current_prices = pd.Series([crypto_1_price, crypto_2_price])
    current_holdings = pd.Series([crypto_1_count, crypto_2_count])

    current_balance = current_prices.dot(current_holdings) + stable_coin_count
    ideal_holdings = current_balance * ideal_position.values / current_prices
    print("Ideal holdings: ", ideal_holdings.values)
    print("Current holdings: ", current_holdings.values)
    trade_volume = ideal_holdings - current_holdings
    print("Trade volume: ", trade_volume.values)
    abs_trade_stable_coin_value = abs(trade_volume).dot(abs(current_prices))

    trade_threshold = threshold * current_balance
    print(f"{abs_trade_stable_coin_value=}, {trade_threshold=}, {current_balance=}")

    if abs_trade_stable_coin_value > trade_threshold:
        print("Greater than threshold, Do the trade")
        print(f"{trade_volume.values=}")

        if trade_volume[0] < 0 < trade_volume[1]:
            print(f"Selling {crypto_1} and buying {crypto_2}")
            sell_crypto(crypto_1, stable_coin, trade_volume[0], account)
            stable_coin_balance = float(
                account_api.get_account_balance(stable_coin)['data'][0]['details'][0]['availBal'])
            buy_crypto(crypto_2, stable_coin, stable_coin_balance - 0.01, account)
        elif trade_volume[0] > 0 > trade_volume[1]:
            print(f"Selling {crypto_2} and buying {crypto_1}")
            sell_crypto(crypto_2, stable_coin, trade_volume[1], account)
            stable_coin_balance = float(
                account_api.get_account_balance(stable_coin)['data'][0]['details'][0]['availBal'])
            buy_crypto(crypto_1, stable_coin, stable_coin_balance - 0.01, account)
        elif trade_volume[0] > 0 and trade_volume[1] > 0:
            print(f"Buying {crypto_1} and {crypto_2}")
            buy_crypto(crypto_1, stable_coin, trade_volume[0] * crypto_1_price - 0.01, account)
            buy_crypto(crypto_2, stable_coin, trade_volume[1] * crypto_2_price - 0.01, account)

        for balance_info in coin_balance[0]['details']:
            if balance_info['ccy'] == crypto_1:
                crypto_1_count = float(balance_info['availBal'])
            elif balance_info['ccy'] == crypto_2:
                crypto_2_count = float(balance_info['availBal'])
            elif balance_info['ccy'] == stable_coin:
                stable_coin_count = float(balance_info['availBal'])
        print("reblance finished, new balance: ")
        print(
            f"{crypto_1}_count: {crypto_1_count}, {crypto_2}_count: {crypto_2_count}, {stable_coin_count}_count: {stable_coin_count}")
    else:
        print("Less than threshold, No trade, Exit")


rebalance("NEAR", "OP", "USDT", pd.Series([0.85, 1.15]), trading_account)
# add more crypto pairs here
