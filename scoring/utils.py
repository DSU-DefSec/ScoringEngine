import importlib

def load_module(module_str):
    """
    Get the module specified by the given string.
    
    Arguments:
        module_str (str): String representing the module's import path

    Returns:
        Module: The module represented by the string
    """
    parts = module_str.split('.')
    par_module_str = '.'.join(parts[:len(parts)-1])
    module = importlib.import_module(par_module_str)
    module_obj = getattr(module, parts[-1])
    return module_obj

