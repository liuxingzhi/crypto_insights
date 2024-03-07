from dash import Dash, dcc, html, Input, Output, dash_table, callback, State
import dash_mantine_components as dmc
import plotly.express as px
from data import crypto_price_df
import sqlite3
import pandas as pd
from strategy import run_regression
from datetime import datetime, timedelta, date

app = Dash(__name__)
app.layout = dmc.Container(
    [
        dmc.Title(
            "Equity prices", align="center"),
        dmc.Space(h=20),
        dmc.Button("Download Table Data", id="download-csv-btn"),
        dcc.Download(id="download-dataframe-csv"),
        dmc.Space(h=10),
        dmc.MultiSelect(
            label="Select crypto!",
            placeholder="Select all cryptos you like!",
            id="crypto-dropdown",
            value=[crypto_name for crypto_name in crypto_price_df.columns if crypto_name != "snapshot_time"][:2],
            data=sorted([{"label": i, "value": i} for i in crypto_price_df.columns[1:]], key=lambda x: x["label"]),
        ),
        dmc.Space(h=60),
        dmc.SimpleGrid(
            [
                dcc.Graph(id="crypto-price-line-chart"),
                dash_table.DataTable(
                    crypto_price_df.to_dict("records"),
                    [{"name": i, "id": i} for i in crypto_price_df.columns],
                    page_size=10,
                    style_table={"overflow-x": "auto"},
                ),
                dmc.Title(
                    "Regression Test", align="center"),
                dmc.Space(h=20),
                dmc.SimpleGrid(
                    [
                        dmc.Select(
                            label="Select First Crypto!",
                            placeholder="Select all cryptos you like!",
                            id="regression-first-crypto-select",
                            data=sorted([{"label": i, "value": i} for i in crypto_price_df.columns if
                                         i != "snapshot_time" and "_" not in i],
                                        key=lambda x: x["label"]),
                        ),
                        dmc.Select(
                            label="Select Second Crypto!",
                            placeholder="Select all cryptos you like!",
                            id="regression-second-crypto-select",
                            data=sorted([{"label": i, "value": i} for i in crypto_price_df.columns if
                                         i != "snapshot_time" and "_" not in i],
                                        key=lambda x: x["label"]),
                        ),
                        dmc.TextInput(
                            label="start date",
                            placeholder="YYYY-MM-DD to YYYY-MM-DD",
                            id="stat-start-date-input",
                            value="2022-01-01"
                        ),
                        dmc.TextInput(
                            label="end date",
                            placeholder="YYYY-MM-DD to YYYY-MM-DD",
                            id="stat-end-date-input",
                            value=datetime.now().strftime("%Y-%m-%d")
                        ),
                        dmc.Space(h=10),
                    ],
                    cols=2
                ),

                dash_table.DataTable(
                    page_size=10,
                    style_table={"overflow-x": "auto"},
                    id="pre-run-statistics-table",
                ),

                dmc.SimpleGrid(
                    [
                        dmc.NumberInput(
                            label="Input Ratio Range Lower Bound!",
                            placeholder="Select all cryptos you like!",
                            id="ratio-range-lower-bound",
                            precision=2,
                            value=0.85,
                        ),
                        dmc.NumberInput(
                            label="Input Ratio Range Upper Bound!",
                            placeholder="Select all cryptos you like!",
                            id="ratio-range-upper-bound",
                            precision=2,
                            value=1.15,
                        ),
                        dmc.TextInput(
                            label="start date",
                            placeholder="YYYY-MM-DD to YYYY-MM-DD",
                            id="regression-start-date-input",
                            value="2022-01-01"
                        ),
                        dmc.TextInput(
                            label="end date",
                            placeholder="YYYY-MM-DD to YYYY-MM-DD",
                            id="regression-end-date-input",
                            value=datetime.now().strftime("%Y-%m-%d")
                        ),
                        dmc.NumberInput(
                            label="exchange threshold",
                            placeholder="from 0.1 to 1",
                            id="exchange-ratio-threshold",
                            precision=2,
                            value=0.5,
                        ),
                        dmc.Space(h=60),
                    ],
                    cols=2
                ),
                dmc.Button("Run Regression", id="run-regression-btn"),
                dcc.Graph(id="regression-result-chart"),
                dash_table.DataTable(
                    page_size=10,
                    style_table={"overflow-x": "auto"},
                    id="regression-result-table",
                ),
            ],
        ),
    ],
    fluid=True,
)


@callback(
    Output("crypto-price-line-chart", "figure"),
    Output("regression-first-crypto-select", "value"),
    Output("regression-second-crypto-select", "value"),
    Input("crypto-dropdown", "value"),
)
def select_cryptos(cryptos_selected):
    fig = px.line(data_frame=crypto_price_df, x="snapshot_time", y=cryptos_selected, template="simple_white")
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25), yaxis_title="Price", xaxis_title="Date"
    )

    return (fig,
            cryptos_selected[0] if len(cryptos_selected) >= 1 else None,
            cryptos_selected[1] if len(cryptos_selected) >= 2 else None)


@callback(
    Output("pre-run-statistics-table", "columns"),
    Output("pre-run-statistics-table", "data"),
    Output("ratio-range-lower-bound", "value"),
    Output("ratio-range-upper-bound", "value"),
    Input("regression-first-crypto-select", "value"),  # 不触发回调，但在回调中使用的State
    Input("regression-second-crypto-select", "value"),
    Input("stat-start-date-input", "value"),
    Input("stat-end-date-input", "value"),
    prevent_initial_call=True,
)
def calculate_statistics(crypto_1, crypto_2, start_date, end_date):
    if not crypto_1 or not crypto_2 or not start_date or not end_date:
        return [], []

    crypto_1 = crypto_1.upper()
    crypto_2 = crypto_2.upper()
    con = sqlite3.connect("crypto.db")

    stat_query = f"""
            with {crypto_1} as (select *
                        from Crypto
                        where symbol = '{crypto_1}'),
                 {crypto_2} as (select *
                          from Crypto
                          where symbol = '{crypto_2}'),
                 price_ratio as (select {crypto_1}.snapshot_time              as snapshot_time,
                                        {crypto_1}.price_usd / {crypto_2}.price_usd as price_ratio
                                 from {crypto_1}
                                      join {crypto_2}
                                           on {crypto_1}.snapshot_time = {crypto_2}.snapshot_time
                                 where {crypto_1}.snapshot_time >= '{start_date}' and {crypto_1}.snapshot_time <= '{end_date}'),
                 aggregated as (select avg(price_ratio)                    as avg_ratio,
                                       min(price_ratio)                    as min_ratio,
                                       max(price_ratio)                    as max_ratio,
                                       max(price_ratio) - min(price_ratio) as ratio_range
                                from price_ratio)
            
            select avg_ratio,
                   min_ratio,
                   max_ratio,
                   ratio_range,
                   (SELECT COUNT(*) FROM price_ratio WHERE price_ratio > (SELECT avg_ratio FROM Aggregated)) AS count_gt,
                   (SELECT COUNT(*) FROM price_ratio WHERE price_ratio < (SELECT avg_ratio FROM Aggregated)) AS count_lt
            from aggregated;
        """
    # print(stat_query)
    stat_df = pd.read_sql(stat_query, con=con)
    columns = [{"name": i, "id": i} for i in stat_df.columns]
    return columns, stat_df.to_dict("records"), stat_df["min_ratio"].iloc[0], stat_df["max_ratio"].iloc[0]


@callback(
    Output("regression-result-chart", "figure"),
    Output("regression-result-table", "columns"),
    Output("regression-result-table", "data"),
    State("regression-first-crypto-select", "value"),  # 不触发回调，但在回调中使用的State
    State("regression-second-crypto-select", "value"),
    State("ratio-range-lower-bound", "value"),
    State("ratio-range-upper-bound", "value"),
    State("regression-start-date-input", "value"),
    State("regression-end-date-input", "value"),
    State("exchange-ratio-threshold", "value"),
    Input("run-regression-btn", "n_clicks"),
    prevent_initial_call=True,
)
def regression_handler(crypto_1, crypto_2, ratio_range_lower_bound, ratio_range_upper_bound, regression_start_date,
                       regression_end_date, exchange_ratio_threshold, n_clicks):
    if not crypto_1 or not crypto_2 or not ratio_range_lower_bound or not ratio_range_upper_bound:
        return {}, [], []

    regression_result_df = run_regression(crypto_1, crypto_2,
                                          pd.Series([ratio_range_lower_bound, ratio_range_upper_bound]),
                                          regression_start_date, regression_end_date,
                                          exchange_ratio_threshold=exchange_ratio_threshold)
    crypto_1 = crypto_1.upper()
    crypto_2 = crypto_2.upper()

    fig = px.line(data_frame=regression_result_df, x="snapshot_time",
                  y=[f"All in {crypto_1}", f"All in {crypto_2}", "Net Balance"],
                  template="simple_white")
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25), yaxis_title="Net Balance", xaxis_title="Date"
    )
    columns = [{"name": i, "id": i} for i in regression_result_df.columns]
    # return fig
    return fig, columns, regression_result_df.to_dict("records")


@callback(
    Output("download-dataframe-csv", "data"),
    Input("download-csv-btn", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    print(n_clicks, "clicked")
    return dcc.send_data_frame(crypto_price_df.to_csv, "crypto_download.csv")


if __name__ == "__main__":
    app.run_server(debug=True)
