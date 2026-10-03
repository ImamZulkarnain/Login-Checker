"""Check cuckoo insertion, lookup, relocation, and failure rollback."""

import unittest
from unittest.mock import patch

from methods.cuckoo_filter import CuckooFilter


class TestCuckooFilter(unittest.TestCase):
    def test_empty_filter(self):
        cuckoo = CuckooFilter(100, 0.01)
        self.assertFalse(cuckoo.contains("alice"))
        self.assertEqual(cuckoo.item_count, 0)

    def test_insert_and_lookup(self):
        cuckoo = CuckooFilter(100, 0.01)
        keys = ["alice", "Alice", "", "caf\u00e9", "User_42-test"]
        for key in keys:
            self.assertTrue(cuckoo.insert(key))
        for key in keys:
            self.assertTrue(cuckoo.contains(key))
        self.assertEqual(cuckoo.item_count, len(keys))

    def test_duplicate_insertions_count_as_separate_entries(self):
        cuckoo = CuckooFilter(10, 0.01)
        self.assertTrue(cuckoo.insert("alice"))
        self.assertTrue(cuckoo.insert("alice"))
        self.assertEqual(cuckoo.item_count, 2)
        self.assertTrue(cuckoo.contains("alice"))

    def test_alternate_index_is_reversible(self):
        cuckoo = CuckooFilter(100, 0.01)
        for number in range(100):
            fingerprint, first, second = cuckoo._get_indices(str(number))
            self.assertGreaterEqual(second, 0)
            self.assertLess(second, cuckoo.bucket_count)
            self.assertEqual(cuckoo._alternate_index(second, fingerprint), first)

    def test_uses_second_bucket_when_first_is_full(self):
        cuckoo = CuckooFilter(10, 0.01)
        cuckoo.buckets[0] = [1, 2, 3, 4]
        cuckoo.item_count = 4
        with patch.object(cuckoo, "_get_indices", return_value=(99, 0, 1)):
            self.assertTrue(cuckoo.insert("new"))
            self.assertTrue(cuckoo.contains("new"))
        self.assertEqual(cuckoo.buckets[1][0], 99)
        self.assertEqual(cuckoo.item_count, 5)

    def test_successful_relocation(self):
        cuckoo = CuckooFilter(10, 0.01)
        cuckoo.buckets[0] = [11, 12, 13, 14]
        cuckoo.buckets[1] = [21, 22, 23, 24]
        cuckoo.item_count = 8

        # Force the new key into slot 0 of bucket 0, moving fingerprint 11
        # into empty bucket 2. This reliably exercises relocation.
        with patch.object(cuckoo, "_get_indices", return_value=(99, 0, 1)):
            with patch.object(cuckoo.random_generator, "choice", return_value=0):
                with patch.object(cuckoo.random_generator, "randrange", return_value=0):
                    with patch.object(cuckoo, "_alternate_index", return_value=2):
                        self.assertTrue(cuckoo.insert("new"))

        self.assertEqual(cuckoo.buckets[0], [99, 12, 13, 14])
        self.assertEqual(cuckoo.buckets[1], [21, 22, 23, 24])
        self.assertEqual(cuckoo.buckets[2], [11, None, None, None])
        self.assertEqual(cuckoo.item_count, 9)

    def test_failed_insertion_restores_every_slot(self):
        for max_kicks in [1, 2, 7, 20]:
            with self.subTest(max_kicks=max_kicks):
                # A one-bucket filter has exactly four slots.
                cuckoo = CuckooFilter(1, 0.01, max_kicks=max_kicks)
                keys = ["alice", "bob", "carol", "dave"]
                for key in keys:
                    self.assertTrue(cuckoo.insert(key))
                before = [bucket.copy() for bucket in cuckoo.buckets]

                self.assertFalse(cuckoo.insert("extra"))

                self.assertEqual(cuckoo.buckets, before)
                self.assertEqual(cuckoo.item_count, 4)
                for key in keys:
                    self.assertTrue(cuckoo.contains(key))

    def test_many_insertions_preserve_all_successful_keys(self):
        cuckoo = CuckooFilter(100, 0.01, max_kicks=30)
        stored_keys = []
        for number in range(200):
            key = "user_" + str(number)
            if cuckoo.insert(key):
                stored_keys.append(key)
            # Check after successes and failures to catch lost fingerprints.
            for stored_key in stored_keys:
                self.assertTrue(cuckoo.contains(stored_key))
        self.assertEqual(cuckoo.item_count, len(stored_keys))

    def test_zero_fingerprint_is_valid(self):
        cuckoo = CuckooFilter(10, 0.01)
        with patch.object(cuckoo, "_fingerprint", return_value=0):
            self.assertFalse(cuckoo.contains("alice"))
            self.assertTrue(cuckoo.insert("alice"))
            self.assertTrue(cuckoo.contains("alice"))

    def test_unsupported_fingerprint_width(self):
        for rate in [1e-12, 1e-320]:
            with self.assertRaises(ValueError):
                CuckooFilter(100, rate)

    def test_invalid_inputs(self):
        for count in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                CuckooFilter(count, 0.01)
        for kicks in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                CuckooFilter(10, 0.01, max_kicks=kicks)
        for rate in [0, 1, -0.1, 1.5]:
            with self.assertRaises(ValueError):
                CuckooFilter(10, rate)


if __name__ == "__main__":
    unittest.main()
