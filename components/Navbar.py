import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

def Navbar(title, rpDate, app):
    deps = [
    'AMAZONAS',
    'ANCASH',
    'APURIMAC',
    'AREQUIPA',
    'AYACUCHO',
    'CAJAMARCA',
    'CALLAO',
    'CUSCO',
    'EXTRANJERO',
    'HUANCAVELICA',
    'HUANUCO',
    'ICA',
    'JUNIN',
    'LA LIBERTAD',
    'LAMBAYEQUE',
    'LIMA',
    'LORETO',
    'MADRE DE DIOS',
    'MOQUEGUA',
    'PASCO',
    'PIURA',
    'PUNO',
    'SAN MARTIN',
    'SIN REGISTRO',
    'TACNA',
    'TUMBES',
    'UCAYALI'
    ]

    return html.Nav([
        html.Div([
            html.A(title, className='navbar-brand'),
            html.Button(
                [ html.Span(className='navbar-toggler-icon') ],
                className='navbar-toggler',
                type='button',
                **{
                    'data-toggle': 'collapse',
                    'data-target': '#navbarText',
                    'aria-controls': 'navbarText',
                    'aria-expanded': 'false',
                    'aria-label': 'Toggle navigation'
                }
            ),
            html.Div([
                html.Ul([
                    html.Li([
                        html.A("Nacional", href="#", className = "nav-link active", id="nav-link-1")
                    ], className='nav-item active'),
                    html.Li([
                        html.A("Lima", href="#", className = "nav-link", id="nav-link-2")
                    ], className='nav-item'),
                    html.Li([
                        html.A("Provincias", href="#", className = "nav-link", id="nav-link-3")
                    ], className='nav-item'),
                    html.Li([
                        html.Div([
                            dcc.Dropdown(
                                id='deps-dropdown',
                                options=[ {'label': x , 'value': x } for x in deps ],
                                style={'width': '200px',  'display': 'inline-block'}
                            ),
                        ], style={"width": "100%"},)
                    ], className='nav-item'),


                ], className='navbar-nav me-auto mb-2 mb-lg-0'),
                html.Span([
                    html.Span(className="fa fa-calendar-alt justify-content-center mr-3"),
                    html.Span("Actualizado el "+ rpDate, id="rp-date")
                ], className="navbar-text")
            ], id="navbarText", className='collapse navbar-collapse'),

        ], className= 'container-fluid')

    ], className='navbar navbar-expand-lg navbar-light navbar-inverse fixed-top')
