# Login Checker — COSC 520 Assignment 1

Compare five manually implemented username-membership methods: linear search, binary search with merge sort, a hash table with linear probing, a Bloom filter, and a Cuckoo filter. The benchmark measures construction time and lookup time for present and absent usernames separately.

- Repository: https://github.com/ImamZulkarnain/Login-Checker
- Downloadable datasets: https://drive.google.com/drive/folders/1WTZ6HO4-pudKRQyk-faQq7lXppp96cCN?usp=sharing

## 1. Get the project and install dependencies

Install Python 3 and Git first. Use a virtual environment to keep dependencies separate from other projects. Python 3.12 or newer is a suitable starting point; the original benchmark's exact Python version and package versions are not recorded in the saved CSVs.

Clone the repository, then work from the folder containing `main.py`:

```bash
git clone https://github.com/ImamZulkarnain/Login-Checker.git
cd Login-Checker
```

Alternatively, download the repository ZIP from GitHub, extract it, and open a terminal in the extracted folder.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If `py` is unavailable but `python --version` works, use `python -m venv .venv`. If PowerShell blocks activation, activation is optional: replace `python` in every subsequent command with `.\.venv\Scripts\python.exe`, including the dependency installation command.

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The dependencies are `tqdm` for progress, `mmh3` for hash primitives inside the filters, and `matplotlib` for plots. Membership structures and search algorithms are implemented in `methods/`.

Keep this terminal in the project root for all commands below.

## 2. Run the unit tests

No dataset download is needed for the tests:

```bash
python -m unittest discover -s tests -v
```

A successful run ends with `OK`. The reviewed test suite contains 71 tests covering all five methods, sorting, collisions, resizing, filter behavior, Cuckoo rollback, and benchmark accounting.

## 3. Quick end-to-end run (no large download)

Generate 10,000 usernames, run all five methods at two sizes with two trials, and create the plots:

```bash
python -m scripts.generate_usernames --count 10000 --seed 42 --output data/peer_demo.txt
python main.py --dataset data/peer_demo.txt --sizes 1000 10000 --queries 50 --trials 2 --seed 42 --false-positive-rate 0.01 --output results/peer_demo.csv
python -m scripts.plot --input results/peer_demo.csv
python -m scripts.plot --input results/peer_demo.csv --exclude-linear
```

Expected outputs:

- `data/peer_demo.txt`: 10,000 unique usernames, one per line.
- `results/peer_demo.csv`: 20 measurement rows plus a header (5 methods × 2 sizes × 2 trials).
- `results/plots/peer_demo/`: `build_time.png`, `present_lookup_time.png`, and `absent_lookup_time.png`.
- `results/plots/peer_demo_without_linear/`: the same three filenames, showing only the four faster methods.

Plots are saved as PNG files; no graphical window is required.

**Rerunning:** the generator replaces an existing dataset at its output path. The benchmark refuses to overwrite a CSV: choose a new `--output` filename and use that filename when plotting. Plotting again replaces the PNGs for that CSV. Always give the generator an explicit output path so it does not overwrite `data/usernames.txt`.

## 4. Run the report's benchmark workload

The report uses these settings:

| Setting | Value |
| --- | --- |
| Dataset sizes | 10,000; 100,000; 1,000,000; 10,000,000 |
| Present queries per size and trial | 1,000 |
| Absent queries per size and trial | 1,000 |
| Trials | 2 |
| Base query seed | 42 (trial seeds 42 and 43) |
| Target filter false-positive probability | 0.01 |
| Cuckoo slots per bucket / relocation limit | 4 / 500 |

Download the original dataset from the link above and place the extracted text file in `data/`. If using `usernames_100M.txt`, run:

```bash
python main.py --dataset data/usernames_100M.txt --sizes 10000 100000 1000000 10000000 --queries 1000 --trials 2 --seed 42 --false-positive-rate 0.01 --output results/peer_report.csv
python -m scripts.plot --input results/peer_report.csv
python -m scripts.plot --input results/peer_report.csv --exclude-linear
```

If the downloaded file has another name, change `--dataset` accordingly. It must contain at least ten million unique, nonempty usernames. The program reads only the largest requested prefix and uses smaller prefixes for smaller sizes. Do not reorder or edit the original data when reproducing an experiment.

The full workload produces 40 measurement rows. Allow substantially more time and RAM than for the quick run: Python objects, validation sets, sorting, and filter buckets occupy more memory than the text file itself. If memory is insufficient, remove `10000000` from `--sizes` and document the smaller maximum; that is a partial replication of the report workload.

For a new synthetic experiment without downloading the original data, generate a separate dataset:

```bash
python -m scripts.generate_usernames --count 10000000 --seed 42 --output data/peer_generated_10M.txt
```

Then use that path with the full benchmark command. Generation retains the usernames and a uniqueness set in memory. This recreates the workload design, but an independently generated file is not established as identical to the report's dataset: the historical dataset filename/hash and generation seed are not stored in the results CSV.

## 5. Recreate plots from the supplied results

`results/combined.csv` contains the report's five-method measurements. Some copies contain trailing rows consisting only of commas, which the strict plotter rejects. Preserve the original and create a copy that drops only completely empty records:

```bash
python -c "import csv; from pathlib import Path; source=Path('results/combined.csv'); rows=list(csv.reader(source.open(newline='', encoding='utf-8-sig'))); target=Path('results/combined_clean.csv'); f=target.open('x', newline='', encoding='utf-8'); csv.writer(f).writerows(row for row in rows if any(cell.strip() for cell in row)); f.close()"
python -m scripts.plot --input results/combined_clean.csv
python -m scripts.plot --input results/combined_clean.csv --exclude-linear
```

The cleaning command intentionally refuses to overwrite an existing `combined_clean.csv`. If it already exists from a previous run, use that file directly. The separately supplied four-method file can be plotted with:

```bash
python -m scripts.plot --input "results/combined - linear.csv" --exclude-linear
```

Use `--input` explicitly: automatic selection searches only for `benchmark_*.csv`, not `combined.csv`. `--exclude-linear` changes the plots only; it does not skip linear search during benchmarking.

## 6. Interpret and reproduce the measurements

Each CSV row represents one method, dataset size, and trial. The nine columns are:

```text
method,dataset_size,trial,build_seconds,present_seconds_per_query,absent_seconds_per_query,false_positives,false_negatives,failed_insertions
```

- All timing columns are in seconds. Lookup columns are averages per query; plots convert lookup times to microseconds.
- Construction includes list copying, merge sorting, table allocation/resizing, or filter insertion as appropriate.
- File loading, query generation, correctness counting, and CSV writing are excluded from timing. Lookup timing includes Python calls, loops, and answer collection.
- Every method receives the same queries within a trial. Method order is shuffled reproducibly; three queries of each category warm up lookup first.
- Plot points are arithmetic means across trials. Error bars show minimum and maximum, not confidence intervals.
- Exact methods should have zero false positives, false negatives, and failed insertions. Filters can return false positives. For the report workload, divide a row's false-positive count by 1,000 to obtain its observed rate.
- Rejected Cuckoo insertions are recorded separately and excluded from false-negative counts. A nonzero `failed_insertions` count means the filter did not store the complete dataset. The plotter rejects such results.

Identical timings are not expected across machines or repeated runs. Use the same dataset, code revision, settings, Python version, and dependency versions to make comparisons meaningful. The requirements file specifies version ranges rather than a historical lockfile.



## Project layout

```text
main.py                     Benchmark command-line interface and CSV output
requirements.txt            Dependency version ranges
methods/                    Five membership/search implementations
benchmarking/               Dataset loading, query generation, and timing
scripts/generate_usernames.py  Reproducible synthetic dataset generator
scripts/plot.py              CSV validation and plot generation
tests/                      Unit tests and test instructions
data/                       Downloaded or locally generated datasets
results/                    Saved measurements and plots
```
