## Sam Loyd Chess Puzzle Viewer

A simple static website for browsing chess problems in three sections:

- Two Move Mates
- Three Move Mates
- Four Move Mates

Each puzzle page shows a puzzle diagram, the puzzle number, a button to reveal the solution, and navigation controls to move backward or forward by 1 or 10 puzzles.

## Project Status

This repository contains the website code and a local extraction script.

It does **not** include:

- the source PDF
- extracted puzzle images
- extracted solution images

## How to use

If you generate puzzle images locally, the site expects them in this structure:

puzzles/
├── 1/
│   ├── 1_puzzle.png
│   ├── 1_solution.png
│   └── ...
├── 2/
│   ├── 1_puzzle.png
│   ├── 1_solution.png
│   └── ...
└── 3/
    ├── 1_puzzle.png
    ├── 1_solution.png
    └── ...

Section folders correspond to:
1 = Two Move Mates
2 = Three Move Mates
3 = Four Move Mates

extract.py is a helper script for local extraction of puzzle diagrams and solution images from selected PDF page ranges.
Configure these values at the top of the script:
PDF_FILE = "puzzle_king.pdf"
OUTPUT_DIR = "puzzles"
PAGE_RANGES = [(13, 46), (49, 119), (123, 156)]

The generated files should follow this naming pattern:
1_puzzle.png
1_solution.png
2_puzzle.png
2_solution.png

And you are done.

## Running Locally

From the project directory:
python3 -m http.server 8000

Then open:
http://localhost:8000

To listen on all network interfaces:
python3 -m http.server 8000 --bind 0.0.0.0

## Copyright Notice

This repository does not include the source PDF or extracted puzzle/solution images.

## AI Disclosure

The project idea and direction are by the repository author.
The code in this repository was written by AI and reviewed/edited by the repository author.

