# Unit tests

Run these commands from the project folder (H:\COSC520_A1).
No username dataset files are needed. Install the project dependencies first with python -m pip install -r requirements.txt; the Bloom filter tests require mmh3.

Run all tests:

```powershell
python -m unittest discover -s tests -v
```

Run just the hash table tests:

```powershell
python -m unittest discover -s tests -p test_hash_table.py -v
```

The tests use small examples so they finish quickly. They check correctness,
not runtime performance. test_binary_search.py also checks manual merge sort.
CollisionHashTable is a test helper that deliberately forces collisions; it
is not used by the application. Each test method starts with test_ so unittest
can discover it. assertTrue, assertFalse, and assertEqual check expected results.


Run just the Bloom filter tests:

```powershell
python -m unittest discover -s tests -p test_bloom_filter.py -v
```

Bloom filter tests allow false positives and check that inserted keys remain
findable. A one-bit example demonstrates a guaranteed false positive. These
unit tests do not certify the target false-positive rate; measure that separately
in benchmarks using absent queries.
