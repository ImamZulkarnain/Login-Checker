"""Check benchmark data preparation and result accounting."""

import unittest
from unittest.mock import mock_open, patch

from benchmarking.data import load_usernames, create_queries
from benchmarking.runners import (
    measure_lookups,
    benchmark_linear_search,
    benchmark_binary_search,
    benchmark_hash_table,
    benchmark_bloom_filter,
    benchmark_cuckoo_filter,
)


class TestBenchmark(unittest.TestCase):
    def test_loader_stops_at_requested_prefix(self):
        with patch("builtins.open", mock_open(read_data="alice\nbob\ncarol\n")):
            self.assertEqual(load_usernames("unused.txt", 2), ["alice", "bob"])

    def test_loader_rejects_short_file(self):
        with patch("builtins.open", mock_open(read_data="alice\n")):
            with self.assertRaises(ValueError):
                load_usernames("unused.txt", 2)

    def test_loader_rejects_duplicates(self):
        with patch("builtins.open", mock_open(read_data="alice\nalice\n")):
            with self.assertRaises(ValueError):
                load_usernames("unused.txt", 2)

    def test_queries_are_repeatable_unique_and_disjoint(self):
        usernames = ["alice", "bob", "carol"]
        present, absent = create_queries(usernames, 3, 42)
        self.assertEqual((present, absent), create_queries(usernames, 3, 42))
        self.assertEqual(set(present), set(usernames))
        self.assertEqual(len(set(absent)), 3)
        self.assertTrue(set(absent).isdisjoint(usernames))

    def test_invalid_query_count(self):
        for count in [0, 2]:
            with self.assertRaises(ValueError):
                create_queries(["alice"], count, 42)

    def test_rejected_keys_are_not_counted_as_false_negatives(self):
        def lookup(key):
            return key == "alice"

        result = measure_lookups(lookup, ["alice", "bob"], ["missing"], {"bob"})
        self.assertEqual(result["failed_present_queries"], 1)
        self.assertEqual(result["present_misses"], 1)
        self.assertEqual(result["false_negatives"], 0)
        self.assertEqual(result["false_positives"], 0)

    def test_counts_false_positives_and_false_negatives(self):
        def lookup(key):
            return key == "missing"

        result = measure_lookups(lookup, ["alice"], ["missing"], set())
        self.assertEqual(result["false_negatives"], 1)
        self.assertEqual(result["false_positives"], 1)
        self.assertEqual(result["observed_false_positive_rate"], 1)

    def test_all_five_methods_return_valid_measurements(self):
        usernames = ["alice", "bob", "carol"]
        benchmarks = [benchmark_linear_search, benchmark_binary_search,
                      benchmark_hash_table, benchmark_bloom_filter,
                      benchmark_cuckoo_filter]
        for benchmark in benchmarks:
            with self.subTest(method=benchmark.__name__):
                result = benchmark(usernames, usernames, ["absent"], 0.01, 42)
                self.assertEqual(result["successful_insertions"], 3)
                self.assertEqual(result["failed_insertions"], 0)
                self.assertEqual(result["false_negatives"], 0)
                self.assertEqual(result["present_query_count"], 3)
                self.assertGreaterEqual(result["build_seconds"], 0)
                self.assertGreaterEqual(result["absent_search_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
