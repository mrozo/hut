import unittest
from hacker import *



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
            TestData(list(), mkCallRequest(hacker_pattern)),
            TestData(['show', '-i' 'deadbeef'], mkCallRequest(hacker_pattern, hid="deadbeef")),
            TestData(['show', '-e' 'e@d.c'], mkCallRequest(hacker_pattern, email="e@d.c")),
            TestData(['show', '-n' 'myname'], mkCallRequest(hacker_pattern, name="myname")),
            TestData(['show', '-ln', 'mylastname'], mkCallRequest(hacker_pattern, last_name="mylastname")),
            TestData(['show', '-nn', 'mynickname'], mkCallRequest(hacker_pattern, nick="mynickname")),
            TestData(['show', '-g', 'g1,g2,g3'], mkCallRequest(hacker_pattern, groups="g1,g2,g3")),
        ]

        for i, test_data in zip(range(len(tests)), tests):
            with self.subTest(i=i, args=test_data.input, expected_call=test_data.output):
                parsed_args = hacker_cli_argparse.parse_args(test_data.input)
                self.assertEqual(hacker_cli_args2filter_call(parsed_args), test_data.output)
