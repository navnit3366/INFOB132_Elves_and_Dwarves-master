import pickle

def save_data_map(data_map):
    """Load a saved game.

    Parameters:
    -----------
    data_map_saved: name of the file to load (str)

    Version:
    --------
    specification: Laurent Emilie v.1 (11/02/16)
    implementation: Pirlot Sylvain v.1 & Bienvenu Joffrey (21/03/16)
    """
    pickle.dump(data_map, open("save.p", "wb"))



def load_data_map():
    """Save the game.

    Parameters:
    -----------
    data_map: the whole database of the game (dict)

    Version:
    --------
    specification: Laurent Emilie v.1 (11/02/16)
    implementation: Pirlot Sylvain v.1 & Bienvenu Joffrey (21/03/16)
    """

    return pickle.load(open("save.p", "rb"))
