"""Measure construction and lookup for the five username methods."""

import time

from methods.linear_search import linear_search
from methods.binary_search import merge_sort, binary_search
from methods.hash_table import HashTable
from methods.bloom_filter import BloomFilter
from methods.cuckoo_filter import CuckooFilter


def time_queries(lookup, queries):
    """Call lookup for each query and return elapsed seconds and its answers.

    Answer storage and loop overhead are included for every method. Correctness
    counting, printing, and file writing happen after the timer stops.
    """
    answers = []
    start = time.perf_counter()
    for query in queries:
        answer = lookup(query)
        answers.append(answer)
    elapsed = time.perf_counter() - start
    return elapsed, answers


def measure_lookups(lookup, present_queries, absent_queries, failed_keys):
    """Return lookup timings and correctness counts for a built structure.

    failed_keys contains rejected insertions, if any. Queries for these keys
    stay in the shared workload but are excluded from false-negative counts.
    A short untimed warmup runs before the measured lookups.
    """

    # warm up run with 3 present and 3 absent queries to account for first-call overhead
    for query in present_queries[:3]:
        lookup(query)
    for query in absent_queries[:3]:
        lookup(query)

    present_seconds, present_answers = time_queries(lookup, present_queries)
    absent_seconds, absent_answers = time_queries(lookup, absent_queries)

    false_negatives = 0
    failed_present_queries = 0
    present_misses = 0
    for index in range(len(present_queries)):
        query = present_queries[index]
        answer = present_answers[index]
        if not answer:
            present_misses += 1
        if query in failed_keys:
            failed_present_queries += 1
        elif not answer:
            false_negatives += 1

    false_positives = 0
    for answer in absent_answers:
        if answer:
            false_positives += 1

    result = {
        "present_query_count": len(present_queries),
        "present_search_seconds": present_seconds,
        "present_seconds_per_query": present_seconds / len(present_queries),
        "absent_query_count": len(absent_queries),
        "absent_search_seconds": absent_seconds,
        "absent_seconds_per_query": absent_seconds / len(absent_queries),
        "false_positives": false_positives,
        "observed_false_positive_rate": false_positives / len(absent_queries),
        "false_negatives": false_negatives,
        "present_misses": present_misses,
        "failed_present_queries": failed_present_queries,
    }
    return result


def benchmark_linear_search(usernames, present_queries, absent_queries, rate, seed):
    """Return list-copy build timing and linear lookup measurements.

    rate and seed are unused here; all benchmark functions share these inputs.
    """
    start = time.perf_counter()
    stored_usernames = usernames.copy()
    build_seconds = time.perf_counter() - start

    def lookup(key):
        return linear_search(stored_usernames, key)

    result = measure_lookups(lookup, present_queries, absent_queries, set())
    result.update(method="linear_search", build_seconds=build_seconds,
                  successful_insertions=len(usernames), failed_insertions=0)
    return result


def benchmark_binary_search(usernames, present_queries, absent_queries, rate, seed):
    """Return manual merge-sort build timing and binary lookup measurements.

    Sorting is included only in build time. rate and seed are unused here.
    """
    start = time.perf_counter()
    sorted_usernames = merge_sort(usernames)
    build_seconds = time.perf_counter() - start

    def lookup(key):
        return binary_search(sorted_usernames, key)

    result = measure_lookups(lookup, present_queries, absent_queries, set())
    result.update(method="binary_search", build_seconds=build_seconds,
                  successful_insertions=len(usernames), failed_insertions=0)
    return result


def benchmark_hash_table(usernames, present_queries, absent_queries, rate, seed):
    """Return hash table construction and lookup measurements.

    Include default-capacity construction, insertions, and automatic resizing
    in build time. rate and seed are unused for this exact structure.
    """
    start = time.perf_counter()
    table = HashTable()
    for username in usernames:
        table.insert(username)
    build_seconds = time.perf_counter() - start

    result = measure_lookups(table.contains, present_queries, absent_queries, set())
    result.update(method="hash_table", build_seconds=build_seconds,
                  successful_insertions=table.size,
                  failed_insertions=len(usernames) - table.size,
                  capacity_slots=table.capacity,
                  load_factor=table.size / table.capacity)
    return result


def benchmark_bloom_filter(usernames, present_queries, absent_queries, rate, seed):
    """Return Bloom construction, lookup, and false-positive measurements.

    rate is the target false-positive probability. seed is unused because the
    Bloom implementation uses fixed hash seeds. Reject oversized bit arrays
    that its current 32-bit hashes cannot address uniformly.
    """
    bit_count = BloomFilter._calculate_bit_count(len(usernames), rate)
    if bit_count > 2 ** 32:
        raise ValueError("This Bloom configuration exceeds its 32-bit hash range.")

    start = time.perf_counter()
    bloom = BloomFilter(len(usernames), rate)
    for username in usernames:
        bloom.insert(username)
    build_seconds = time.perf_counter() - start

    result = measure_lookups(bloom.contains, present_queries, absent_queries, set())
    result.update(method="bloom_filter", build_seconds=build_seconds,
                  successful_insertions=len(usernames), failed_insertions=0,
                  target_false_positive_rate=rate,
                  bit_count=bloom.bit_count, hash_count=bloom.hash_count)
    return result


def benchmark_cuckoo_filter(usernames, present_queries, absent_queries, rate, seed):
    """Return Cuckoo construction, lookup, and rejected-insertion measurements.

    Use rate for sizing and seed for repeatable relocations. Failed-key tracking
    is included in build time. Do not count rejected keys as false negatives.
    """
    start = time.perf_counter()
    cuckoo = CuckooFilter(len(usernames), rate, seed=seed)
    failed_keys = set()
    for username in usernames:
        inserted = cuckoo.insert(username)
        if not inserted:
            failed_keys.add(username)
    build_seconds = time.perf_counter() - start

    result = measure_lookups(cuckoo.contains, present_queries, absent_queries, failed_keys)
    capacity_slots = cuckoo.bucket_count * cuckoo.bucket_size
    result.update(method="cuckoo_filter", build_seconds=build_seconds,
                  successful_insertions=cuckoo.item_count,
                  failed_insertions=len(failed_keys),
                  target_false_positive_rate=rate,
                  capacity_slots=capacity_slots,
                  load_factor=cuckoo.item_count / capacity_slots,
                  fingerprint_bits=cuckoo.fingerprint_bits,
                  max_kicks=cuckoo.max_kicks)
    return result


