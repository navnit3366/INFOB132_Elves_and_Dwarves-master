#  -*- coding: ascii -*-


def ia_action(data_map, data_ia, player):
    """The artificial intelligence of the game. Generate an instruction and return it.

    Parameters:
    -----------
    data_map: the whole database of the game (dict).
    data_ia: the ia identifier ('player1' or 'player2', string).
    player: the player identifier ('player1' or 'player2', string).

    Return:
    -------
    command: the instruction of the ia (string).

    Version:
    --------
    specification: Laurent Emilie and Bienvenu Joffrey v. 1 (02/03/16)
    implementation: Bienvenu Joffrey and Jonathan Maroit & Laurent Emilie v.4 (01/05/16)
    """
    raw_commands = ia_reflexion(data_ia, data_map, player)

    # Rewrite the command into a single string.
    string_commands = ''
    for key in raw_commands:
        string_commands += ('0' + str(raw_commands[key][0][0]))[-2:] + '_' + ('0' + str(raw_commands[key][0][1]))[-2:] + raw_commands[key][1] + ('0' + str(raw_commands[key][2][0]))[-2:] + '_' + ('0' + str(raw_commands[key][2][1]))[-2:] + '   '
    return string_commands
