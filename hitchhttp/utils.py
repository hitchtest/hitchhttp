from urllib import parse


def parse_qsl_as_dict(querystring):
    qs = {}
    for key, value in parse.parse_qsl(querystring):
        if key in qs:
            qs[key].add(value)
        else:
            qs[key] = {value}
    return qs
