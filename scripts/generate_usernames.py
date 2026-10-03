"""Generate unique random usernames and save one username per line."""

import argparse
import random
import string
from tqdm import tqdm
from pathlib import Path


PROJECT_FOLDER = Path(__file__).resolve().parents[1]

MIN_LENGTH = 8
MAX_LENGTH = 24
SPECIAL_CHARACTERS = "_-"
ALLOWED_CHARACTERS = string.ascii_letters + string.digits + SPECIAL_CHARACTERS


def generate_random_username(random_generator):
    """Use the supplied random generator to return one 8-24 character username.

    Each position can contain a lowercase letter, uppercase letter, digit,
    underscore or hyphen. No character category is required.
    """
    length = random_generator.randint(MIN_LENGTH, MAX_LENGTH)
    characters = []

    for position in range(length):
        character = random_generator.choice(ALLOWED_CHARACTERS)
        characters.append(character)

    username = "".join(characters)
    return username


def generate_dataset(count, seed):
    """Take a count and seed, and return that many unique random usernames.

    A fixed seed makes the result reproducible. A temporary set tracks duplicates
    during dataset preparation. The list preserves the order of generation.
    Memory usage grows with the number of usernames.
    """
    if count < 0:
        raise ValueError("count must be non-negative")

    random_generator = random.Random(seed)
    usernames = []
    seen_usernames = set()

    with tqdm(total=count, desc="Generating", unit="username") as progress_bar:
        while len(usernames) < count:
            username = generate_random_username(random_generator)

            if username in seen_usernames:
                continue

            seen_usernames.add(username)
            usernames.append(username)

            # Count only a new, unique username as progress.
            progress_bar.update(1)

    return usernames


def save_dataset(usernames, output_path):
    """Take usernames and a file path, and write one username per line.

    Create the parent directory if needed. Replace an existing output file.
    This function does not return a value.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="\n") as output_file:
        for username in tqdm(usernames, desc="Saving", unit="username"):
            output_file.write(username)
            output_file.write("\n")


def main():
    """Read command-line options, generate and save the dataset, and print counts.

    Inputs come from --count, --seed, and --output. No value is returned.
    """
    parser = argparse.ArgumentParser(
        description="Generate a reproducible dataset of unique random usernames."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100_000,
        help="number of unique usernames (default: 100000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_FOLDER / "data" / "usernames.txt",
        help="output text file (default: data/usernames.txt)",
    )
    args = parser.parse_args()

    if args.count < 0:
        parser.error("--count must be non-negative")

    usernames = generate_dataset(args.count, args.seed)
    save_dataset(usernames, args.output)

    print(f"Saved {len(usernames):,} unique usernames to {args.output}")
    print(f"Username length: {MIN_LENGTH}-{MAX_LENGTH} characters")
    print(f"Allowed special characters: {SPECIAL_CHARACTERS}")
    print(f"Seed: {args.seed}")


if __name__ == "__main__":
    main()




