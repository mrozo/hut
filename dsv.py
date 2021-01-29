from typing import List, Iterable


def dsv_escape(string):
    return str(string).replace('\\','\\\\').replace('\n', '\\n').replace(';','\;')


def dsv_record_dump(elements):
    return ";".join(map(dsv_escape, elements))


def dsv_value_load(line):
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
        elif c==';':
            break
        else:
            value+=c
    return value, offset


def dsv_record_load(line):
    offset=0
    parsed = []
    while offset <len(line):
        value, parsed_chars = dsv_value_load(line[offset:])
        offset += parsed_chars
        parsed.append(value)
    return parsed


def dsv_reader(data_source: Iterable[str]) -> Iterable[List[str]]:
    return map(dsv_record_load, data_source)


if __name__ == "__main__":
    test_data=['1', '1.1', 2, '3.3', ';', 'żółw', '\n\n\t;dupa']
    dumped_data=dsv_record_dump(test_data)
    loaded_data=dsv_record_load(dumped_data)
    if not all(map(lambda a,b: str(a)==str(b), test_data, loaded_data)) or len(test_data) != len(loaded_data):
        print(f"test_data:'{test_data} != loaded_data:'{loaded_data}")
        exit(1)

