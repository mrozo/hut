from hacker import hacker_add, hacker_reader, hacker_remove, HackerNotFoundException, hacker_assign_to_groups, \
     patter_matches, hacker_init, hacker_matches, hacker_remove_group, hacker_pattern
import secrets
import unittest

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


class TestStringMethods(unittest.TestCase):
    
    def test_hacker_add(self):
        edited_hackers = hacker_add(hacker_reader(test_file_lines), test_hacker)
        hacker_found = filter(lambda h: h.hid == test_hacker.hid, edited_hackers)
        self.assertTrue(len(list(hacker_found)) == 1)
    
    def test_hacker_remove_nonexistent(self):
        edited_hackers = hacker_remove(hacker_reader(test_file_lines), hid="dupa")
        try:
            len(list(edited_hackers))
        except HackerNotFoundException:
            pass
    
    def test_hacker_remove(self):
        edited_hackers = hacker_remove(hacker_reader(test_file_lines), hid=test_id1)
        self.assertTrue(len(list(edited_hackers)) == len(test_file_lines) - 1)

    def test_add_to_groups(self):
        new_groups = {"dupa", "test", "zarzad"}
        edited_hackers = hacker_assign_to_groups(hacker_reader(test_file_lines), new_groups, hid=test_id1)
        edited_hacker = next(filter(lambda h: h.hid == test_id1, edited_hackers))
        self.assertTrue(new_groups.issubset(edited_hacker.groups))
    
    def test_matcher(self):
        self.assertTrue(patter_matches("dupa", "d*a"))
        self.assertTrue(patter_matches("dupa", "dupa"))
        self.assertTrue(patter_matches("dupa", "*pa"))
        self.assertTrue(patter_matches("dupa", "d*"))
        self.assertTrue(patter_matches("dupa", "*"))
        self.assertTrue(patter_matches("dupa", "*a"))
        self.assertFalse(patter_matches("dupa", "kupa"))
    
    def test_hacker_matcher(self):
        h1 = hacker_init('1', 'nick1', '2020-01-01', 'test@example.com', 'n1', 'sn1', 'g1,g2,g3,long-group-name1')
        h2 = hacker_init('2', 'nick2', '2020-01-02', 'test@example.com', 'n2', 'sn2', 'g1,g2,g3,long-group-name2')
        pattern1 = hacker_init(None, "n*1", None, None, None, None, 'long-group-name1,g2')
        pattern2 = hacker_init(None, None, None, None, None, None, 'nonexisting-*-1')
        self.assertTrue(hacker_matches(h1, pattern1))
        self.assertFalse(hacker_matches(h2, pattern1))
        self.assertFalse(hacker_matches(h1, pattern2))
    
    def test_hacker_remove_group(self):
        test_groups = {"zarzad", "benis"}
        edited_hackers = hacker_remove_group(hacker_reader(test_file_lines), test_groups, hacker_pattern(hid=test_id1))
        hacker_found = next(filter(lambda h: hacker_matches(h, hacker_pattern(hid=test_id1)), edited_hackers))
        self.assertTrue(hacker_found.groups.isdisjoint(test_groups))


if __name__ == '__main__':
    unittest.main()
