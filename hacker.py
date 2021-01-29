from sys import stderr
import sys
from dsv import dsv_reader
from collections import namedtuple
from typing import Callable, Iterable, Set
import secrets
import argparse


Hacker = namedtuple('Hacker', ['hid', 'nick', 'entry_date', 'email', 'name', 'last_name', 'groups'])


def hacker_init(hid: str, nick: str, entry_date: str, email: str, name: str, last_name: str, groups: [set, str]):
    groups = groups or set()
    if isinstance(groups, str):
        groups = set(groups.split(','))
    return Hacker(hid, nick, entry_date, email, name, last_name, groups)


def hacker_pattern(hid: str = None, nick: str = None, entry_date: str = None, email: str = None, name: str = None,
                   last_name: str = None, groups: [set, str] = None):
    return hacker_init(hid, nick, entry_date, email, name, last_name, groups)


test_id1 = r"ffee998211"

test_data = [
    [test_id1,     r"ziom1",  r"2016-08-01", r"ziom@example.com", r"kowalski", r"jan", r"zarzad,benis"],
    [r"cccdddaaa11112", r"benis1", r"2020-12-01", r"benis1@example.com", r"john",  r"doe", r"benis",]
]

test_hacker = hacker_init(secrets.token_hex(32), "ziom3", "2021-01-31", "benis3@example.com", "karol", "nowacki", '')

test_file_lines = [
    r"""ffee998211;ziom1;2016-08-01;ziom@example.com;kowalski;jan;zarzad,benis""",
    r"""cccdddaaa11112;benis1;2020-12-01;benis1@example.com;john;doe;benis"""
]


def hacker_reader(data_source: Iterable[str], filter_method: [None, Callable[[Hacker], bool]] = None):
    for hacker in filter(filter_method, map(lambda d: hacker_init(*d), dsv_reader(data_source))):
        yield hacker


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
    for field in set(Hacker._fields) ^ {'groups'}:
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


def hacker_assign_to_groups(current_hackers: Iterable[Hacker], groups: [str, set],  hid: str = None,
                            email: str = None, nick: str = None):
    hackers_edited = 0
    for h in current_hackers:
        if hacker_match(h, hid, email, nick):
            hackers_edited += 1
            updated_hacker_data = h._asdict()
            updated_hacker_data['groups'] = h.groups | groups
            yield hacker_init(*updated_hacker_data.values())
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


def test_hacker_add():
    edited_hackers = hacker_add(hacker_reader(test_file_lines), test_hacker)
    hacker_found = filter(lambda h: h.hid == test_hacker.hid, edited_hackers)
    assert(len(list(hacker_found)) == 1)


def test_hacker_remove_nonexistent():
    edited_hackers = hacker_remove(hacker_reader(test_file_lines), hid="dupa")
    try:
        len(list(edited_hackers))
    except HackerNotFoundException:
        pass


def test_hacker_remove():
    edited_hackers = hacker_remove(hacker_reader(test_file_lines), hid=test_id1)
    assert(len(list(edited_hackers)) == len(test_file_lines) - 1)


def test_add_to_groups():
    new_groups = {"dupa", "test", "zarzad"}
    edited_hackers = hacker_assign_to_groups(hacker_reader(test_file_lines), new_groups, hid=test_id1)
    edited_hacker = next(filter(lambda h: h.hid == test_id1, edited_hackers))
    assert(new_groups.issubset(edited_hacker.groups))


def test_matcher():
    assert(patter_matches("dupa", "d*a"))
    assert(patter_matches("dupa", "dupa"))
    assert(patter_matches("dupa", "*pa"))
    assert(patter_matches("dupa", "d*"))
    assert(patter_matches("dupa", "*"))
    assert(patter_matches("dupa", "*a"))
    assert(patter_matches("dupa", "kupa") is False)


def test_hacker_matcher():
    h1 = hacker_init('1', 'nick1', '2020-01-01', 'test@example.com', 'n1', 'sn1', 'g1,g2,g3,long-group-name1')
    h2 = hacker_init('2', 'nick2', '2020-01-02', 'test@example.com', 'n2', 'sn2', 'g1,g2,g3,long-group-name2')
    pattern1 = hacker_init(None, "n*1", None, None, None, None, 'long-group-name1,g2')
    pattern2 = hacker_init(None, None, None, None, None, None, 'nonexisting-*-1')
    assert(hacker_matches(h1, pattern1))
    assert(not hacker_matches(h2, pattern1))
    assert(not hacker_matches(h1, pattern2))


def test_hacker_remove_group():
    test_groups = {"zarzad", "benis"}
    edited_hackers = hacker_remove_group(hacker_reader(test_file_lines), test_groups, hacker_pattern(hid=test_id1))
    hacker_found = next(filter(lambda h: hacker_matches(h, hacker_pattern(hid=test_id1)), edited_hackers))
    assert(hacker_found.groups.isdisjoint(test_groups))


if __name__ == "__main__":
    test_hacker_remove_group()
    test_hacker_add()
    test_hacker_remove()
    test_hacker_remove_nonexistent()
    test_add_to_groups()
    test_matcher()
    test_hacker_matcher()
