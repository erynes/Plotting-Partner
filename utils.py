import os
from textwrap import wrap, fill

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ------- Begin utility declarations ------------------------
#
# Set of 20 contrasting colors used by Tableau
# https://github.com/jrnold/ggthemes/blob/main/data-raw/theme-data/tableau.yml
tableau20 = ["#4E79A7","#A0CBE8","#F28E2B","#FFBE7D","#59A14F","#8CD17D","#B6992D",
             "#F1CE63","#499894","#86BCB6","#E15759","#FF9D9A","#79706E","#BAB0AC",
             "#D37295","#FABFD2","#B07AA1","#D4A6C8","#9D7660","#D7B5A6"]

ADD_NEW_CATEGORY = 'Click here to add a new label. Click an existing label to change it.'
ADD_NEW_CATEGORY = {'label':ADD_NEW_CATEGORY, 'value':ADD_NEW_CATEGORY}

LIGHT_GRAY = '#CCCCCC'
WHITE = '#FFFFFF'

DEFAULT_FONT_FAMILY = 'Arial'
DEFAULT_FONT_SIZE = 16
DEFAULT_YLABEL_FONT_SIZE = 12 # plotly's default y-axis font size
DEFAULT_MAX_YLABEL_LEN = 14 # empirically determined by Eric
ERR_MSG_LINE_LEN = 40
OPTIONAL_LEFT_MARGIN = '3rem' # for use as left padding, e.g. style = {'margin-left': OPTIONAL_LEFT_MARGIN}

# Lookup table for "index" values of 'color_displayed' Div elements
# that receive a color string from the color picker.
div_display = ['new cat', 'edit cat', 'line plot']
div_display = dict(zip(div_display, range(len(div_display))))
#
# ------- End utility declarations --------------------------

# Utility functions

def default_format_fig(figure):
    # https://community.plotly.com/t/change-the-background-colour-and-or-theme/66799/2
    figure.update_layout(
        plot_bgcolor='white'
    )
    figure.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
    )
    figure.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        zeroline=True, zerolinecolor='lightgrey', zerolinewidth=1
    )
    return figure


def xexpand_MeanAndSD_vs_Day(df_in : pd.DataFrame, group : str='Treatment',
                             delta_t : float=.01):
    """
    Function to receive a DataFrame that's set up for "property vs. Day"
    to be plotted as mean ± SD on the y-axis and return a DataFrame in which
    series of small Δt values have been added to the per-group Day values
    so that the dot-and-error-bars representations won't overlap.
    E.g., if we have data for 5 treatments at Day=4, instead of plotting
    all 5 of them at x=4, we might plot them at x = [3.98,3.99,4.00,4.01,4.02].
    
    Parameters
    ----------
    df_in : pd.DataFrame
        An input DataFrame grouped by [group], Day, and ideally 'prop name' or a
        named property of interest, with mean per [group] per property per Day in column 'mean'
        and SD of the same in column 'std'. Technically speaking,
        this function only requires columns '[group]' and 'Day' to be present,
        but it's very highly recommended that the grouping and calculating be completed
        prior to calling this function, because grouping by integer Day is guaranteed to work,
        while grouping by float Day (which this function will return) is risky.
    group : str, default : 'Treatment'
        The column in df_in by which the rows should be grouped to compute mean ± SD.
    delta_t : float, default : 0.01
        The unit of a fractional Day by which x=Day values will be 'expanded'
        in the x direction: ..., -2*delta_t, -1*delta_t, 0, 1*delta_t, 2*delta_t, ...
        This works whether the number of groups measured at a given Day is odd or even;
        if it's odd, the deltas will be ..., -1*delta_t, 0, 1*delta_t, ...,
        and if it's even, they'll be ..., -1*delta_t, 1*delta_t, ...
        
    Returns
    -------
    DataFrame
        A copy (df_in.copy()) of the input DataFrame in which the column of integer Days
        has been replaced by a column of float Days "fanned out" around each Day value.
        
    Raises
    ------
    ValueError
        If any of the required columns listed above is absent from df_in.
    """
    lowercase_column_names = [x.lower() for x in df_in.columns]
    for name in [group, 'Day']:   #, 'prop name', 'mean', 'std']:
        if not name.lower() in lowercase_column_names:
            raise ValueError(f"Required column named {name} was not found in DataFrame.")
    day_string = 'Day'
    for col_name in df_in.columns:
        if col_name.lower() == 'day':
            day_string = col_name # use the column title's actual capitalization
            break
    delta_t = abs(delta_t) # just in case the user supplied a value < 0
    df = df_in.copy()
    day_dict = {}
    for day in df[day_string].unique():
        group_dict = {} # keys will be the members of the group, e.g. different treatments
        vals = df[day==df[day_string]][group].unique()
        N = len(vals)
        dt = delta_t*(np.arange(N) - np.median(np.arange(N))) # works whether N is odd or even
        for i in range(N):
            group_dict[vals[i]] = float(day) + dt[i]
        day_dict[day] = group_dict
    day_float_array = np.zeros(len(df), dtype=float)
    for i in range(len(df)):
        day, val = df.iloc[i][[day_string, group]]
        day_float_array[i] = day_dict[day][val]
    df.drop(columns=day_string, inplace=True)
    df[day_string] = day_float_array
    return df


def linewrap_ylabel(ylabel : str, num_facets : int):
    """
    Function to perform line wrapping on y-axis labels, when necessary.
    The greater the number of facets, the greater the need for line wrapping.
    Hard-coded numbers herein were empirically determined by Eric.
    This function uses the "textwrap" package.

    Parameters
    ----------
    ylabel : str
       The y-axis label for a given facet in a multi-faceted plot.
    num_facets : int
       The number of facets in the plot.

    Returns
    -------
    str, int
       The unchanged input y-axis label (or a line-wrapped version of it)
       and the font size that should be used to display it.
    """
    ylabel_font_size = DEFAULT_YLABEL_FONT_SIZE
    # BUGBUG The following updates were made for the demo. Should these become permanent?
    ylabel_max_len = 18 # updated for demo; was DEFAULT_MAX_YLABEL_LEN
    if 1 == num_facets:
        ylabel_max_len = 34 # updated for demo; was 30
    elif num_facets > 2:
        ylabel_font_size = 9 # updated for demo; was 8
        ylabel_max_len = 14 # updated for demo; was 11
        if 3 == num_facets and len(ylabel) <= ylabel_max_len:
            ylabel_font_size = 12 # updated for demo; was 10
    if len(ylabel) > ylabel_max_len:
        ylabel = '<br>'.join(wrap(ylabel, width=ylabel_max_len))
    return ylabel, ylabel_font_size


def make_custom_multifaceted_bar_plot(df_in : pd.DataFrame, props : list, custom_color_mapping : dict,
                                      label_list : list, x_column : str, hide_x_ticks : bool):
    """
    Function for making (or updating) vertically stacked bar plots (a.k.a. a faceted plot),
    with sample IDs on the x-axis. This function assumes the input has been validated, formatted,
    and sorted by a callback function.
    
    Parameters
    ----------
    df_in : pd.DataFrame
        The input DataFrame. Contains columns named 'prop name', 'prop value',
        and the value in parameter x_column.
    props : list
        The unique entries in column 'prop name', in the appropriate sort order.
    custom_color_mapping : dict
        A mapping from x_column value (str) to color (str, hex value). The bars of the bar plot
        will be colored according to this mapping.        
    label_list : list of dict
        A list of the labels the user has (interactively) defined. Each label has a name and a color.
        For each entry, its 'value' key gives the name. The 'label' key gives what's essentially a JSON
        string that contains the color and a duplicate copy of the name. This parameter is used to
        retrieve the label names that correspond to the colors in custom_color_mapping; these names
        will be shown in the plot's legend. Labels created by the user but not assigned to any sample
        will be excluded from the legend.
    x_column : str
        The name of the column in df_in to be plotted on the x-axis. Typically 'sample' or 'Patient ID'.
    hide_x_ticks : bool
        Whether to hide the ticks for the x-axis.
    
    Returns
    -------
    figure
        A faceted stacked bar plot with a common x-axis.
    """
    fig = default_format_fig(px.bar(df_in,
                                    x=x_column, y='prop value', facet_row='prop name',
                                    color=x_column, color_discrete_map=custom_color_mapping))
    color_to_label = {}
    if label_list is not None:
        unique_colors_used = list(set(custom_color_mapping.values()))
        for label in label_list:
            label_name = label['value']
            label_color = label['label']['props']['children'][0]['props']['style']['color']
            if label_color in unique_colors_used:
                color_to_label[label_color] = label_name
        if len(color_to_label) == 0:
            # This will be the case after the user defines a label and before any label is assigned to a sample.
            fig.update_layout(showlegend=False)
    else:
        fig.update_layout(showlegend=False)
    fig.update_yaxes(matches=None) # enforce distinct y-axis ranges

    num_facets = len(props)
    for i in range(num_facets):
        # Here we assign y-axis labels on the left and remove them on the right.
        # From top to bottom, the props[] in the facet plot will be displayed in the order 0, 1, 2, ...,
        # but the corresponding yaxis names from top to bottom are automatically named yaxisN, ..., yaxis2, yaxis.
        # With a shared x-axis, the bars will be horizontally sorted according to the sort order of the top y-axis (props[0]).
        fig.layout.annotations[i].text = '' # remove right y-axis labels
        yaxis_name = 'yaxis'
        if i < len(props)-1:
            yaxis_name += str(len(props) - i)
        ylabel, ylabel_font_size = linewrap_ylabel(props[i], num_facets)
        # https://stackoverflow.com/questions/58167028/single-axis-caption-in-plotly-express-facet-plot
        fig['layout'][yaxis_name]['title']['text'] = ylabel
        fig['layout'][yaxis_name]['title']['font']['size'] = ylabel_font_size
    fig.update_xaxes(tickangle=-90) # put the "business end" of the Parent ID closest to the data
    if len(color_to_label) > 0:
        # Here we build the legend, using the example shown here:
        # https://stackoverflow.com/questions/69683950/manually-defined-legend-in-plotly-on-python
        # (Eric tried to find a way to do this without using plotly.graph_objects, but didn't find one.)
        # Eric found empirically that setting y=[None] keeps the bar plot looking the way we want it to,
        # whereas providing no 'y' parameter (i.e. y=None rather than y=[None]) shifts the bars rightward (boo!).
        # Another note: parameter 'marker_color', shown on the web page above, seems to work well,
        # despite not being listed in the documentation(?!) for go.Bar.
        fig.update_traces(showlegend=False).add_traces([go.Bar(x=[fig.data[0].x[0]],
                                                               y=[None],
                                                               name=color_to_label[c],
                                                               marker_color=c,
                                                               showlegend=True)
                                                        for c in color_to_label])
        fig.update_layout(legend_title_text=None) # personal preference: no legend title
    if hide_x_ticks:
        fig.update_xaxes(tickcolor='white',tickfont={'color':'white'},tickangle=0) # maybe add 'size':1 or 4 or ...?        
    return fig


def make_custom_multifaceted_line_plot(df_in : pd.DataFrame, x_column : str='day', line_group : str='sample',
                                       agg_group : str='Treatment', display_meanSD : bool=False, dt : float=0):
    """
    Function to make a multi-faceted (or single facet) line plot.

    Parameters
    ----------
    df_in : pd.DataFrame
       The input data. Contains columns x_column, 'prop name', 'prop value', line_group, and agg_group.
    x_column : str, default : 'day'
       The name of the column holding the x-axis data.
    line_group : str, default : 'sample'
       The name of the column for grouping replicates. If display_meanSD is true, lines with the same line_group
       value will be a single line showing mean ± SD.
    agg_group : str, default : 'Treatment'
       The name of the column for coloring lines.
    display_meanSD : bool, default : False
       Whether to display one line per replicate, or mean ± SD over line_group.
    dt : float, default : 0
       The value by which to subtly spread data points along the x-axis. See xexpand_MeanAndSD_vs_Day().

    Returns
    --------
    Figure
       A (multifaceted) line plot figure.

    Notes
    -----
    Calls default_format_fig().
    Calls xexpand_MeanAndSD_vs_Day() if display_meanSD is True.
    """
    these_colors = tableau20
    if display_meanSD:
        df_copy = df_in.copy()
        df_copy['mean'] = df_copy['prop value'].copy()
        df_copy['std'] = df_copy['prop value'].copy()
        # Go ahead and compute mean ± SD regardless of replicates. We'll remove NaNs immediately afterwards.
        df_agg = df_copy.groupby([agg_group, x_column, 'prop name'],
                                 as_index=False).agg({agg_group:'first',
                                                      x_column:'first',
                                                      'prop name':'first',
                                                      'mean':'mean',
                                                      'std':'std'})
        df_agg['std'] = df_agg['std'].fillna(0)        
        plot_options = {'x':x_column, 'y':'mean', 'error_y':'std', 'facet_row':'prop name',
                        'color':agg_group, 'color_discrete_sequence':these_colors, 'height':540}
        if x_column.lower() == 'day':
            plot_options['hover_data'] = {x_column:':.0f'} # display Day as an integer
        ret_val = xexpand_MeanAndSD_vs_Day(df_agg, group=agg_group, delta_t=dt)
        fig = default_format_fig(px.line(xexpand_MeanAndSD_vs_Day(df_agg, group=agg_group, delta_t=dt),
                                         **plot_options))
    else:
        fig = default_format_fig(px.line(df_in, x=x_column, y='prop value', facet_row='prop name',
                                         line_group=line_group, color=agg_group, color_discrete_sequence=these_colors,
                                         height=540))
    fig.update_yaxes(matches=None) # enforce distinct y-axis ranges
    num_facets = len(fig.layout.annotations)
    for i in range(num_facets):
        # Here we assign y-axis labels on the left and remove them on the right.
        # The package assigns the variable names yaxis, yaxis2, ..., yaxisN to the y-axes.
        y_label = ''.join(fig.layout.annotations[i].text.split('=')[1:]) # 'prop name=Viability (%)', etc.
        y_label, ylabel_font_size = linewrap_ylabel(y_label, num_facets)
        fig.layout.annotations[i].text = '' # remove right y-axis labels
        yaxis_name = 'yaxis'
        if i > 0:
            yaxis_name += str(i+1)
        # https://stackoverflow.com/questions/58167028/single-axis-caption-in-plotly-express-facet-plot
        fig['layout'][yaxis_name]['title']['text'] = y_label
        fig['layout'][yaxis_name]['title']['font']['size'] = ylabel_font_size
    return fig


def add_group_to_style_map(group : str, style_map : dict, fig : dict, df : pd.DataFrame, sample_string : str,
                           one_trace_per_group : bool, samples_string : str='Sample IDs'):
    """
    Function to add styling (color assignments) for a sample grouping to the style map.
    Builds the map if it's empty.

    Parameters
    ----------
    group : str
       The name or label of the sample grouping to add to the map. This is a column in `df`.
       Example: 'Treatment', with underlying group values 'Placebo', "Formulation 1', etc.
    style_map : dict
       The current style map. If it's empty, it will get built.
    fig : dict
       A figure that was created & returned by make_custom_multifaceted_line_plot().
       The color assignments within it will be extracted and stored in `style_map`.
    df : pd.DataFrame
       The DataFrame containing the data for the facets that appear in `fig`.
       It must contain columns whose names match the values of `group` and `sample_string`.
    sample_string : str
       The name of the column in `df` that holds the sample ID values.
       This could be 'Sample', 'Patient ID', etc.
    one_trace_per_group : bool
       Whether there is a single trace (curve) for all samples with the same group value
       within each facet (e.g., if mean ± SD is being displayed).
    samples_string : str, default : 'Sample IDs'
       This is merely here for shorthand and flexibility. This string is only used
       within the style_map itself; it is never displayed. if `sample_string` is
       'Patient ID', you could set samples_string to 'Patient IDs' (plural),
       but 'Sample IDs' should work fine in all cases.

    Returns
    -------
    dict
       The updated style map.
    
    Notes
    -----
    The general form of the style map is:

    style_map = {'Sample IDs' : { 'id1':{'facets':{'group1':{'facet1':{'color':'color1'},
                                                             'facet2':{'color':'color2'}, ...
                                                            },
                                                   'group2':{'facet1':{'color':'color1'},
                                                             'facet2':{'color':'color2'}, ...
                                                            }, ...
                                                  },
                                         'group1':'id1_group1_value',
                                         'group2':'id1_group2_value', ...
                                        },
                                  'id2':{...}, ...
                                },
                 group1 : { 'group1_value1':{'facets':{'facet1':{'color':'color1'},
                                                       'facet2':{'color':'color2'}, ...
                                                      },
                                             'Sample IDs':['id1','id2',...]
                                            },
                            'group2_value2':{'facets':{...},
                                             'Sample IDs':['id7','id8',...]
                                            }, ...
                          },
                 group2 : {...},
                 ...
                }

    'facet1', 'facet2', etc. are time-varying properties that have been measured,
    e.g. 'Neutrophils (%)', 'WBC (10^9 cells/L)', etc.

    'group1', 'group2', etc. are characteristics by which samples can be grouped,
    e.g. 'Treatment', 'Age (years)',etc.

    'group1_value1', 'group2_value1', etc. are the values of the samples in those groups,
    e.g. 'Placebo', '13-17', etc.
    """
    sample_IDs_map = {}
    group_values_map = {}
    if style_map:
        sample_IDs_map = style_map[samples_string]
        if group in style_map:
            group_values_map = style_map[group]
    
    group_values_to_sampleIDs = {}
    if one_trace_per_group:
        for group_value in df[group].unique(): # e.g., group='Treatment', group_value='Placebo'
            samples_with_this_val = df[df[group]==group_value][sample_string].tolist() # sample_string = 'Patient ID', etc.
            group_value = str(group_value) # needed for rare(?) case of val being numeric, e.g. group='Age (yrs)', val=5
            group_values_to_sampleIDs[val] = samples_with_this_val

    # Iterate through all the curves (or 'traces') in all the facets of the figure,
    # extract the labeling data and color for each, and store that color in the style map. 
    for curve_number in range(len(fig['data'])):
        hov_str = fig['data'][curve_number]['hovertemplate'] # it's an HTML string! :)
        curve_data = {}
        for entry in hov_str.split('<br>'):
            key, value = entry.split('=')
            curve_data[key] = value
        this_facet = curve_data['prop name'] # 'Neutrophils (%)', etc.
        this_color_and_dashing = fig['data'][curve_number]['line'] # dict: 'color' (e.g. '#D4A6C8') & 'dash' (e.g. 'solid')
        this_group_value = curve_data[group] # 'Placebo', etc.
        these_sample_ids = []
        if sample_string in curve_data: # sample_string is 'Sample', or 'Patient ID', etc.
            these_sample_ids = [curve_data[sample_string]] # ['id-001234'] or similar. We'll append to this 1-item list.
        else:
            # there's one trace per group (mean ± SD, etc.)
            these_sample_ids = group_values_to_sampleIDs[this_group_value]
        for this_sample_id in these_sample_ids:
            if this_sample_id in sample_IDs_map:
                if group in sample_IDs_map[this_sample_id]['facets']:
                    sample_IDs_map[this_sample_id]['facets'][group][this_facet] = this_color_and_dashing
                else:
                    sample_IDs_map[this_sample_id][group] = this_group_value
                    sample_IDs_map[this_sample_id]['facets'][group] = {this_facet : this_color_and_dashing}
            else:
                sample_IDs_map[this_sample_id] = {'facets' : {group : {this_facet : this_color_and_dashing}},
                                                  group : this_group_value}
            if this_group_value in group_values_map:
                group_values_map[this_group_value][samples_string].append(this_sample_id)
                if this_facet not in group_values_map[this_group_value]['facets']:
                    group_values_map[this_group_value]['facets'][this_facet] = this_color_and_dashing
            else:
                group_values_map[this_group_value] = {'facets' : {this_facet : this_color_and_dashing},
                                                      samples_string : [this_sample_id]}
    if group not in style_map:
        style_map[group] = group_values_map
    if samples_string not in style_map:
        style_map[samples_string] = sample_IDs_map                
    return style_map


def add_facet_to_style_map(style_map : dict, new_facet : str, samples_string : str='Sample IDs'):

    """
    This function gets called when the user creates a line plot with one or more facets,
    then specifies that another facet should be added. This function updates the style map
    to include the new facet. It assigns styles to the new facet using "majority rule":
    if sample3 is red in facet 0, red in facet 1, and blue in facet 2, it will get assigned
    red in the new facet. (Implementing "majority rule" is probably overkill.)

    Parameters
    ----------
    style_map : dict
       The style map we're updating.
    new_facet : str
       The name of the property being plotted in the new facet.
    samples_string : str, default : 'Sample IDs'
       The name of the key in style_map that corresponds to the "sample strings" (plural) concept.
       It could be 'Sample IDs', 'Patient IDs', etc. This is for style_map use only; it's never displayed.

    Returns
    -------
    dict
       The updated style map.
    """
    for k in style_map:
        if k == samples_string:
            """
            style_map[k] = { 'id1':{'facets':{'group1':{'facet1':{'color':'color1'},
                                                        'facet2':{'color':'color2'}, ...
                                                       },
                                              'group2':{'facet1':{'color':'color1'},
                                                        'facet2':{'color':'color2'}, ...
                                                       }, ...
                                             },
                                    'group1':'id1_group1_value',
                                    'group2':'id1_group2_value', ...
                                   },
                             'id2':{...}, ...
                           }
            """
            for sample_id in style_map[samples_string]:
                for group in style_map[samples_string][sample_id]['facets']:
                    colors = []
                    for facet in style_map[samples_string][sample_id]['facets'][group]:
                        colors.append(style_map[samples_string][sample_id]['facets'][group][facet]['color'])
                    v, c = np.unique(colors, return_counts=True)
                    majority_rule_color = str(v[np.argmax(c)])
                    style_map[samples_string][sample_id]['facets'][group][new_facet] = {'color':majority_rule_color}
        else: 
            """
            style_map[k] = { 'group_value1':{'facets':{'facet1':{'color':'color1'},
                                                       'facet2':{'color':'color2'}, ...
                                                      },
                                             samples_string:['id1','id2',...]
                                            },
                             'group_value2':{'facets':{...},
                                             samples_string:['id7','id8',...]
                                            }, ...
                           }
            """
            group = k
            # example: group = 'Treatment' and group_value = 'Placebo'
            for group_value in style_map[group]:
                colors = []
                for facet in style_map[group][group_value]['facets']:
                    colors.append(style_map[group][group_value]['facets'][facet]['color'])
                v, c = np.unique(colors, return_counts=True)
                majority_rule_color = str(v[np.argmax(c)])
                style_map[group][group_value]['facets'][new_facet] = {'color':majority_rule_color}
    return style_map


def remove_facet_from_style_map(style_map : dict, old_facet : str, samples_string : str='Sample IDs'):

    """
    This function gets called when the user creates a line plot with two or more facets,
    then specifies that a facet should be removed. This function removes the facet
    from the style map.

    Parameters
    ----------
    style_map : dict
       The style map we're updating.
    old_facet : str
       The name of the property being plotted in the facet to be removed.
    samples_string : str, default : 'Sample IDs'
       The name of the key in style_map that corresponds to the "sample strings" (plural) concept.
       It could be 'Sample IDs', 'Patient IDs', etc. This is for style_map use only; it's never displayed.

    Returns
    -------
    dict
       The updated style map.
    """
    for k in style_map:
        if k == samples_string:
            """
            style_map[k] = { 'id1':{'facets':{'group1':{'facet1':{'color':'color1'},
                                                        'facet2':{'color':'color2'}, ...
                                                       },
                                              'group2':{'facet1':{'color':'color1'},
                                                        'facet2':{'color':'color2'}, ...
                                                       }, ...
                                             },
                                    'group1':'id1_group1_value',
                                    'group2':'id1_group2_value', ...
                                   },
                             'id2':{...}, ...
                           }
            """
            for sample_id in style_map[samples_string]:
                for group in style_map[samples_string][sample_id]['facets']:
                    style_map[samples_string][sample_id]['facets'][group].pop(old_facet, None)
        else: 
            """
            style_map[k] = { 'group_value1':{'facets':{'facet1':{'color':'color1'},
                                                       'facet2':{'color':'color2'}, ...
                                                      },
                                             samples_string:['id1','id2',...]
                                            },
                             'group_value2':{'facets':{...},
                                             samples_string:['id7','id8',...]
                                            }, ...
                           }
            """
            group = k
            # example: group = 'Treatment' and group_value1 = 'Placebo'
            for group_value in style_map[group]:
                style_map[group][group_value]['facets'].pop(old_facet, None)
    return style_map


def boundary_val_and_op_to_idx(vals : list, op : str, bv : str):
    """
    Function to facilitate subsetting the bar plot by its x-axis values (strings).
    NOTE: If your values contain variable-width numbers whose sort-order needs to
    preserve numerical order (e.g. 'id-9-y' < 'id-10-x' not 'id-10-x' < 'id-9-y'),
    you'll need to add code to this function to handle this. Hints are given below.

    vals : list of str
       A list of sample IDs sorted in ascending order.
       If the sort order is anything other than basic string order
       (string1 < string2), you'll need to add code to handle this.
    op : str
       Operator. One of '>=', '>', '==', '<', '<='.
    bv : str
       Boundary value. A sample ID in vals, or a fake ID.
       If the ID strings are 6-digit integers and the user wants to
       access all entries beginning with '0', '1', or '2',
       they could set op = '<' and bv = '300000' regardless of whether
       '300000' is in the set of IDs.

    Returns
    -------
    int
       The index into vals to which bv translates.
       The caller will use this as vals[idx:] (idx<0) or vals[:idx] (idx>=0)
       to obtain the desired subset.
    """
    try:
        idx = vals.index(bv)
        if op == '>=':
            bv = -(len(vals) - idx)
        elif op == '>':
            bv = -(len(vals) - idx - 1)
        elif op == '==' or op == '<':
            bv = idx
        else: # '<='
            bv = idx + 1 #  this will not exceed len(vals))
    except ValueError: # bv is not in vals
        # Coding hint for sort orders other than simple str1 < str2:
        # Here, you might want to extract (e.g.) string and int parts
        # from bv and store them in variables like bv_string_part
        # and bv_int_part.
        if op == '==':
            bv = None # not found
        elif op == '<' or op == '<=':
            idx = 0
            while idx < len(vals):
                # Coding hint for sort orders other than simple str1 < str2:
                # If above you stored bv_string_part and bv_int_part,
                # here you might want to do the same (store these in, e.g.,
                # cur_string_part and cur_int_part) and replace
                # the lines 'if vals[idx] > bv: break' with something like this,
                # e.g. if you have 'apple-9', 'apple-10', and 'banana-7':
                # if cur_string_part > bv_string_part \
                #    or (cur_string_part==bv_string_part and cur_int_part > bv_int_part):
                #     break
                if vals[idx] > bv:
                    break
                idx += 1
            bv = idx
        else: # '>=' or '>'
            idx = -1
            while abs(idx) < len(vals):
                # Coding hint for sort orders other than simple str1 < str2:
                # Analogous to the replacement of 'if vals[idx] > bv: break' above,
                # you'd do the same thing here, with '>' above switched to '<' here:
                # if cur_string_part < bv_string_part \
                #    or (cur_string_part==bv_string_part and cur_int_part < bv_int_part):
                #     break
                if vals[idx] < bv:
                    idx += 1
                    break
                idx -= 1
            bv = idx
    return bv


def process_query_part(query : list, df : pd.DataFrame):
    """
    Function to parse a subquery within a set of conditions (query) defining a subset of samples
    which are to receive a label in the bar plot, and to return the subset as a list.
    This function parses and processes "data-driven" subqueries like (in English)
    "Yield in top 20" and "Purity >= %ile 95".
    This function is called by process_subsetting_query().
    NOTE: Queries on the bar labels (x-values) are allowed, but if the sort order
    is anything more complex than a simple x1 < x2 (e.g., if x-values 'id-10-x' and 'id-9-y'
    must obey 9 < 10 rather than '10' < '9'), you'll need to add code to this function
    to handle your special case. Hints are given below.

    Parameters
    ----------
    query : list of str
       A parsed subquery.
       Example: [['Age', '>=', '21'], 'OR', ['Height', '>', '168']]

    df : pd.DataFrame
       A melted DataFrame with 3 columns: 'sample', 'prop name', and 'prop value'.
       (Variations on 'sample', like 'Sample' or 'Sample ID', are allowed,
       and are inferred as the name of the column that's neither 'prop name' nor 'prop value'.)

    Returns
    -------
    list of str
       IDs of samples meeting the criteria in this subquery.

    Raises
    ------
    ValueError
       If there's a syntax or logic error, etc.
    """
    if not query:
        return []
    # Get the name of the column whose entries are plotted on the x-axis of the bar plot. Typically 'sample'.
    non_prop_columns = list(set(df.columns.to_list()) - set(['prop name', 'prop value']))
    if len(non_prop_columns) != 1:
        err_msg = f"Found 0 or multiple non-'property' columns in 'metrics' {non_prop_columns}. Expected 1."
        raise ImplementationError(err_msg)
    x_column = non_prop_columns[0]
    # Force the columns into the following order, to simplify querying.
    df = df[[x_column, 'prop name', 'prop value']]
    x_vals = None # filled in later if needed
    # 'query' is of the form [[query_parts], operator, [query_parts], ...],
    # where 'operator' is 'AND' or 'OR'.
    logic_op = 'AND'
    if len(query) > 1:
        logic_op = list(set([query[i] for i in range(1, len(query), 2)]))
        if len(logic_op) < 1:
            raise ValueError(f"process_query_part() didn't receive any logic operators (AND, OR).")
        if len(logic_op) > 1:
            raise ValueError(f"process_query_part() received both AND and OR; must receive only one of these.")
        logic_op = logic_op[0]
    prop_names = [query[i][0] for i in range(0, len(query), 2)]
    if x_column in prop_names:
        # Prep the x-values for querying.
        x_vals = list(df[x_column].unique().astype(str))
        x_vals.sort() # default sort
        # Coding hint:
        # If you need a more complex sort order,
        # add code for it here and use x_vals.sort(key=lambda x: [thing_1(x), thing_2(x)]).
        # Recommendation:
        # Use something like "if x_vals is fancy: sort accordingly, else: x_vals.sort()."
    comp_ops = [query[i][1] for i in range(0, len(query), 2)]
    boundary_vals = [query[i][2] for i in range(0, len(query), 2)]
    # process "special" comp_ops and boundary_vals here
    for i in range(len(comp_ops)):
        if comp_ops[i] == 'in top' or comp_ops[i] == 'in bottom':
            # Convert into "an expression in standard form."
            # E.g., if prop_names[i] is 'Purity (%)' and the values are [99, 98, 97, 96, 95],
            # then "purity in top 3" --> "purity >= 97".
            # First, ensure the entry is valid (a positive integer):
            try:
                if int(boundary_vals[i].strip()) < 1: # int() will raise ValueError if its arg isn't convertible to int
                    raise ValueError
            except ValueError:
                raise ValueError(f"'in top' and 'in bottom' must be followed by a positive integer; {boundary_vals[i]} is not allowed.")
            boundary_vals[i] = boundary_vals[i].strip()
            vals = None
            if prop_names[i] != x_column:
                vals = df[df['prop name'] == prop_names[i]]['prop value'].to_list()
            if comp_ops[i] == 'in top':
                comp_ops[i] = '>='
                if prop_names[i] != x_column:
                    vals.sort(reverse=True)
                else:
                    boundary_vals[i] = -min(int(boundary_vals[i]), len(x_vals)) # this will be an index into x_vals
            else:
                comp_ops[i] = '<='
                if prop_names[i] != x_column:
                    vals.sort()
                else:
                    boundary_vals[i] = min(int(boundary_vals[i]), len(x_vals)) # this will be an index into x_vals
            if prop_names[i] != x_column:
                boundary_vals[i] = vals[min(int(boundary_vals[i])-1, len(vals)-1)]
        else:
            data_driven_entry = False
            bv_stripped_lower = boundary_vals[i].strip().lower()
            if bv_stripped_lower in ['mean', 'median'] or bv_stripped_lower[:5] == '%ile ':
                data_driven_entry = True
            bad_entry_msg = f'Invalid entry "{boundary_vals[i]}".\n' \
                +'Options are "mean", "median", "%ile num", and val,\nwhere val is a number or a label-compatible string.\n' \
                +'(If using "%ile", num > 0 and num < 100.)'
            if data_driven_entry: # 'mean', 'median', or '%ile [num]'
                parts = boundary_vals[i].strip().lower().split(' ')
                parts = [z for z in parts if z!=''] # strip any excess separator whitespace, e.g. "%ile   90"
                if parts == ['median'] or (prop_names[i]==x_column and parts==['mean']):
                    parts = ['%ile', '50']
                if len(parts) == 1:
                    parts = parts[0]
                    if parts == 'mean':
                        boundary_vals[i] = df[df['prop name'] == prop_names[i]]['prop value'].to_numpy().mean()
                    else:
                        raise ValueError(bad_entry_msg)
                elif len(parts) == 2:
                    try:
                        percentile = float(parts[1]) # will raise ValueError if not convertible to float
                        if parts[0] != "%ile" or percentile <= 0 or percentile >= 100:
                            raise ValueError # this exception is caught below
                        if prop_names[i] != x_column:
                            boundary_vals[i] = np.percentile( \
                                                              df[df['prop name'] == prop_names[i]]['prop value'].to_numpy(dtype=float),
                                                              percentile,
                                                              method='inverted_cdf')
                        else:
                            idx = np.percentile(np.arange(len(x_vals)), percentile, method='inverted_cdf')
                            bv = boundary_vals[i] # shorthand; this will become an index into x_vals
                            if comp_ops[i] == '==' or comp_ops[i] == '<':
                                bv = idx
                            elif comp_ops[i] == '<=':
                                bv = min(idx+1, len(x_vals))
                            elif comp_ops[i] == '>':
                                bv = -(len(x_vals) - idx)
                            else: # '>='
                                bv = max(-(len(x_vals) - idx + 1), -len(x_vals))
                            boundary_vals[i] = bv # this is now an index into x_vals that will be used accordingly below
                    except ValueError:
                        raise ValueError(bad_entry_msg)
                else:
                    raise ValueError(bad_entry_msg)
            else: # Query is simply of the form 'column_name > value', etc. No action necessary here unless it's the x_column.
                boundary_vals[i] = boundary_vals[i].strip()
                if prop_names[i] == x_column:
                    boundary_vals[i] = boundary_val_and_op_to_idx(x_vals, comp_ops[i],
                                                                  boundary_vals[i])
    if logic_op == 'AND':
        filtered_samples = list(df[x_column].unique().astype(str)) # prep for the case of a query solely on x_column
        for i in range(len(prop_names)):
            if prop_names[i] != x_column:
                if len(query)==1:
                    filter_string = "["
                else:
                    filter_string = f"[x[0] in {filtered_samples} and "
                filter_string += f"x[1]=='{prop_names[i]}' and x[2] {comp_ops[i]} {boundary_vals[i]} for x in df.to_numpy()]"
                filtered_samples = df[eval(filter_string)][x_column].to_list()
            else:
                filtered_samples = set(filtered_samples)
                new_filtered_samples = set()
                if comp_ops[i] == '==':
                    if boundary_vals[i] is not None:
                        new_filtered_samples = set([x_vals[boundary_vals[i]]])
                else:
                    if boundary_vals[i] < 0:
                        new_filtered_samples = set(x_vals[boundary_vals[i]:])
                    else:
                        new_filtered_samples = set(x_vals[:boundary_vals[i]]) # empty set if user searched for entries below the min
                filtered_samples &= new_filtered_samples
    else: # 'OR'
        filtered_samples = set([])
        for i in range(len(prop_names)):
            new_filtered_samples = set()
            if prop_names[i] != x_column:
                filter_string = f"[x[1]=='{prop_names[i]}' " \
                    +f"and x[2] {comp_ops[i]} {boundary_vals[i]} " \
                    +f"for x in df.to_numpy()]"
                new_filtered_samples = set(df[eval(filter_string)][x_column].to_list())
            else:
                if comp_ops[i] == '==':
                    if boundary_vals[i] is not None:
                        new_filtered_samples = set([x_vals[boundary_vals[i]]])
                else:
                    if boundary_vals[i] < 0:
                        new_filtered_samples = set(x_vals[boundary_vals[i]:])
                    else:
                        new_filtered_samples = set(x_vals[:boundary_vals[i]]) # empty set if user searched for entries below the min
            filtered_samples |= new_filtered_samples
        filtered_samples = list(filtered_samples)
    return filtered_samples


def process_subsetting_query(raw_query : list, df : pd.DataFrame):
    """
    Function to parse a set of conditions (query) defining a subset of samples
    which are to receive a label in the bar plot, and to return the subset as a list.

    Parameters
    ----------
    raw_query : list of list of str
       A user-built query with no nested parentheticals.
       Example: [['', 'Qscore', '>', '1.0', ''], ['AND', '(', 'Yield', '>=', '8', ''],
                 ['OR', '', 'Purity', '>', '95', ')']]

    df : pd.DataFrame
       A melted DataFrame with 3 columns: 'sample', 'prop name', and 'prop value'.
       (Variations on 'sample', like 'Sample' or 'Sample ID', are allowed,
       and are inferred as the name of the column that's neither 'prop name' nor 'prop value'.)

    Returns
    -------
    list of str
       IDs of samples meeting the user's criteria.

    Raises
    ------
    ValueError
       If the user does something stoopid.

    Notes
    -----
    Calls process_query_part(), which raises ValueError if the user does something stoopid.
    """
    # First, parse the query and put it into a digestible format.
    query = []
    within_parens = False
    for filter in raw_query:
        fN = filter[-1] # either '' or ')'
        op = filter[0] # operator: either 'AND' or 'OR'
        f1 = filter[1] # either '' or '('
        if len(filter) == 5:
            op = '' # This is the initial filter. It has no operator.
            f1 = filter[0]
            filter = filter[1:-1]
        else:
            filter = filter[2:-1]
        if not within_parens:
            if fN == ')':
                raise ValueError('Error:  ")" before or without "(".\nCorrect this to continue.')
            if op:
                query.append(op)
            query.append(filter)
            if f1 == '(':
                within_parens = True
        else:
            query[-1] = [query[-1], op, filter]
            if fN == ')':
                within_parens = False
    if within_parens:
        raise ValueError('Error:  "(" without a closing ")".\nCorrect this to continue.')
    if len(query) == 1:
        logic_op = 'AND'
    else:
        logic_op = list(set([query[i] for i in range(1, len(query), 2)]))
        if len(logic_op) > 1:
            raise ValueError(f"process_subsetting_query() received both AND and OR outside parentheses-enclosed subqueries; must receive only one of these.")
        logic_op = logic_op[0]
    # Process any subqueries in parentheses, store the results, and remove them from the query.
    filtered_samples = set([])
    subqueries = [] # array locations (indices) of any subqueries will be stored here
    is_first_subquery = True # this is only needed when logic_op == 'AND'
    for i in range(0, len(query), 2):
        if type(query[i][0]) is list:
            these_samples = process_query_part(query[i], df)
            if logic_op == 'AND':
                if is_first_subquery:
                    filtered_samples = set(these_samples)
                    is_first_subquery = False
                else:
                    filtered_samples &= set(these_samples)
            else:
                    filtered_samples |= set(these_samples)
            subqueries = [i, *subqueries]
    for i in range(len(subqueries)):
        del query[subqueries[i]:subqueries[i]+2]
    if query and query[-1] == logic_op:
        query.pop() # delete 'AND' or 'OR' at the end of the remaining query
    final_step = [] if not query else process_query_part(query, df)
    final_result = []
    if logic_op == 'AND':
        if not subqueries:
            final_result = final_step
        else:
            final_result = list(set(final_step) & filtered_samples)
    else: # 'OR'
        final_result = list(set(final_step) | filtered_samples)
    return final_result
