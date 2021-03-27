def pformat(text):
    text = text.lower()
    text = text.replace(" ", "_")
    for s in "%()":
        text = text.replace(s, "")
    return text


def realtime(time):
    """
    Converts times in the format XXX.xxx into h m s ms
    """
    ms = int(time * 1000)
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    ms = "{:03d}".format(ms)
    s = "{:02d}".format(s)
    if h > 0:
        m = "{:02d}".format(m)
    return (
        ((h > 0) * (str(h) + "h "))
        + str(m)
        + "m "
        + str(s)
        + "s "
        + ((str(ms) + "ms") * (ms != "000"))
    )


def joinWithAnd(array: list):
    """Turns ["a", "b", "c", "d"] into `a, b, c, and d`"""
    return ", ".join([str(i) for i in array[:-1]]) + ", and {}".format(str(array[-1]))
