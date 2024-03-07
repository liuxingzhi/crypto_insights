import requests
import sqlite3
import datetime
import pandas as pd


def gen_date_list(start, end, step_length_day=30):
    date = start
    while date < end:
        yield date
        date += datetime.timedelta(days=step_length_day)


headers = {"User-Agent": "Mozilla/5.0", "accept-language": "en-US,en"}

for date in gen_date_list(datetime.date(2014, 1, 1),
                          datetime.date(2018, 1, 1),
                          1):
    api = f"https://coincodex.com/api/coincodex/get_historical_snapshot/{date}/0/1000"
    r = requests.get(api, headers=headers)
    try:
        coins_data = r.json()['coins']
        for rank, coin in enumerate(coins_data, start=1):
            coin['snapshot_time'] = date
            coin['market_cap_rank'] = rank

        db_conn = sqlite3.connect('crypto.db')
        cursor = db_conn.cursor()
        cursor.executemany("""insert or ignore into crypto (symbol, name, market_cap_usd, price_usd, snapshot_time, market_cap_rank)
                           values (:symbol, :name, :market_cap_usd, :last_price_usd, :snapshot_time, :market_cap_rank)""",
                           coins_data)
        db_conn.commit()
    except Exception as e:
        print(e)
        print(r.text)
    finally:
        cursor.close()
