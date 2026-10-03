class HashTable:
    """
    Hash table for storing unique string keys using open addressing
    with linear probing.

    The table uses the 64-bit FNV-1a hash function and automatically
    doubles its capacity when an insertion would cause the load factor
    to exceed 0.7.
    """

    def __init__(self, capacity=8, max_load_factor=0.7):
        """
        Initialize an empty hash table.

        Input:
            capacity (int): Initial number of slots in the hash table.
            max_load_factor (float): Maximum allowed load factor before
                                    resizing. Defaults to 0.7.

        Output:
            None

        The table initially contains no keys and automatically resizes
        when an insertion would exceed the specified maximum load factor.
        """

        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0.")

        if not 0 < max_load_factor < 1:
            raise ValueError("Maximum load factor must be between 0 and 1.")
    
        self.capacity = capacity
        self.size = 0
        self.max_load_factor = max_load_factor
        self.table = [None] * capacity


    def _hash(self, key):
        """
        Compute a 64-bit FNV-1a hash for a string key.

        Input:
            key (str): The string to hash.

        Output:
            int: The 64-bit hash value of the key.

        The key is encoded as UTF-8 bytes. Each byte is XORed with
        the current hash value, which is then multiplied by the
        64-bit FNV prime.
        """

        hash_value = 14695981039346656037

        for byte in key.encode("utf-8"):
            hash_value ^= byte
            hash_value *= 1099511628211
            hash_value &= 0xFFFFFFFFFFFFFFFF

        return hash_value


    def _get_index(self, key):
        """
        Determine the starting table index for a key.

        Input:
            key (str): The key whose table index is required.

        Output:
            int: An index between 0 and capacity - 1.

        The FNV-1a hash value is mapped to the current table
        capacity using the modulo operation.
        """

        return self._hash(key) % self.capacity


    def insert(self, key):
        """
        Insert a key into the hash table using linear probing.

        Input:
            key (str): The key to insert.

        Output:
            bool: True if the key was inserted successfully,
                  False if the key already exists.

        If a collision occurs, consecutive table positions are
        examined until the key or an empty slot is found. Before
        inserting a new key, the table is resized if the resulting
        load factor would exceed max_load_factor.
        """

        index = self._get_index(key)

        for _ in range(self.capacity):

            if self.table[index] == key:
                return False

            if self.table[index] is None:

                if (self.size + 1) / self.capacity > self.max_load_factor:
                    self._resize()
                    return self.insert(key)

                self.table[index] = key
                self.size += 1
                return True

            index = (index + 1) % self.capacity

        return False
    

    def _resize(self):
        """
        Double the capacity of the hash table and rehash all keys.

        Input:
            None

        Output:
            None

        A new table with twice the previous capacity is created.
        Existing keys are reinserted because their table indexes
        may change when the capacity changes.
        """

        old_table = self.table

        self.capacity *= 2
        self.table = [None] * self.capacity
        self.size = 0

        for key in old_table:
            if key is not None:
                self.insert(key)


    def contains(self, key):
        """
        Check whether a key exists in the hash table.

        Input:
            key (str): The key to search for.

        Output:
            bool: True if the key exists, otherwise False.

        The search begins at the key's hashed index and follows
        the same linear-probing sequence used during insertion.
        The search stops when the key is found or an empty slot
        is encountered.
        """
        
        index = self._get_index(key)

        for _ in range(self.capacity):
            if self.table[index] is None:
                return False

            if self.table[index] == key:
                return True

            index = (index + 1) % self.capacity

        return False



