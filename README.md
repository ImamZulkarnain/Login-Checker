<<<<<<< HEAD
# Username search benchmarks

Install dependencies from the project folder:

```bash
python -m pip install -r requirements.txt
```

Run the default experiment (10,000 and 100,000 usernames from data/usernames_100M.txt;
100 present and 100 absent queries per size; three trials):

```bash
python main.py
```

Run a shorter experiment:

```bash
python main.py --sizes 1000 10000 --queries 50 --trials 2
```

Select a dataset and output file:

```bash
python main.py --dataset data/usernames_1M.txt --sizes 10000 100000 --queries 100 --trials 3 --output results/my_run.csv
```

Output files must be new. By default, a timestamped CSV is saved in results/.
Only the largest requested prefix of the dataset is loaded. Smaller sizes use
prefixes of that same data. Duplicate usernames and insufficient data are errors.
The loader and query preparation use temporary sets for validation, not for
implementing or timing any of the five search methods.

## Measurements

Each row represents one method, dataset size, and trial. All five methods get
the same present and absent queries within a trial. Seeds are repeatable, and
method order is shuffled reproducibly. Three queries from each category warm
up lookup before timing. Present lookups are timed before absent lookups.

Build time includes copying for linear search, manual merge sort for binary
search, and allocation/insertion for the three structures. Hash-table resizing
is included. Cuckoo failure tracking is also included. File loading, query
preparation, correctness counting, printing, and CSV writing are excluded.
Lookup times include the loop, function calls, and collection of the answers.
Only one built structure is retained at a time, but the input list remains in
memory. Garbage collection runs before each method, outside its timer.

Present queries are sampled without replacement. Absent queries are generated
using the same length/character rules as the dataset generator, then checked
against the selected dataset. They are absent from that experiment's dataset,
not necessarily from every larger file. The default 100 absent queries are
suitable for a quick runtime experiment, not a precise false-positive estimate.
Increase --queries for more precise estimates, at the cost of slower linear search.

The simplified CSV saves nine columns: method, dataset_size, trial,
build_seconds, present_seconds_per_query, absent_seconds_per_query,
false_positives, false_negatives, and failed_insertions. Record the command,
seed, query count, filter target rate, and machine details with your experiment
notes because these settings are not saved in this CSV.

false_negatives counts missed queries for successfully inserted keys. Rejected
Cuckoo keys are excluded from that count. Always inspect failed_insertions:
a partially built Cuckoo filter is not a successful full-dataset build.

The benchmark does not measure memory. HashTable uses a Python hash
implementation; the filters use mmh3, which affects practical timing comparisons.
Use python -m scripts.plot to generate charts from the saved measurements.

The runner rejects Bloom configurations above 2**32 bits and Cuckoo fingerprint
widths above 32 bits. These limits reflect the current implementations.

## Tests

```bash
python -m unittest discover -s tests -v
```

The methods/ folder contains algorithms; tests/ contains correctness tests.
The generator can create another dataset with a chosen count, seed, and path:

```bash
python -m scripts.generate_usernames --count 1000000 --seed 42 --output data/new_usernames.txt
```

Generation holds the usernames in memory and replaces an existing output file.

## Plot results

Install the updated dependencies, then plot the most recently modified
benchmark_*.csv file in results/:

```bash
python -m pip install -r requirements.txt
python -m scripts.plot
```

Select a specific experiment:

```bash
python -m scripts.plot --input results/my_run.csv
```

Three 300-DPI PNG files are saved under results/plots/<CSV filename>/:
construction time in seconds, and present/absent lookup time in microseconds
per query. Each point is the arithmetic mean across trials; error bars show
minimum and maximum, not confidence intervals. Axes are logarithmic unless a
zero timing requires a linear time axis. Repeating the command replaces the
three plots for that CSV. --output-dir selects a different output folder.

The plotter rejects incomplete size/trial groups, duplicate rows, failed
insertions, false negatives, and false positives from exact methods. Filter
false positives are permitted. No false-positive rate chart is produced because
the simplified CSV does not record the query count needed to calculate rates.


## Project structure

- main.py: command-line settings, progress bars, experiment loops, and CSV output.
- benchmarking/data.py: load usernames and prepare present/absent queries.
- benchmarking/runners.py: construction timing, search timing, and correctness counts.
- methods/: the five algorithm implementations.
- scripts/generate_usernames.py: dataset generation.
- scripts/plot.py: plots from benchmark CSV files.
- tests/: unit tests.
- data/: datasets.
- results/: CSV measurements and generated plots.

Run commands from the project root. Use python -m scripts.generate_usernames
and python -m scripts.plot so Python resolves package imports correctly.
Default dataset and result locations are relative to the project folder;
explicit relative paths passed on the command line use the working directory.

Plot all methods except linear search:

```bash
python -m scripts.plot --input results/combined.csv --exclude-linear
```

This accepts a full CSV or one with linear-search rows removed. The other four
methods must be present for each size/trial. Default output goes into
results/plots/combined_without_linear/ to preserve the five-method plots.
=======
# Login-Checker
>>>>>>> 97aa2070f1fa649ee26f6df6290a4c3b3dbc29ad
