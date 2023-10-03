def get_exception_message(ex):
    if hasattr(ex, "message"):
        return ex.message
    else:
        return f"{ex}"

