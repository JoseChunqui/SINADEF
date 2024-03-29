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
from dash.exceptions import PreventUpdate


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
rpDate = '-'
exdat_text = '-'
exdef = '-'
exdef_percent = '-'

def vaccinations_layout():
    graph_bar_title = html.Div(html.Span("Vacunación diaria. Perú", id="vaccinations_graph-title"), className="col-8")

    dash_vaccinations_graph = html.Div(
        html.Div([
            html.Div(graph_bar_title, className="chart-title"),
            dcc.Loading(
                id="loading-1",
                type="default",
                children=dcc.Graph(
                        style={"height": "100%"},
                        id='vaccinations_graph',
                        config={
                            'displayModeBar': False,
                        },
                        className='mt-5'
                    ),

            ),
            ] ,className="card-body", id="my-div"),
        className="card",
    )

    navbar = Navbar("VACUNACIÓN", rpDate, app)
    return html.Div([
        navbar,
        dash_vaccinations_graph,
    ], className='container-fluid', id="ServeLayout")

def sinadef_layout():
    graph_bar_title = html.Div(html.Span("Mortalidad por todas las causas. Perú", id="sinadef_graph-title"), className="col-8")

    dash_sinadef_graph = html.Div(
        html.Div([
            html.Div(graph_bar_title, className="chart-title"),
            dcc.Loading(
                id="loading-1",
                type="default",
                children=dcc.Graph(
                        style={"height": "100%"},
                        id='sinadef_graph',
                        config={
                            'displayModeBar': False,
                        },
                        className='mt-5'
                    ),

            ),
            ] ,className="card-body", id="my-div"),
        className="card",
    )

    navbar = Navbar("SINADEF", rpDate, app)
    indicators = Indicators(exdat_text, exdef, exdef_percent)
    return html.Div([
        navbar,
        indicators,
        dash_sinadef_graph,
    ], className='container-fluid', id="ServeLayout")

@app.callback(
    Output('sinadef_graph', 'figure'),
    [Output(f"indicator-{i}", "children") for i in range(1, 4)],
    Output('rp-date', 'children'),
    Output('sinadef_graph-title', 'children'),
    [Input(f"nav-link-{i}", "n_clicks") for i in range(1, 4)],
    [dash.dependencies.Input('deps-dropdown', 'value')]
)
def update_figure(*args):
    ctx = dash.callback_context

    value_id = 'Nacional'
    st_title = 'Mortalidad por todas las causas. '
    dm_title = 'Perú'
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        value_id = ctx.triggered[0]['value']

    data_file = os.path.join(os.path.dirname('__file__'), 'data/sinadefv2.csv')
    df = pandas.read_csv(data_file)
    df = df[df['IDX'] != 229].reset_index(drop=True)

    if button_id == 'nav-link-2':
        df = df[(df['DEPARTAMENTO'] == 'LIMA') | (df['DEPARTAMENTO'].isnull())].sort_values('TheDate', ascending=True).reset_index()
        dm_title = 'LIMA'
    elif button_id == 'nav-link-3':
        df = df[(df['DEPARTAMENTO'] != 'LIMA') | (df['DEPARTAMENTO'].isnull())]
        df = df.groupby(['NFECHA', 'IDX', 'TheYear', 'TheDate']).agg({'CANT': "sum"}).reset_index().replace({'CANT':{0: np.nan}}).sort_values('TheDate', ascending=True)
        dm_title = 'PROVINCIAS'
    elif button_id == 'deps-dropdown' and value_id != None and value_id != '':
        df = df[(df['DEPARTAMENTO'] == value_id) | (df['DEPARTAMENTO'].isnull())].sort_values('TheDate', ascending=True).reset_index()
        dm_title = value_id
    else:
        df = df.groupby(['NFECHA', 'IDX', 'TheYear', 'TheDate']).agg({'CANT': "sum"}).reset_index().replace({'CANT':{0: np.nan}}).sort_values('TheDate', ascending=True)


    df['moving'] = df['CANT'].transform(lambda x: x.rolling(7, 7).mean())
    df.moving.fillna(df['CANT'], inplace=True)
    df["fecha"] = df["NFECHA"].astype(str) + df['TheYear'].apply(lambda x: ' ' + str(x % 100))

    maxDate = max(df.loc[~np.isnan(df['CANT'])]['TheDate'])
    maxDate = datetime.datetime.strptime(maxDate,"%Y-%m-%d")
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

    fig.add_trace(go.Scatter(x=df_cmax["fecha"], y=df_cmax['CANT'],
                        line = dict(color='rgba(176,182,188,1)', width=1),
                        name='Esperadas M'))
    fig.add_trace(go.Scatter(x=df_cmin["fecha"], y=df_cmin['CANT'],
                        line = dict(color='rgba(176,182,188,1)', width=1), fill='tonexty', fillcolor='rgba(185,207,228,1)',
                        name='Esperadas m'))
    fig.add_trace(go.Scatter(x=df_cmean["fecha"], y=df_cmean['CANT'],
                        line = dict(color='rgba(22,96,167,1)', width=2), fill='tonexty', fillcolor='rgba(185,207,228,1)',
                        name='Esperadas'))
    fig.add_trace(go.Scatter(x=df_cd_wk["fecha"], y=df_cd_wk['CANT'],
                        line = dict(color='blue', width=1, dash='dot'),
                        name='Observadas'))
    fig.add_trace(go.Scatter(x=df_cd_wk["fecha"], y=df_cd_wk['moving'],
                        line = dict(color='black', width=3),
                        name='Media Móvil'))


    fig.update(layout_showlegend=False)
    fig.update_layout(
        autosize=True,
        height=600,
        margin=dict(
            l=0,
            r=0,
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
    return fig, exdat_text, '{:,.0f}'.format(exdef), exdef_percent, "Actualizado el "+ rpDate, st_title + dm_title

@app.callback(
    Output('vaccinations_graph', 'figure'),
    Output('rp-date', 'children'),
    Output('vaccinations_graph-title', 'children'),
    [Input(f"nav-link-{i}", "n_clicks") for i in range(1, 4)],
    [dash.dependencies.Input('deps-dropdown', 'value')]
)
def update_vaccinations_figure(*args):
    ctx = dash.callback_context

    value_id = 'Nacional'
    st_title = 'Vacunación diaria. '
    dm_title = 'Perú'
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        value_id = ctx.triggered[0]['value']

    data_file = os.path.join(os.path.dirname('__file__'), 'data/vacunas.csv')
    df = pandas.read_csv(data_file)

    df['TheYear'] = [ datetime.datetime.strptime(str(x), '%Y%m%d').strftime('%y') for x in df['FECHA_VACUNACION'] ]
    df['TheMonth'] = [ datetime.datetime.strptime(str(x), '%Y%m%d').strftime('%m') for x in df['FECHA_VACUNACION'] ]
    df['TheMonthName'] = [ {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun','07':'Jul','08':'Ago','09':'Set','10':'Oct','11':'Nov','12':'Dic'}[x] for x in df['TheMonth'] ]
    df['TheDay'] = [ datetime.datetime.strptime(str(x), '%Y%m%d').strftime('%d') for x in df['FECHA_VACUNACION'] ]
    df['TheDate'] = [ datetime.datetime.strptime(str(x), '%Y%m%d').strftime('%Y-%m-%d') for x in df['FECHA_VACUNACION'] ]
    df['Fecha'] = df['TheDay'] + ' ' + df['TheMonthName'] + ' ' +  df['TheYear']

    if button_id == 'nav-link-2':
        df = df[(df['DEPARTAMENTO'] == 'LIMA') | (df['DEPARTAMENTO'].isnull())].sort_values('TheDate', ascending=True).reset_index()
        dm_title = 'LIMA'
    elif button_id == 'nav-link-3':
        df = df[(df['DEPARTAMENTO'] != 'LIMA') | (df['DEPARTAMENTO'].isnull())]
        dm_title = 'PROVINCIAS'
    elif button_id == 'deps-dropdown' and value_id != None and value_id != '':
        df = df[(df['DEPARTAMENTO'] == value_id) | (df['DEPARTAMENTO'].isnull())].sort_values('TheDate', ascending=True).reset_index()
        dm_title = value_id

    df = df.groupby(['Fecha','TheDate']).agg({'CANT': "sum"}).reset_index().replace({'CANT':{0: np.nan}}).sort_values('TheDate', ascending=True)
    df['CANT'] = df['CANT'] / 1000
    df.round({'CANT': 1})

    df['moving'] = df['CANT'].transform(lambda x: x.rolling(15, 15).mean())
    df.moving.fillna(df['CANT'], inplace=True)

    maxDate = max(df.loc[~np.isnan(df['CANT'])]['TheDate'])
    maxDate = datetime.datetime.strptime(maxDate,"%Y-%m-%d")
    rpDate = ( maxDate + datetime.timedelta(days=2)).strftime('%Y-%m-%d')

    fig = go.Figure(layout=go.Layout(
            xaxis=go.layout.XAxis(title="Fecha"),
            yaxis=go.layout.YAxis(title="Vacunacion")
        ))

    fig.add_trace(go.Scatter(x=df["Fecha"], y=df['CANT'],
                        line = dict(color='blue', width=1, dash='dot'),
                        name='Observadas'))
    fig.add_trace(go.Scatter(x=df["Fecha"], y=df['moving'],
                        line = dict(color='black', width=3),
                        name='Media Móvil'))


    fig.update(layout_showlegend=False)
    fig.update_layout(
        autosize=True,
        height=1000,
        margin=dict(
            l=0,
            r=0,
            b=0,
            t=20,
            pad=0
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x"
    )
    fig.update_layout(yaxis_range=[0,500])
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(238,238,238,1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(238,238,238,1)')
    return fig, "Actualizado el "+ rpDate, st_title + dm_title

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
    print(button_id)
    if(button_id == 'deps-dropdown'):
        if(ctx.triggered[0]["value"] == None):
            return ["btn btn-link shadow-none nav-link active" if i == 1 else "btn btn-link shadow-none nav-link" for i in range(1, 4)]
        else:
            return ["btn btn-link shadow-none nav-link" for _ in range(1, 4)]

    return [ "btn btn-link shadow-none nav-link active" if button_id == f"nav-link-{i}" else "btn btn-link shadow-none nav-link" for i in range(1, 4) ]

app.title = 'SINADEF'
app.layout = html.Div([
    # represents the URL bar, doesn't render anything
    dcc.Location(id='url', refresh=False),

    # content will be rendered in this element
    html.Div(id='page-content')
])

@app.callback(dash.dependencies.Output('page-content', 'children'),
              dash.dependencies.Output("nav-link-1", "n_clicks"),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    print(pathname)
    if (pathname == '/vacunacion'):
        return vaccinations_layout(),1
    else:
        return sinadef_layout(),1

if __name__ == '__main__':
    app.run_server(debug=True)
