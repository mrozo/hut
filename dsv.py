from typing import List, Iterable


def dsv_escape(string, delimiter=';'):
    return str(string).replace('\\', '\\\\').replace('\n', '\\n').replace(delimiter, f'\{delimiter}')


def dsv_record_dump(elements, delimiter=';'):
    return delimiter.join(map(dsv_escape, elements))


def dsv_value_load(line, delimiter=';'):
    escape_sequences = {
        'a':'\a',
        'b':'\b',
        'f':'\f',
        'n':'\n',
        'r':'\r',
        't':'\t',
        'v':'\v'
    }
    escape=False
    offset=0
    value=''
    while offset < len(line):
        c = line[offset]
        offset+=1
        if escape:
            value += escape_sequences.get(c, c)
            escape = False
        elif c=='\\':
            escape=True
        elif c==delimiter:
            break
        else:
            value+=c
    return value, offset


def dsv_record_load(line, delimiter=';'):
    line=line.strip()
    offset = 0
    parsed = []
    while offset < len(line):
        value, parsed_chars = dsv_value_load(line[offset:], delimiter)
        offset += parsed_chars
        parsed.append(value)
    return parsed


def dsv_reader(data_source: Iterable[str], delimiter=';') -> Iterable[List[str]]:
    return map(lambda l: dsv_record_load(l, delimiter), data_source)


def interleave_list_with_element(the_list: Iterable, element):
    for list_element in the_list:
        yield list_element
        yield element


def dsv_generator(data_source: Iterable, method='as_dsv'):
    return interleave_list_with_element(map(lambda r: getattr(r, method)(), data_source), "\n")


if __name__ == "__main__":
    test_data = ['1', '1.1', 2, '3.3', ';', 'żółw', '\n\n\t;dupa']
    dumped_data=dsv_record_dump(test_data)
    loaded_data=dsv_record_load(dumped_data)
    if not all(map(lambda a,b: str(a) == str(b), test_data, loaded_data)) or len(test_data) != len(loaded_data):
        print(f"test_data:'{test_data} != loaded_data:'{loaded_data}")
        exit(1)

