import inspect


def call_context():
    """
    Returns the context of the caller.
    """
    return dict(inspect.getmembers(inspect.stack()[2][0]))["f_globals"]
