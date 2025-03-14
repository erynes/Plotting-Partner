import base64
import io
import os
from textwrap import fill

import pandas as pd
import numpy as np
from dash import html, callback, Input, Output, State, no_update, ALL, ctx

import utils
import layout

#------------- Begin simple error message popup functionality --------------
#
@callback(Output('err-modal', 'is_open', allow_duplicate=True),
          Input('err-msg', 'children'),
          prevent_initial_call=True) # was: 'initial_duplicate')
def show_error_message(msg : str):
    """
    Any callback can trigger a popup error message by sending an error message
    to Output('err_msg', 'children').
    """
    return True


@callback(Output('err-modal', 'is_open', allow_duplicate=True),
          Input('close-err-modal', 'n_clicks'),
          prevent_initial_call='initial_duplicate')
def close_error_modal(n_clicks : int):
    if n_clicks > 0:
        return False # close the window: 'is_open' = False
    return no_update
#
#------------- End simple error message popup functionality ----------------

@callback(Output('lineplot-dataGroups-div', 'hidden'),
          Output('lineplot-df-melted-dict', 'data'),
          Output('lineplot-facetVars-checklist', 'options'),
          Output('lineplot-facetVars-checklist', 'value'),
          Output('lineplot-groupBy-dropdown', 'options'),
          Output('metrics-dict', 'data'),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('demo-welcome-banner-div', 'title'),
          prevent_initial_call='initial_duplicate') # necessary due to err-msg usage
def load_fake_demo_data(_):
    """
    Load fake data for the demo. Currently hardcoded. Will replace with interactive data loading.
    """
    num_outputs = len(ctx.outputs_list)
    no_updates = [no_update]*num_outputs
    infile_timeseries = 'assets/fake_timeseries_data.csv'
    infile_demographics = 'assets/fake_demographic_data.csv'
    groupBy_options = ['Treatment', 'Home location'] # BUGBUG: Hardcoded for demo. Use a checkbox?
    try:
        df_infile_timeseries = pd.read_csv(infile_timeseries)
    except FileNotFoundError:
        err_msg = f"Whoops, file {infile_timeseries} was not found."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    except Exception as e:
        err_msg = f"Failed to connect to the data source.\nReceived the following exception:\n{e}."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    try:
        df_infile_demographics = pd.read_csv(infile_demographics)
    except FileNotFoundError:
        err_msg = f"Whoops, file {infile_demographics} was not found."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    except Exception as e:
        err_msg = f"Failed to connect to the data source.\nReceived the following exception:\n{e}."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    vv_timeseries = list(set(df_infile_timeseries.columns.tolist()) - set(['Patient ID', 'Day'])
                         - set(groupBy_options)) # "vv_" for "value_vars"
    df_all = df_infile_timeseries.melt(id_vars=list(set(['Patient ID', 'Day']+groupBy_options)),
                                       value_vars=vv_timeseries,
                                       var_name='prop name', value_name='prop value',
                                       ignore_index=True) # .dropna()
    df_all['Patient ID'] = df_all['Patient ID'].astype(str)
    del(df_infile_timeseries)
    vv_demog = list(set(df_infile_demographics.columns.tolist()) - set(['Patient ID']))
    df_metrics = df_infile_demographics.melt(id_vars=['Patient ID'],
                                             value_vars=vv_demog,
                                             var_name='prop name', value_name='prop value',
                                             ignore_index=True) # .dropna()
    del(df_infile_demographics)
    df_metrics['Patient ID'] = df_metrics['Patient ID'].astype(str)        
    # groupBy_options = list(set(df_all.columns.tolist()) - set(['Patient ID','Day','prop name','prop value']))
    for opt in groupBy_options:
        if opt not in df_all.columns:
            err_msg = f"Whoops, groupBy option {opt} is not an option."
            no_updates[-1] = err_msg
            return tuple(no_updates)
    lineplot_facet_options = df_all['prop name'].unique().tolist()
    lineplot_facet_options = [{'label':' '+opt, 'value':opt} for opt in lineplot_facet_options]
    lineplot_facet_values = [] # initialize to "no items checked"
    # Put 'Patient ID' into column 0. Other functions will expect it to be there.
    df_all = df_all[['Patient ID', *list(set(df_all.columns) - set(['Patient ID']))]]
    df_metrics = df_metrics[['Patient ID', *list(set(df_metrics.columns) - set(['Patient ID']))]]
    return False, df_all.to_dict('records'), lineplot_facet_options, lineplot_facet_values, groupBy_options, \
        df_metrics.to_dict('records'), no_update



#---------------Begin initialization and 'initial click' callbacks-----------------
#
@callback(Output('barplot-div', 'hidden'),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('metrics-dict', 'data'),
          prevent_initial_call='initial_duplicate')
def hide_bar_plot(df_as_dict : list):
    """
    This function is called after "metrics" data (demographics or other snapshots in time)
    has been loaded into a DataFrame. If this data is present and has been loaded,
    this function "creates" a Div into which a bar plot will be created by "un-hiding" it.
    This action then triggers a call to initialize_barplot_components().
    """
    if not df_as_dict:
        return no_update, no_update
    if len(pd.DataFrame.from_dict(df_as_dict)) == 0:
        err_msg = "No metrics data was found,\nso the bar plot of metrics will not be shown."
        return no_update, err_msg
    # The bar plot is hidden, so to show it, we return False, thereby "un-hiding" it.
    return False, no_update


@callback(Output('sample-to-color-map', 'data', allow_duplicate=True),
          Output('sample-to-IsDefaultColor-map', 'data', allow_duplicate=True),
          Output('samples-dropdown', 'options', allow_duplicate=True),
          Output('sortorder-dropdown', 'options'),
          Output('sortorder-dropdown', 'value'),
          Output('barplot-facetVars-checklist', 'options'),
          Output('barplot-facetVars-checklist', 'value'),
          Input('barplot-div', 'hidden'),
          State('metrics-dict', 'data'),
          prevent_initial_call='initial_duplicate')
def initialize_barplot_components(_, df_as_dict : list):
    """
    Function to initialize the components for a bar plot of "metrics" data.
    The input DataFrame, received here as a dict, was validated by the loading function.
    This callback initializes the color maps for the sample names and the contents of the
    "sort order" dropdown (sort bar plot by age, or by sample name, or...)
    and the "choose which properties to show as facets" dropdown.

    Notes
    -----
    If your x-column values (sample IDs, patient IDs, etc.) require a custom sort order
    (not simple string sorting), you'll need to add code for this. Coding hints
    are given below.
    """
    num_outputs = len(ctx.outputs_list)
    no_updates = [no_update]*num_outputs
    if not df_as_dict:
        return tuple(no_updates)
    # Get the initial values for populating the bar plot's accompanying maps and dropdowns.
    df_metrics = pd.DataFrame.from_dict(df_as_dict)
    sample_id_string = df_metrics.columns[0]
    facet_options = df_metrics['prop name'].unique().tolist()
    sort_options = [sample_id_string, *facet_options]
    facet_values = [opt for opt in facet_options] # initialize to "all items checked"
    facet_options = [{'label':' '+opt, 'value':opt} for opt in facet_options]
        
    # Coding hint: If your bar labels (x-axis values) require a custom sort order,
    # add a sort key (lambda function) to the following line.
    the_samples = sorted(df_metrics[sample_id_string].unique().tolist())
    
    all_gray = [utils.LIGHT_GRAY]*len(the_samples)
    all_true = [True]*len(the_samples)
    color_mapping = dict(zip(the_samples, all_gray))
    is_default = dict(zip(the_samples, all_true)) # whether a sample should be given the default color
    sample_list = []
    for sample in the_samples:
        sample_list.append({'label':html.Span([html.Span('■',
                                                         style={'color':utils.LIGHT_GRAY,'font-size':36}),
                                               html.Span(sample, style={'padding-left':6})]),
                            'value':sample,
                            # Note: you can use something like 'search':int(sample.split('-')[-1])
                            # to enable the user to search a long list of samples by something other than
                            # the alphanumeric beginning of each sample name.
                            'search':sample})
    return color_mapping, is_default, sample_list, sort_options, sort_options[-1], facet_options, facet_values


@callback(Output('new-cat-modal', 'is_open', allow_duplicate=True),
          Output('edit-cat-modal', 'is_open', allow_duplicate=True),
          Input('categories-dropdown', 'value'),
          prevent_initial_call='initial_duplicate')
def category_chosen_from_dropdown(choice):
    """
    Dropdown of categories (labels): Add a new one, or edit an existing one.
    Selection triggers the display of the approprate modal.
    """
    if choice is None:
        return no_update, no_update
    if utils.ADD_NEW_CATEGORY['value'] == choice:
        return True, no_update
    return no_update, True
#
#-----------------End initialization and 'initial click' callbacks-----------------

#-------------------Begin 'define new label' callbacks-----------------------------
#
@callback(Output('color-picker', 'is_open', allow_duplicate=True),
          Output('idx-of-parent-modal', 'data', allow_duplicate=True),
          Input('choose-new-color-btn', 'n_clicks'),
          prevent_initial_call='initial_duplicate')
def new_label__show_color_picker(n_clicks : int):
    if n_clicks > 0:
        return True, utils.div_display['new cat']
    return no_update, no_update


@callback(Output('categories-dropdown', 'options', allow_duplicate=True),
          Output('label-assignment-dropdown', 'options', allow_duplicate=True),
          Output('categories-dropdown', 'value', allow_duplicate=True),
          Output('new-cat-modal', 'is_open', allow_duplicate=True),
          Output('samples-dropdown', 'options', allow_duplicate=True),
          Output('sample-to-color-map', 'data', allow_duplicate=True),
          Output('default-color', 'data', allow_duplicate=True),
          Input('new-cat-ok', 'n_clicks'),
          State('new-category-name', 'value'),
          State({'type':'color-displayed', 'index':utils.div_display['new cat']}, 'style'),
          State('categories-dropdown', 'options'),
          State('new-default-cat', 'value'),
          State('samples-dropdown', 'options'),
          State('sample-to-color-map', 'data'),
          State('sample-to-IsDefaultColor-map', 'data'),
          prevent_initial_call='initial_duplicate')
def accept_new_label(n_clicks : int, name : str, style : dict, options : list, is_default : bool,
                     sample_options : list, color_map : dict, isDefaultColor_map : dict):
    """
    User clicked 'OK' in the 'create new label' modal.
    
    Because this is a new label (introducing a new color), it hasn't been assigned to any sample.
    If the user checked the 'make this the default label' box, this means 'find all samples
    flagged as having the default label, and change their label to this new label (and color).'
    """
    num_outputs = len(ctx.outputs_list)
    ret_vals = [no_update]*num_outputs
    if n_clicks > 0:
        new_color = style['background']
        new_option = {'label':html.Span([html.Span('■',style={'color':new_color,'font-size':36}),
                                         html.Span(name, style={'padding-left':6})]),
                      'value':name,
                      'search':name}
        options.append(new_option)
        options_sans_option0 = options[1:]
        ret_vals[0] = options     # the updated label options
        ret_vals[1] = options_sans_option0 # the updated label options, sans the 'click to add new label' option
        ret_vals[2] = None # clear the value in categories_dropdown
        ret_vals[3] = False # close the modal (window)
        sample_label_changed = False
        if is_default:
            # Any sample marked as being 'the default' receives this new color.
            for i in range(len(sample_options)):
                sample_name = sample_options[i]['label']['props']['children'][1]['props']['children']
                if True == isDefaultColor_map[sample_name]:
                    color_map[sample_name] = new_color
                    sample_options[i]['label'] = html.Span([html.Span('■',
                                                                      style={'color':new_color,
                                                                             'font-size':36}),
                                                            html.Span(sample_name,
                                                                      style={'padding-left':6})])
                    sample_label_changed = True
            ret_vals[6] = new_color # propagate the default color to storage
        if sample_label_changed:
            ret_vals[4] = sample_options
            ret_vals[5] = color_map
    return tuple(ret_vals)


@callback(Output('new-cat-modal', 'is_open', allow_duplicate=True),
          Output('new-category-name', 'value', allow_duplicate=True),
          Output({'type':'color-displayed', 'index':utils.div_display['new cat']}, 'style', allow_duplicate=True),
          Output('categories-dropdown', 'value', allow_duplicate=True),
          Input('new-cat-cancel', 'n_clicks'),
          State({'type':'color-displayed', 'index':utils.div_display['new cat']}, 'style'),
          prevent_initial_call='initial_duplicate')
def cancel_new_label(n_clicks : int, style_to_cancel : dict):
    """
    User clicked 'Cancel' in the 'create new label' modal
    """
    if n_clicks > 0:
        blank_style = style_to_cancel.copy()
        blank_style['background'] = 'white'
        blank_style['color'] = blank_style['background']
        return False, '', blank_style, None
    return no_update, no_update, no_update, no_update


@callback(Output('new-category-name', 'value', allow_duplicate=True),
          Output({'type':'color-displayed', 'index':utils.div_display['new cat']}, 'style', allow_duplicate=True),
          Output('new-default-cat', 'value', allow_duplicate=True),
          Input('new-cat-modal', 'is_open'),
          State({'type':'color-displayed', 'index':utils.div_display['new cat']}, 'style'),
          prevent_initial_call='initial_duplicate')
def on_new_cat_modal_close(is_opening : bool, style_to_reset : dict):
    """
    Set/reset the components of the 'define a new category' modal when it closes.
    """
    if is_opening:
        return no_update, no_update, no_update
    style_to_reset['background'] = 'white'
    style_to_reset['color'] = style_to_reset['background']
    return None, style_to_reset, False
#
#---------------------End 'define new label' callbacks-----------------------------

#-------------------Begin 'edit new label' callbacks-------------------------------
#
@callback(Output('color-picker', 'is_open', allow_duplicate=True),
          Output('idx-of-parent-modal', 'data', allow_duplicate=True),
          Input('edit-color-btn', 'n_clicks'),
          prevent_initial_call='initial_duplicate')
def edit_label__show_color_picker(n_clicks : int):
    if n_clicks > 0:
        return True, utils.div_display['edit cat']
    return no_update, no_update


@callback(Output('cat-to-edit', 'children', allow_duplicate=True),
          Output('edit-category-name', 'value', allow_duplicate=True),
          Output({'type':'color-displayed', 'index':utils.div_display['edit cat']}, 'style', allow_duplicate=True),
          Output('edit-default-cat', 'value', allow_duplicate=True),
          Output('edit-default-cat', 'disabled', allow_duplicate=True),
          Input('edit-cat-modal', 'is_open'),
          State('categories-dropdown', 'value'),
          State('categories-dropdown', 'options'),
          State({'type':'color-displayed', 'index':utils.div_display['edit cat']}, 'style'),
          State('default-color', 'data'),
          prevent_initial_call='initial_duplicate')
def process_edit_cat_modal_OpeningClosing(is_opening : bool, choice : str, label_options : list,
                                          old_editing_modal_style : dict, default_color : str):
    """
    This callback handles the 'edit existing category' modal when it opens and closes.
    """
    if not is_opening:
        # Set/reset things. It seems helpful to have this in here... is it truly?
        old_editing_modal_style['background'] = 'white'
        old_editing_modal_style['color'] = old_editing_modal_style['background']
        return '', None, old_editing_modal_style, False, False
    for i in range(len(label_options)):
        # Get the formatted label (with color).
        if label_options[i]['value'] == choice:
            current_color = label_options[i]['label']['props']['children'][0]['props']['style']['color']
            formatted_choice = label_options[i]['label'].copy() # contains the color swatch
            new_editing_modal_style = old_editing_modal_style.copy()
            new_editing_modal_style['background'] = current_color
            new_editing_modal_style['color'] = new_editing_modal_style['background']
            if current_color == default_color:
                return formatted_choice, choice, new_editing_modal_style, True, True
            return formatted_choice, choice, new_editing_modal_style, False, False
    return no_update, no_update, no_update, no_update, no_update


@callback(Output('categories-dropdown', 'options', allow_duplicate=True),
          Output('label-assignment-dropdown', 'options', allow_duplicate=True),
          Output('categories-dropdown', 'value', allow_duplicate=True),
          Output('edit-cat-modal', 'is_open', allow_duplicate=True),
          Output('samples-dropdown', 'options', allow_duplicate=True),
          Output('sample-to-color-map', 'data', allow_duplicate=True),
          Output('sample-to-IsDefaultColor-map', 'data', allow_duplicate=True),
          Output('default-color', 'data', allow_duplicate=True),
          Input('edit-cat-ok', 'n_clicks'),
          State('edit-category-name', 'value'),
          State({'type':'color-displayed', 'index':utils.div_display['edit cat']}, 'style'),
          State('categories-dropdown', 'options'),
          State('categories-dropdown', 'value'),
          State('edit-default-cat', 'value'),
          State('samples-dropdown', 'options'),
          State('sample-to-color-map', 'data'),
          State('sample-to-IsDefaultColor-map', 'data'),
          prevent_initial_call='initial_duplicate')
def accept_edited_label(n_clicks : int, new_name : str, style : dict, label_options : list,
                        unedited_name : str, is_default : bool, sample_options : list,
                        color_map : dict, isDefaultColor_map : dict):
    """
    User clicked 'OK' in the 'edit existing label' modal
    
    Note: The user's 'edit' can be to only the color or only the color's 'is default' status;
    in these cases, new_name and unedited_choice will be equal. (This is just an "FYI.")
    """
    num_outputs = len(ctx.outputs_list)
    ret_vals = [no_update]*num_outputs
    if n_clicks > 0:
        ret_vals[2] = None  # clear the value in categories_dropdown
        ret_vals[3] = False # close the modal (window)
        new_color = style['background']
        new_option = {'label':html.Span([html.Span('■',style={'color':new_color,'font-size':36}),
                                         html.Span(new_name, style={'padding-left':6})]),
                      'value':new_name,
                      'search':new_name}
        label_option_changed = False # Typically True; will be False if the 'edit' was "notDefaut -> default."
        # Find this label among the 'options' of the Dropdown of labels and replace it if necessary.
        for i in range(len(label_options)):
            if label_options[i]['value'] == unedited_name:
                unedited_color = label_options[i]['label']['props']['children'][0]['props']['style']['color']
                if new_name != unedited_name or new_color != unedited_color:
                    label_options[i] = new_option
                    label_option_changed = True
                break
        sample_option_changed = False
        color_map_changed = False
        isDefaultColor_map_changed = False
        # Traverse the samples (sample = color label + parent ID) and make any necessary updates.
        for i in range(len(sample_options)):
            sample_name = sample_options[i]['label']['props']['children'][1]['props']['children']
            sample_color = sample_options[i]['label']['props']['children'][0]['props']['style']['color']
            # Make changes if:
            # 1. The sample has the original (unedited) color and that color has changed.
            # 2. The sample is flagged as needing the 'default' color and this edit makes new_color the default.
            # 3. The sample already has the new color and this edit makes new_color the default.
            #    In this case, change its 'is default' flag to True.
            if sample_color == unedited_color and unedited_color != new_color: # case 1
                color_map[sample_name] = new_color
                sample_options[i]['label']['props']['children'][0]['props']['style']['color'] = new_color
                color_map_changed = True
                sample_option_changed = True
            if is_default:
                if isDefaultColor_map[sample_name]:
                    if sample_color != new_color:                              # case 2
                        color_map[sample_name] = new_color
                        sample_options[i]['label']['props']['children'][0]['props']['style']['color'] = new_color
                        color_map_changed = True
                        sample_option_changed = True
                    # Otherwise new_color is the default, the sample needs the default color,
                    # and the sample already has it.
                elif sample_color == new_color:                                # case 3
                    isDefaultColor_map[sample_name] = True
                    isDefaultColor_map_changed = True
        if label_option_changed:
            label_options_sans_option0 = label_options[1:]
            ret_vals[0] = label_options
            ret_vals[1] = label_options_sans_option0
        if sample_option_changed:
            ret_vals[4] = sample_options
        if color_map_changed:
            ret_vals[5] = color_map
        if isDefaultColor_map_changed:
            ret_vals[6] = isDefaultColor_map
        if is_default:
            ret_vals[7] = new_color # Update even if new_color==unedited_color. Edit could be 'make default' alone.
    return tuple(ret_vals)


@callback(Output('edit-cat-modal', 'is_open', allow_duplicate=True),
          Output('edit-category-name', 'value', allow_duplicate=True),
          Output({'type':'color-displayed', 'index':utils.div_display['edit cat']}, 'style', allow_duplicate=True),
          Output('categories-dropdown', 'value', allow_duplicate=True),
          Input('edit-cat-cancel', 'n_clicks'),
          State({'type':'color-displayed', 'index':utils.div_display['edit cat']}, 'style'),
          prevent_initial_call='initial_duplicate')
def cancel_edited_label(n_clicks : int, style_to_cancel : dict):
    """
    User clicked 'Cancel' in the 'edit existing label' modal
    """
    if n_clicks > 0:
        blank_style = style_to_cancel.copy()
        blank_style['background'] = 'white'
        blank_style['color'] = blank_style['background']
        return False, None, blank_style, None
    return no_update, no_update, no_update, no_update
#
#---------------------End 'edit new label' callbacks-------------------------------

#-------------------Begin 'color picker' callbacks---------------------------------
#
"""
   Within the 'color picker', there are 3 ways to specify a color:
   1. click a swatch within the grid of swatches
   2. click what I'm calling a "color wheel" in the lower left-hand corner of the modal
   3. type a hex string into the Input box and hit 'enter'
   Options 1 and 2 will update the hex string in the Input box.
   That update, or a direct update to it (option 3 above), will update the
   color swatch (Div) immediately to the left of the Input box.
   Clicking the 'OK' button will send the color of the Div to the appropriate component
   and close the 'color picker' modal.
"""

@callback(Output('color-choice-string', 'value', allow_duplicate=True),
          Output('color-choice-string', 'n_submit', allow_duplicate=True),
          Input({'type':'ColorChoice', 'index':ALL}, 'n_clicks'),
          State('color-choice-string', 'n_submit'),
          prevent_initial_call='initial_duplicate')
def on_color_swatch_click(n_clicks : list, n_submit : int):
    """
    Option 1 above:  click a swatch within the grid of swatches.
    Forwards the hex color string to the Input and mimics the user clicking 'enter'.
    """
    if n_clicks and ctx.triggered_id:
        # ctx.triggered_id is a Dash extension of dict
        triggered_index = ctx.triggered_id['index']
        color_chosen = utils.tableau20[triggered_index]
        return color_chosen, n_submit+1
    return no_update, no_update


@callback(Output('color-choice-string', 'value', allow_duplicate=True),
          Output('color-choice-string', 'n_submit', allow_duplicate=True),
          Input('color-wheel', 'value'),
          State('color-choice-string', 'n_submit'),
          prevent_initial_call='initial_duplicate') 
def on_color_wheel_click(this_hex_color : str, n_submit : int):
    """
    Option 2 above:  click the "show color wheel" button and choose a color.
    Forwards the hex color string to the Input and mimics the user clicking 'enter'.
    """
    return this_hex_color, n_submit+1


@callback(Output('final-color-choice', 'style'),
          Output('color-choice-string', 'value', allow_duplicate=True),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('color-choice-string', 'n_submit'),
          State('color-choice-string', 'value'),
          State('final-color-choice', 'style'),
          prevent_initial_call='initial_duplicate')
def on_hex_color_string_input(n_submit : int, hex_string : str, style : dict):
    """
    This can be triggered by option 3 above (user enters a string and clicks 'enter')
    or by options 1 and 2 automatically "entering the string and clicking 'enter'."
    """
    if n_submit > 0:
        # Validate hex_string before proceeding!
        # Note: Eric first used try/raise on int_value = int(hex_string[1:], 16),
        # but the edge cases were annoying. Hence what follows.
        invalid_hex_string = False
        if len(hex_string) == 6:
            hex_string = '#' + hex_string
        if len(hex_string) != 7 or hex_string[0] != '#':
            invalid_hex_string = True
        i = 1
        while i < 7 and not invalid_hex_string:
            c = hex_string[i]
            if c.isalpha():
                if c.lower() > 'f':
                    invalid_hex_string = True
            elif not c.isdigit():
                invalid_hex_string = True
            i += 1
        if invalid_hex_string:
            err_msg = f'\"{hex_string}\" is not a valid color specification.\n' \
                +'This must be a 6-digit hexadecimal value, e.g. \"#FF0000\" for \"red.\"'
            # Reset the hex string and the accompanying Div that displays that color.
            style['color'] = style['background'] = '#FFFFFF'
            return style, '#FFFFFF', err_msg
        style['color'] = style['background'] = hex_string
        return style, no_update, no_update
    return no_update, no_update, no_update


@callback(Output({'type':'color-displayed', 'index':ALL}, 'style', allow_duplicate=True),
          Output('color-wheel', 'value', allow_duplicate=True),
          Output('color-picker', 'is_open', allow_duplicate=True),
          Input('ok-color-choice', 'n_clicks'),
          State('final-color-choice', 'style'),
          State({'type':'color-displayed', 'index':ALL}, 'style'),
          State('idx-of-parent-modal', 'data'),
          prevent_initial_call='initial_duplicate')
def apply_color(n_clicks : int, style_with_color_choice : dict, old_styles : list, idx : int):
    """
    Display the chosen color in the parent modal and close the 'color-picker' modal.
    Also reset the "color wheel" button to white.
    """
    output_style_list = [no_update]*len(old_styles)
    if n_clicks > 0:
        color_choice = style_with_color_choice['color']
        new_style = old_styles[idx].copy()
        new_style['color'] = new_style['background'] = color_choice
        output_style_list[idx] = new_style
        return output_style_list, "#FFFFFF", False
    return output_style_list, "#FFFFFF", no_update


@callback(Output('color-picker', 'is_open', allow_duplicate=True),
          Output('color-wheel', 'value', allow_duplicate=True),
          Output('lineplot-graph-id', 'clickData', allow_duplicate=True),
          Input('cancel-color-choice', 'n_clicks'),
          State('idx-of-parent-modal', 'data'),
          prevent_initial_call='initial_duplicate')
def cancel_color_picker(n_clicks : int, idx : int):
    """
    This is for the canceling/closing the modal of color options.
    If the color picker was triggered by the user clicking on a trace in a plot,
    we reset that plot's clickData so the user can edit that trace by clicking on it.
    (If we don't reset clickData, repeated clicks on the trace will do nothing.)
    """
    num_outputs = len(ctx.outputs_list)
    no_updates = [no_update]*num_outputs
    if n_clicks > 0:
        if idx == utils.div_display['line plot']:
            return False, utils.WHITE, None
        return False, utils.WHITE, no_update
    return no_updates
#
#---------------------End 'color picker' callbacks---------------------------------


#-------------------Begin 'label a sample' callbacks-------------------------------
#
@callback(Output('assign-label-modal', 'is_open', allow_duplicate=True),
          Output('labeled-sample', 'children', allow_duplicate=True),
          Input('samples-dropdown', 'value'),
          State('samples-dropdown', 'options'),
          prevent_initial_call='initial_duplicate')
def sample_chosen_from_dropdown(choice, samples_options):
    """
    Dropdown of labeled samples: selection triggers label-assignment modal.
    """
    for i in range(len(samples_options)):
        if samples_options[i]['value'] == choice:
            return True, samples_options[i]['label'].copy()
    return no_update, no_update


@callback(Output('sample-to-color-map', 'data', allow_duplicate=True),
          Output('samples-dropdown', 'options', allow_duplicate=True),
          Output('samples-dropdown', 'value', allow_duplicate=True),
          Output('assign-label-modal', 'is_open', allow_duplicate=True),
          Output('label-assignment-dropdown', 'value', allow_duplicate=True),
          Output('sample-to-IsDefaultColor-map', 'data', allow_duplicate=True),
          Input('label-assignment-ok', 'n_clicks'),
          State('labeled-sample', 'children'),
          State('label-assignment-dropdown', 'value'),
          State('label-assignment-dropdown', 'options'),
          State('samples-dropdown', 'options'),
          State('sample-to-color-map', 'data'),
          State('sample-to-IsDefaultColor-map', 'data'),
          State('default-color', 'data'),
          prevent_initial_call='initial_duplicate')
def assign_label_to_sample(n_clicks : int, sample_to_be_labeled, new_label_str, label_options,
                           sample_options, color_map, isDefaultColor_map : dict, default_color : str):
    """
    User clicked 'OK' to assign a label to a sample.
    """
    if n_clicks > 0:
        sample_name = sample_to_be_labeled['props']['children'][1]['props']['children']
        for i in range(len(label_options)):
            if label_options[i]['value'] == new_label_str:
                new_sample_color = label_options[i]['label']['props']['children'][0]['props']['style']['color']
                break
        newly_labeled_sample = html.Span([html.Span('■', style={'color':new_sample_color,'font-size':36}),
                                          html.Span(sample_name, style={'padding-left':6})])
        for i in range(len(sample_options)):
            if sample_options[i]['value'] == sample_name:
                sample_options[i]['label'] = newly_labeled_sample
                break
        color_map[sample_name] = new_sample_color
        orig_bool_entry = isDefaultColor_map[sample_name]
        isDefaultColor_map[sample_name] = (new_sample_color == default_color)
        if isDefaultColor_map[sample_name] != orig_bool_entry:
            return color_map, sample_options, None, False, None, isDefaultColor_map
        return color_map, sample_options, None, False, None, no_update
    return no_update, no_update, no_update, no_update, no_update, no_update


@callback(Output('assign-label-modal', 'is_open', allow_duplicate=True),
          Output('labeled-sample', 'children', allow_duplicate=True),
          Output('samples-dropdown', 'value', allow_duplicate=True),
          Output('label-assignment-dropdown', 'value', allow_duplicate=True),
          Input('label-assignment-cancel', 'n_clicks'),
          prevent_initial_call='initial_duplicate')
def cancel_label_assignment(n_clicks : int):
    """
    User clicked 'Cancel' while on the modal for assigning a label to a sample.
    """
    if n_clicks > 0:
        return False, None, None, None
    return no_update, no_update, no_update, no_update


@callback(Output('subset-label-assignment', 'is_open', allow_duplicate=True),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('label-a-subset-button', 'n_clicks'),
          State('label-assignment-dropdown', 'options'),
          prevent_initial_call='initial_duplicate')
def show_subset_label_assignment_modal(n_clicks : int, label_options : list):
    """
    User clicked the 'Label a subset' button above the bar plot.
    Opens the modal for doing this, or displays an error message
    if the user has not yet created any labels.
    """
    if n_clicks:
        if not label_options:
            err_msg = 'Click the "Labels for samples" dropdown menu\n' \
                +'to create a label for one or more samples.'
            return no_update, err_msg
        return True, no_update
    return no_update, no_update


@callback(Output('label-assignment-dropdown-2', 'options'),
          Output('expanding-query-div', 'children', allow_duplicate=True),
          Output('query-results-tally', 'children', allow_duplicate=True),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('subset-label-assignment', 'is_open'),
          State('label-assignment-dropdown', 'options'),
          State('metrics-dict', 'data'),
          prevent_initial_call='initial_duplicate')
def load_subset_label_assignment_modal(is_opening : bool, label_options : list,
                                       df_as_dicts : list):
    """
    Function to populate the "subset label assignment" modal when it opens.

    Parameters
    ----------
    is_opening : bool
       Whether the modal is opening or closing.
    label_options : list
       The 'options' list of available labels, from the dropdown on the dashboard.
    df_as_dicts : list
       The "metrics" records, i.e. a list of rows with each row expressed as a dict.

    Returns
    -------
    list of dbc.Row(), str, str
       A one-element list of dbc.Row(), the string '0 samples selected', and no_update,
       or no_update, no_update, and an error message.
    """
    num_outputs = len(ctx.outputs_list)
    no_updates = [no_update]*num_outputs
    if not is_opening or not label_options or not df_as_dicts:
        return tuple(no_updates)
    for required_column in ['prop value', 'prop name']:
        if required_column not in df_as_dicts[0]:
            err_msg = f"Error: Required column {required_column} was not found in 'metrics'."
            no_updates[-1] = err_msg
            return tuple(no_updates)
    df_in = pd.DataFrame.from_dict(df_as_dicts)
    non_prop_columns = list(set(df_in.columns.to_list()) - set(['prop name', 'prop value']))
    if len(non_prop_columns) != 1:
        err_msg = f"Found 0 or multiple non-'property' columns in 'metrics' {non_prop_columns}. Expected 1."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    x_column = non_prop_columns[0] # typically 'sample'
    rows = []
    return label_options, layout.make_query_row(rows, [*list(df_in['prop name'].unique()), x_column]), \
        '0 samples selected', no_update


@callback(Output('expanding-query-div', 'children', allow_duplicate=True),
          Input({'type':'add-another', 'index':ALL}, 'n_clicks'),
          State('expanding-query-div', 'children'),
          prevent_initial_call=True)
def add_row_to_query(n_clicks : int, rows : list):
    if not rows or not n_clicks or not n_clicks[-1]:
        return no_update
    prop_names_and_xcolumn = rows[-1]['props']['children'][2]['props']['children']['props']['options']
    return layout.make_query_row(rows, prop_names_and_xcolumn)


@callback(Output('samples-dropdown', 'options', allow_duplicate=True),
          Output('sample-to-color-map', 'data', allow_duplicate=True),
          Output('sample-to-IsDefaultColor-map', 'data', allow_duplicate=True),
          Output('subset-label-assignment', 'is_open', allow_duplicate=True),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('subset-label-assignment-ok', 'n_clicks'),
          State('expanding-query-div', 'children'),
          State('metrics-dict', 'data'),
          State('label-assignment-dropdown-2', 'value'),
          State('label-assignment-dropdown-2', 'options'),
          State('samples-dropdown', 'options'),
          State('sample-to-color-map', 'data'),
          State('sample-to-IsDefaultColor-map', 'data'),
          State('default-color', 'data'),
          prevent_initial_call=True)
def do_query(n_clicks : int, rows : list, df_as_dicts : list,
             new_label_str, label_options, sample_options,
             color_map, isDefaultColor_map : dict, default_color : str):
    num_outputs = len(ctx.outputs_list)
    no_updates = [no_update]*num_outputs
    if not n_clicks or not rows:
        return tuple(no_updates)
    if not new_label_str:
        err_msg = 'Choose a label from the available options, or click Cancel.'
        no_updates[-1] = err_msg
        return tuple(no_updates)
    df_in = pd.DataFrame.from_dict(df_as_dicts)
    num_rows = len(rows)
    subset = []
    raw_query = []
    for entry in ctx.args_grouping:
        if entry['id'] == 'expanding-query-div':
            for j in range(len(entry['value'])):
                raw_query_row = []
                err_msg = ""
                for i in range(int(j==0),6): # 1,...,5 for the initial row; 0,...,5 otherwise
                    # Slots 2, 3, and 4 are mandatory. Display an error message if any are missing.
                    props_dict = entry['value'][j]['props']['children'][i]['props']['children']['props']
                    if i==2 and ('value' not in props_dict or props_dict['value'] is None):
                        err_msg = "Choose a property on which to filter, or click Cancel."
                        break
                    if i==3 and ('value' not in props_dict or props_dict['value'] is None):
                        err_msg = "Choose an operator (>, ==, etc.) for the filter, or click Cancel."
                        break
                    if i==4 and ('value' not in props_dict or not props_dict['value']):
                        err_msg = 'Enter a bound for the filter (e.g. 1.5, "mean", "%ile 95"),\nor click Cancel.'
                        break
                    raw_query_row.append(entry['value'][j]['props']['children'][i]['props']['children']['props']['value'])
                if err_msg:
                    no_updates[-1] = err_msg
                    return tuple(no_updates)
                raw_query.append(raw_query_row)
            break
    try:
        subset = set(utils.process_subsetting_query(raw_query, df_in))
        if not subset:
            err_msg = "No results were found for this query."
            no_updates[-1] = err_msg
            return tuple(no_updates)
    except ValueError as e:
        err_msg = str(e)
        no_updates[-1] = err_msg
        return tuple(no_updates)
    # Get the color corresponding to new_label_str:
    for i in range(len(label_options)):
        if label_options[i]['value'] == new_label_str:
            new_sample_color = label_options[i]['label']['props']['children'][0]['props']['style']['color']
            break
    newColor_is_the_defaultColor = (new_sample_color == default_color)
    isDefaultColor_map_changed = False
    color_map_changed = False
    # Assign the label to all samples in the selected subset and update the color map(s).
    for i in range(len(sample_options)):
        sample_name = sample_options[i]['value']
        if sample_name in subset:
            old_sample_color = color_map[sample_name]
            oldColor_was_the_defaultColor = (old_sample_color == default_color)
            if old_sample_color == new_sample_color:
                continue
            newly_labeled_sample = html.Span([html.Span('■', style={'color':new_sample_color,'font-size':36}),
                                              html.Span(sample_name, style={'padding-left':6})])
            sample_options[i]['label'] = newly_labeled_sample
            color_map[sample_name] = new_sample_color
            color_map_changed = True
            if newColor_is_the_defaultColor:
                isDefaultColor_map[sample_name] = True
                isDefaultColor_map_changed = True
            elif oldColor_was_the_defaultColor:
                isDefaultColor_map[sample_name] = False
                isDefaultColor_map_changed = True

    retvals = [sample_options, no_update, no_update, False, no_update] # False = "close the modal"
    if color_map_changed:
        retvals[1] = color_map
    if isDefaultColor_map_changed:
        retvals[2] = isDefaultColor_map
    return tuple(retvals)


@callback(Output('subset-label-assignment', 'is_open', allow_duplicate=True),
          Input('subset-label-assignment-cancel', 'n_clicks'),
          prevent_initial_call='initial_duplicate')
def cancel_subset_label_assignment(n_clicks : int):
    """
    User clicked 'Cancel' while on the modal for assigning a label to a sample.
    """
    if n_clicks:
        return False
    return no_update
#
#---------------------End 'label a sample' callbacks-------------------------------

#-------------Begin 'interactive plotting options' callbacks-----------------------
#
@callback(Output('barplot-graph-id', 'figure'),
          Output('samples-dropdown', 'options', allow_duplicate=True),
          Output('sortorder-dropdown', 'options', allow_duplicate=True),
          Output('sortorder-dropdown', 'value', allow_duplicate=True),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('render-barplot-button', 'n_clicks'),
          Input('sample-to-color-map', 'data'),
          Input('label-assignment-dropdown', 'options'),
          Input('barPlot-hideXticks-checkbox', 'value'),
          Input('sortorder-dropdown', 'value'),
          Input('sortorder-radioitems', 'value'),
          State('metrics-dict', 'data'),
          State('samples-dropdown', 'options'),
          State('barplot-facetVars-checklist', 'value'),
          prevent_initial_call='initial_duplicate')
def update_barplot(n_clicks : int, color_map : dict, list_of_labels : list,
                   hide_x_ticks : bool, sorting_key : str,
                   sorting_direction : int, df_as_dict : list, labeled_samples : list,
                   props_to_plot : list):
    """
    Function to make/update the faceted bar plot.
    This will be called (the plot will be updated) when the user:
    * sets or changes the map from ID to color (includes actions defining the 'default' label)
    * assigns a new label to a sample
    * clicks the checkbox to hide or "un-hide" the x-axis tick labels
    * changes the property by which the data should be sorted
    * changes the direction of the sort

    Parameters
    ----------
    n_clicks : int
       The number of times this button has been clicked.
    color_map : dict
       A mapping from ID (str) to color (hex str).
    list_of_labels : list
       The current list of options in the 'labels' dropdown (color swatch + label name).
    hide_x_ticks : bool
       Whether to hide the x-axis tick labels.
    sorting_key : str
       The property name (or column, e.g. 'Patient ID') by whose values the bars should be sorted.
    sorting_direction : int
       1 = ascending, 0 = descending
    df_as_dict : list
       List of dicts (one per DF row) created by calling "to_dict" on a DataFrame in another callback.
       Should contain, at minimum, columns [x-axis name], 'prop name', and 'prop value'.
    labeled_samples : list
       The current list of options in the 'samples' dropdown (color swatch + parent ID).
    props_to_plot : list
       The properties to plot (one facet for each) vs. ID ('Patient ID', 'Sample ID', etc.).

    Returns
    -------
    figure, list (of labeled samples), str (error message)
       The figure will be displayed and the 'samples' dropdown options will get re-sorted if necessary.
       Or a modal window displaying the error message will appear.

    Notes
    -----
    If your bar labels (x-axis values, e.g. for 'Patient ID' or 'Sample') require a custom sort order,
    you will need to add code to this function to handle it. Coding hints are included below.
    """
    num_outputs = len(ctx.outputs_list)
    no_updates = [no_update]*num_outputs
    if not df_as_dict:
        return tuple(no_updates)
    for required_column in ['prop value', 'prop name']:
        if required_column not in df_as_dict[0]:
            err_msg = f"Cannot make the bar plot; required column {required_column} was not found."
            no_updates[-1] = err_msg
            return tuple(no_updates)
    if ctx.triggered_id == 'render-barplot-button' and n_clicks > 0:
        # Presumably the facets have changed?
        if sorting_key not in props_to_plot:
            sorting_key = props_to_plot[0]
    df_in = pd.DataFrame.from_dict(df_as_dict)
    non_prop_columns = list(set(df_in.columns.to_list()) - set(['prop name', 'prop value']))
    if len(non_prop_columns) != 1:
        err_msg = f"Found 0 or multiple non-'property' columns in 'metrics' {non_prop_columns}. Expected 1."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    x_column = non_prop_columns[0] # typically 'sample', 'Patient ID', etc.
    if not props_to_plot:
        err_msg = "No properties were selected for the y-axes.\n"
        err_msg += "Select one or more properties and click the 'plot' button."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    # At least for now, drop any row with a NaN.
    df_facets = df_in[[True if prop in props_to_plot \
                       else False for prop in df_in['prop name']]].dropna(how='any',
                                                                          ignore_index=True,
                                                                          axis=0)
    if len(df_facets)==0:
        err_msg = "Missing data was found for the selected properties.\n"
        err_msg += "Select different properties and click the 'plot' button."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    if sorting_key != x_column and sorting_key not in df_facets['prop name'].unique():
        err_msg = f"Required property '{sorting_key}' was not found in the 'prop name' column of the DataFrame."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    ascending = bool(sorting_direction)
    if x_column == sorting_key:
        # Coding hint: If your x_column values require a sort order different from
        # standard string sort order, add code here to implement that.
        # Hint: If your x_column values have different parts ('part1_part2', 'p1-p2-p3', etc.),
        # you can add columns to a copy of df_facets, sort on those, and then drop those columns.
        # E.g.:
        # df_final = df_facets.copy()
        # df_final['p1'] = list of 'part1' substrings from your x_column values
        # df_final['p2'] = ditto for 'part2' substrings
        # df_final = df_final.sort_values(by=['p1','p2'],
        #                                 ascending=[ascending,ascending]).drop(['p1','p2'],
        #                                                                       axis=1).reset_index(drop=True)
        # It might be best to use an if/else block:
        # if fancy_sort_needed: fancy_sort else: standard_sort
        df_final = df_facets.sort_values(by=[x_column], ascending=[ascending])
        props = df_final['prop name'].unique().tolist()
    else:
        props = df_facets['prop name'].unique().tolist() # returned in the order in which they appear at the moment
        props[props.index(sorting_key)] = props[0]
        props[0] = sorting_key
        this_sort_order = dict(zip(props, range(len(props))))
        df_prelim = df_facets.sort_values(by=['prop value'], ascending=[ascending])
        # Critically important: Must choose a final 'kind' of sorting that's stable, i.e. that preserves the prelim sort.
        # According to the pandas docs, the two stable options are 'stable' and 'mergesort'.
        df_final = df_prelim.sort_values(by=['prop name'], key=lambda z : z.map(this_sort_order), kind='stable')
    # Currently there's no code in the following call that explicitly raises an exception. But try/except doesn't hurt.
    try:
        fig = utils.make_custom_multifaceted_bar_plot(df_final, props, color_map,
                                                      list_of_labels, x_column, hide_x_ticks)
    except Exception as e:
        err_msg = f"Unable to render the bar plot. {e}"
        no_updates[-1] = err_msg
        return tuple(no_updates)
    # Get the x_column values  in the order in which they have now been sorted.
    # Note: When sorting_key is a property name and len(props_to_plot)>1, samples/parents for which that property is absent
    # but any of the other props_to_plot is present will be placed at the end of the sorted list,
    # evidently lexicographically, in the direction given by the variable 'ascending'.
    sorted_parents = list(dict.fromkeys(df_final[x_column].tolist())) # order is preserved in the keys of a dict for python 3.7+
    # If sorting_key is a property name, samples/parents for which all of props_to_plot are absent
    # will be absent from this list. In this case, we append them here:
    if len(sorted_parents) != len(labeled_samples):
        sorted_parents += list(set(df_final[x_column].unique().tolist()) - set(sorted_parents))
    # Now put the entries in the labeled samples dropdown (one per parent) into this order for ease of use:
    for i in range(len(sorted_parents)):
        labeled_samples[i]['value'] = sorted_parents[i]
        labeled_samples[i]['label']['props']['children'][1]['props']['children'] = sorted_parents[i]
        labeled_samples[i]['search'] = sorted_parents[i].split('-')[-1]
        labeled_samples[i]['label']['props']['children'][0]['props']['style']['color'] = color_map[sorted_parents[i]]
    sortorder_retvals = (no_update, no_update)
    if ctx.triggered_id == 'render-barplot-button' and n_clicks > 0:
        # Ensure the sort options match the current set of facets.
        sort_options = [x_column, *df_final['prop name'].unique().tolist()]
        sort_options = [{'label':' '+opt, 'value':opt} for opt in sort_options]
        sortorder_retvals = (sort_options, sorting_key)
    return fig, labeled_samples, *sortorder_retvals, no_update


@callback(Output('lineplot-slider-div', 'hidden'),
          Input('lineplot-replicates-radioitems', 'value'))
def hide_lineplot_slider_div(radioitem_value : int):
    """
    The user can show all replicates or condense them into mean ± SD.
    In the latter case, a slider provides additional control over the display.
    This slider should be displayed in the latter case and hidden otherwise.
    This callback manages this display.
    """
    if radioitem_value is None:
        return no_update
    if radioitem_value != 2:
        return True
    return False


@callback(Output('color-picker', 'is_open', allow_duplicate=True),
          Output('idx-of-parent-modal', 'data', allow_duplicate=True),
          Input('lineplot-graph-id', 'clickData'),
          prevent_initial_call='initial_duplicate')
def on_lineplot_trace_click(click_data):
    """
    The user can click on a trace in the line plot ('line plot') and change its color.
    The 'color picker' modal will appear to provide color options (and a Cancel button).
    A hidden Div will receive the color choice.
    """
    if not click_data:
        return no_update, no_update
    return True, utils.div_display['line plot']


@callback(Output('lineplot-graph-id', 'figure', allow_duplicate=True),
          Output('lineplot-graph-id', 'clickData', allow_duplicate=True),
          Output('lineplot-style-map', 'data', allow_duplicate=True),
          Input({'type':'color-displayed', 'index':utils.div_display['line plot']}, 'style'),
          State('lineplot-graph-id', 'clickData'),
          State('lineplot-graph-id', 'figure'),
          State('lineplot-style-map', 'data'),
          State('lineplot-replicates-radioitems', 'value'),
          State('lineplot-applyToFacets-checkbox', 'value'),
          State('lineplot-oneStylePerReplicate-checkbox', 'value'),
          State('lineplot-groupBy-dropdown', 'value'),
          prevent_initial_call='initial_duplicate')
def apply_trace_color_choice_to_lineplot(trace_style : dict, click_data : dict, fig : dict,
                                         style_map : dict, radioitem_value : int,
                                         apply_across_facets : bool, one_style_per_replicate : bool,
                                         group : str):
    """
    This is the final callback in a chain that applies a color choice to a trace in the line plot.

    Parameters
    ----------
    trace_style : dict
      The style ('color' and 'dash') to be assigned to the trace upon which the user clicked.
    click_data : dict
      The identifying data for the clicked trace.
    fig : dict
       The figure containing the clicked trace.
    style_map : dict
       A custom stored mapping from group (e.g. 'Cohort') and sample_string (e.g. 'sample'
       or 'Sample ID') to styles to be applied to traces. See update_line_plot() for its structure.
    radioitem_value : int
       Specifies whether replicates are collapsed (one trace per group)
       or shown (one trace per sample). Necessary for properly updating the trace(s).
    apply_across_facets : bool
       Whether the change made to the trace should be propagated to traces with the same
       group (or sample_string) in the other facets.
    one_style_per_replicate : bool
       Whether the trace change should be restricted to the chosen replicate,
       rather than propagated to the other replicates of its group.
    group : str
       Category by which replicates are grouped, e.g. 'Cohort' or 'Treatment'.

    Returns
    -------
    dict, None, dict
      The updated figure and style_map. "None" must be sent to returned to clickData to reset it;
      otherwise repeated clicks on the same trace will have no effect.
    """
    if not click_data or not trace_style or not fig:
        return no_update, no_update, no_update
    sample_string = 'Patient ID' # BUGBUG: Hardcoded for demo. Could be 'sample', 'Sample ID', ...
    one_trace_per_group = False
    if 2 == radioitem_value: # hacky... declare a list of values in utils?
        one_trace_per_group = True
    # https://community.plotly.com/t/referencing-updating-trace-by-curve-number/57450/2
    curve_number = click_data['points'][0]['curveNumber']
    # Extract the properties of the clicked trace (group, facet, sample_id) from its 'hovertemplate'.
    hov_str = fig['data'][curve_number]['hovertemplate'] # it's an HTML string! :)
    curve_data = {}
    for entry in hov_str.split('<br>'):
        key, value = entry.split('=')
        curve_data[key] = value
    val = curve_data[group] # e.g., group=='Treatment' and val=='Placebo'
    facet = curve_data['prop name']
    # FYI: color_and_dashing = fig['data'][curve_number]['line'] # dict: 'color' (e.g. '#D4A6C8') & 'dash' (e.g. 'solid')
    new_color = trace_style['color']
    sample_id = None
    if sample_string in curve_data:
        sample_id = curve_data[sample_string]
    update_all_replicates = True
    if one_style_per_replicate:
        update_all_replicates = False
        if one_trace_per_group:
            # Exception: Apply this color to all replicates in the map
            # if no replicate for this group has this color.
            new_color_found = False
            for sample in style_map[group][val]['Sample IDs']:
                for facet_name in style_map['Sample IDs'][sample]['facets'][group]:
                    sample_color = style_map['Sample IDs'][sample]['facets'][group][facet_name]['color']
                    # sample_dashing = style_map['Sample IDs'][sample]['facets'][group][facet_name]['dash'] # useful in future?
                    if sample_color == new_color:
                        new_color_found = True
                        break
                if new_color_found:
                    break
            if not new_color_found:
                update_all_replicates = True
    if not update_all_replicates:
        if not apply_across_facets:
            # Only update this single trace in the plot and this single entry in the map.
            fig['data'][curve_number]['line']['color'] = new_color
            if one_trace_per_group:
                style_map[group][val]['facets'][facet]['color'] = new_color
            else:
                style_map['Sample IDs'][sample_id]['facets'][group][facet]['color'] = new_color
        else:
            # Update one trace per facet and all facets for this entry in the map.
            for c in range(len(fig['data'])):
                hov_str = fig['data'][c]['hovertemplate']
                curve_data = {}
                for entry in hov_str.split('<br>'):
                    key, value = entry.split('=')
                    curve_data[key] = value
                this_val = curve_data[group]
                if this_val != val:
                    continue
                this_facet = curve_data['prop name']
                if one_trace_per_group:
                    fig['data'][c]['line']['color'] = new_color
                    style_map[group][val]['facets'][this_facet]['color'] = new_color
                else:
                    if curve_data[sample_string] == sample_id:
                        fig['data'][c]['line']['color'] = new_color
                        style_map['Sample IDs'][sample_id]['facets'][group][this_facet]['color'] = new_color
    else:
        # Update all replicates for this group.
        for c in range(len(fig['data'])):
            hov_str = fig['data'][c]['hovertemplate']
            curve_data = {}
            for entry in hov_str.split('<br>'):
                key, value = entry.split('=')
                curve_data[key] = value
            this_val = curve_data[group]
            if this_val != val:
                continue
            this_facet = curve_data['prop name']
            if this_facet != facet and not apply_across_facets:
                continue
            fig['data'][c]['line']['color'] = new_color
            style_map[group][val]['facets'][this_facet]['color'] = new_color
            if one_trace_per_group:
                # Update all replicates in the map (no replicate has this new color).
                for sample in style_map[group][val]['Sample IDs']:
                    style_map['Sample IDs'][sample]['facets'][group][this_facet]['color'] = new_color
                if not apply_across_facets:
                    # All necessary updates have been completed. (c == curve_number if we reach here.)
                    break
            else:
                # Update this replicate in the map.
                style_map['Sample IDs'][curve_data[sample_string]]['facets'][group][this_facet]['color'] = new_color
    return fig, None, style_map # "None" = "reset clickData;" otherwise repeated clicks on the trace will do nothing


@callback(Output('lineplot-div', 'hidden', allow_duplicate=True), # allow... may no longer be needed here
          Output('lineplot-graph-id', 'figure', allow_duplicate=True),
          Output('lineplot-style-map', 'data', allow_duplicate=True),
          Output('err-msg', 'children', allow_duplicate=True),
          Input('render-lineplot-button', 'n_clicks'),
          Input('lineplot-replicates-radioitems', 'value'),
          Input('lineplot-slider', 'value'),
          State('lineplot-df-melted-dict', 'data'),
          State('lineplot-style-map', 'data'),
          State('lineplot-facetVars-checklist', 'value'),
          State('lineplot-groupBy-dropdown', 'value'),
          prevent_initial_call='initial_duplicate')
def update_line_plot(n_clicks : int, radioitem_value : int, slider_value : float,
                     df_as_dict : list, style_map : dict,
                     props_to_plot : list, group : str):
    """
    Make or update the line plot. Builds the "lineplot style map" if it doesn't yet exist.

    Parameters
    ----------
    n_clicks : int
       The number of times the render-lineplot-button button has been clicked.
    radioitem_value : int
       The summary statistic (or none) chosen by the user. 1==show all replicates.
    slider_value : float
       The small increment by which points should be spread out horizontally,
       e.g. from four points at Day=2 to points at 1.97, 1.99, 2.01, 2.03.
    df_as_dict : list of dict
       The input DataFrame rendered as a list of records via to_dict().
    style_map : dict
       A map to keep track of color edits made via the user clicking on curves in the plot.
    props_to_plot : list of str
       The properties in the 'prop name' column of the DataFrame in df_as_dict
       to be included in the plot (one facet per property).
    group : str
       The property by which the samples should be grouped (colored, aggregated).
       A common value for this is 'Molecule':  "plot all replicates of molecule M-123
       in green;" "for each molecule, show only the mean ± SD over replicates."

    Returns
    -------
    bool, figure, dict, str, str
       "hidden", line plot, style map, "group by" property, error message,
       where "hidden" is the "hidden" attribute of the enclosing Div (i.e., False = "un-hide this Div")
    """
    num_outputs = len(ctx.outputs_list)
    no_updates = [no_update]*num_outputs
    if not n_clicks:
        # This callback needn't be triggered by a click on the render-lineplot-button,
        # but that button needs to have been clicked at least once before we can render the plot.
        return tuple(no_updates)
    if not df_as_dict:
        return tuple(no_updates)
    display_meanSD = False
    if 2 == radioitem_value: # hacky... declare a list of values in utils?
        display_meanSD = True
    one_trace_per_group = display_meanSD
    df_in = pd.DataFrame.from_dict(df_as_dict)
    if not props_to_plot:
        err_msg = "No properties were selected for the y-axes.\n"
        err_msg += "Select one or more properties and click the 'plot' button."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    if not group:
        err_msg = "Select a property by which to group the data,\n"
        err_msg += "then click the 'show plot' button.\n"
        err_msg += "The available options are in the dropdown menu next to this button."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    # At least for now, drop any row with a NaN 'prop value' for a target 'prop name'.
    df_facets = df_in[[True if prop in props_to_plot \
                       else False for prop in df_in['prop name']]]
    df_facets = df_facets[[not pd.isna(x) for x in df_facets['prop value']]].reset_index(drop=True)
    if len(df_facets)==0:
        err_msg = "All data is missing (NaN) for the selected properties.\n"
        err_msg += "Select different properties and click the 'plot' button."
        no_updates[-1] = err_msg
        return tuple(no_updates)
    sample_string = df_in.columns[0]
    day_string = 'Day'
    for col_name in df_in.columns:
        if col_name.lower() == 'day':
            day_string = col_name # use the column title's actual capitalization
            break

    fig = utils.make_custom_multifaceted_line_plot(df_facets, x_column=day_string,
                                                   line_group=sample_string, agg_group=group,
                                                   display_meanSD=display_meanSD, dt=slider_value)

    # Update (or build) the style map if necessary.
    if style_map is None:
        style_map = {}
    updated_style_map = False
    add_group_to_style_map = True
    samples_string = 'Sample IDs' # not to be confused with sample_string, which could be 'sample', 'Patient ID', etc.
    # First, make the facets in the style map match the user's current choices for the facets.
    # Then, if the current grouping isn't in the map, add it.
    if samples_string in style_map: # otherwise it's empty
        facets_in_style_map = set()
        for sample in style_map[samples_string]:
            for group_ in style_map[samples_string][sample]['facets']: # 'group_' so we don't overwrite 'group'
                for facet in style_map[samples_string][sample]['facets'][group_]:
                    facets_in_style_map.add(facet)
        for facet in props_to_plot:
            if facet not in facets_in_style_map:
                utils.add_facet_to_style_map(style_map, facet, samples_string)
                updated_style_map = True
        for facet in facets_in_style_map:
            if facet not in props_to_plot:
                utils.remove_facet_from_style_map(style_map, facet, samples_string)
                updated_style_map = True
        if group in style_map:
            add_group_to_style_map = False
    if add_group_to_style_map:
        style_map = utils.add_group_to_style_map(group, style_map, fig, df_facets,
                                                 sample_string, one_trace_per_group, samples_string)
        updated_style_map = True

    # Now use the style map.
    for curve_number in range(len(fig['data'])):
        hov_str = fig['data'][curve_number]['hovertemplate']
        curve_data = {}
        for entry in hov_str.split('<br>'):
            key, value = entry.split('=')
            curve_data[key] = value
        group_value = curve_data[group] # e.g., group='Treatment', group_value='Placebo'
        facet = curve_data['prop name']
        if one_trace_per_group:
            fig['data'][curve_number]['line'] = style_map[group][group_value]['facets'][facet]
        else:
            sample_id = curve_data[sample_string] # sample_string is 'sample', 'Sample ID', etc.
            fig['data'][curve_number]['line'] = style_map[samples_string][sample_id]['facets'][group][facet]
    # "False" below means "un-hide the Div enclosing this plot and its controls."
    if updated_style_map:
        return False, fig, style_map, no_update
    return False, fig, no_update, no_update
#
#---------------End 'interactive plotting options' callbacks-----------------------
