# Project Plan: Analyzing the Gap Between Chess Opening Theory and Practical Execution

## Overview
This project aims to analyze the relationship between deep chess opening theory and practical execution of players online. Our goal is to perform a thorough statistical analysis of win probabilities of complicated opening variations and actual win rates of players in mid-level human play, which is about 1500 Elo. In order to execute this project, we will acquire millions of raw chess games from the Lichess open database and link them to a database that contains fundamental information about opening theories. We aim to build an automated Python workflow, which allows us to identify which openings translate into victories for amateur players and which ones have complexities that can lead to critical blunders. 

In addition to focusing on intermediate players, we also want to take advantage of the fact that the Lichess dataset contains games from a very wide range of player ratings, from beginners to professional-level players. Because of this, we want to expand the project beyond a single Elo group and compare the win rates of openings across rating categories. This will allow us to examine whether certain openings are more beginner-friendly while others only perform well when executed by stronger players with deeper theoretical knowledge. For example, an opening that is considered highly accurate or theoretically strong at the grandmaster level may not actually be effective for beginner or lower-rated players if it requires precise move orders or advanced positional understanding. By comparing opening performance across rating groups, we hope to identify which openings are practical, accessible, and successful for beginners and intermediate players, and which openings may be too sharp or too complex to produce consistent results.

More broadly, this project is about understanding the gap between theory and practice. Chess theory often assumes best play, but online games between non-elite players are full of inaccuracies, missed tactics, and deviations from preparation. Therefore, a theoretically advantageous opening may not always be the most effective choice in real play. Our project seeks to measure that difference in a data-driven way and provide evidence for which openings work best not only in theory, but also in practice at different levels of play.

## Team
* **Yunsu Han:** Primary responsibilities are managing the Git repository, building Python scripts to parse and clean the complex PGN text files into a nicely structured database, extracting initial moves from the cleaned database, and handling an automated workflow using Snakemake.
* **Taeseok Kang:** Primary responsibilities are designing a relational database schema for opening codes (ECO), integrating two databases using Python and Pandas, applying appropriate probability distributions and variance testing to the win rates, and drafting a machine-readable descriptive metadata. 

## Research Questions
Our project aims to respond to the following research questions:
* Do chess openings classified mathematically “advantageous for white” in grandmaster level underperform when executed by amateur chess players (around 1500 Elo)?
* Which specific opening variations display the highest variance in win rates between professional chess players and amateur players? 
* Does the length of theoretical openings (how many moves are in the lines) correlate with the accuracy of players once they are out of preparation and within the midgame? 
* Since the Lichess dataset includes players from beginner rating to professional rating, how do opening win rates differ across rating groups such as beginner, intermediate, and advanced players?
* Which openings can be considered the most beginner-friendly, meaning they are easier to execute and lead to stronger or more stable win rates for lower-rated players?
* Are some openings theoretically strong but practically too complex for beginners, causing them to underperform relative to simpler but more intuitive openings?

These research questions will help us move beyond the usual assumption that the strongest theoretical openings are always the best practical choices. Instead, we want to investigate whether opening success depends heavily on the rating and skill level of the player using it.

## Datasets
Our project employs the following two datasets:
* **[Lichess Open Database](https://database.lichess.org):** This dataset contains billions of raw chess games played by online players on Lichess, one of the most renowned online chess platforms. It includes metadata, such as player ratings, time played, and final results, with a standardized formatting option in chess called PGN. For each move, it shows the evaluation of the machine of how good or bad each move is for each player. We will programmatically acquire the dataset using HTTPS requests from the Lichess open data portal.
* **[Encyclopedia of Chess Openings (ECO) Database](https://github.com/Destaq/chess-graph/blob/master/elo_reading/openings_sheet.csv):** This is a rather simple dataset that contains basic information about standardized chess openings with their move orders. This was created by a user on GitHub, which might be complemented in the later stages of the project when not enough information is available. It contains metadata such as ECO, name, and moves. 

These datasets will be integrated by extracting the first five to ten moves from the Lichess open dataset PGN strings, and using the ECO dataset to match and find which opening the players were playing. The cleaned dataset will later be integrated with various information from the Lichess dataset, such as player ratings and win rates. 

## Timeline

| Task | Description | Due Date | Owner |
| :--- | :--- | :--- | :--- |
| **1: Project Plan Formulation** | Finalize and submit `ProjectPlan.md`. | Mar 14, 2026 | Yunsu & Taeseok |
| **2: Data Acquisition** | Write Python scripts to systematically download Lichess PGN files with a streamlined workflow. | Mar 17, 2026 | Yunsu |
| **3: Data Cleaning** | Develop text-parsing algorithms to clean the PGN files, handle abandoned games (done within 5 moves), and standardize string formats. | Mar 24, 2026 | Yunsu |
| **4: Data Integration** | Utilize Pandas to merge the cleaned opening sequence with the ECO database. | Mar 29, 2026 | Taeseok |
| **5: Interim Status Report** | Submit a 1000-word report with updates and workflow challenges. | Mar 31, 2026 | Yunsu & Taeseok |
| **6: Statistical Analysis** | Apply probability distribution to calculate win rate variance and draft visualizations. | Apr 14, 2026 | Taeseok |
| **7: Workflow Automation** | Compile scripts into a cohesive pipeline using Snakemake. | Apr 21, 2026 | Yunsu |
| **8: Final Project Submission** | Finalize the report, ensure reproducibility through the automation scripts, and generate a GitHub release. | May 3, 2026 | Yunsu & Taeseok |

## Constraints
* **Technical Limitations:** One of the prominent challenges currently is the technical difficulties of processing the data. The Lichess PGN files are immensely large with an average of 30GB for each file, which only contains one month of raw game data. We are worried that batch processing and memory management on Python will be slow and might crash if the system is overloaded.
* **Semantic Data Cleaning (Transpositions):** Another significant constraint involves semantic data cleaning methodologies. In chess, different move orders can lead to the exact same board position. It is also known as a concept called "transposition." Simple string matching of the move text cannot catch these identical positions, meaning a robust algorithmic solution (such as parsing the moves into FEN notation) is required to ensure data completeness and accurate opening identification.

## Gaps
* **Automation Scale:** We currently have a gap in understanding how automation can be successfully employed in the project with massive text files. 
* **Metadata Standards:** We need guidance on how to format final machine-readable metadata with standards such as DCAT or DataCite. Our plan is to learn those topics as we move forward in the course and gain more technical knowledge. 
