from urllib import parse


def parse_qsl_as_dict(querystring):
    qs = {}
    for key, value in parse.parse_qsl(querystring, keep_blank_values=True):
        if key in qs:
            qs[key].add(value)
        else:
            qs[key] = {value}
    return qs


def xml_elements_equal(e1, e2):
    if e1.tag != e2.tag:
        return False
    if e1.text != e2.text:
        return False
    if e1.tail != e2.tail:
        return False
    if e1.attrib != e2.attrib:
        return False
    if len(e1) != len(e2):
        return False
    return all(xml_elements_equal(c1, c2) for c1, c2 in zip(e1, e2))
