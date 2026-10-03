"""Load benchmark datasets and prepare repeatable search queries."""

import random

from scripts.generate_usernames import generate_random_username


def load_usernames(file_path, count):
    """Read count unique usernames from a file and return them in file order.

    Reject duplicates and short files so every method receives the requested
    number of distinct entries. Reading and validation are not benchmarked.
    Only the requested prefix is read, even if the file is much larger.
    """
    if count <= 0:
        raise ValueError("The requested dataset size must be positive.")

    usernames = []
    seen_usernames = set()

    with open(file_path, "r", encoding="utf-8") as source:
        for line in source:
            username = line.strip()
            if username == "":
                continue
            if username in seen_usernames:
                raise ValueError("The selected dataset contains duplicate usernames.")

            usernames.append(username)
            seen_usernames.add(username)
            if len(usernames) == count:
                break

    if len(usernames) < count:
        raise ValueError(
            f"Requested {count:,} usernames, but found only {len(usernames):,}."
        )
    return usernames


def create_queries(usernames, query_count, seed):
    """Return present and absent query lists using a repeatable random seed.

    Present queries are sampled without replacement. Absent queries use the
    dataset generator's character and length rules and are checked against the
    entire selected dataset. Query preparation is outside the timed sections.
    """
    if query_count <= 0 or query_count > len(usernames):
        raise ValueError("Query count must be between 1 and the dataset size.")

    random_generator = random.Random(seed)
    present_queries = random_generator.sample(usernames, query_count)
    existing_usernames = set(usernames)
    absent_queries = []
    seen_queries = set()

    while len(absent_queries) < query_count:
        username = generate_random_username(random_generator)
        if username in existing_usernames or username in seen_queries:
            continue
        absent_queries.append(username)
        seen_queries.add(username)

    return present_queries, absent_queries


