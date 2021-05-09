import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import datetime
import locale
import os
import pyodbc
import pandas
import numpy as np
# from fbprophet import Prophet
import os
from components import Navbar, Indicators

locale.setlocale(locale.LC_TIME, 'es_pe')

external_scripts = [
        "https://code.jquery.com/jquery-3.3.1.slim.min.js",
        "https://cdn.jsdelivr.net/npm/bootstrap@5.0.0/dist/js/bootstrap.bundle.min.js"
        ]

external_stylesheets = [
        "https://cdn.jsdelivr.net/npm/bootstrap@5.0.0/dist/css/bootstrap.min.css",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css"
        ]
app = dash.Dash(
    __name__,
    requests_pathname_prefix= "/" if (__name__ == '__main__') else '/wsgi/',
    external_stylesheets = external_stylesheets,
    external_scripts = external_scripts,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

server = app.server

stYears = [2017,2018,2019];

#indicators
rpDate = ''
exdat_text = ''
exdef = ''
exdef_percent = ''

def serve_layout():

    graph_bar_title = html.Div(html.Span("Mortalidad por todas las causas. Perú"), className="col-8")

    dash_sinadef_graph = html.Div(
        html.Div([

            html.Div(graph_bar_title, className="chart-title"),
            dcc.Graph(
                id='sinadef_graph',
                config={
                    'displayModeBar': False,
                }
            ),

            ] ,className="card-body", id="my-div"),
        className="card my-1",
    )

    navbar = Navbar("SINADEF", rpDate, app)
    indicators = Indicators(exdat_text, exdef, exdef_percent)
    return html.Div([
        navbar,
        # indicators,
        dash_sinadef_graph,
    ], className='content', id="ServeLayout")

app.title = 'SINADEF'
app.layout = serve_layout

@app.callback(
    Output('sinadef_graph', 'figure'),
    [Input(f"nav-link-{i}", "n_clicks") for i in range(1, 4)],
    [dash.dependencies.Input('deps-dropdown', 'value')]
)
def update_figure(*args):
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
        value_id = ''
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        value_id = ctx.triggered[0]['value']

    print(value_id)

    global rpDate
    global exdat_text
    global exdef
    global exdef_percent

    data_file = os.path.join(os.path.dirname('__file__'), 'data/sinadefv2.csv')
    df = pandas.read_csv(data_file)
    df = df[df['IDX'] != 229].reset_index(drop=True)

    if(button_id == 'nav-link-1' or button_id == 'No clicks yet'):
        df = df.groupby(['NFECHA', 'IDX', 'TheYear', 'TheDate']).agg({'CANT': "sum"}).reset_index().replace({'CANT':{0: np.nan}}).sort_values('TheDate', ascending=True)

    if( button_id == 'nav-link-2' ):
        df = df[(df['DEPARTAMENTO'] == 'LIMA') | (df['DEPARTAMENTO'].isnull())].sort_values('TheDate', ascending=True)

    if( button_id == 'nav-link-3' ):
        df = df[(df['DEPARTAMENTO'] != 'LIMA') | (df['DEPARTAMENTO'].isnull())]
        df = df.groupby(['NFECHA', 'IDX', 'TheYear', 'TheDate']).agg({'CANT': "sum"}).reset_index().replace({'CANT':{0: np.nan}}).sort_values('TheDate', ascending=True)

    if( button_id == 'deps-dropdown' ):
        df = df[(df['DEPARTAMENTO'] == value_id) | (df['DEPARTAMENTO'].isnull())].sort_values('TheDate', ascending=True)

    df['moving'] = df['CANT'].transform(lambda x: x.rolling(7, 7).mean())
    df.moving.fillna(df['CANT'], inplace=True)
    df["fecha"] = df["NFECHA"].astype(str) + df['TheYear'].apply(lambda x: ' ' + str(x % 100))

    maxDate = max(df.loc[~np.isnan(df['CANT'])]['TheDate'])
    maxDate = datetime.datetime.strptime(maxDate,"%Y-%m-%d")
    date_current = maxDate.month * 100 + maxDate.day
    rpDate = ( maxDate + datetime.timedelta(days=2)).strftime('%Y-%m-%d')

    df_cd = df[~df['TheYear'].isin(stYears)].copy()
    df_ad = df[df['TheYear'].isin(stYears)].copy()
    df_2019 = df[df['TheYear'] == 2019].copy()
    crYears =  df_cd.TheYear.unique();
    crYears = sorted(crYears)
    mxYear = max(crYears)

    column_max = df_ad.groupby(['IDX','NFECHA'], as_index=False)['moving'].max()
    column_max.columns = ['IDX', 'NFECHA', 'CANT']
    column_min = df_ad.groupby(['IDX','NFECHA'], as_index=False)['moving'].min()
    column_min.columns = ['IDX', 'NFECHA', 'CANT']
    column_mean = df_ad.groupby(['IDX','NFECHA'], as_index=False)['moving'].mean()
    column_mean.columns = ['IDX', 'NFECHA', 'CANT']

    fixfactor_mean = column_mean.loc[column_max['IDX'] < 301]['CANT'].sum()
    fixfactor_current = df.loc[(df['TheYear']==2020) & (df['IDX']<301)]['moving'].sum()

    fixfactor =  fixfactor_current / fixfactor_mean
    column_mean['CANT'] =  column_mean['CANT'].apply(lambda x: x*fixfactor)
    column_min['CANT'] =  column_min['CANT'].apply(lambda x: x*fixfactor)
    column_max['CANT'] =  column_max['CANT'].apply(lambda x: x*fixfactor)

    df_cd_wk = pandas.DataFrame()
    df_abase = pandas.DataFrame()
    df_cmean = pandas.DataFrame()
    df_cmax = pandas.DataFrame()
    df_cmin = pandas.DataFrame()
    for yy in crYears:
        df_cd_crYY = df_cd.loc[(df_cd['TheYear'] == yy) & (~np.isnan(df_cd['CANT']))].copy()
        mxd = max(df_cd_crYY['IDX'])
        mxdw = mxd + 100
        df_abase_crYY = df_2019[df_2019['IDX'] <= mxd ][['IDX', 'CANT']].copy()
        df_abase_crYY['referenceYear'] = yy

        df_cmean_crYY = column_mean[column_mean['IDX'] <= mxdw].copy()
        df_cmean_crYY['CANT'] = df_cmean_crYY['CANT']*(1 + (yy - 2020)*(0.05))
        df_cmean_crYY['referenceYear'] = yy

        df_cmax_crYY = column_max[column_max['IDX'] <= mxdw].copy()
        df_cmax_crYY['CANT'] = df_cmax_crYY['CANT']*(1 + (yy - 2020)*(0.05))
        df_cmax_crYY['referenceYear'] = yy

        df_cmin_crYY = column_min[column_min['IDX'] <= mxdw].copy()
        df_cmin_crYY['CANT'] = df_cmin_crYY['CANT']*(1 + (yy - 2020)*(0.05))
        df_cmin_crYY['referenceYear'] = yy

        df_abase = df_abase.append(df_abase_crYY)
        df_cd_wk = df_cd_wk.append(df_cd_crYY)

        df_cmean = df_cmean.append(df_cmean_crYY)
        df_cmax = df_cmax.append(df_cmax_crYY)
        df_cmin = df_cmin.append(df_cmin_crYY)

    df_cmean['fecha'] = df_cmean["NFECHA"].astype(str) + df_cmean['referenceYear'].apply(lambda x: ' ' + str(x % 100))
    df_cmean['TheDate'] = df_cmean['referenceYear'].astype(str) + df_cmean["IDX"].apply(lambda x: str(x).zfill(4))
    df_cmean['TheDate'] = df_cmean['TheDate'].apply(lambda x: datetime.datetime.strptime(x, "%Y%m%d"))
    df_cmax['fecha'] = df_cmax["NFECHA"].astype(str) + df_cmax['referenceYear'].apply(lambda x: ' ' + str(x % 100))
    df_cmax['TheDate'] = df_cmax['referenceYear'].astype(str) + df_cmax["IDX"].apply(lambda x: str(x).zfill(4))
    df_cmax['TheDate'] = df_cmax['TheDate'].apply(lambda x: datetime.datetime.strptime(x, "%Y%m%d"))
    df_cmin['fecha'] = df_cmin["NFECHA"].astype(str) + df_cmin['referenceYear'].apply(lambda x: ' ' + str(x % 100))
    df_cmin['TheDate'] = df_cmin['referenceYear'].astype(str) + df_cmin["IDX"].apply(lambda x: str(x).zfill(4))
    df_cmin['TheDate'] = df_cmin['TheDate'].apply(lambda x: datetime.datetime.strptime(x, "%Y%m%d"))

    def_current = df_cd_wk['CANT'].sum()
    def_expected = df_abase['CANT'].sum()

    exdef = def_current - def_expected
    exdef_percent = np.rint((exdef / def_current)*100)

    x = df_cd_wk[['TheDate', 'moving']].reset_index(drop=True)
    y = df_cmax[['TheDate', 'CANT']].reset_index(drop=True)
    df_compare = pandas.DataFrame({"TheDate":x['TheDate'],"Value_x":x['moving'], "Value_y":y['CANT']})
    df_compare['isEx'] = df_compare['Value_x'] > df_compare['Value_y']
    exdat_start = str(df_compare.loc[df_compare['isEx']]['TheDate'].min())
    exdat_end = str(df_compare.loc[df_compare['isEx']]['TheDate'].max())
    exdat_text = datetime.datetime.strptime(exdat_start, '%Y-%m-%d').strftime("%d %b %Y") + ' a ' + datetime.datetime.strptime(exdat_end, '%Y-%m-%d').strftime("%d %b %Y")

    fig = go.Figure(layout=go.Layout(
            xaxis=go.layout.XAxis(title="Fecha"),
            yaxis=go.layout.YAxis(title="Defunciones")
        ))

    fig.add_trace(go.Scatter(x=df_cmax["fecha"].unique(), y=df_cmax['CANT'],
                        line = dict(color='rgba(176,182,188,1)', width=1),
                        name='Esperadas M'))
    fig.add_trace(go.Scatter(x=df_cmin["fecha"].unique(), y=df_cmin['CANT'],
                        line = dict(color='rgba(176,182,188,1)', width=1), fill='tonexty', fillcolor='rgba(185,207,228,1)',
                        name='Esperadas m'))
    fig.add_trace(go.Scatter(x=df_cmean["fecha"], y=df_cmean['CANT'],
                        line = dict(color='rgba(22,96,167,1)', width=2), fill='tonexty', fillcolor='rgba(185,207,228,1)',
                        name='Esperadas'))
    fig.add_trace(go.Scatter(x=df_cd_wk["fecha"].unique(), y=df_cd_wk['CANT'],
                        line = dict(color='blue', width=1, dash='dot'),
                        name='Observadas'))
    fig.add_trace(go.Scatter(x=df_cd_wk["fecha"].unique(), y=df_cd_wk['moving'],
                        line = dict(color='black', width=3),
                        name='Media Móvil'))


    fig.update(layout_showlegend=False)
    fig.update_layout(
        autosize=True,
        height=600,
        margin=dict(
            l=0,
            r=10,
            b=0,
            t=20,
            pad=0
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x"
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(238,238,238,1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(238,238,238,1)')
    return fig

@app.callback(
    [Output(f"nav-link-{i}", "className") for i in range(1, 4)],
    [Input(f"nav-link-{i}", "n_clicks") for i in range(1, 4)],
    [dash.dependencies.Input('deps-dropdown', 'value')]
)
def set_active(*args):
    ctx = dash.callback_context

    if not ctx.triggered or not any(args):
        return ["nav-link active" if i == 1 else "nav-link" for i in range(1, 4)]

    # get id of triggering button
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if(button_id =='deps-dropdown'):
        if(ctx.triggered[0]["value"] == None):
            return ["nav-link active" if i == 1 else "nav-link" for i in range(1, 4)]
        else:
            return ["nav-link" for _ in range(1, 4)]

    return [
        "nav-link active" if button_id == f"nav-link-{i}" else "nav-link" for i in range(1, 4)
    ]

@app.callback(
    Output("deps-dropdown", "value"),
    [Input(f"nav-link-{i}", "n_clicks") for i in range(1, 4)],
)
def set_active(*args):
    return ''


if __name__ == '__main__':
    app.run_server(debug=True)
