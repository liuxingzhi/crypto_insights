from dash import Dash, dcc, html, Input, Output, dash_table, callback
import dash_mantine_components as dmc
import plotly.express as px
from data import crypto_price_df

app = Dash(__name__)

app.layout = dmc.Container(
    [
        dmc.Title(
            "Equity prices", align="center"),
        dmc.Space(h=20),
        dmc.Button("Download Table Data", id="btn_download_csv"),
        dcc.Download(id="download-dataframe-csv"),
        dmc.Space(h=10),
        dmc.MultiSelect(
            label="Select crypto!",
            placeholder="Select all cryptos you like!",
            id="crypto-dropdown",
            # value=["op", "near"],
            data=sorted([{"label": i, "value": i} for i in crypto_price_df.columns[1:]], key=lambda x: x["label"]),
        ),
        dmc.Space(h=60),
        dmc.SimpleGrid(
            [
                dcc.Graph(id="line_chart"),
                dash_table.DataTable(
                    crypto_price_df.to_dict("records"),
                    [{"name": i, "id": i} for i in crypto_price_df.columns],
                    page_size=10,
                    style_table={"overflow-x": "auto"},
                ),
            ],
        ),
    ],
    fluid=True,
)


@callback(
    Output("line_chart", "figure"),
    Input("crypto-dropdown", "value"),
)
def select_stocks(cryptos_selected):
    fig = px.line(data_frame=crypto_price_df, x="snapshot_time", y=cryptos_selected, template="simple_white")
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25), yaxis_title="Price", xaxis_title="Date"
    )
    return fig


@callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_download_csv", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    print(n_clicks, "clicked")
    return dcc.send_data_frame(crypto_price_df.to_csv, "crypto_download.csv")


if __name__ == "__main__":
    app.run_server(debug=True)
