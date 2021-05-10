import dash_html_components as html

def Indicators(exPeriod, exdef, exdef_percent):
    values = [exPeriod, exdef, exdef_percent]
    subtitles = ["Periodo de exceso de mortalidad","Defunciones en exceso",r"% defunciones en exceso"]
    incons = ["fa fa-calendar-alt", "fa fa-chart-line", "fa fa-percentage"]
    cards = []
    iterator = 1
    for x in range(3):
        content_card = html.Div([
                            html.Div([
                                html.P(values[x], className="value text-center text-lg-left", id=f"indicator-{iterator}"),
                                html.P(subtitles[x], className="caption text-center text-lg-left")
                            ], className="inner"),
                            html.Div([
                                html.I(className=incons[x],
                                    **{
                                        'aria-hidden':"true"
                                    }
                                ),
                            ], className="icon d-none d-lg-block"),
                        ], className="card-box bg-dashboard")
        content_card_col = html.Div(content_card, className="col-xl-4 col-12")
        cards.append(content_card_col)
        iterator = iterator + 1

    return html.Div(cards, className="row no-gutters my-2 mx-4")
