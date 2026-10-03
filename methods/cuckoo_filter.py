"""Approximate string membership using fingerprints and two candidate buckets."""

import math
import random
import mmh3


class CuckooFilter:
    """Store fingerprints in fixed-size buckets using cuckoo relocation.

    contains returns False for definitely absent and True for possibly present.
    insert returns True when stored and False when relocation fails. A failed
    insertion restores the original buckets, preserving previously stored keys.

    Duplicate insertions occupy additional slots: fingerprints cannot reliably
    distinguish a duplicate key from a different key with the same fingerprint.
    item_count counts successful insertions, not distinct usernames.

    Buckets use Python lists and integers, not packed storage. The filter does
    not grow automatically and does not currently support deletion.
    """

    def __init__(self, expected_items, false_positive_rate, max_kicks=500, seed=42):
        """Create an empty filter and its random generator.

        Input:
            expected_items: Positive integer number of planned insertions.
            false_positive_rate: Target probability strictly between 0 and 1.
            max_kicks: Positive integer limit on relocation attempts.
            seed: Random seed for repeatable relocation choices (default 42).
        Output:
            None. Initialize buckets, fingerprint settings, and item_count.

        Size for approximately 95% occupancy, then round the bucket count up
        to a power of two. The false-positive target is an estimate, not an
        exact guarantee. Reject fingerprint widths above the 32-bit hash width.
        """
        if (
            isinstance(expected_items, bool)
            or not isinstance(expected_items, int)
            or expected_items <= 0
        ):
            raise ValueError("Expected items must be a positive integer.")

        if not 0 < false_positive_rate < 1:
            raise ValueError("False positive rate must be between 0 and 1.")

        if (
            isinstance(max_kicks, bool)
            or not isinstance(max_kicks, int)
            or max_kicks <= 0
        ):
            raise ValueError("Maximum kicks must be a positive integer.")

        self.expected_items = expected_items
        self.false_positive_rate = false_positive_rate
        self.max_kicks = max_kicks
        self.random_generator = random.Random(seed)
        self.bucket_size = 4

        # Subtract logarithms to avoid overflow for extremely small probabilities.
        self.fingerprint_bits = math.ceil(
            math.log2(2 * self.bucket_size) - math.log2(false_positive_rate)
        )
        if self.fingerprint_bits > 32:
            raise ValueError("Target rate requires fingerprints wider than 32 bits.")

        required_buckets = math.ceil(
            expected_items / (self.bucket_size * 0.95)
        )
        self.bucket_count = 1
        while self.bucket_count < required_buckets:
            self.bucket_count *= 2

        if self.bucket_count > 2 ** 32:
            raise ValueError("Bucket count exceeds the 32-bit hash range.")

        self.buckets = []
        for bucket_index in range(self.bucket_count):
            bucket = [None] * self.bucket_size
            self.buckets.append(bucket)

        self.item_count = 0

    def _fingerprint(self, key):
        """Take a string and return its short integer fingerprint.

        Hash UTF-8 bytes and keep fingerprint_bits low bits. Zero is valid;
        empty slots use None rather than zero.
        """
        key_bytes = key.encode("utf-8")
        hash_value = mmh3.hash(key_bytes, 0, signed=False)
        mask = (1 << self.fingerprint_bits) - 1
        return hash_value & mask

    def _first_index(self, key):
        """Take a string and return its first bucket index using a separate seed."""
        key_bytes = key.encode("utf-8")
        hash_value = mmh3.hash(key_bytes, 1, signed=False)
        return hash_value % self.bucket_count

    def _alternate_index(self, index, fingerprint):
        """Take a bucket index and fingerprint; return the other candidate index.

        XOR is reversible: applying this operation twice returns the original
        index. The power-of-two bucket count keeps the result in range. The two
        candidate indexes can sometimes be equal.
        """
        byte_count = (self.fingerprint_bits + 7) // 8
        fingerprint_bytes = fingerprint.to_bytes(byte_count, "little")
        hash_value = mmh3.hash(fingerprint_bytes, 2, signed=False)
        offset = hash_value % self.bucket_count
        return index ^ offset

    def _get_indices(self, key):
        """Take a string and return its fingerprint and two candidate indexes."""
        fingerprint = self._fingerprint(key)
        index1 = self._first_index(key)
        index2 = self._alternate_index(index1, fingerprint)
        return fingerprint, index1, index2

    def _insert_into_bucket(self, index, fingerprint):
        """Try storing a fingerprint in a specified bucket's first empty slot.

        Input: Valid bucket index and integer fingerprint.
        Output: True if stored, otherwise False. Does not update item_count.
        """
        bucket = self.buckets[index]
        for slot in range(self.bucket_size):
            if bucket[slot] is None:
                bucket[slot] = fingerprint
                return True
        return False

    def insert(self, key):
        """Take a string; return True if stored or False if no space is found.

        Try both buckets, then relocate fingerprints up to max_kicks times.
        Record each swap so a failed attempt can be undone in reverse order.
        Increment item_count only after successful storage. Callers must check
        the returned value; a failed key is not guaranteed to be present.
        """
        fingerprint, index1, index2 = self._get_indices(key)

        if self._insert_into_bucket(index1, fingerprint):
            self.item_count += 1
            return True

        if self._insert_into_bucket(index2, fingerprint):
            self.item_count += 1
            return True

        index = self.random_generator.choice([index1, index2])
        changes = []

        for attempt in range(self.max_kicks):
            slot = self.random_generator.randrange(self.bucket_size)
            displaced_fingerprint = self.buckets[index][slot]
            changes.append((index, slot, displaced_fingerprint))

            self.buckets[index][slot] = fingerprint
            fingerprint = displaced_fingerprint
            index = self._alternate_index(index, fingerprint)

            if self._insert_into_bucket(index, fingerprint):
                self.item_count += 1
                return True

        # Reverse every swap, including repeated visits to the same slot.
        for index, slot, old_fingerprint in reversed(changes):
            self.buckets[index][slot] = old_fingerprint

        return False

    def contains(self, key):
        """Take a string; return False if absent or True if possibly present.

        Check for its fingerprint in both candidate buckets. A matching
        fingerprint can belong to another key, so True is not an exact match.
        """
        fingerprint, index1, index2 = self._get_indices(key)
        for index in [index1, index2]:
            for stored_fingerprint in self.buckets[index]:
                if stored_fingerprint == fingerprint:
                    return True
        return False
