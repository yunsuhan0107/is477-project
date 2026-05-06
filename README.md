# Analyzing the Gap Between Chess Opening Theory and Practical Execution

## Contributors

- Yunsu Han
- Taeseok Kang

---

## Summary

The theory behind chess openings relies upon extended analysis performed by grandmasters, evaluations made by electronic engines, and experimentation by actual players in competition with each other through time. The theory utilizes the idea that the black pieces will have the advantage when both players play perfectly, and the white pieces will also have the same as long as both players play properly, and that the opening is still an equal opportunity for the two players. The data used to build this project is derived from regular people (i.e., amateurs), not from professional players, who frequently make mistakes; deviate from their prepared opening lines; and miscalculate their tactical ability.

To identify the differences between opening theory and how the openings are actually played by amateur and intermediate players, two separate data sets will be used: the Lichess Open Database and the Encyclopedia of Chess Openings (ECO). A fully automated end-to-end process has been put into place for this study, which will download the raw games, clean up and parse the PGN (portable Game Notation) f, match the PGN files against a standard EPC opening classification, and calculate the win percentage for the six rating groups that have been defined: beginners, novices, intermediates, advanced, experts, and masters. There will be two different data sets utilized; the Lichess Database and the Encyclopedia of Chess Openings (ECO).

The January 2017 Lichess dataset was the focus of our analysis. In this analysis we utilize a feature that is available in the data for the first time: engine evaluation annotations that are tagged as %eval (for engine eval). The use of this feature allows us to analyze win rates for different player levels based upon the openings played as well as to measure the accuracy of players after leaving the opening (post-opening) according to their Average Centipawn Loss (ACPL) in relationship to the length of the opening line played. Therefore, it will help with addressing our research question concerning the relationship between longer, more theoretical opening lines and overall poor mid-game performance when players have exited from their openings.

In our study of 10,000 chess games, we identified 84 legitimate openings with enough game counts to allow us to analyze reliably. We found that there are numerous significant differences in both white winning percentages for each opening (35% ≤ white wins and 72% ≥ white wins) and the way certain openings perform at various skill levels. The Owen Defense, in particular, has the largest variance in win rate across all groups (standard deviation = 21.0), indicating that players will have much different results by playing this opening based on their skill level as opposed to some sort of general expectation. In a separate analysis, we also found that there is a significantly negative correlation (r = -0.871, p = 0.001) between the length of ECO lines and ACPL after the opening phase. In other words, players who play longer (more theoretical) ECO lines show greater accuracy during the subsequent midgame than do players who play shorter (<3) ECO lines (the general assumption is that once players go beyond their preparation for ECO openings, they will 'fall off a cliff' in their play).

Based on our analysis of the collected data, it appears that theoretical evaluations do not yield accurate predictions of practical results for non-elite players, and that the empirical win rates should dictate the openings an amateur chess player chooses to play.

---

## Data Profile

### Dataset 1: Lichess Open Database

**Source:** [https://database.lichess.org](https://database.lichess.org)

**License:** Creative Commons CC0 (Public Domain). Lichess provides all of its game data for free and allows users to use, redistribute and modify at their discretion.

**Data format:** PGN (Portable Game Notation) compressed in Zstandard (extension is `.zst`). Every file corresponds to one month of rated standard games played on Lichess.

**Method of accessing data:** Programmatic HTTP download via `acquire_data.py`. Streams the `.zst` file into 8MB chunks and decompresses each chunk without loading the complete decompressed file into memory. Once decompressed, a SHA-256 checksum is calculated and saved alongside the decompressed file for integrity verification purposes.

**Data source:** The one-month period of January 2017 (`lichess_db_standard_rated_2017-01.pgn.zst`) was selected for use in Research Question 3 as it is the first month to contain evaluation information for per move black and white (`%eval`) so that the post-opening accuracy of both players can be assessed. There are no months that have evaluation information from earlier in the data set (e.g. before 2013).

**File Size:** The PGN file generated from decompression will be greater than 50MB in size therefore; there is insufficient space to store compressed PGN files through GitHub. Thus, the full-size decompressed PGN from January 2017 has been uploaded to Illinois Box, and can be accessed at the following link:

> **Box link:** *[Click here](https://uofi.box.com/s/zjrns6ghe7rsm33so5sx2wih6t2kj4k3)*
>
> Once downloaded, save the file to: `data/raw/lichess_2017-01.pgn`. Alternatively, follow the guideline in `run_all.py` to acquire the raw PGN dataset. 

**SHA-256 checksum:** `fb8800b...` (see `data/raw/lichess_2017-01.pgn.sha256`)

**Content:** Each game record contains structured PGN headers including `WhiteElo`, `BlackElo`, `Result`, `TimeControl`, and `Opening`, followed by the full move list. Moves after the opening phase include engine evaluation comments in the format `{ [%eval 0.23] }` or `{ [%eval #3] }` for forced-mate positions.

**Fields extracted:**
| Field | Description |
|---|---|
| `white_elo`, `black_elo` | Integer Elo ratings of both players |
| `result` | Outcome encoded as `white`, `black`, or `draw` |
| `time_control` | Time control string (e.g., `300+0`) |
| `opening_moves` | First ten half-moves extracted from board state |
| `num_opening_moves` | Actual number of opening moves played (≤10) |
| `post_opening_acpl` | Average centipawn loss per move after move 10 |

**Ethical and legal considerations:** The Lichess Database is published under a CC0 license, and there is no PII in the original Lichess data, including usernames (which we also do not store). There are no consent issues because all Lichess user data was voluntarily provided to the public and has been explicitly released by Lichess for use in research.

---

### Dataset 2: Encyclopedia of Chess Openings (ECO) Database

**Source:** [https://github.com/lichess-org/chess-openings](https://github.com/lichess-org/chess-openings)

**License:** Creative Commons CC0 (Public Domain).

**Format:** Five TSV files (`a.tsv` through `e.tsv`) with columns `eco`, `name`, and `pgn`.

**Method of accessing data:** A programmatic HTTP download of the five files using `integrate_data.py` and the `requests` library has been done. The files were downloaded and combined together into a single file located at `data/eco/eco_openings.csv`.

**Size:** 3,690 unique opening entries across all five volumes.

**Fields extracted and derived:**
| Field | Description |
|---|---|
| `eco_code` | ECO classification code (e.g., `B20`) |
| `opening_name` | Full name of the opening variation |
| `moves_clean` | Normalised move string used for prefix matching |
| `eco_line_length` | Number of half-moves in the theoretical line |

**Ethical and legal considerations:** This dataset does not contain any personally identifiable information and is licensed as CC0.

---

### Integration

The two datasets are merged in the file `integrate_data.py` using a longest-prefix matching method. Each game's `opening_moves` string will be compared against the normalized ECO move sequences based on the full 10 move prefixes first, and then shorter prefixes as needed. The use of the board state allows for proper handling of transpositions, as the moves are being taken from board state rather than PGN text.

In addition to adding the `eco_code`, `opening_name`, `eco_line_length`, `average_elo`, and `rating_group` to the game record, this merged dataset uses the average Elo to assign each game to one of six rating groups:

| Group | Elo Range |
|---|---|
| beginner | < 1000 |
| novice | 1000 – 1299 |
| intermediate | 1300 – 1599 |
| advanced | 1600 – 1899 |
| expert | 1900 – 2199 |
| master | ≥ 2200 |

All of the 10,000 cleaned games had a successful match with an ECO opening (100% match rate).

---

## Data Quality

The file `profile_data.py` completed an analysis of data quality and generated a complete report located at `results/lichess_2017-01/data_quality_report.txt`. 

**Completeness:** A total of 10,110 raw games were read, and of those 110 (1.1%) of the games were omitted due to missing Elo ratings or due to results that could not be recognised. The 10,000 game set used for analysis contained no missing values for the key data fields. The `post_opening_acpl` column represents an intentional sparsity, as of the 10,000 games only 1,146 (11.5%) contained eval annotated moves. Thus, it is a characteristic of the early 2017 dataset structure, not an indicator of data quality.

**Validity:** Elo ratings fit within the plausible range for Lichess (400-3500). All results fall within one of the three valid result categories. ECO line length is generally between 1 and 10 half moves (mean = 3.95, std = 2.19), which was expected.

**Consistency:** Transpositions that occurred during the extraction of moves based on the board state resulted in identical opening moves strings being extracted. 100% of the ECO matched to known theoretical lines verifying that all extracted sequences correspond to known theoretical lines.

**Distribution:** The distribution of players by rating groups is skewed toward intermediate and advanced chess players (intermediate = 2,802; advanced = 4,226) typical of the actual user base of Lichess. The distributions of players at the two extremes of the rating spectrum (beginning = 28; master = 340) are small, limiting the ability to obtain sufficient statistical power.

**Duplicates:** There were no duplicate rows contained within either the cleaned or integrated databases.

---

## Data Cleaning

The following preprocessing steps were performed on the raw PGN files we've collected before performing any analysis of the data in `clean_data.py`.

**Filter — Missing Elo ratings:** We removed any games that had either `WhiteElo` or `BlackElo` set to `"?"`, which were almost all of the 110 games we removed from the data. Most of the games we removed were between players who were not rated or were playing anonymously.

**Filter — Unrecognised results:** We removed any game that did not have a result of `1-0` (white wins), `0-1` (black wins), or `1/2-1/2` (draw). This included any game where the result was `*` (ongoing).

**Filter — Abandoned games:** We removed any game where there were fewer than five half-moves, since they would not provide any useful opening data.

**Extraction — Board-state-based move parsing:** Instead of extracting the actual opening moves as raw PGN text, we used the `python-chess` library to replay the game from the starting position and generate a SAN string for each move using the state of the board. This allows us to correctly handle transpositions — one of the significant problems we identified in our project plan and which this method solves.

**Extraction — Post-opening ACPL:** We used a regular expression that matches the Lichess engine evaluation comment format of `[%eval N]` to parse engine evaluation comments and to represent mate scores (i.e., `#N`) as ±1000 centipawns. We computed the loss in centipawns per move as the reduction in evaluation based on the perspective of the player making the move; however, we only included moves that were made after the first ten half-moves and required at least two evaluation comments after the opening in order to produce an evaluation.

**Result encoding:** We mapped the PGN result strings of `1-0`, `0-1`, and `1/2-1/2` to `white`, `black`, and `draw`, respectively.

---