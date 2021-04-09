#!/bin/env python3
from data_structures import Hacker, Event
from dsv import dsv_reader, dsv_generator
from collections import namedtuple
from typing import Callable, Iterable, Set

def hacker_init(hid: str, nick: str, entry_date: str, email: str, name: str, last_name: str, groups: [set, str]):
    groups = groups or set()
    if isinstance(groups, str):
        groups = set(groups.split(','))
    return Hacker(hid, nick, entry_date, email, name, last_name, groups)


def hacker_pattern(hid: str = None, nick: str = None, entry_date: str = None, email: str = None, name: str = None,
                   last_name: str = None, groups: [set, str] = None):
    return hacker_init(hid, nick, entry_date, email, name, last_name, groups)


def hacker_reader(data_source: Iterable[str], filter_method: [None, Callable[[Hacker], bool]] = None):
    return filter(filter_method, map(lambda d: hacker_init(*d), dsv_reader(data_source)))


def hacker_record_collide(hacker: Hacker, new_hacker: Hacker) -> bool:
    return hacker.hid == new_hacker.hid or hacker.email == new_hacker.email or hacker.nick == new_hacker.nick


class HackerAlreadyExistsException(Exception):
    pass


class HackerNotFoundException(Exception):
    pass


def hacker_add(current_hackers: Iterable[Hacker], new_hacker: Hacker) -> Iterable[Hacker]:
    for h in current_hackers:
        if hacker_record_collide(h, new_hacker):
            raise HackerAlreadyExistsException()
        yield h
    yield new_hacker


def hacker_match(hacker: Hacker, hid: str = None, email: str = None, nick: str = None) -> True:
    return (hid is not None and hid == hacker.hid) \
            | (email is not None and hid == hacker.email) \
            | (nick is not None and nick == hacker.nick)


def hacker_doesnt_match(hacker: Hacker, hid: str = None, email: str = None, nick: str = None) -> True:
    return not hacker_match(hacker, hid, email, nick)


def hacker_remove(current_hackers: Iterable[Hacker], hid: str = None, email: str = None,
                  nick: str = None) -> Iterable[Hacker]:
    hackers_removed = 0
    for h in current_hackers:
        if hacker_match(h, hid, email, nick):
            hackers_removed += 1
            continue
        yield h
    if hackers_removed == 0:
        raise HackerNotFoundException()
    # a co jesli w pliku jest dwoch hackerow o tym samym id/email/nick? na razie olejmy sprawe


def hacker_pass(hackers: Iterable[Hacker], *args, **kwargs) -> Iterable[Hacker]:
    return hackers


def patter_matches(val: str, pattern: str):
    if pattern is None:
        return True
    if val is None:
        return False

    offset = 0
    was_wildcard = False
    for pattern_part in pattern.split('*'):
        if pattern_part == '':
            was_wildcard = True
            continue
        new_offset = val.find(pattern_part, offset)
        if not was_wildcard and new_offset != offset:
            return False
        offset = new_offset + len(pattern_part)
        was_wildcard = True

    if pattern[-1] != '*' and offset != len(val):
        return False
    return True


def hacker_match_groups(hacker_groups: Set[str], pattern_groups: Set[str]) -> str:
    if not pattern_groups:
        return True
    if not hacker_groups and pattern_groups:
        return False
    return bool(pattern_groups - hacker_groups)


def hacker_matches(hacker: Hacker, pattern: Hacker):
    for field in Hacker.fields ^ {'groups'}:
        pattern_field_val = getattr(pattern, field, None)
        hacker_field_val = getattr(hacker, field, None)
        if pattern_field_val and not patter_matches(hacker_field_val, pattern_field_val):
            return False

    if pattern.groups:
        if hacker.groups:
            if pattern.groups - hacker.groups:
                return False
        else:
            if pattern.groups != '*':
                return False
    return True


def hacker_assign_to_groups(current_hackers: Iterable[Hacker], groups: [str, set], hid: str = None,
                            email: str = None, nick: str = None):
    hackers_edited = 0
    for h in current_hackers:
        if hacker_match(h, hid, email, nick):
            hackers_edited += 1
            updated_hacker_data = {f: getattr(h, f) for f in Hacker.fields}
            updated_hacker_data['groups'] = h.groups | groups
            yield Hacker(*updated_hacker_data.values())
        else:
            yield h
    if hackers_edited == 0:
        raise HackerNotFoundException()


def hacker_remove_group(current_hackers: Iterable[Hacker], groups: Set[str], pattern: Hacker):
    hacker_found = False
    for h in current_hackers:
        if hacker_matches(h, pattern):
            hacker_found = True
            hacker_data = h._asdict()
            hacker_data['groups'] = hacker_data['groups'] - groups
            h = hacker_init(**hacker_data)
        yield h
    if not hacker_found:
        raise HackerNotFoundException


CallRequest = namedtuple('CallRequest', ['function', 'args', 'kwargs'])


def mkCallRequest(function: Callable, *args, **kwargs) -> CallRequest:
    return CallRequest(function, args, kwargs)


def hacker_cli_args2filter_call(args_namespace):
    args = vars(args_namespace)
    pattern_kwargs = {
        k: args[k] for k in Hacker.fields if args.get(k, None)
    }
    return mkCallRequest(hacker_pattern, **pattern_kwargs)


import argparse
hacker_cli_argparse = argparse.ArgumentParser()
hacker_cli_argparse.add_argument("-if", action="store", dest="input_file", default="-", required=False)
hacker_cli_argparse.add_argument("-of", action="store", dest="output_file", default="-", required=False)

subparsers = hacker_cli_argparse.add_subparsers(help='subcommands')

show_cmd_parser = subparsers.add_parser('show')
show_cmd_parser.add_argument("-if", action="store", dest="input_file", default="-", required=False)
show_cmd_parser.add_argument("-of", action="store", dest="output_file", default="-", required=False)
show_cmd_parser.add_argument("-f",  action="store", dest="format", default="dsv", required=False)

show_cmd_parser.add_argument("-e", action='store', dest='email', default=None, required=False)
show_cmd_parser.add_argument("-i", action='store', dest='hid', default=None, required=False)
show_cmd_parser.add_argument("-n", action='store', dest='name', default=None, required=False)
show_cmd_parser.add_argument("-nn", action='store', dest='nick', default=None, required=False)
show_cmd_parser.add_argument("-ln", action='store', dest='last_name', default=None, required=False)
show_cmd_parser.add_argument("-g", action='store', dest='groups', default=None, required=False)
show_cmd_parser.set_defaults(func=hacker_cli_args2filter_call)

remove_cmd_parser = subparsers.add_parser('rm')
remove_cmd_parser.add_argument("-if", action="store", dest="input_file", default="-", required=False)
remove_cmd_parser.add_argument("-of", action="store", dest="output_file", default="-", required=False)
remove_cmd_parser.add_argument("-f",  action="store", dest="format", default="dsv", required=False)

remove_cmd_parser.add_argument("-i", action='store', dest='hid', default=None)
remove_cmd_parser.set_defaults(func=hacker_cli_args2filter_call)
remove_cmd_parser.set_defaults(reader=lambda id: hacker_remove())


def hacker_cli_args2call(vargs: list) -> CallRequest:
    return mkCallRequest(hacker_reader)


def bad_method(*args, **kwargs):
    raise Exception("error")


def hacker2event(hacker: Hacker) -> Event:
    return Event(date=hacker.entry_date, type="newMember", args_str=hacker.email)


def event_generator(hackers: Iterable[Hacker]):
    hackers = sorted(hackers, key=lambda h: h.entry_date)
    return dsv_generator(map(hacker2event, hackers))


if __name__ == "__main__":
    import sys
    args = hacker_cli_argparse.parse_args()
    input_file = sys.stdin if args.input_file == '-' else open(args.input_file)
    output_file = sys.stdout if args.output_file == '-' else open(args.output_file)
    formatter = dsv_generator if args.format == 'dsv' else event_generator
    func = getattr(args, 'func', None)
    if not func:
        sys.stderr.write("missing/wrong function\n")
        hacker_cli_argparse.print_help()
        exit(1)
    pattern = func(args)
    pattern = pattern.function(*pattern.args, **pattern.kwargs)

    output_file.writelines(formatter(hacker_reader(input_file, lambda hacker: hacker_matches(hacker, pattern))))
