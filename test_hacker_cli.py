import unittest
from copy import copy
from hacker import *

group1="g1"
group2="g2"
technical_group1="tg1"
technical_group2="tg2"
email_domain1="foo.com"
email_domain2="bar.com"

user1= f"1;nn1;2020-01-01;email1@{email_domain1};name1;lastname1;{group1},{technical_group1},{technical_group2}",
user2= f"1;nn2;2020-01-02;email1@{email_domain1};name2;lastname2;{group1},{technical_group1},{technical_group2}",
user3= f"1;nn3;2020-01-03;email1@{email_domain1};name3;lastname3;{group2},{technical_group1},{technical_group2}",
user4= f"1;nn4;2020-02-01;email1@{email_domain1};name4;lastname4;{group2},{technical_group1},{technical_group2}",
user5= f"1;nn5;2020-03-01;email1@{email_domain1};name5;lastname5;{group1},{technical_group1},{technical_group2}",
user6= f"1;nn6;2020-04-01;email1@{email_domain2};name6;lastname6;{group1},{technical_group1},{technical_group2}",
user7= f"1;nn7;2020-05-01;email1@{email_domain2};name7;lastname7;{group1},{group2},{technical_group1},{technical_group2}",
user8= f"1;nn8;2020-05-01;email1@{email_domain2};name8;lastname8;{group1},{group2},{technical_group1},{technical_group2}",
user9= f"1;nn9;2020-05-01;email1@{email_domain2};name9;lastname9;{group1},{group2},{technical_group1},{technical_group2}",
user10=f"1;nn10;2021-01-01;email1@{email_domain2};name10;lastname10;{group1},{group2},{technical_group1},{technical_group2}",

test_users = [
    user1,
    user2,
    user3,
    user4,
    user5,
    user6,
    user7,
    user8,
    user9,
    user10,
]


from collections import namedtuple


TestData = namedtuple('TestData', ['input', 'output'])


def are_lists_equal(l1: list, l2: list):
    return len(l1) == len(l2) and all(map(lambda a, b: a == b), l1, l2)


def are_dicts_equal(d1: dict, d2: dict):
    return len(d1) == len(d2) and are_lists_equal(d1.keys(), d2.keys()) \
           and all(map(lambda k: d1[k] == d2[k], d1.keys()))


class TestStringMethods(unittest.TestCase):

    def assertCallRequestsEqual(self, c1: CallRequest, c2: CallRequest):
        if c1.function != c2.function or not are_lists_equal(c1.args, c2.args) \
                or not are_dicts_equal(c1.kwargs, c2.kwargs):
            raise self.failureException(msg=f"""Call requests are not equal:\nc1: {c1}\nc2: {c2}""")

    def setUp(self) -> None:
        pass

    def test_list(self):
        args = []
        expected_call = mkCallRequest(hacker_reader)
        self.assertEqual(hacker_cli_args2call(args), expected_call)

    def test_filter_parser(self):
        tests = [
            TestData(['show'], mkCallRequest(hacker_pattern)),
            TestData(['show', '-e' 'e@d.c'], mkCallRequest(hacker_pattern, email="e@d.c")),
        ]

        for i, test_data in zip(range(len(tests)), tests):
            with self.subTest(i=i, args=test_data.input, expected_call=test_data.output):
                self.assertEqual(hacker_cli_args2filter_call(test_data.input), test_data.output)
