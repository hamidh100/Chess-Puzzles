import cv2
import pytesseract
import re
import os
from pdf2image import convert_from_path
from PIL import Image
import numpy as np


PDF_FILE = "puzzle_king.pdf"
OUTPUT_DIR = "puzzles"

PAGE_RANGES = [(13, 46), (49, 119), (123, 156)]
DPI = 300

os.makedirs(OUTPUT_DIR, exist_ok=True)


def detect_chessboards(page_cv):
    gray = cv2.cvtColor(page_cv, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    _, thresh = cv2.threshold(
        blur,
        180,
        255,
        cv2.THRESH_BINARY_INV
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        morph,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    boards = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect = w / float(h)

        if 0.85 < aspect < 1.15 and w > 300 and h > 300:
            boards.append((x, y, w, h))

    return boards


def order_boards_for_numbering(boards):
    """
    Sam Loyd pages are usually numbered by columns:

        41    43
        42    44

    So numbering order is:
        top-left, bottom-left, top-right, bottom-right
    """
    if not boards:
        return []

    if len(boards) <= 2:
        return sorted(boards, key=lambda rect: (rect[1], rect[0]))

    centers = [(x + w / 2, y + h / 2, (x, y, w, h)) for x, y, w, h in boards]
    centers_sorted = sorted(centers, key=lambda item: item[0])

    page_columns = []

    for item in centers_sorted:
        cx, cy, board = item

        placed = False

        for column in page_columns:
            column_cx = np.mean([entry[0] for entry in column])

            if abs(cx - column_cx) < board[2] * 0.75:
                column.append(item)
                placed = True
                break

        if not placed:
            page_columns.append([item])

    page_columns.sort(key=lambda column: np.mean([entry[0] for entry in column]))

    ordered = []

    for column in page_columns:
        column.sort(key=lambda item: item[1])
        ordered.extend([item[2] for item in column])

    return ordered


def preprocess_header_for_ocr(header_cv):
    if header_cv is None or header_cv.size == 0:
        return None

    gray = cv2.cvtColor(header_cv, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(
        gray,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    _, thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return Image.fromarray(thresh)


def extract_number_from_header(page_cv, board):
    """
    Only accepts numbers connected to No / No.
    It intentionally rejects bare numbers like 1, 2, 21, etc.
    """
    x, y, w, h = board
    page_h, page_w = page_cv.shape[:2]

    header_y1 = max(y - int(h * 0.45), 0)
    header_y2 = max(y - int(h * 0.03), 0)

    # Keep the crop tight horizontally.
    # Wide crops caused nearby puzzle numbers to be stolen.
    header_x1 = max(x - int(w * 0.05), 0)
    header_x2 = min(x + w + int(w * 0.05), page_w)

    header = page_cv[header_y1:header_y2, header_x1:header_x2]

    header_pil = preprocess_header_for_ocr(header)

    if header_pil is None:
        return None

    configs = [
        "--psm 6",
        "--psm 7",
        "--psm 11",
    ]

    for config in configs:
        text = pytesseract.image_to_string(header_pil, config=config)

        cleaned = (
            text.replace("N0", "No")
            .replace("n0", "no")
            .replace("N o", "No")
            .replace("n o", "no")
            .replace("N.", "No.")
            .replace("No:", "No.")
            .replace("NO.", "No.")
            .replace("NO", "No")
        )

        match = re.search(
            r"\bN[o0]\.?\s*(\d{1,4})\b",
            cleaned,
            re.IGNORECASE
        )

        if match:
            return int(match.group(1))

    return None


def number_matches_expected(ocr_number, expected_number):
    if ocr_number is None:
        return False

    if ocr_number == expected_number:
        return True

    ocr_text = str(ocr_number)
    expected_text = str(expected_number)

    # Fix OCR cases like:
    # 02 instead of 52
    # 04 instead of 54
    # 37 instead of 57
    if len(ocr_text) < len(expected_text):
        return expected_text.endswith(ocr_text)

    differences = sum(
        1
        for a, b in zip(ocr_text, expected_text)
        if a != b
    )

    return len(ocr_text) == len(expected_text) and differences <= 1


def choose_page_numbers(ordered_boards, page_cv, next_expected_number):
    """
    Uses expected sequence as the source of truth.
    OCR is used only to initialize or confirm the sequence.
    """
    ocr_numbers = [
        extract_number_from_header(page_cv, board)
        for board in ordered_boards
    ]

    count = len(ordered_boards)

    if next_expected_number is None:
        valid_numbers = [number for number in ocr_numbers if number is not None]

        if valid_numbers:
            base_number = min(valid_numbers)
        else:
            return [None] * count, None, ocr_numbers
    else:
        base_number = next_expected_number

    repaired_numbers = [
        base_number + offset
        for offset in range(count)
    ]

    # If OCR strongly suggests a different base, use it only when it forms
    # a clean consecutive set. This helps if a page range starts mid-book.
    valid_numbers = [number for number in ocr_numbers if number is not None]

    if next_expected_number is None and len(valid_numbers) >= 2:
        possible_base = min(valid_numbers)
        possible_numbers = [possible_base + offset for offset in range(count)]

        matches = 0

        for ocr_number, expected_number in zip(ocr_numbers, possible_numbers):
            if number_matches_expected(ocr_number, expected_number):
                matches += 1

        if matches >= 2:
            repaired_numbers = possible_numbers
            base_number = possible_base

    next_number = base_number + count

    return repaired_numbers, next_number, ocr_numbers


def extract_solution(page_cv, x, y, w, h):
    height, width = page_cv.shape[:2]

    sol_y1 = y + h

    if sol_y1 >= height - 10:
        return None

    sol_y2 = sol_y1

    WHITE_THRESHOLD = 0.90
    RUN_LENGTH = 20

    white_run = 0

    while sol_y2 < height - 5:
        row = page_cv[sol_y2:sol_y2 + 5, x:x + w]

        if row.size == 0:
            break

        gray = cv2.cvtColor(row, cv2.COLOR_BGR2GRAY)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            15,
            10
        )

        white_ratio = np.mean(thresh == 255)

        if white_ratio > WHITE_THRESHOLD:
            white_run += 1

            if white_run >= RUN_LENGTH:
                break
        else:
            white_run = 0

        sol_y2 += 5

    if sol_y2 - sol_y1 < 40:
        sol_y2 = min(height, sol_y1 + int(h * 0.7))

    sol_pad = int(w * 0.15)

    x1 = max(x - sol_pad, 0)
    x2 = min(x + w + sol_pad, width)

    if sol_y2 <= sol_y1 or x2 <= x1:
        return None

    solution = page_cv[sol_y1:sol_y2, x1:x2]

    if solution.size == 0:
        return None

    return solution


def process_pdf():
    next_expected_number = None

    for range_index, (start, end) in enumerate(PAGE_RANGES, start=1):
        range_output_dir = os.path.join(OUTPUT_DIR, str(range_index))
        os.makedirs(range_output_dir, exist_ok=True)

        print(f"Processing range {range_index}: pages {start}-{end}")

        for page_number in range(start, end + 1):
            print(f"Processing page {page_number}")

            page = convert_from_path(
                PDF_FILE,
                dpi=DPI,
                first_page=page_number,
                last_page=page_number
            )[0]

            page_cv = cv2.cvtColor(
                np.array(page),
                cv2.COLOR_RGB2BGR
            )

            boards = detect_chessboards(page_cv)

            if len(boards) == 0:
                print("  No puzzles found.")
                continue

            ordered_boards = order_boards_for_numbering(boards)

            page_numbers, next_expected_number, ocr_numbers = choose_page_numbers(
                ordered_boards,
                page_cv,
                next_expected_number
            )

            print(f"  Found {len(ordered_boards)} puzzles")
            print(f"  OCR numbers: {ocr_numbers}")
            print(f"  Final numbers: {page_numbers}")

            for board_index, board in enumerate(ordered_boards, start=1):
                x, y, w, h = board
                puzzle_number = page_numbers[board_index - 1]

                if puzzle_number is None:
                    puzzle_number = f"{page_number}_{board_index}"

                puzzle = page_cv[y:y + h, x:x + w]

                if puzzle.size == 0:
                    print(f"  Warning: empty puzzle crop for {puzzle_number}, skipping.")
                    continue

                solution = extract_solution(page_cv, x, y, w, h)

                if solution is None or solution.size == 0:
                    print(f"  Warning: solution not found for {puzzle_number}, skipping.")
                    continue

                puzzle_pil = Image.fromarray(
                    cv2.cvtColor(puzzle, cv2.COLOR_BGR2RGB)
                )

                solution_pil = Image.fromarray(
                    cv2.cvtColor(solution, cv2.COLOR_BGR2RGB)
                )

                puzzle_file = f"{puzzle_number}_puzzle.png"
                solution_file = f"{puzzle_number}_solution.png"

                puzzle_path = os.path.join(range_output_dir, puzzle_file)
                solution_path = os.path.join(range_output_dir, solution_file)

                puzzle_pil.save(puzzle_path)
                solution_pil.save(solution_path)

                print(f"  Saved {puzzle_file}, {solution_file}")

    print("Done.")


if __name__ == "__main__":
    process_pdf()
