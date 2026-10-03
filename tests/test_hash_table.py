"""Unit tests for hash table insertion, lookup, collisions, and resizing."""

import unittest

from methods.hash_table import HashTable


class CollisionHashTable(HashTable):
    """Test helper: force every key to start at the last slot.

    This deliberately creates collisions and wraparound without depending on
    which usernames happen to collide under the normal hash function.
    """

    def _hash(self, key):
        return self.capacity - 1


class TestHashTable(unittest.TestCase):
    def test_empty_table(self):
        table = HashTable()
        self.assertEqual(table.size, 0)
        self.assertFalse(table.contains("alice"))

    def test_insert_and_find(self):
        table = HashTable()
        self.assertTrue(table.insert("alice"))
        self.assertTrue(table.contains("alice"))
        self.assertEqual(table.size, 1)
        self.assertFalse(table.contains("bob"))

    def test_duplicate_does_not_increase_size(self):
        table = HashTable()
        table.insert("alice")
        self.assertFalse(table.insert("alice"))
        self.assertEqual(table.size, 1)

    def test_duplicate_does_not_trigger_resize(self):
        table = HashTable(capacity=4, max_load_factor=0.5)
        table.insert("alice")
        table.insert("bob")
        self.assertFalse(table.insert("alice"))
        self.assertEqual(table.capacity, 4)
        self.assertEqual(table.size, 2)

    def test_resize_at_custom_load_factor(self):
        table = HashTable(capacity=4, max_load_factor=0.5)
        table.insert("alice")
        table.insert("bob")
        self.assertEqual(table.capacity, 4)
        table.insert("carol")
        self.assertEqual(table.capacity, 8)
        self.assertEqual(table.size, 3)
        for key in ["alice", "bob", "carol"]:
            self.assertTrue(table.contains(key))

    def test_repeated_resizing_preserves_all_keys(self):
        table = HashTable(capacity=1)
        usernames = []
        for number in range(200):
            username = "user_" + str(number)
            usernames.append(username)
            self.assertTrue(table.insert(username))
            self.assertLessEqual(table.size / table.capacity, 0.7)

        self.assertEqual(table.size, 200)
        for username in usernames:
            with self.subTest(username=username):
                self.assertTrue(table.contains(username))
        self.assertFalse(table.contains("missing"))

    def test_collisions_and_wraparound(self):
        table = CollisionHashTable(capacity=8)
        for key in ["alice", "bob", "carol"]:
            self.assertTrue(table.insert(key))

        # The last slot is occupied first; probing continues at index zero.
        self.assertEqual(table.table[7], "alice")
        self.assertEqual(table.table[0], "bob")
        self.assertEqual(table.table[1], "carol")
        for key in ["alice", "bob", "carol"]:
            self.assertTrue(table.contains(key))
        self.assertFalse(table.contains("missing"))
        self.assertFalse(table.insert("carol"))
        self.assertEqual(table.size, 3)

    def test_collisions_survive_resizing(self):
        table = CollisionHashTable(capacity=4)
        usernames = ["alice", "bob", "carol", "dave", "eve", "frank"]
        for username in usernames:
            self.assertTrue(table.insert(username))
        self.assertGreater(table.capacity, 4)
        for username in usernames:
            self.assertTrue(table.contains(username))
            self.assertFalse(table.insert(username))
        self.assertEqual(table.size, len(usernames))
        self.assertFalse(table.contains("missing"))

    def test_case_sensitive_keys(self):
        table = HashTable()
        table.insert("Alice")
        self.assertFalse(table.contains("alice"))
        self.assertTrue(table.insert("alice"))
        self.assertTrue(table.contains("Alice"))
        self.assertTrue(table.contains("alice"))
        self.assertEqual(table.size, 2)

    def test_empty_unicode_and_special_character_keys(self):
        table = HashTable()
        for key in ["", "caf\u00e9", "User_42-test"]:
            self.assertTrue(table.insert(key))
            self.assertTrue(table.contains(key))
            self.assertFalse(table.insert(key))
        self.assertEqual(table.size, 3)

    def test_invalid_capacity(self):
        for capacity in [0, -1]:
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    HashTable(capacity=capacity)

    def test_invalid_load_factor(self):
        for load_factor in [-0.1, 0, 1, 1.5]:
            with self.subTest(load_factor=load_factor):
                with self.assertRaises(ValueError):
                    HashTable(max_load_factor=load_factor)


if __name__ == "__main__":
    unittest.main()
