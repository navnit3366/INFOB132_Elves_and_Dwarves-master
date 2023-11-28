# -*- coding: ascii -*-


def start_game(remote=1, player1='player 1', player2='player_2', map_size=7, file_name=None, sound=False, clear=False):
    """Start the entire game.
    Parameters:
    -----------
    player1: Name of the first player or IA (optional, str).
    player2: Name of the second player or IA (optional, str).
    map_size: Size of the map that players wanted to play with (optional, int).
    file_name: File of the name to load if necessary (optional, str).
    sound: Activate the sound or not (optional, bool).
    clear: Activate the "clear_output" of the notebook. Game looks more realistic, but do not work properly on each computer (optional, bool).
    Notes:
    ------
    It is the main function that gonna call the other functions.
    map_size must be contained between 7 and 30
    file_name load a game only if the game was saved earlier
    Version:
    -------
    specification: Laurent Emilie & Maroit Jonathan v.1 (10/03/16)
    implementation: Maroit Jonathan & Bienvenu Joffrey v.1(21/03/16)
    """
    # Creation of the database or load it.
    if file_name:
        data_map = load_map()
    else:
        data_map = create_data_map(remote, map_size, player1, player2, clear)
        data_ia = create_data_ia(map_size, remote)

    # If we play versus another ia, connect to her.
    if remote:
        connection = connect_to_player(player_id)
    else:
        connection = None

    # Diplay introduction event and the map.
    event_display(data_map, 'intro')
    play_event(sound, player, player_name, 'intro')

    # Run de game turn by turn
    continue_game = True
    while continue_game:
        display_map(data_map, clear)
        data_map = choose_action(data_map, connection, data_ia)
        save_data_map(data_map)
        continue_game, loser, winner = is_not_game_ended(data_map)

    # Once the game is finished, disconnect from the other player.
    if remote:
        disconnect_from_player(connection)

    # Display the game-over event (versus IA).
    if player1 == 'IA' or player2 == 'IA':
        player = loser
        event_display(data_map, 'game_over', player)
    # Display the win event (versus real player).
    else:
        player = winner
        event_display(data_map, 'win', player)
