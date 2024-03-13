import okx.PublicData as PublicData
import okx.MarketData as MarketData

flag = "0"  # live trading: 0, demo trading: 1

# PublicDataAPI = PublicData.PublicAPI(flag=flag)
#
# result = PublicDataAPI.get_instruments(
#     instType="SPOT"
# )
#
# print(result)
#
# r = PublicDataAPI.get_estimated_price(
#     'SPOT',
#     instId=f"OP-USDT-SPOT")
#
# print(r)

market = MarketData.MarketAPI(flag=flag)
r = market.get_ticker("ASTR-USDT")['data'][0]['last']
print(r)