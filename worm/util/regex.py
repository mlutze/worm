def capture(regex: str) -> str:
    return "(" + regex + ")"


def either(regex1: str, regex2: str) -> str:
    return "(?:" + regex1 + "|" + regex2 + ")"


def separated(regex: str, sep: str) -> str:
    return "(?:" + regex + "(?:" + sep + regex + ")*)"
