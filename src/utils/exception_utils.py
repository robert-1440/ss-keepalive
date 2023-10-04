from io import StringIO
from traceback import print_exc


def get_exception_message(ex):
    if hasattr(ex, "message"):
        return ex.message
    else:
        return f"{ex}"


def dump_ex() -> str:
    """
    Used to dump the current exception.

    :return: the stack trace string
    """
    io = StringIO()
    print_exc(None, io)
    return io.getvalue()
