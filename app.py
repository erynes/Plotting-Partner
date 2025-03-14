from dash import Dash
import dash_bootstrap_components as dbc
import layout
import callbacks
import argparse

# Our stylesheets. If you're not connected to the internet, the fonts/etc. will look different.
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    ]

# Note: If you run this, and stop it and change the title,
# the browser tab will not change. You need to close the tab
# and open a new one to see the change.
app = Dash(__name__,  external_stylesheets=external_stylesheets,
           title=layout.app_title, suppress_callback_exceptions=True)
app.layout = layout.master_layout
server = app.server

# Themes available from dbc:
dbc_themes = {}
dbc_themes['BOOTSTRAP'] = dbc.themes.BOOTSTRAP
dbc_themes['CERULEAN'] = dbc.themes.CERULEAN
dbc_themes['COSMO'] = dbc.themes.COSMO
dbc_themes['CYBORG'] = dbc.themes.CYBORG
dbc_themes['DARKLY'] = dbc.themes.DARKLY
dbc_themes['FLATLY'] = dbc.themes.FLATLY
dbc_themes['GRID'] = dbc.themes.GRID
dbc_themes['JOURNAL'] = dbc.themes.JOURNAL
dbc_themes['LITERA'] = dbc.themes.LITERA
dbc_themes['LUMEN'] = dbc.themes.LUMEN
dbc_themes['LUX'] = dbc.themes.LUX
dbc_themes['MATERIA'] = dbc.themes.MATERIA
dbc_themes['MINTY'] = dbc.themes.MINTY
dbc_themes['MORPH'] = dbc.themes.MORPH
dbc_themes['PULSE'] = dbc.themes.PULSE
dbc_themes['QUARTZ'] = dbc.themes.QUARTZ
dbc_themes['SANDSTONE'] = dbc.themes.SANDSTONE
dbc_themes['SIMPLEX'] = dbc.themes.SIMPLEX
dbc_themes['SKETCHY'] = dbc.themes.SKETCHY
dbc_themes['SLATE'] = dbc.themes.SLATE
dbc_themes['SOLAR'] = dbc.themes.SOLAR
dbc_themes['SPACELAB'] = dbc.themes.SPACELAB
dbc_themes['SUPERHERO'] = dbc.themes.SUPERHERO
dbc_themes['UNITED'] = dbc.themes.UNITED
dbc_themes['VAPOR'] = dbc.themes.VAPOR
dbc_themes['YETI'] = dbc.themes.YETI
dbc_themes['ZEPHYR'] = dbc.themes.ZEPHYR

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    dbc_theme_help_string = 'Dash Bootstrap Components theme. See options at ' \
        +'https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/.'
    parser.add_argument('--theme',
                        help=dbc_theme_help_string, required=False)
    parser.add_argument('--debug', help='run in debug mode', action='store_true', required=False)
    args = vars(parser.parse_args()) # returns a dict, via vars()
    theme = dbc_themes['BOOTSTRAP'] # our default theme
    if args['theme'] is not None and args['theme'].upper() in dbc_themes:
        theme = dbc_themes[args['theme'].upper()]
    app.config.external_stylesheets += [theme]
    app.run(debug=args['debug'])
