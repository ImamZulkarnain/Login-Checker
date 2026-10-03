"""Coordinate username benchmarks and save measurements to CSV."""

import argparse
import csv
import gc
import math
import platform
import random
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

from benchmarking.data import load_usernames, create_queries
from benchmarking.runners import (
    benchmark_linear_search,
    benchmark_binary_search,
    benchmark_hash_table,
    benchmark_bloom_filter,
    benchmark_cuckoo_filter,
)
from methods.bloom_filter import BloomFilter


PROJECT_FOLDER = Path(__file__).resolve().parent


def save_results(writer, output_file, result):
    """Write and flush one result row so completed experiments are preserved.

    Inputs are a CSV DictWriter, its open file, and one result dictionary.
    Return nothing. File writing is outside algorithm timing.
    """
    writer.writerow(result)
    output_file.flush()


def main():
    """Read terminal options, benchmark each size and trial, and save a CSV.

    No value is returned. Print progress between methods rather than within
    timed loops. The default run reads a prefix of the existing 100-million-name dataset.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path,
                        default=PROJECT_FOLDER / "data" / "usernames_100M.txt")
    parser.add_argument("--sizes", type=int, nargs="+", default=[10000, 100000])
    parser.add_argument("--queries", type=int, default=100,
                        help="number of present AND absent queries per trial")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--false-positive-rate", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path,
                        help="new output CSV path; default is a timestamped file in results")
    args = parser.parse_args()

    if min(args.sizes) <= 0 or len(set(args.sizes)) != len(args.sizes):
        parser.error("Dataset sizes must be positive and must not repeat.")
    if args.queries <= 0 or args.queries > min(args.sizes):
        parser.error("--queries must be positive and no larger than the smallest size.")
    if args.trials <= 0:
        parser.error("--trials must be positive.")
    if not 0 < args.false_positive_rate < 1:
        parser.error("--false-positive-rate must be between 0 and 1.")
    fingerprint_bits = math.ceil(3 - math.log2(args.false_positive_rate))
    if fingerprint_bits > 32:
        parser.error("The requested rate needs unsupported Cuckoo fingerprints above 32 bits.")
    if BloomFilter._calculate_bit_count(max(args.sizes), args.false_positive_rate) > 2 ** 32:
        parser.error("The requested Bloom filter exceeds its current 32-bit hash range.")

    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        args.output = PROJECT_FOLDER / "results" / ("benchmark_" + timestamp + ".csv")
    if args.output.exists():
        parser.error("The output file already exists. Choose a new --output path.")

    print("Loading and validating", max(args.sizes), "usernames...", flush=True)
    try:
        all_usernames = load_usernames(args.dataset, max(args.sizes))
    except (OSError, ValueError) as error:
        parser.error(str(error))

    benchmark_functions = [
        benchmark_linear_search,
        benchmark_binary_search,
        benchmark_hash_table,
        benchmark_bloom_filter,
        benchmark_cuckoo_filter,
    ]
    columns = [
        "method", "dataset_size", "trial", "build_seconds", "present_seconds_per_query",
        "absent_seconds_per_query", "false_positives", "false_negatives", "failed_insertions",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=columns,
            extrasaction="ignore"
        )
        writer.writeheader()

        for size in args.sizes:
            usernames = all_usernames[:size]
            total_steps = args.trials * len(benchmark_functions)

            # Update progress only between benchmarks, outside all timers.
            with tqdm(
                total=total_steps,
                desc=f"{size:,} usernames",
                unit="run",
                dynamic_ncols=True
            ) as progress_bar:
                for trial in range(1, args.trials + 1):
                    progress_bar.set_postfix_str(f"Trial {trial}: preparing queries")
                    query_seed = args.seed + trial - 1
                    present_queries, absent_queries = create_queries(
                        usernames, args.queries, query_seed
                    )
                    # Vary execution order to reduce consistent first/last effects.
                    methods = benchmark_functions.copy()
                    random.Random(query_seed).shuffle(methods)

                    for order, benchmark in enumerate(methods, start=1):
                        method_name = benchmark.__name__.replace("benchmark_", "")
                        progress_bar.set_postfix_str(f"Trial {trial}: {method_name}")
                        gc.collect()
                        result = benchmark(
                            usernames, present_queries, absent_queries,
                            args.false_positive_rate, query_seed
                        )
                        result.update(dataset_size=size, trial=trial, query_seed=query_seed,
                                      method_order=order, dataset_path=str(args.dataset.resolve()),
                                      python_version=platform.python_version(),
                                      platform=platform.platform())
                        save_results(writer, output_file, result)

                        if result["failed_insertions"]:
                            tqdm.write(
                                f"Warning: {method_name}, size {size:,}, trial {trial}: "
                                f"{result['failed_insertions']:,} rejected insertions."
                            )
                        if result["false_negatives"]:
                            raise RuntimeError("An inserted query was not found; inspect the saved results.")
                        if result["method"] in ["linear_search", "binary_search", "hash_table"]:
                            if result["false_positives"] or result["failed_insertions"]:
                                raise RuntimeError("An exact method failed a correctness check.")

                        progress_bar.update(1)

                progress_bar.set_postfix_str("Complete")

    print("Results saved to:", args.output)


if __name__ == "__main__":
    main()

