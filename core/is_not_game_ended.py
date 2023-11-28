# -*- coding: ascii -*-


def is_not_game_ended(data_map):
    """Check if the game is allow to continue.

    Parameter:
    ----------
    data_map: the whole database (dict)

    Returns:
    --------
    continue_game : boolean value who said if the game need to continue(bool).
    loser : the player who lose the game(str).
    winner : the player who won the game(str).

    Notes:
    ------
    The game stop when a player run out of unit or if 20 turn have been played without any attack.
    In this case, the player 1 win.

    Version:
    -------
    specification: Maroit Jonathan(v.1 21/03/16)
    implementation: Maroit Jonathan & Bienvenu Joffrey (v.1.1 22/03/16)
    """

    continue_game = True
    loser = None
    winner = None

    # If a player has not any units, the other player win.
    for i in range(2):
        if not len(data_map['player' + str(i + 1)]) and continue_game:
            loser = 'player' + str(i + 1)
            winner = 'player' + str(3 - (i + 1))
            continue_game = False

    # If there's 20 turn without any attack, player1 loose and player2 win.
    if float(data_map['attack_turn']) / 2 > 19:
        loser = 'player1'
        winner = 'player2'
        continue_game = False

    return continue_game, loser, winner
