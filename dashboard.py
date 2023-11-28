import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import plotly.express as px


def read_data_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return pd.DataFrame.from_dict(data, orient='index')


app = dash.Dash(__name__)


dataframe = read_data_from_json('orders.json')

app.layout = html.Div([
    html.H1("Телеграм-бот Dashboard"),

    html.Div([
        html.Label('Выберите статус:'),
        dcc.Dropdown(
            id='status-filter',
            multi=True
        )
    ]),

    dcc.Graph(id='status-distribution'),

    html.Button('Обновить данные', id='update-button'),

    html.Div([
        dcc.Input(
            id='search-input',
            type='text',
            placeholder='Введите ID заказа или контакт'
        ),
        html.Button('Поиск', id='search-button')
    ]),

    dash_table.DataTable(
        id='orders-table',
        columns=[{"name": i, "id": i} for i in dataframe.columns],
        data=dataframe.to_dict('records'),
        page_action="native",
        sort_action="native",
        filter_action="native"
    )
])


@app.callback(
    Output('status-filter', 'options'),
    [Input('update-button', 'n_clicks')]
)
def update_status_filter_options(n_clicks):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    df = read_data_from_json('orders.json')
    updated_options = [{'label': s, 'value': s} for s in df['status'].unique()]
    return updated_options


@app.callback(
    [
        Output('orders-table', 'data'),
        Output('status-distribution', 'figure'),
    ],
    [
        Input('update-button', 'n_clicks'),
        Input('status-filter', 'value'),
        Input('search-button', 'n_clicks'),
    ],
    [State('search-input', 'value')]
)
def update_elements(update_clicks, selected_status, search_clicks, search_value):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'update-button':
        df = read_data_from_json('orders.json')
    else:
        df = dataframe

    if selected_status:
        df = df[df['status'].isin(selected_status)]

    if search_value:
        df = df[df['order_id'].str.contains(search_value) | df['contact'].str.contains(search_value)]

    table_data = df.to_dict('records')

    status_counts = df['status'].value_counts()
    fig = px.bar(x=status_counts.index, y=status_counts.values, labels={'x': 'Статус', 'y': 'Количество'})
    fig.update_layout(title='Распределение заказов по статусам')

    return table_data, fig


if __name__ == '__main__':
    app.run_server(debug=True)
