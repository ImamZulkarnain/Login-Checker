# Login Checker — COSC 520 Assignment 1

Compare five manually implemented username-membership methods: linear search, binary search with merge sort, a hash table with linear probing, a Bloom filter, and a Cuckoo filter. The benchmark measures construction time and lookup time for present and absent usernames separately.

- Repository: https://github.com/ImamZulkarnain/Login-Checker
- Downloadable datasets: https://drive.google.com/drive/folders/1WTZ6HO4-pudKRQyk-faQq7lXppp96cCN?usp=sharing

## 1. Get the project and install dependencies

Install Anaconda or Miniconda, and Git if cloning the repository. Use a Conda environment to keep dependencies separate from other projects.

Clone the repository, then work from the folder containing `main.py`:

```bash
git clone https://github.com/ImamZulkarnain/Login-Checker.git
cd Login-Checker
```

Alternatively, download the repository ZIP from GitHub, extract it, and open a terminal in the extracted folder.

### Conda setup (Windows, macOS, and Linux)

On Windows, open Anaconda Prompt. On macOS or Linux, open a terminal where `conda` is available. From the project folder, run these commands one at a time:

```bash
conda create -n login-checker python=3.12 pip
conda activate login-checker
python -m pip install -r requirements.txt
```

The dependencies are `tqdm` for progress, `mmh3` for hash primitives inside the filters, and `matplotlib` for plots. Membership structures and search algorithms are implemented in `methods/`.

Keep this terminal in the project root for all commands below.

## 2. Run the unit tests

No dataset download is needed for the tests:

```bash
python -m unittest discover -s tests -v
```

A successful run ends with `OK`. The reviewed test suite contains 71 tests covering all five methods.

## 3. Run a small experiment without downloading a large dataset

Generate 10,000 usernames, run all five methods at two sizes with two trials, and create the plots:

```bash
python -m scripts.generate_usernames --count 10000 --seed 42 --output data/usernames_10K.txt
python main.py --dataset data/usernames_10K.txt --sizes 1000 10000 --queries 50 --trials 2 --seed 42 --false-positive-rate 0.01 --output results/usernames_10K.csv
python -m scripts.plot --input results/usernames_10K.csv
python -m scripts.plot --input results/usernames_10K.csv --exclude-linear
```

Expected outputs:

- `data/usernames_10K.txt`: 10,000 unique usernames, one per line.
- `results/usernames_10K.csv`: 20 measurement rows plus a header (5 methods × 2 sizes × 2 trials).
- `results/plots/usernames_10K/`: `build_time.png`, `present_lookup_time.png`, and `absent_lookup_time.png`.
- `results/plots/usernames_10K_without_linear/`: the same three filenames, showing four methods excluding linear for closer comparison.


**Rerunning:** the generator replaces an existing dataset at its output path. The benchmark doesn't overwrite an existing CSV: choose a new `--output` filename and use that filename when plotting. Always give the generator an explicit output path so it does not overwrite `data/usernames.txt`.

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

Download the original dataset from the link above and place the extracted text file in `data/`. Then run:

```bash
python main.py --dataset data/usernames_100M.txt --sizes 10000 100000 1000000 10000000 --queries 1000 --trials 2 --seed 42 --false-positive-rate 0.01 --output results/peer_report.csv
python -m scripts.plot --input results/peer_report.csv
python -m scripts.plot --input results/peer_report.csv --exclude-linear
```

The program reads only the largest requested prefix and uses smaller prefixes for smaller sizes. Do not reorder or edit the original data when reproducing the experiment.

The full workload produces 40 measurement rows. Allow substantially more time and RAM than for the quick run.

For a new synthetic experiment without downloading the original data, generate a separate dataset:

```bash
python -m scripts.generate_usernames --count 10000000 --seed 42 --output data/newly_generated_10M.txt
```

Then use that path with the full benchmark command.


### If in any case your system generates csv files with trailing rows of only commas, preserve the original and create a copy that drops only completely empty records:

```bash
python -c "import csv; from pathlib import Path; source=Path('results/peer_report.csv'); rows=list(csv.reader(source.open(newline='', encoding='utf-8-sig'))); target=Path('results/peer_report_clean.csv'); f=target.open('x', newline='', encoding='utf-8'); csv.writer(f).writerows(row for row in rows if any(cell.strip() for cell in row)); f.close()"
```

Then use that cleaned file to plot as before.


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
