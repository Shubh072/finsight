def success_response(message="", data=None):
    if data is None:
        data = {}
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(message="", errors=None):
    if errors is None:
        errors = {}
    return {
        "success": False,
        "message": message,
        "errors": errors,
    }

