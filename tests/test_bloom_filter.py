"""Test Bloom filter correctness using small, deterministic examples.

False positives are allowed, so absent keys are not generally required to return
False after insertion. Measuring their frequency belongs in the benchmarks.
"""

import unittest

from methods.bloom_filter import BloomFilter


class TestBloomFilter(unittest.TestCase):
    def test_empty_filter_reports_absent(self):
        bloom = BloomFilter(100, 0.01)

        for key in ["alice", "User_42-test", ""]:
            with self.subTest(key=key):
                self.assertFalse(bloom.contains(key))

    def test_known_filter_size(self):
        # Reference sizing for 1,000 items and a 1% target probability.
        bloom = BloomFilter(1000, 0.01)

        self.assertEqual(bloom.bit_count, 9586)
        self.assertEqual(bloom.hash_count, 7)
        self.assertEqual(len(bloom.bits), 1199)
        self.assertEqual(bloom.bits, bytearray(1199))

    def test_inserted_key_is_found(self):
        bloom = BloomFilter(100, 0.01)
        bloom.insert("alice")

        self.assertTrue(bloom.contains("alice"))

    def test_no_false_negatives_after_many_insertions(self):
        bloom = BloomFilter(1000, 0.01)
        usernames = []

        for number in range(1000):
            username = "user_" + str(number)
            usernames.append(username)
            bloom.insert(username)

        # Check after all insertions: later keys must not erase earlier keys.
        for username in usernames:
            with self.subTest(username=username):
                self.assertTrue(bloom.contains(username))

    def test_duplicate_insertion_does_not_change_bits(self):
        bloom = BloomFilter(100, 0.01)
        bloom.insert("alice")
        original_bits = bytes(bloom.bits)

        bloom.insert("alice")

        self.assertEqual(bytes(bloom.bits), original_bits)
        self.assertTrue(bloom.contains("alice"))

    def test_empty_unicode_and_mixed_character_keys(self):
        bloom = BloomFilter(100, 0.01)
        keys = ["", "caf\u00e9", "Alice", "alice", "User_42-test"]

        for key in keys:
            bloom.insert(key)

        for key in keys:
            with self.subTest(key=key):
                self.assertTrue(bloom.contains(key))

    def test_lookup_does_not_change_bits(self):
        bloom = BloomFilter(100, 0.01)
        bloom.insert("alice")
        original_bits = bytes(bloom.bits)

        bloom.contains("alice")
        bloom.contains("missing")

        self.assertEqual(bytes(bloom.bits), original_bits)

    def test_filter_instances_are_independent(self):
        first_filter = BloomFilter(100, 0.01)
        second_filter = BloomFilter(100, 0.01)

        first_filter.insert("alice")

        self.assertTrue(first_filter.contains("alice"))
        self.assertFalse(second_filter.contains("alice"))

    def test_bit_operations_across_byte_boundary(self):
        bloom = BloomFilter(100, 0.01)
        positions = [0, 7, 8, bloom.bit_count - 1]

        for position in positions:
            bloom._set_bit(position)

        # Setting one bit must preserve previously set bits and its neighbors.
        for position in range(bloom.bit_count):
            with self.subTest(position=position):
                if position in positions:
                    self.assertTrue(bloom._get_bit(position))
                else:
                    self.assertFalse(bloom._get_bit(position))

    def test_setting_same_bit_twice_does_not_clear_it(self):
        bloom = BloomFilter(100, 0.01)
        bloom._set_bit(7)
        bloom._set_bit(7)

        self.assertTrue(bloom._get_bit(7))

    def test_hash_positions_are_valid_and_repeatable(self):
        bloom = BloomFilter(100, 0.01)

        for key in ["alice", "", "caf\u00e9", "User_42-test"]:
            positions = bloom._get_hashes(key)
            self.assertEqual(len(positions), bloom.hash_count)
            self.assertEqual(positions, bloom._get_hashes(key))

            for position in positions:
                self.assertGreaterEqual(position, 0)
                self.assertLess(position, bloom.bit_count)

    def test_small_filter_can_produce_false_positive(self):
        # These settings create a one-bit filter with one hash position.
        bloom = BloomFilter(1, 0.9)
        self.assertEqual(bloom.bit_count, 1)
        self.assertEqual(bloom.hash_count, 1)
        self.assertFalse(bloom.contains("bob"))

        bloom.insert("alice")

        self.assertTrue(bloom.contains("alice"))
        # Bob was never inserted, but shares the only available bit.
        self.assertTrue(bloom.contains("bob"))

    def test_exceeding_expected_items_preserves_inserted_keys(self):
        bloom = BloomFilter(2, 0.01)
        original_bit_count = bloom.bit_count
        keys = ["alice", "bob", "carol", "dave", "eve"]

        for key in keys:
            bloom.insert(key)

        self.assertEqual(bloom.bit_count, original_bit_count)
        for key in keys:
            self.assertTrue(bloom.contains(key))
        # Overfilling may increase false positives, not create false negatives.

    def test_invalid_expected_items(self):
        for expected_items in [0, -1]:
            with self.subTest(expected_items=expected_items):
                with self.assertRaises(ValueError):
                    BloomFilter(expected_items, 0.01)

    def test_invalid_false_positive_rate(self):
        for rate in [-0.1, 0, 1, 1.5]:
            with self.subTest(rate=rate):
                with self.assertRaises(ValueError):
                    BloomFilter(100, rate)


if __name__ == "__main__":
    unittest.main()
