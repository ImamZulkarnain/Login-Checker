"""Create runtime comparison plots from a saved benchmark CSV."""

import argparse
import csv
import math
import statistics
from pathlib import Path

import matplotlib

# Save images without requiring a desktop window.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


PROJECT_FOLDER = Path(__file__).resolve().parents[1]
METHOD_LABELS = {
    "linear_search": "Linear search",
    "binary_search": "Binary search",
    "hash_table": "Hash table",
    "bloom_filter": "Bloom filter",
    "cuckoo_filter": "Cuckoo filter",
}
METRICS = [
    "build_seconds",
    "present_seconds_per_query",
    "absent_seconds_per_query",
]


def find_latest_csv():
    """Return the most recently modified benchmark CSV in results/.

    Raise ValueError when there are no benchmark files. Files named smoke_test
    are not selected automatically; they can be selected with --input.
    """
    files = list((PROJECT_FOLDER / "results").glob("benchmark_*.csv"))
    if not files:
        raise ValueError("No benchmark CSV found. Run main.py or supply --input.")
    latest_file = max(files, key=lambda path: path.stat().st_mtime)
    return latest_file


def load_results(file_path, exclude_linear=False):
    """Read a benchmark CSV and return validated rows with numeric values.

    Require every selected method for each size/trial pair.
    When exclude_linear is True, ignore linear-search rows if present. Reject duplicate rows,
    invalid timings, false negatives, and failed insertions so the charts do not
    present incomplete builds as successful full-dataset comparisons.
    """
    required_columns = [
        "method", "dataset_size", "trial", "false_positives",
        "false_negatives", "failed_insertions",
    ] + METRICS
    expected_methods = set(METHOD_LABELS)
    if exclude_linear:
        expected_methods.remove("linear_search")

    results = []
    seen_rows = set()
    methods_per_run = {}

    with file_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        for column in required_columns:
            if column not in (reader.fieldnames or []):
                raise ValueError(f"Missing CSV column: {column}")

        for line_number, row in enumerate(reader, start=2):
            try:
                method = row["method"]
                if method not in METHOD_LABELS:
                    raise ValueError("Unknown method.")
                if exclude_linear and method == "linear_search":
                    continue
                row["dataset_size"] = int(row["dataset_size"])
                row["trial"] = int(row["trial"])
                if row["dataset_size"] <= 0 or row["trial"] <= 0:
                    raise ValueError("Dataset size and trial must be positive.")

                for metric in METRICS:
                    row[metric] = float(row[metric])
                    if not math.isfinite(row[metric]) or row[metric] < 0:
                        raise ValueError("Timing must be finite and nonnegative.")

                for column in ["false_positives", "false_negatives", "failed_insertions"]:
                    row[column] = int(row[column])
                    if row[column] < 0:
                        raise ValueError("Error counts must not be negative.")
                if row["false_negatives"] or row["failed_insertions"]:
                    raise ValueError("Fix false negatives or rejected insertions before plotting.")
                if method in ["linear_search", "binary_search", "hash_table"]:
                    if row["false_positives"]:
                        raise ValueError("An exact method returned false positives.")

                key = (method, row["dataset_size"], row["trial"])
                if key in seen_rows:
                    raise ValueError("Duplicate method/size/trial row.")
                seen_rows.add(key)

                run = (row["dataset_size"], row["trial"])
                if run not in methods_per_run:
                    methods_per_run[run] = set()
                methods_per_run[run].add(method)
                results.append(row)
            except (ValueError, TypeError) as error:
                raise ValueError(f"CSV line {line_number}: {error}") from error

    if not results:
        raise ValueError("The CSV has no measurements.")
    for run, methods in methods_per_run.items():
        if methods != expected_methods:
            raise ValueError(f"Incomplete results for size/trial {run}: expected every selected method.")
    return results


def summarize_results(results, method, metric):
    """Return sorted sizes, means, minimums, and maximums for one method/metric.

    Each trial contributes one measurement. Ranges describe observed variation,
    not confidence intervals. With one trial, the range has zero width.
    """
    measurements = {}
    for row in results:
        if row["method"] == method:
            size = row["dataset_size"]
            if size not in measurements:
                measurements[size] = []
            measurements[size].append(row[metric])

    sizes = sorted(measurements)
    means = []
    minimums = []
    maximums = []
    for size in sizes:
        values = measurements[size]
        means.append(statistics.mean(values))
        minimums.append(min(values))
        maximums.append(max(values))
    return sizes, means, minimums, maximums


def create_plot(results, metric, title, y_label, multiplier, output_path):
    """Save a PNG comparing all methods for one timing metric; return nothing.

    multiplier converts seconds to the displayed unit. Use logarithmic axes to
    show different scales; use a linear y-axis if any measurement is zero.
    """
    figure, axes = plt.subplots(figsize=(9, 5.5))
    colors = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]
    markers = ["o", "s", "^", "D", "v"]

    for index, method in enumerate(METHOD_LABELS):
        sizes, means, minimums, maximums = summarize_results(results, method, metric)
        if not sizes:
            continue
        display_means = []
        lower_errors = []
        upper_errors = []
        for point in range(len(sizes)):
            display_means.append(means[point] * multiplier)
            lower_errors.append((means[point] - minimums[point]) * multiplier)
            upper_errors.append((maximums[point] - means[point]) * multiplier)

        axes.errorbar(
            sizes, display_means,
            yerr=[lower_errors, upper_errors],
            label=METHOD_LABELS[method], color=colors[index], marker=markers[index],
            linewidth=1.7, markersize=6, capsize=4,
        )

    axes.set_xscale("log")
    if all(row[metric] > 0 for row in results):
        axes.set_yscale("log")
        scale_note = "Logarithmic axes"
    else:
        scale_note = "Logarithmic x-axis; linear y-axis (zero timings present)"

    sizes = sorted(set(row["dataset_size"] for row in results))
    axes.set_xticks(sizes)
    axes.xaxis.set_major_formatter(FuncFormatter(lambda value, position: f"{value:,.0f}"))
    axes.set_xlabel("Number of usernames")
    axes.set_ylabel(y_label)
    if not any(row["method"] == "linear_search" for row in results):
        title += " (excluding linear search)"
    axes.set_title(title, fontsize=14, pad=14)
    axes.grid(True, which="major", alpha=0.25)
    axes.legend(loc="best", fontsize=9)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    figure.text(0.5, 0.025, "Mean across trials; error bars show min-max. " + scale_note,
                ha="center", fontsize=9)
    figure.tight_layout(rect=[0, 0.055, 1, 1])
    figure.savefig(output_path, dpi=300)
    plt.close(figure)


def main():
    """Read CLI settings and save three charts from one CSV; return nothing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="CSV file; defaults to latest benchmark CSV")
    parser.add_argument("--output-dir", type=Path, help="folder for generated PNG files")
    parser.add_argument("--exclude-linear", action="store_true",
                        help="plot only binary search, hash table, Bloom and Cuckoo filters")
    args = parser.parse_args()

    try:
        if args.input is None:
            args.input = find_latest_csv()
        results = load_results(args.input, exclude_linear=args.exclude_linear)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    if args.output_dir is None:
        folder_name = args.input.stem
        if args.exclude_linear:
            folder_name += "_without_linear"
        args.output_dir = PROJECT_FOLDER / "results" / "plots" / folder_name
    args.output_dir.mkdir(parents=True, exist_ok=True)

    create_plot(results, "build_seconds", "Construction time",
                "Build time (seconds)", 1, args.output_dir / "build_time.png")
    create_plot(results, "present_seconds_per_query", "Lookup time: present usernames",
                "Time per query (microseconds)", 1000000,
                args.output_dir / "present_lookup_time.png")
    create_plot(results, "absent_seconds_per_query", "Lookup time: absent usernames",
                "Time per query (microseconds)", 1000000,
                args.output_dir / "absent_lookup_time.png")

    print("CSV used:", args.input)
    print("Three plots saved to:", args.output_dir)


if __name__ == "__main__":
    main()
