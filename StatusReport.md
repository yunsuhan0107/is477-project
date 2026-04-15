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

A Python program was created, which was a piece of software that allowed downloading the monthly archives of Lichess PGNs using an algorithm. The system was able to stream these HTTP downloads in conjunction with Zstandard (.zst) decompression at the same time by employing the Zstandard algorithm library to parse out the PGN data in 8 MB chunks without having to hold the entire (~30 GB) file in RAM. The code also included the ability to have a live progress report and to validate the checksum with MD5 before proceeding. For testing purposes, the data being used was the January 2013 Lichess data set, which is much smaller than the current monthly archives and has an identical structural format, allowing full processing of the pipeline to be verified prior to scaling the data out. You can obtain the data using:

```bash
python acquire_data.py --year 2013 --month 01 --outdir data/raw --checksum
```

---

### Task 3: Data Cleaning

**Due Date:** March 24, 2026 | **Status:** Complete

In order to create an easily maintainable structured CSV, I developed a Python script called clean_data.py to parse the raw PGN. The way this script works is as follows: It reads the games using the python library chess to prevent memory overload, only reading one game at the time until all games are read from the file. The script has the following filters:

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

---

## 4. Challenges and Issues

### Challenge 1: Large File Sizes and Memory Management

Monthly PGN Files From Lichess.com are very large; they average 30 GB (compressed) in size. To handle this problem; acquire_data.py uses streaming HTTP(s) downloads of the PGN with chunked Zstandard decompression, and clean_data.py uses python-chess to read each PGN (game-by-game). Neither script loads the entire file into memory. We will also use data from January 2013 (which is up to an order of magnitude smaller than any dataset used in acquiring the most current datasets available for the project) until just before development starts to reduce risk when developing and create the most accurate model possible.

### Challenge 2: Transposition Handling in Opening Identification

The various combinations of moves that can lead to an identical set of pieces on the chessboard indicate that using only a simple string representation of moves in PGN movement text will not accurately identify which opening has been played. This problem was solved in clean_data.py by utilizing the library python-chess to identify the moves used for the creation of a board position based on the current state of the board instead of on the text of moves. This allows the board's tracking of position to be independent of ordering of the moves, resolving the transposition issue noted in the project plan.

---

## 5. Individual Contributions

### Yunsu Han

I took care of establishing & maintaining our GitHub repo & providing the first version of ProjectPlan.md. For the data pipeline component, I created the acquire_data.py file (Task 2) to allow for live downloading as well as performing Zstandard decompression on Lichess PGN files as well as the clean_data.py file (Task 3) to allow for the parsing, filtering, & extracting structured fields from raw PGN data using python-chess. I also identified the monthly PGN dataset from January 2013 as a good choice for test datasets during the development of our data pipeline. This milestone reflects the temporary and permanent Task Update sections for Tasks 1, 2, 3, 5 and 7, along with the revised Timeline and Challenges sections of this report.

### Taeseok Kang


