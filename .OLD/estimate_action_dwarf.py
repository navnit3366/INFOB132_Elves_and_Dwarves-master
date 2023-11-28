# -*- coding: ascii -*-


def estimate_action_dwarf(data_ia, build_formation, are_enemy, where_enemies):
    """Estimate which action may the dwarves doing and compute amount of points to allow the action.

    Parameters:
    -----------
    data_ia: the whole database (dict)
    build_formation: tells whether the situation requires to build the formation (bool)
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
