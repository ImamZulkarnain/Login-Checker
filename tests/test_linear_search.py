"""Unit tests for linear search. Run from the project folder with unittest."""

import unittest

from methods.linear_search import linear_search


class TestLinearSearch(unittest.TestCase):
    def test_finds_first_middle_and_last_usernames(self):
        usernames = ["alice", "bob", "carol"]

        for target in usernames:
            with self.subTest(target=target):
                self.assertTrue(linear_search(usernames, target))

    def test_missing_username(self):
        self.assertFalse(linear_search(["alice", "bob"], "carol"))

    def test_empty_list(self):
        self.assertFalse(linear_search([], "alice"))

    def test_single_username(self):
        self.assertTrue(linear_search(["alice"], "alice"))
        self.assertFalse(linear_search(["alice"], "bob"))

    def test_case_sensitive_search(self):
        self.assertTrue(linear_search(["Alice"], "Alice"))
        self.assertFalse(linear_search(["Alice"], "alice"))

    def test_duplicate_usernames(self):
        self.assertTrue(linear_search(["alice", "alice"], "alice"))

    def test_empty_string_and_special_characters(self):
        usernames = ["", "User_42-test"]
        self.assertTrue(linear_search(usernames, ""))
        self.assertTrue(linear_search(usernames, "User_42-test"))

    def test_search_does_not_change_list(self):
        usernames = ["carol", "alice", "bob"]
        linear_search(usernames, "bob")
        self.assertEqual(usernames, ["carol", "alice", "bob"])


if __name__ == "__main__":
    unittest.main()
