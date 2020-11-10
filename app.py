import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
import datetime
import locale
import os
import pyodbc
import pandas
import numpy as np
# from fbprophet import Prophet
import os
from components import Navbar, Indicators

locale.setlocale(locale.LC_TIME, '')

external_scripts = [
        "https://code.jquery.com/jquery-3.3.1.slim.min.js",
        "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"
        ]

external_stylesheets = [
        "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css"
        ]
app = dash.Dash(
    __name__,
    requests_pathname_prefix= "/" if (__name__ == '__main__') else '/wsgi/',
    external_scripts = external_scripts,
    external_stylesheets = external_stylesheets,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

server = app.server

def serve_layout():

    data_file = os.path.join(os.path.dirname('__file__'), 'data/sinadef.csv')
    df = pandas.read_csv(data_file)
    maxDate = max(df.loc[~np.isnan(df['CANT'])]['TheDate'])
    rpDate = ( datetime.datetime.strptime(maxDate,"%Y-%m-%d") + datetime.timedelta(days=2)).strftime('%Y-%m-%d')

    df['moving'] = df.groupby(['TheYear'])['CANT'].transform(lambda x: x.rolling(7, 7).mean())
    column_max = df[df['TheYear']!=2020].groupby(['IDX','NFECHA'], as_index=False)['moving'].max()
    column_max.columns = ['IDX', 'NFECHA', 'CANT']
    column_min = df[df['TheYear']!=2020].groupby(['IDX','NFECHA'], as_index=False)['moving'].min()
    column_min.columns = ['IDX', 'NFECHA', 'CANT']
    column_mean = df[df['TheYear']!=2020].groupby(['IDX','NFECHA'], as_index=False)['moving'].mean()
    column_mean.columns = ['IDX', 'NFECHA', 'CANT']

    febBis = df.loc[(df['TheYear']==2020) & (df['IDX']==229)]['moving']
    fixfactor_mean = column_mean.loc[column_max['IDX'] < 301]['CANT'].sum()
    fixfactor_current = df.loc[(df['TheYear']==2020) & (df['IDX']<301)]['moving'].sum() - febBis

    fixfactor =  fixfactor_current / fixfactor_mean

    column_mean['CANT'] =  column_mean['CANT'].apply(lambda x: x*fixfactor)
    column_min['CANT'] =  column_min['CANT'].apply(lambda x: x*fixfactor)
    column_max['CANT'] =  column_max['CANT'].apply(lambda x: x*fixfactor)

    date_current = df.loc[(df['TheYear']==2020) & (~np.isnan(df['CANT']))]['IDX'].max()

    def_current = df.loc[(df['TheYear']==2020) & (df['IDX']<=date_current)]['CANT'].sum()
    def_expected = df.loc[(df['TheYear']==2019) & (df['IDX']<=date_current)]['CANT'].sum()

    exdef = def_current - def_expected
    exdef_percent = np.rint((exdef / def_current)*100)

    x = df.loc[(df['TheYear']==2020) & (df['IDX']<=date_current) & (df['IDX'] != 229)][['IDX', 'moving']].reset_index(drop=True)
    y = column_max.loc[column_max['IDX']<=date_current]['CANT'].reset_index(drop=True)
    df_compare = pandas.DataFrame({"IDX":x['IDX'],"Value_x":x['moving'], "Value_y":y})
    df_compare['isEx'] = df_compare['Value_x'] > df_compare['Value_y']
    exdat_start = '2020'+ str(df_compare.loc[df_compare['isEx']]['IDX'].min()).zfill(4)
    exdat_end = '2020' + str(df_compare.loc[df_compare['isEx']]['IDX'].max()).zfill(4)
    exdat_start = datetime.datetime.strptime(exdat_start, "%Y%m%d").strftime("%d %B").lower()
    exdat_end = datetime.datetime.strptime(exdat_end, "%Y%m%d").strftime("%d %B").lower()
    exdat_text = exdat_start + ' a ' + exdat_end

    fig = go.Figure(layout=go.Layout(
            xaxis=go.layout.XAxis(title="Fecha"),
            yaxis=go.layout.YAxis(title="Defunciones")
        ))

    fig.add_trace(go.Scatter(x=df["NFECHA"].unique(), y=column_max['CANT'],
                        line = dict(color='rgba(176,182,188,1)', width=1),
                        name='Esperadas M'))
    fig.add_trace(go.Scatter(x=df["NFECHA"].unique(), y=column_min['CANT'],
                        line = dict(color='rgba(176,182,188,1)', width=1), fill='tonexty', fillcolor='rgba(185,207,228,1)',
                        name='Esperadas m'))
    fig.add_trace(go.Scatter(x=column_mean["NFECHA"], y=column_mean['CANT'],
                        line = dict(color='rgba(22,96,167,1)', width=2), fill='tonexty', fillcolor='rgba(185,207,228,1)',
                        name='Esperadas'))
    fig.add_trace(go.Scatter(x=df["NFECHA"].unique(), y=df[df['TheYear']==2020]['CANT'],
                        line = dict(color='blue', width=1, dash='dot'),
                        name='Observadas'))
    fig.add_trace(go.Scatter(x=df["NFECHA"].unique(), y=df[df['TheYear']==2020]['moving'],
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

    graph_bar_title = html.Div(html.Span("Mortalidad por todas las causas. Perú"), className="col-8")

    dash_sinadef_graph = html.Div(
        html.Div([
            html.Div(graph_bar_title, className="chart-title"),
            dcc.Graph(
                id='my-graph',
                figure=fig,
                config={
                    'displayModeBar': False,
                }
            ),

            ] ,className="card-body"),
        className="card my-1",
    )

    navbar = Navbar("SINADEF", rpDate, app)
    indicators = Indicators(exdat_text, exdef, exdef_percent)
    return html.Div([
        navbar,
        indicators,
        dash_sinadef_graph,
    ], className='content')

app.title = 'SINADEF'
app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)
