import sqlite3
import pandas as pd
con = sqlite3.connect("crypto.db")

query_crypto = """
with btc as (select *
             from Crypto
             where symbol = 'BTC'
               and snapshot_time > '2022-01-01'
             order by snapshot_time desc, market_cap_rank asc),
     eth as (select *
             from Crypto
             where symbol = 'ETH'
               and snapshot_time > '2022-01-01'
             order by snapshot_time desc, market_cap_rank asc),
     stx as (select *
             from Crypto
             where symbol = 'STX'
               and snapshot_time > '2022-01-01'
             order by snapshot_time desc, market_cap_rank asc),
     arb as (select *
             from Crypto
             where symbol = 'ARB'
               and snapshot_time > '2022-01-01'
             order by snapshot_time desc, market_cap_rank asc),
     matic as (select *
               from Crypto
               where symbol = 'MATIC'
                 and snapshot_time > '2022-01-01'
               order by snapshot_time desc, market_cap_rank asc),
     atom as (select *
              from Crypto
              where symbol = 'ATOM'
                and snapshot_time > '2022-01-01'
              order by snapshot_time desc, market_cap_rank asc),
     dot as (select *
             from Crypto
             where symbol = 'DOT'
               and snapshot_time > '2022-01-01'
             order by snapshot_time desc, market_cap_rank asc),
     flow as (select *
              from Crypto
              where symbol = 'FLOW'
                and snapshot_time > '2022-01-01'
              order by snapshot_time desc, market_cap_rank asc),
     op as (select *
            from Crypto
            where symbol = 'OP'
              and snapshot_time > '2022-01-01'
            order by snapshot_time desc, market_cap_rank asc),
     near as (select *
              from Crypto
              where symbol = 'NEAR'
                and snapshot_time > '2022-01-01'
              order by snapshot_time desc, market_cap_rank asc),
    sol as (select *
            from Crypto
            where symbol = 'SOL'
                and snapshot_time > '2022-01-01')
        

select btc.snapshot_time    as snapshot_time,
       btc.price_usd        as btc,
       eth.price_usd        as eth,
       eth.price_usd * 15   as eth_15x,
       eth.price_usd * 17   as eth_17x,
       eth.price_usd * 20   as eth_20x,
       stx.price_usd        as stx,
       arb.price_usd        as arb,
       matic.price_usd      as matic,
       matic.price_usd * 12 as matic_12x,
       atom.price_usd       as atom,
       dot.price_usd        as dot,
       dot.price_usd * 1.5  as 'dot_1.5x',
       flow.price_usd       as flow,
       flow.price_usd * 1.2 as 'flow_1.2x',
       flow.price_usd * 8   as flow_8x,
       flow.price_usd * 9   as flow_9x,
       flow.price_usd * 10  as flow_10x,
       flow.price_usd * 12  as flow_12x,
       op.price_usd         as op,
       op.price_usd * 3     as op_3x,
       near.price_usd       as near,
       near.price_usd * 3   as near_3x,
       sol.price_usd        as sol

from btc
     join eth on btc.snapshot_time = eth.snapshot_time
     join stx on btc.snapshot_time = stx.snapshot_time
     join arb on btc.snapshot_time = arb.snapshot_time
     join matic on btc.snapshot_time = matic.snapshot_time
     join atom on btc.snapshot_time = atom.snapshot_time
     join dot on btc.snapshot_time = dot.snapshot_time
     join flow on btc.snapshot_time = flow.snapshot_time
     join op on btc.snapshot_time = op.snapshot_time
     join near on btc.snapshot_time = near.snapshot_time
     join sol on btc.snapshot_time = sol.snapshot_time;
"""

#
# query_crypto = """
# with btc as (select *
#              from Crypto
#              where symbol = 'BTC'
#                and snapshot_time > '2023-01-23'
#              order by snapshot_time desc, market_cap_rank asc),
#      eth as (select *
#              from Crypto
#              where symbol = 'ETH'
#                and snapshot_time > '2023-01-23'
#              order by snapshot_time desc, market_cap_rank asc),
#      op as (select *
#             from Crypto
#             where symbol = 'OP'
#               and snapshot_time > '2023-01-23'
#             order by snapshot_time desc, market_cap_rank asc),
#      near as (select *
#               from Crypto
#               where symbol = 'NEAR'
#                 and snapshot_time > '2023-01-23'
#               order by snapshot_time desc, market_cap_rank asc)
#
# select btc.snapshot_time    as snapshot_time,
#        btc.price_usd        as btc,
#        eth.price_usd        as eth,
#        eth.price_usd * 15   as eth_15x,
#        eth.price_usd * 17   as eth_17x,
#        eth.price_usd * 20   as eth_20x,
#        op.price_usd         as op,
#        op.price_usd * 3     as op_3x,
#        near.price_usd       as near,
#        near.price_usd * 3   as near_3x
#
# from btc
#      join eth on btc.snapshot_time = eth.snapshot_time
#      join op on btc.snapshot_time = op.snapshot_time
#      join near on btc.snapshot_time = near.snapshot_time;
# """
crypto_price_df = pd.read_sql(query_crypto, con=con)


