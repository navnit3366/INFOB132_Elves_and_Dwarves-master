# -*- coding: utf-8 -*-
import time
from IPython.display import clear_output
from colorama import Fore, Back, Style


def event_display(data_map, event, player=0):
    """Print a line of the screen which representst the actualy situation with the name of the concerned player.

    Parameters:
    -----------
    data_map: the whole database (dict)
    event : the event who represent the situation ; introduction , game over or winner screen (str)
    player: which player has an event to display (int, optional)

    Version:
    -------
    specification: Maroit Jonathan and Laurent Emilie (v.2 03/04/16)
    implementation: Maroit Jonathan (v.1 16/02/16)
    """

    if event == 'intro':

        l0 = '                                                                                                                                '
        l1 = '    ██████  ████                                     ███            ████                                                        '
        l2 = '    ██        ██                                    ██ ██           ██ ██                                                       '
        l3 = '    ██        ██    ██  ██   ████    █████          ██ ██           ██  ██  ██   ██  ████   ██  ██  ██  ██   ████    █████      '
        l4 = '    ██        ██    ██  ██  ██  ██  ██               ███            ██  ██  ██ █ ██     ██  ██ ███  ██  ██  ██  ██  ██          '
        l5 = '    █████     ██    ██  ██  ██  ██  ██              ██              ██  ██  ██ █ ██     ██  ███     ██  ██  ██  ██  ██          '
        l6 = '    ██        ██    ██  ██  ██████   ████           ██ ████         ██  ██  ██ █ ██  █████  ██      ██  ██  ██████   ████       '
        l7 = '    ██        ██    ██  ██  ██          ██          ██  ██          ██  ██  ██ █ ██ ██  ██  ██      ██  ██  ██          ██      '
        l8 = '    ██        ██     ████   ██          ██          ██  ██          ██ ██    ██ ██  ██  ██  ██       ████   ██          ██      '
        l9 = '    ██████  ██████    ██     ████   █████            ███ ██         ████     ██ ██   █████  ██        ██     ████   █████       '
        l10 = '                                                                                                                                '
        l11 = '                        GROUPE 42 : EMILIE LAURENT, JOFFREY BIENVENU, JONATHAN MAROIT ET SYLVAIN PIRLOT                         '

        line_list = [l0, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11]
        final_list = []

        for line in line_list:
            if line == l11:
                print (Fore.BLACK + Back.YELLOW + line)
            elif line == l0 or line == l10:
                print (Fore.BLACK + Back.BLACK + line)
            else:
                print (Fore.YELLOW + Back.BLACK + line)

            time.sleep(0.5)
        time.sleep(4)
        clear_output()

    else:
        player_name = data_map[player + 'info'][1]

        if len(player_name) < 9:
            player_name += (9 - len(player_name)) * ' '
        player_name = player_name[0:9]
        color_player = Back.RED
        if player == 'player1':
            color_player = Back.BLUE


        if event == 'game_over':
            d0 = (Fore.BLACK + Back.WHITE) + '                             ' + (
            'The loser is: ' + player_name) + '                        '
            d1 = '████████████        ████████████████████████████████████        ████████████'
            d2 = '████████████        ████████████████████████████████████        ████████████'
            d3 = '████████████████████    ████                    ████    ████████████████████'
            d4 = '████████████████████    ████                    ████    ████████████████████'
            d5 = '████████████████████████                            ████████████████████████'
            d6 = '████████████████████████    ████████    ████████    ████████████████████████'
            d7 = '████████████████████████    ████████    ████████    ████████████████████████'
            d8 = '████████████████████████    ████████    ████████    ████████████████████████'
            d9 = '████████████████████████    ████            ████    ████████████████████████'
            d10 = '████████████████████████    ████            ████    ████████████████████████'
            d11 = '████████████████████████            ████            ████████████████████████'
            d12 = '████████████████████████            ████            ████████████████████████'
            d13 = '████████████████████    ████                    ████    ████████████████████'
            d14 = '████████████████████    ████                    ████    ████████████████████'
            d15 = '████████████        ████████    ████    ████    ████████        ████████████'
            d16 = '████████████        ████████    ████    ████    ████████        ████████████'
            d17 = (Fore.BLACK + Back.WHITE) + '                                                                            '
            death_list = [d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17]

            for line in death_list:
                print (Fore.BLACK + color_player + line)
                time.sleep(0.5)

        else:
            w0 = Back.BLACK + Fore.WHITE + '                          THE                           '
            wa = '                                                        '
            w1 = '     ██   ██  ████   ██   ██ ██   ██ ██████  █████      '
            w2 = '     ██   ██   ██    ██   ██ ██   ██ ██      ██  ██     '
            w3 = '     ██   ██   ██    ███  ██ ███  ██ ██      ██  ██     '
            w4 = '     ██ █ ██   ██    ████ ██ ████ ██ ██      ██  ██     '
            w5 = '     ██ █ ██   ██    ██ ████ ██ ████ █████   █████      '
            w6 = '     ██ █ ██   ██    ██  ███ ██  ███ ██      ██ ██      '
            w7 = '      ██ ██    ██    ██   ██ ██   ██ ██      ██  ██     '
            w8 = '      ██ ██    ██    ██   ██ ██   ██ ██      ██  ██     '
            w9 = '      ██ ██   ████   ██   ██ ██   ██ ██████  ██  ██     '
            wb = '                                                        '
            w10 = Back.BLACK + Fore.WHITE + '                          IS                            '
            w11 = (Fore.WHITE + Back.BLACK) + '                        ' + player_name + '                       '
            win_list = [w0, wa, w1, w2, w3, w4, w5, w6, w7, w8, w9, wb, w10, w11]

            for win_line in win_list:
                print (Fore.BLACK + color_player + win_line)
                time.sleep(0.5)