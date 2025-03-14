from dash import html, dcc
import dash_bootstrap_components as dbc
import utils

#        1         2         3         4         5         6         7         8         9         0
#234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890

app_title = 'Plotting Partner'

# A matrix of 20 color swatches, each one a button for picking that color,
# plus "find your own color" and "enter your own hex color string" options.
# This modal has a header, body, and footer.
color_picker_modal_header = dbc.ModalHeader( \
    html.Div(dcc.Markdown('Click a color to select it, or enter a hex code\n' \
                          'or click the lower left-hand button to define your own.\n' \
                          'If you type in a hex code, hit \"enter\" afterwards.')),
                                             style={'display':'flex','text-align':'center',
                                                   'justify-content':'center','white-space':'pre'},
                                             close_button=False)

color_picker_modal_body = dbc.ModalBody( \
    html.Div(dbc.Container([dbc.Row([dbc.Col(dbc.Button('',
                                                        id={'type':'ColorChoice', 'index':r*4+c},
                                                        style={'background':utils.tableau20[r*4+c],
                                                               'height':'50px','width':'100%'},
                                                        # remove dbc default border+shape:
                                                        className='border-0 rounded-0',
                                                        n_clicks=0),
                                             # set border style at the Col level:
                                             style={'border':'2px solid black'},
                                             width=3) for c in range(4)],  # 4 cols
                                    className='g-0') for r in range(5)]))) # 5 rows

color_picker_modal_footer = dbc.ModalFooter( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(dbc.Input(type='color', id='color-wheel',
                                                      value=utils.WHITE,
                                                      style={'width':38,'height':38,
                                                             'margin':0, 'padding':0})),
                                    dbc.Col(html.Div('foo',
                                                     style={'color':utils.WHITE,
                                                            'background':utils.WHITE,
                                                            'height':28},
                                                     id='final-color-choice')),
                                    dbc.Col(dbc.Input(type='text', value=utils.WHITE,
                                                      id='color-choice-string',
                                                      style={'height':'100%','textAlign':'center'},
                                                      n_submit=0)),
                                    # Styling for Button didn't work until I wrapped it in a Div.
                                    dbc.Col(html.Div(dbc.Button('OK', id='ok-color-choice',
                                                                color='primary',
                                                                className='ms-auto',
                                                                style={'width':'70%'}, n_clicks=0),
                                                     style={'textAlign':'right'})),
                                    dbc.Col(html.Div(dbc.Button('Cancel', id='cancel-color-choice',
                                                                color='primary',
                                                                className='ms-auto',
                                                                style={'width':'70%'}, n_clicks=0),
                                                     style={'textAlign':'left'})),
                                    ], align='center')),
             style={'width':'100%'}))

color_picker_modal = dbc.Modal([color_picker_modal_header,
                                color_picker_modal_body,
                                color_picker_modal_footer],
                               id='color-picker', is_open=False, size='l')

# A modal (i.e., a popup window) for defining a new category (a.k.a. label) for a subset of samples.
# This modal has a header, body, and footer.
new_cat_modal_header = dbc.ModalHeader( \
    html.Div(dcc.Markdown('Name a new group of patients and choose its color:')),
                                        style={'display':'flex','justify-content':'center'},
                                        close_button=False)

new_cat_modal_body = dbc.ModalBody( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(dbc.Input(id='new-category-name', type='text',
                                                      placeholder='Type a label name...')),
                                    dbc.Col(dbc.Button('Choose color', id='choose-new-color-btn',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0)),
                                    dbc.Col(html.Div(children='color',
                                                     id={'type':'color-displayed',
                                                         'index':utils.div_display['new cat']},
                                                     style={'width':'100%', 'height':'100%',
                                                            'color':'white',
                                                            'background':'white'}))],
                                   className='g-0')),
             ))

new_cat_modal_footer = dbc.ModalFooter( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(dbc.Checkbox(id='new-default-cat',
                                                         label='Make this the default label',
                                                         value=False)),
                                    dbc.Col(dbc.Button('OK', id='new-cat-ok',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0)),
                                    dbc.Col(dbc.Button('Cancel', id='new-cat-cancel',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0))],
                                   className='g-0'))
             ))

new_cat_modal  = dbc.Modal([new_cat_modal_header,
                            new_cat_modal_body,
                            new_cat_modal_footer],
                           id='new-cat-modal', is_open=False)

# A modal for editing an existing category for a subset of samples:
# changing the category's name, color, or both.
# This modal has a header, body, and footer.
edit_cat_modal_header = dbc.ModalHeader( \
    html.Div(id='cat-to-edit', children=''),
                                         style={'display':'flex','justify-content':'center'},
                                         close_button=False)

edit_cat_modal_body = dbc.ModalBody( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(dbc.Input(id='edit-category-name', type='text')),
                                    dbc.Col(dbc.Button('Change color',id='edit-color-btn',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0)),
                                    dbc.Col(html.Div(children='color',
                                                     id={'type':'color-displayed',
                                                         'index':utils.div_display['edit cat']},
                                                     style={'width':'100%',
                                                            'height':'100%',
                                                            'color':'white'}))],
                                   className='g-0')),
             ))

edit_cat_modal_footer = dbc.ModalFooter( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(dbc.Checkbox(id='edit-default-cat',
                                                         label='Make this the default label',
                                                         value=False)),
                                    dbc.Col(dbc.Button('OK', id='edit-cat-ok',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0)),
                                    dbc.Col(dbc.Button('Cancel', id='edit-cat-cancel',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0))],
                                   className='g-0'))
             ))

edit_cat_modal  = dbc.Modal([edit_cat_modal_header,
                             edit_cat_modal_body,
                             edit_cat_modal_footer],
                            id='edit-cat-modal', is_open=False)

# A modal for assigning a label to a sample.
# This modal has a header, body, and footer.
assign_label_modal_header = dbc.ModalHeader( \
    html.Div('Assign a new label to this patient:'),
                                             style={'display':'flex','justify-content':'center'},
                                             close_button=False)

assign_label_modal_body = dbc.ModalBody( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(html.Div(id='labeled-sample')),
                                    dbc.Col(html.Div('→ → → →')),
                                    dbc.Col(dcc.Dropdown(id='label-assignment-dropdown',
                                                         placeholder='Available labels'))],
                                   className='g-0'))
             ))

assign_label_modal_footer = dbc.ModalFooter( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(dbc.Button('OK', id='label-assignment-ok',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0)),
                                    dbc.Col(dbc.Button('Cancel', id='label-assignment-cancel',
                                                       color='primary',
                                                       className='ms-auto', n_clicks=0))],
                                   className='g-0'))
             ))

assign_label_modal = dbc.Modal([assign_label_modal_header,
                                assign_label_modal_body,
                                assign_label_modal_footer],
                               id='assign-label-modal', is_open=False)

# A modal for enabling a user to define a subset of samples and assign a label to them.
# This modal has a header, body, and footer.
subset_label_assignment_modal_header = dbc.ModalHeader( \
    html.Div(dcc.Markdown('Select a label, then define the properties of the patients\n' \
                          'to which you want to assign the label. Click the "+" button\n' \
                          'to add multiple criteria to your definition. For each cutoff,\n' \
                          'you can enter a number or "mean", "median", or "%ile _num_"\n'
                          'where _num_ is a number (e.g. 90 for the 90th percentile).')),
                                                        style={'display':'flex',
                                                               'text-align':'center',
                                                               'justify-content':'center',
                                                               'white-space':'pre',
                                                               'font-size':'125%'},
                                                        close_button=False)

subset_label_assignment_modal_body = dbc.ModalBody( \
    html.Div(dbc.Container([dbc.Row(html.Div('', style={'color':utils.WHITE,
                                                              'background':utils.WHITE})),
                            dbc.Row([dbc.Col(html.Div('',
                                                      style={'color':utils.WHITE,
                                                             'background':utils.WHITE}),
                                             width=3),
                                     dbc.Col(dcc.Dropdown(id='label-assignment-dropdown-2',
                                                          placeholder='Available labels'),
                                             width=6),
                                     dbc.Col(html.Div('',
                                                      style={'color':utils.WHITE,
                                                             'background':utils.WHITE}),
                                             width=3)]),
                            dbc.Row(html.Div(dbc.Container(id='expanding-query-div', fluid=True))),
                            dbc.Row(html.Div(id='query-results-tally', hidden=True)),
                            dbc.Row(html.Div('', style={'color':utils.WHITE,
                                                              'background':utils.WHITE}))
                            ])
             ))

subset_label_assignment_modal_footer = dbc.ModalFooter( \
    html.Div(dbc.Container(dbc.Row([dbc.Col(dbc.Button('OK', \
        id='subset-label-assignment-ok', color='primary', className='ms-auto', n_clicks=0)),
                                    dbc.Col(dbc.Button('Cancel', \
        id='subset-label-assignment-cancel', color='primary', className='ms-auto', n_clicks=0))],
                                   className='g-0'))
             ))

subset_label_assignment_modal = dbc.Modal([subset_label_assignment_modal_header,
                                           subset_label_assignment_modal_body,
                                           subset_label_assignment_modal_footer],
                                          id='subset-label-assignment', is_open=False, size='xl')

# Generic modal for displaying an error message
err_msg_modal = dbc.Modal( \
    [dbc.ModalBody(children='', id='err-msg',
                   style={'font-family':utils.DEFAULT_FONT_FAMILY,
                          'font-size':utils.DEFAULT_FONT_SIZE,
                          'white-space':'pre','width':'100%'}),
     dbc.ModalFooter(dbc.Button("Close", id='close-err-modal',
                                style={'font-family':utils.DEFAULT_FONT_FAMILY,
                                       'font-size':(utils.DEFAULT_FONT_SIZE - 2)},
                                className='ms-auto', n_clicks=0))
     ],
                           id='err-modal', is_open=False)

# Function for appending a row of dropdowns/etc. to the subset label assignment modal
def make_query_row(input_rows : list, prop_names : list):
    """
    Function for appending a row of dropdowns/etc. to the subset label assignment modal.

    Parameters
    ----------
    input_rows : list of dbc.Row()
       The expanding rows of the interactively-built query for subsetting samples.
       Can be an empty list.
    prop_names : list of str
       The available property names, including 'sample'.

    Returns
    -------
    list of dbc.Row()
       input_rows with a new dbc.Row() appended to it.
    """
    row_number = 0
    if type(input_rows) is list and len(input_rows) > 0:
        row_number = len(input_rows)
    if 0 == row_number:
        # The initial row doesn't get 'AND'/'OR' at the front of it.
        logic_op = dbc.Col(html.Div('foo', id={'type':'logic-op', 'index':row_number},
                                    hidden=True), width=1)
    else:
        logic_op = dbc.Col(dcc.Dropdown(id={'type':'logic-op', 'index':row_number},
                                        options=['AND', 'OR'], value='AND'),
                           class_name='g-0', width=1)
    # Optional parentheses are provided to allow for well-defined combos of 'AND'/'OR'.
    # Example: "a AND b OR c" can be interpreted as "(a AND b) OR c" or "a AND (b OR c),"
    # which are not equivalent.
    lparen = dbc.Col(dcc.Dropdown(id={'type':'lparen', 'index':row_number},
                                  options=['', '('], value=''), class_name='g-0', width=1)
    prop_choice = dbc.Col(dcc.Dropdown(id={'type':'prop-choice', 'index':row_number},
                                       options=prop_names), class_name='g-0', width=4)
    comp_op = dbc.Col(dcc.Dropdown(id={'type':'comp-op', 'index':row_number},
                                   options=['>','>=','==','!=','<=','<',
                                            'in top', 'in bottom']), class_name='g-0', width=2)
    boundary_value = dbc.Col(dbc.Input(id={'type':'boundary-value', 'index':row_number},
                                       style={'padding':0,'margin':0,'height':'36px'}),
                             class_name='g-0', width=2)
    rparen = dbc.Col(dcc.Dropdown(id={'type':'rparen', 'index':row_number},
                                  options=['', ')'], value=''), class_name='g-0', width=1)
    add_another = dbc.Col(dbc.Button('+', id={'type':'add-another', 'index':row_number},
                                     color='primary', class_name='ms-auto', n_clicks=0), width=1)
    input_rows.append(dbc.Row([logic_op, lparen, prop_choice, comp_op, boundary_value,
                               rparen, add_another], align='center'))
    return input_rows


# Function for adding controls above line plots
def add_lineplot_controls(radioitems_id : str, slider_id : str, slider_div_id : str,
                          facets_checkbox_id : str, replicates_checkbox_id : str):
    return dbc.Container([dbc.Row([
        dbc.Col('', style={'color':'white'}, # was: 'spacer'
                width=3),
        dbc.Col(html.Div([dbc.Label('show', style={'font-size':'120%'}),
                          dbc.RadioItems(id=radioitems_id,
                                         options=[{'label':'all replicates', 'value':1},
                                                  {'label':'mean ± SD', 'value':2},
                                                  {'label':'any option TBD', 'value':3,
                                                   'disabled':True}],
                                         value=1,
                                         style={'font-size':'120%'})]),
                width=3),
        dbc.Col(html.Div([dbc.Label('Subtly spread the points horizontally',
                                    style={'font-size':'120%'}),
                          dcc.Slider(id=slider_id,
                                     min=0, max=0.08, step=0.01, value=0, marks=None,
                                     tooltip={'placement':'bottom'})
                          ], id=slider_div_id, hidden=True),
                width=3),
        dbc.Col([dbc.Checkbox(id=facets_checkbox_id,
                              label=dcc.Markdown('Apply color edits to all subplots',
                                                 style={'font-size':'120%'}),
                              value=True),
                 dbc.Checkbox(id=replicates_checkbox_id,
                              label=dcc.Markdown('One style per replicate',
                                                 style={'font-size':'120%'}),
                              value=False)],
                width=3)])])


lineplot_facet_and_groupBy_selector = html.Div( \
    [dbc.Container([dbc.Row([dbc.Col(dcc.Markdown('Choose $y$-axes:', mathjax=True,
                                                  style={'font-size':'120%'}),
                                     width=3),
                             dbc.Col(dcc.Markdown('Group data by:',
                                                  style={'font-size':'120%'}),
                                     width=3),
                             dbc.Col(html.Div('spacer', hidden=True),
                                     width=6)]),
                    dbc.Row([dbc.Col(dcc.Checklist(options=[],
                                                   id='lineplot-facetVars-checklist',
                                                   style={'font-size':'120%'}),
                                     width=3),
                             dbc.Col(dcc.Dropdown(id='lineplot-groupBy-dropdown',
                                                  options=[], clearable=False,
                                                  placeholder='Choose a property:'),
                                     width=3),
                             dbc.Col(dbc.Button('SHOW PLOT',
                                                id='render-lineplot-button',
                                                n_clicks=0),
                                     width=1),
                             dbc.Col(html.Div('spacer', hidden=True),
                                     width=5)])])
     ],
                                                id='lineplot-dataGroups-div', hidden=True)


demo_welcome_banner = html.Div([html.Img(src='assets/PPpp.png', style={'height':'50px',
                                                                       'margin-left':utils.OPTIONAL_LEFT_MARGIN}),
                                html.Br(),
                                html.Br(),
                                dcc.Markdown("This is a demo of an interactive plotting app I wrote in Python using Plotly Dash.\n"
                                             +"What&rsquo;s important is that it gives the user a very high level of control "
                                             +"over the plots,\nallowing for efficient custom labeling of subsets for time-varying "
                                             +"and static (e.g. demographic) data.\nTry it and see for yourself!",
                                             style={'font-size':18, 'margin-left':utils.OPTIONAL_LEFT_MARGIN,
                                                    'white-space':'pre'}),
                                html.Br(),
                                html.Br(),
                                dcc.Markdown("Fictitious pilot study of a new drug candidate for bronchitis",
                                             style={'font-weight':'bold','font-size':36, 'margin-left':utils.OPTIONAL_LEFT_MARGIN}),
                                html.Br(),
                                html.Br(),
                                # could add a "load file" dropdown/etc. here if desired
                                # currently using hardcoded infile names for simplicity
                                ],
                               id='demo-welcome-banner-div', hidden=False,
                               title=None) # 'title' --> exactly 1 call to callback


master_layout = html.Div([new_cat_modal,
                          edit_cat_modal,
                          assign_label_modal,
                          subset_label_assignment_modal,
                          color_picker_modal,
                          err_msg_modal,
                          html.Br(),
                          html.Br(),
                          demo_welcome_banner,
                          html.Br(),
                          html.Div(html.Div(dcc.Markdown('Longitudinal plot:'),
                                            style={'font-family':utils.DEFAULT_FONT_FAMILY,
                                                   'font-size':utils.DEFAULT_FONT_SIZE,
                                                   'margin-left':utils.OPTIONAL_LEFT_MARGIN})),
                          lineplot_facet_and_groupBy_selector,
                          html.Br(),
                          html.Br(),
                          # Restrict to fixed-input demo for now, implement this soon...
                          #html.Div([html.Div('Data source for the line plot:',
                          #                   style={'font-family':utils.DEFAULT_FONT_FAMILY,
                          #                          'font-size':utils.DEFAULT_FONT_SIZE}),
                          #          dbc.Container(dbc.Row([dbc.Col(dcc.Dropdown(id='lineplot-source-dropdown',
                          #                                                      options=[], clearable=False),
                          #                                         width=3),
                          #                                 dbc.Col(html.Div('foo',hidden=True),
                          #                                         width=9)]))],
                          #         id='lineplot-source-div', hidden=True),
                          html.Br(),
                          html.Br(),
                          html.Br(),
                          # The following Div serves as a quasi dcc.Store.
                          # It remains hidden throughout.
                          # It's very helpful for the pattern-matching callback in this case.
                          html.Div(id={'type':'color-displayed',
                                       'index':utils.div_display['line plot']},
                                   style={'background':'white','color':'white'}, hidden=True),
                          html.Div([html.Div(id='lineplot-div-title',
                                             style={'font-family':utils.DEFAULT_FONT_FAMILY,
                                                    'font-size':utils.DEFAULT_FONT_SIZE,
                                                    'margin-left':utils.OPTIONAL_LEFT_MARGIN}),
                                    # Different indenting was done here to limit the line lengths.
                                    add_lineplot_controls( \
                                        radioitems_id='lineplot-replicates-radioitems',
                                        slider_id='lineplot-slider',
                                        slider_div_id='lineplot-slider-div',
                                        facets_checkbox_id='lineplot-applyToFacets-checkbox',
                                        replicates_checkbox_id= \
                                                        'lineplot-oneStylePerReplicate-checkbox'),
                                    dcc.Graph(id='lineplot-graph-id')],
                                   id='lineplot-div', hidden=True),
                          html.Br(),
                          html.Br(),
                          dcc.Store(id='dict-of-DFs', data=None),
                          dcc.Store(id='lineplot-df-melted-dict', data=None),
                          dcc.Store(id='lineplot-style-map', data=None),
                          dcc.Store(id='metrics-dict', data=None),
                          dcc.Store(id='sample-to-color-map', data=None),
                          dcc.Store(id='sample-to-IsDefaultColor-map', data=None),
                          dcc.Store(id='default-color', data=utils.LIGHT_GRAY),
                          dcc.Store(id='idx-of-parent-modal', data=0),
                          html.Div([html.Div(dcc.Markdown('Demographics plot:'),
                                             style={'font-family':utils.DEFAULT_FONT_FAMILY,
                                                    'font-size':utils.DEFAULT_FONT_SIZE,
                                                    'margin-left':utils.OPTIONAL_LEFT_MARGIN}),
                                    dbc.Container([ \
                                        dbc.Row([ \
                                            dbc.Col(dcc.Markdown('Choose $y$-axes:',
                                                                 mathjax=True,
                                                                 style={'font-size':'120%'}),
                                                    width=3),
                                            dbc.Col(html.Div('',style={'color':'white'}), # was: 'spacer'
                                                    width=1),
                                            dbc.Col(dcc.Dropdown(id='categories-dropdown',
                                                                 placeholder='Labels for patients',
                                                                 options=[utils.ADD_NEW_CATEGORY],
                                                                 ), className='g-0',
                                                    width=3),
                                            dbc.Col(dcc.Dropdown(id='samples-dropdown',
                                                                 value='', placeholder='Patients',
                                                                 options=[],
                                                                 ), className='g-0',
                                                    width=3),
                                            dbc.Col(dbc.Button('Label a subset',
                                                               id='label-a-subset-button',
                                                               n_clicks=0),
                                                    width=2)]),
                                        dbc.Row([ \
                                            dbc.Col(dcc.Checklist(options=[],
                                                                  id='barplot-facetVars-checklist',
                                                                  style={'font-size':'120%'}),
                                                    width=3),
                                            dbc.Col(dbc.Button('SHOW PLOT',
                                                               id='render-barplot-button',
                                                               n_clicks=0),
                                                    width=1, align='end'),
                                            dbc.Col(html.Div('',style={'color':'white'}), # was: 'spacer'
                                                    width=8)]),
                                        dbc.Row(html.Div(dcc.Graph(id='barplot-graph-id'))),
                                        dbc.Row([ \
                                            dbc.Col('', style={'color':'white'}, # was: 'spacer 1'
                                                    width=3),
                                            dbc.Col(html.Div([dbc.Label('sort by',
                                                                        style={'font-size':'120%'}),
                                                              dcc.Dropdown(id='sortorder-dropdown',
                                                                           options=[],
                                                                           clearable=False)]),
                                                    width=3),
                                            dbc.Col(html.Div(dbc.RadioItems( \
                                                                id='sortorder-radioitems',
                                                                options=[{'label':'descending',
                                                                          'value':0},
                                                                         {'label':'ascending',
                                                                          'value':1},
                                                                         ],
                                                                             value=0,
                                                                             style={'font-size':'120%'})),
                                                    width=3),
                                            dbc.Col(dbc.Checkbox( \
                                                        id='barPlot-hideXticks-checkbox',
                                                        label=dcc.Markdown('Hide tick labels '\
                                                                           'on the $x$-axis',
                                                                           mathjax=True,
                                                                           style={'font-size': \
                                                                                  '120%'}),
                                                                  value=False),
                                                    width=3)])
                                                ])],
                                   id='barplot-div', hidden=True),
                          html.Br(),
                          html.Br(),
                          html.Br(),
                          html.Br()])
