import dash_html_components as html

def Navbar(title, rpDate, app):
    return html.Nav([
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
                    html.A("Nacional", href="#", className = "nav-link")
                ], className='nav-item active'),
            ], className='navbar-nav mr-auto'),
           html.Ul([
               html.Li([
                   html.Div([
                       html.Span(className="fa fa-calendar-alt justify-content-center mr-3"),
                       html.Span("Actualizado el "+ rpDate)
                   ], className="nav-link d-flex flex-row ")
               ], className='nav-item'),
           ], className="navbar-nav")
        ], id="navbarText", className='collapse navbar-collapse'),
    ], className='navbar navbar-expand-lg navbar-light navbar-inverse fixed-top')
