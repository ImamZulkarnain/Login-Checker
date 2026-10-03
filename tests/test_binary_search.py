"""Unit tests for manual merge sort and binary search."""

import unittest

from methods.binary_search import merge, merge_sort, binary_search


class TestMergeSort(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(merge_sort([]), [])

    def test_single_username(self):
        self.assertEqual(merge_sort(["alice"]), ["alice"])

    def test_odd_length_unsorted_list(self):
        usernames = ["dave", "bob", "eve", "alice", "carol"]
        expected = ["alice", "bob", "carol", "dave", "eve"]
        self.assertEqual(merge_sort(usernames), expected)

    def test_even_length_reverse_sorted_list(self):
        usernames = ["dave", "carol", "bob", "alice"]
        expected = ["alice", "bob", "carol", "dave"]
        self.assertEqual(merge_sort(usernames), expected)

    def test_already_sorted_list(self):
        usernames = ["alice", "bob", "carol"]
        self.assertEqual(merge_sort(usernames), usernames)

    def test_preserves_duplicates(self):
        usernames = ["bob", "alice", "bob", "alice"]
        expected = ["alice", "alice", "bob", "bob"]
        self.assertEqual(merge_sort(usernames), expected)

    def test_case_sensitive_character_order(self):
        usernames = ["a", "_", "A", "0", "-", ""]
        expected = ["", "-", "0", "A", "_", "a"]
        self.assertEqual(merge_sort(usernames), expected)

    def test_sort_does_not_change_original_list(self):
        usernames = ["carol", "alice", "bob"]
        merge_sort(usernames)
        self.assertEqual(usernames, ["carol", "alice", "bob"])

    def test_merge_keeps_remaining_entries_from_either_side(self):
        self.assertEqual(merge(["alice", "carol"], ["bob"]),
                         ["alice", "bob", "carol"])
        self.assertEqual(merge(["bob"], ["alice", "carol"]),
                         ["alice", "bob", "carol"])

    def test_merge_with_empty_lists(self):
        self.assertEqual(merge([], ["alice"]), ["alice"])
        self.assertEqual(merge(["alice"], []), ["alice"])
        self.assertEqual(merge([], []), [])


class TestBinarySearch(unittest.TestCase):
    def test_finds_every_position(self):
        # Even and odd lengths exercise different middle positions.
        for usernames in [["alice", "bob", "carol"],
                          ["alice", "bob", "carol", "dave"]]:
            for target in usernames:
                with self.subTest(usernames=usernames, target=target):
                    self.assertTrue(binary_search(usernames, target))

    def test_missing_before_between_and_after_entries(self):
        usernames = ["bob", "dave", "frank"]
        for target in ["alice", "carol", "zoe"]:
            with self.subTest(target=target):
                self.assertFalse(binary_search(usernames, target))

    def test_empty_list(self):
        self.assertFalse(binary_search([], "alice"))

    def test_single_username(self):
        self.assertTrue(binary_search(["bob"], "bob"))
        self.assertFalse(binary_search(["bob"], "alice"))
        self.assertFalse(binary_search(["bob"], "carol"))

    def test_duplicates(self):
        self.assertTrue(binary_search(["alice", "alice", "bob"], "alice"))

    def test_case_sensitive_search(self):
        self.assertTrue(binary_search(["Alice"], "Alice"))
        self.assertFalse(binary_search(["Alice"], "alice"))

    def test_sort_then_search(self):
        usernames = ["user_9", "Alice-42", "", "bob123"]
        sorted_usernames = merge_sort(usernames)
        for target in usernames:
            with self.subTest(target=target):
                self.assertTrue(binary_search(sorted_usernames, target))
        self.assertFalse(binary_search(sorted_usernames, "missing"))


if __name__ == "__main__":
    unittest.main()
