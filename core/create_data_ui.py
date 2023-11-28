# -*- coding: utf-8 -*-
from colorama import Fore, Back, Style


def create_data_ui(data_map, clear):
    """Generate the whole user's interface with the statistics.

    Parameters:
    -----------
    data_map: the whole database (dict)
    clear: Activate the "clear_output" of the notebook. Game looks more realistic (bool)

    Returns:
    --------
    data_ui: the user's interface to print (list)

    Versions:
    ---------
    specification: Laurent Emilie v.1 (15/03/16)
    implementation: Bienvenu Joffrey v.3.1 (24/03/16)
    """
    data_ui = [[]] * (16 + data_map['map_size'])

    # Initialisation of the displaying constants.
    grid_size = 5 * data_map['map_size']
    ui_color = '%(ui_color)s'

    margin = 5
    line_coloured = ui_color + ('█' * (117 + margin)) + Style.RESET_ALL
    if clear:
        margin = 9
        line_coloured = ui_color + ('█' * (121 + margin)) + Style.RESET_ALL


    border_black = Back.BLACK + '  ' + Style.RESET_ALL
    margin_left = ((20 - data_map['map_size']) * 5) / 2
    margin_right = ((20 - data_map['map_size']) * 5) - (((20 - data_map['map_size']) * 5) / 2)
    border_coloured_margin_left = ui_color + ('█' * (margin + margin_left)) + Style.RESET_ALL
    border_coloured_margin_right = ui_color + ('█' * (margin + margin_right)) + Style.RESET_ALL
    border_coloured_left = ui_color + ('█' * margin) + Style.RESET_ALL
    border_coloured_right = ui_color + ('█' * margin) + Style.RESET_ALL
    border_coloured_middle = ui_color + ('█' * 8) + Style.RESET_ALL

    border_white = ' ' * 2

    # Generate and save the top of the UI.
    for i in range(3):
        data_ui[i] = line_coloured

    # Generate and save the top of the grid.
    turn_message = 'Turn %(turn)s - %(playername)s, it\'s up to you ! %(blank)s'
    data_ui[3] = border_coloured_margin_left + Fore.WHITE + Back.BLACK + '  ' + turn_message + '  ' + Style.RESET_ALL + border_coloured_margin_right
    data_ui[4] = border_coloured_margin_left + border_black + ' ' * (grid_size + 8) + border_black + border_coloured_margin_right

    # Generate and save the architecture of the grid.
    for i in range(1, data_map['map_size'] + 1):
        data_ui[i + 4] = border_coloured_margin_left + border_black + Fore.BLACK + ' ' + ('0' + str(i))[-2:] + ' ' + Style.RESET_ALL
        for j in range(1, data_map['map_size'] + 1):
            data_ui[i + 4] += '%((' + str(i) + ',' + str(j) + '))5s' + Style.RESET_ALL
        data_ui[i + 4] += '    ' + border_black + border_coloured_margin_right

    # Generate and save the foot of the grid.
    data_ui[data_map['map_size'] + 5] = border_coloured_margin_left + border_black + Fore.BLACK + '   '
    for i in range(1, data_map['map_size'] + 1):
        data_ui[data_map['map_size'] + 5] += '  ' + ('0' + str(i))[-2:] + ' '
    data_ui[data_map['map_size'] + 5] += '     ' + border_black + border_coloured_margin_right

    data_ui[data_map['map_size'] + 6] = border_coloured_margin_left + Back.BLACK + (grid_size + 12) * ' ' + Style.RESET_ALL + border_coloured_margin_right

    # Generate and save the top of the statistics.
    data_ui[data_map['map_size'] + 7] = line_coloured

    data_ui[data_map['map_size'] + 8] = border_coloured_left + Fore.WHITE + Back.BLACK + '  Your units:' + (' ' * 39) + Style.RESET_ALL + border_coloured_middle
    data_ui[data_map['map_size'] + 8] += Fore.WHITE + Back.BLACK + '  Opponent\'s units:' + (' ' * 33) + Style.RESET_ALL + border_coloured_right

    # Generate and save the content of the statistics.
    for i in range(4):
        data_ui[data_map['map_size'] + 9 + i] = border_coloured_left + border_black + ' ' + border_white + Fore.BLACK + '%(stat' + str(i+1) + '1)s' + border_white + '%(stat' + str(i+1) + '2)s' + border_white + ' ' + border_black + border_coloured_middle
        data_ui[data_map['map_size'] + 9 + i] += border_black + ' ' + border_white + '%(stat' + str(i+1) + '3)s' + border_white + '%(stat' + str(i+1) + '4)s' + border_white + ' ' + border_black + border_coloured_right

    # Generate and save the foot of the statistics.
    data_ui[data_map['map_size'] + 13] = border_coloured_left + Back.BLACK + (' ' * 52) + Style.RESET_ALL + border_coloured_middle
    data_ui[data_map['map_size'] + 13] += Back.BLACK + (' ' * 52) + Style.RESET_ALL + border_coloured_right

    for i in range(2):
        data_ui[data_map['map_size'] + 14 + i] = line_coloured

    return data_ui
