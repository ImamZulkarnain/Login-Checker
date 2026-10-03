import math
import mmh3


class BloomFilter:
    """Use a bit array to check whether a string may have been inserted.

    A lookup returns False for definitely absent and True for possibly present.
    False positives are possible. Successfully inserted keys remain findable as
    long as the filter's bits and settings are not changed externally.

    The filter stores bits rather than complete usernames. It has a fixed size
    and does not support deletion. Inserting more distinct keys than planned
    increases the false-positive rate.

    This version uses 32-bit hashes. Filters larger than 2**32 bits cannot use
    every bit position, so their intended false-positive rate is unreliable.
    """

    def __init__(self, expected_items, false_positive_rate):
        """Create an empty filter sized for the expected number of distinct keys.

        Input:
            expected_items (int): Positive number of distinct keys anticipated.
            false_positive_rate (float): Target probability between 0 and 1.
                For example, 0.01 represents a target of approximately 1%.

        Output:
            None. Initialize the bit array and number of hash functions.

        Raise ValueError for a nonpositive item count or a probability outside
        the allowed range. The target rate is an estimate based on well-spread
        hashes and the planned item count, not an exact guarantee.
        """
        if expected_items <= 0:
            raise ValueError("Expected items must be greater than 0.")

        if not 0 < false_positive_rate < 1:
            raise ValueError("False positive rate must be between 0 and 1.")

        self.expected_items = expected_items
        self.false_positive_rate = false_positive_rate

        self.bit_count = self._calculate_bit_count(
            expected_items,
            false_positive_rate
        )

        self.hash_count = self._calculate_hash_count(
            self.bit_count,
            expected_items
        )

        # Each byte stores eight bits. Round up to include any remaining bits.
        byte_count = math.ceil(self.bit_count / 8)
        self.bits = bytearray(byte_count)

    @staticmethod
    def _calculate_bit_count(n, p):
        """Calculate the number of bits needed for the requested filter size.

        Input:
            n (int): Expected number of distinct keys, greater than zero.
            p (float): Target false-positive probability, between zero and one.

        Output:
            int: Bit count m, rounded upward to a whole number.

        Use m = -n * ln(p) / (ln(2) ** 2), the standard approximate sizing
        formula under ideal hashing. math.log computes the natural logarithm.
        """
        return math.ceil(
            -(n * math.log(p)) / (math.log(2) ** 2)
        )

    @staticmethod
    def _calculate_hash_count(m, n):
        """Calculate how many hash positions to use for each key.

        Input:
            m (int): Number of bits in the filter.
            n (int): Expected number of distinct keys, greater than zero.

        Output:
            int: Hash count k, rounded to an integer and at least one.

        Use k = (m / n) * ln(2), the approximate optimal hash count.
        """
        return max(
            1,
            round((m / n) * math.log(2))
        )

    def _set_bit(self, bit_index):
        """Set one bit to 1 without changing the other bits in its byte.

        Input:
            bit_index (int): Valid bit position from 0 to bit_count - 1.

        Output:
            None. Update the stored byte in place.
        """
        byte_index = bit_index // 8
        bit_offset = bit_index % 8

        # Shift 1 to the desired position; OR sets that bit without clearing any.
        self.bits[byte_index] |= 1 << bit_offset

    def _get_bit(self, bit_index):
        """Read whether a particular bit is set.

        Input:
            bit_index (int): Valid bit position from 0 to bit_count - 1.

        Output:
            bool: True if the bit is 1, otherwise False.
        """
        byte_index = bit_index // 8
        bit_offset = bit_index % 8

        # AND isolates the selected bit. bool converts the result to True/False.
        return bool(
            self.bits[byte_index] & (1 << bit_offset)
        )

    def _get_hashes(self, key):
        """Calculate the bit positions associated with a string key.

        Input:
            key (str): Username or other string to encode as UTF-8.

        Output:
            list: hash_count indexes, each between 0 and bit_count - 1.
                Some positions may repeat.

        Hash the same bytes with different seeds. Modulo maps each hash result
        to a valid bit index, including when the hash result is negative.
        """
        key_bytes = key.encode("utf-8")
        positions = []

        for seed in range(self.hash_count):
            position = mmh3.hash(key_bytes, seed) % self.bit_count
            positions.append(position)

        return positions

    def insert(self, key):
        """Record a string by setting all its hashed bit positions to 1.

        Input:
            key (str): Username or other string to insert.

        Output:
            None. Update the filter's bits.

        Repeating an insertion leaves the bits unchanged. The filter cannot
        determine whether a key is new, and it does not count distinct keys.
        """
        for position in self._get_hashes(key):
            self._set_bit(position)

    def contains(self, key):
        """Check whether a string may have been inserted.

        Input:
            key (str): Username or other string to look up.

        Output:
            bool: False means definitely absent. True means possibly present.

        A zero at any required position proves the key is absent. If all bits
        are set, other keys could have set them, so an exact lookup is needed
        before concluding that the username is already taken.
        """
        for position in self._get_hashes(key):
            if not self._get_bit(position):
                return False

        return True
