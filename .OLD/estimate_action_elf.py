# -*- coding: ascii -*-


def estimate_action_elf(data_ia, are_enemy, where_enemies):
    """Estimate which action may the elves doing and compute amount of points to allow the action.

    Parameters:
    -----------
    data_ia: the whole database (dict)
    are_enemy: tells whether there are enemy in the surroundings (bool)
    where_enemies: position of the enemy's units (list)

    Returns:
    --------
    action_type: actions with amount of points for each one (dict)

    Versions:
    ---------
    specification: Laurent Emilie v1 (19/04/16)
    implementation:
    """
    formation_scheme = pickle.load(open("formation_scheme.pkl", "rb"))

