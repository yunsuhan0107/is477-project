# Status Report — IS477 Final Project

**Team Members:** Yunsu Han, Taeseok Kang  
**Repository:** https://github.com/yunsuhan0107/is477-project  
**Report Date:** April 14, 2026

---

## 1. Task Status Updates

### Task 1: Project Plan Formulation

**Due Date:** March 14, 2026 | **Status:** Complete

The project plan was finalized and submitted as [`ProjectPlan.md`](https://github.com/yunsuhan0107/is477-project/blob/main/ProjectPlan.md) in the repository. It outlines the full scope of the project, including research questions, dataset descriptions, the team's task division, timeline, and identified constraints. A `project-plan` release was also tagged and published on GitHub.

---

### Task 2: Data Acquisition

**Due Date:** March 17, 2026 | **Status:** Complete

A Python program [`acquire_data.py`](https://github.com/yunsuhan0107/is477-project/blob/main/acquire_data.py) was created, which was a piece of software that allowed downloading the monthly archives of Lichess PGNs using an algorithm. The system was able to stream these HTTP downloads in conjunction with Zstandard (.zst) decompression at the same time by employing the Zstandard algorithm library to parse out the PGN data in 8 MB chunks without having to hold the entire (~30 GB) file in RAM. The code also included the ability to have a live progress report and to validate the checksum with MD5 before proceeding. For testing purposes, the data being used was the January 2013 Lichess data set, which is much smaller than the current monthly archives and has an identical structural format, allowing full processing of the pipeline to be verified prior to scaling the data out. You can obtain the data using:

```bash
python acquire_data.py --year 2013 --month 01 --outdir data/raw --checksum
```

---

### Task 3: Data Cleaning

**Due Date:** March 24, 2026 | **Status:** Complete

In order to create an easily maintainable structured CSV, I developed a Python script [`clean_data.py`](https://github.com/yunsuhan0107/is477-project/blob/main/clean_data.py) to parse the raw PGN. The way this script works is as follows: It reads the games using the python library chess to prevent memory overload, only reading one game at the time until all games are read from the file. The script has the following filters:

- Remove any game with no Elo rating
- Remove any game that has an unrecognized or incomplete result
- Remove any abandoned games with less than five half moves

For each valid game, I used the python library chess to get the first ten moves based on the board position (or the state of the board) rather than parse each move using a raw string. This was one of the biggest challenges noted in the project plan, as transpositions (moving to a given state via multiple sequences of moves) need to be accounted as valid movements. The user has the capability to limit the number of games returned from the process, by using the `--max-games` flag.

Output columns: `white_elo`, `black_elo`, `result`, `time_control`, `opening_moves`

```bash
python clean_data.py --input data/raw/lichess_2013-01.pgn \
                     --output data/clean/lichess_2013-01.csv \
                     --max-games 10000
```

---

### Task 4: Data Integration

**Due Date:** March 29, 2026 | **Status:** Complete

The script [`integrate_data.py`](https://github.com/yunsuhan0107/is477-project/blob/main/integrate_data.py) is responsible for consolidating the standardized chess match data with the ECO (Encyclopedia of Chess Openings) database. The application downloads and stores copies of all five of the ECO TSV files available in the official lichess-org/chess-openings project on GitHub. The matching of openings works by applying the longest-prefix approach. That is, for each game, the application attempts to match as long a prefix of its opening moves against ECO entries as possible. Therefore, matches that diverge from theory at an early point receive the most specific opening classification possible.

The application also classifies the average rating of both players in each game based on their average Elo, assigning each player to one of the following rating groups: beginner, novice, intermediate, advanced, expert or master. This allows us to conduct cross-rating analysis as per our research questions.

Output columns: `white_elo`, `black_elo`, `result`, `time_control`, `opening_moves`, `eco_code`, `opening_name`, `avg_elo`, `rating_group`

```bash
python integrate_data.py --games data/clean/lichess_2013-01.csv \
                         --output data/integrated/lichess_2013-01_integrated.csv
```

---

### Task 5: Interim Status Report

**Due Date:** March 31, 2026 | **Status:** In Progress (this document)

This is Task 5 - Status Report, which was due originally on March 31 2026 and is late. This report has been co-written by both authors via their individual contributions, as required, to the repository.

---

### Task 6: Statistical Analysis

**Due Date:** April 14, 2026 | **Status:** Not Yet Started

We have not yet started statistical analysis. In this task, we will be calculating opening win rates by rating group; using probability distributions to measure variance; and producing charts (i.e., bar charts) to visualize the win rate for each rating group and the overall win rate distribution across rating groups. Since we have completed Tasks 2-4 and have access to the integrated dataset, this task will be our next priority. We are on schedule to finish this task by April 28, 2026.

---

### Task 7: Workflow Automation

**Due Date:** April 21, 2026 | **Status:** Not Yet Started

As of this date, none of the Snakemake workflows have been developed. This project will take the three programs listed, acquire_data.py, clean_data.py, and integrate_data.py, and combine them into one unified, reproducible workflow using Snakemake that includes clear rules for determining how they interact and managing dependencies between the three. Our goal is to complete this project by April 30, 2026.

---

### Task 8: Final Project Submission

**Due Date:** May 3, 2026 | **Status:** Not Yet Started

The completed submitted (final) product will be a complete written report, along with a reproducible Snakemake pipeline, machine-readable metadata (in DCAT or DataCite format), and a GitHub release. The original day of submission is still May 3, 2026 as the targeted due date.

---

## 2. Updated Timeline

| Task | Description | Owner | Original Due Date | Revised Due Date | Status |
|------|-------------|-------|-------------------|------------------|--------|
| 1 | Project Plan Formulation | Yunsu & Taeseok | March 14, 2026 | — | Complete |
| 2 | Data Acquisition | Yunsu | March 17, 2026 | April 14, 2026 | Complete |
| 3 | Data Cleaning | Yunsu | March 24, 2026 | April 14, 2026 | Complete |
| 4 | Data Integration | Taeseok | March 29, 2026 | April 14, 2026 | Complete |
| 5 | Interim Status Report | Yunsu & Taeseok | March 31, 2026 | April 14, 2026 | In Progress |
| 6 | Statistical Analysis | Taeseok | April 14, 2026 | April 28, 2026 | Not Started |
| 7 | Workflow Automation | Yunsu | April 21, 2026 | April 30, 2026 | Not Started |
| 8 | Final Project Submission | Yunsu & Taeseok | May 3, 2026 | May 3, 2026 | Not Started |

---

## 3. Changes to the Project Plan

The expanse and direction of the project have not changed, as it is a study of chess opening win rates for ladder-graded players from the open Lichess database and ECO database.

The most significant deviation from the original timeline was the delay in completing Tasks 2-4, which are now all completed allowing the overall project to move immediately into desired statistical analysis.

A methodological adjustment made during the course was that to obtain opening details, a focus on raw chess moves in PGN (Portable Game Notation) was changed to a process of extracting from the board state using Python chess. This process provided solutions to transposition issues; as an example, these were stated as areas of concern in the project approach. The new process allows for a better opening classification of moves than would be achieved through raw text comparison.

In addition to making progress with implementation, we are continuing to develop; however, we are utilizing the Lichess database from January 2013 as a test corpus, so that we can have a verification of the pipeline end-to-end before increasing sample size to a current month and larger data set to complete analysis.

No specific feedback was received for Milestone 2, so no changes to the project plan were made in response to feedback.

---

## 4. Challenges and Issues

### Challenge 1: Large File Sizes and Memory Management

Monthly PGN Files From Lichess.com are very large; they average 30 GB (compressed) in size. To handle this problem; acquire_data.py uses streaming HTTP(s) downloads of the PGN with chunked Zstandard decompression, and clean_data.py uses python-chess to read each PGN (game-by-game). Neither script loads the entire file into memory. We will also use data from January 2013 (which is up to an order of magnitude smaller than any dataset used in acquiring the most current datasets available for the project) until just before development starts to reduce risk when developing and create the most accurate model possible.

### Challenge 2: Transposition Handling in Opening Identification

The various combinations of moves that can lead to an identical set of pieces on the chessboard indicate that using only a simple string representation of moves in PGN movement text will not accurately identify which opening has been played. This problem was solved in clean_data.py by utilizing the library python-chess to identify the moves used for the creation of a board position based on the current state of the board instead of on the text of moves. This allows the board's tracking of position to be independent of ordering of the moves, resolving the transposition issue noted in the project plan.

### Challenge 3: Overall Schedule Delay

Tasks 2, 3, and 4 were all completed later than their original completion date and the completion of this report, which is Task 5, is also late. We do however have all of the data pipeline scripts fully developed and functioning now, as well as a clear plan for the final submission deadline and not all of the scripts are ready for statistical analysis (Task 6) yet.

### Challenge 4: Machine-Readable Metadata Standards

There's still an information gap between DCAT & DataCite metadata formats plus addressing this will be done during the last part of Task 8 with the help of reviewing every course material and the related documentation.

---

## 5. Individual Contributions

### Yunsu Han

I took care of establishing & maintaining our GitHub repo & providing the first version of ProjectPlan.md. For the data pipeline component, I created the acquire_data.py file (Task 2) to allow for live downloading as well as performing Zstandard decompression on Lichess PGN files as well as the clean_data.py file (Task 3) to allow for the parsing, filtering, & extracting structured fields from raw PGN data using python-chess. I also identified the monthly PGN dataset from January 2013 as a good choice for test datasets during the development of our data pipeline. This milestone reflects the temporary and permanent Task Update sections for Tasks 1, 2, 3, 5 and 7, along with the revised Timeline and Challenges sections of this report.

### Taeseok Kang

I was involved in the planning meetings surrounding this project and responsible for both the design of the relational database schema and the method used to integrate data. I also created integrate_data.py (Task 4), which will download the ECO opening database, apply the longest-prefix opening match algorithm to the cleaned-game dataset, and label each game's rating group to facilitate cross-rating analysis. Additionally, I contributed to writing the update sections for Tasks 4 and 6 of this report at this milestone.
