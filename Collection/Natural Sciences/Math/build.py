"""Generate Basic.tsv: formula -> value, for the Math deck.

Front is the formula, Back is the computed value. Run by anki_sync.py check/push
(manifest.json's "build" key), or standalone.
"""

import csv
import math
import os
from decimal import Decimal, ROUND_DOWN

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Basic.tsv")


def sigfigs(x, n=8):
    """Truncate a float to n significant figures, keeping trailing zeros."""
    d = Decimal(repr(x))
    exp = d.adjusted()
    quant = Decimal(1).scaleb(exp - n + 1)
    return format(d.quantize(quant, rounding=ROUND_DOWN), "f")


def repeating_decimal(numerator, denominator):
    """0.<non-repeating><span overline>repeating</span> HTML for numerator/denominator."""
    integer_part = numerator // denominator
    remainder = numerator % denominator
    digits = []
    seen = {}
    while remainder != 0 and remainder not in seen:
        seen[remainder] = len(digits)
        remainder *= 10
        digits.append(remainder // denominator)
        remainder %= denominator
    assert remainder != 0, "expected a repeating (non-terminating) decimal"
    start = seen[remainder]
    non_rep = "".join(str(d) for d in digits[:start])
    rep = "".join(str(d) for d in digits[start:])
    return (
        f"{integer_part}.{non_rep}"
        f'<span style="text-decoration: overline;">{rep}</span>'
    )


def build_rows():
    rows = []

    # Constants, truncated to 8 significant figures unless a shorter count is given.
    constants = [
        ("e", math.e),
        ("&radic;2", math.sqrt(2)),
        ("&radic;2/2", math.sqrt(2) / 2),
        ("&phi;", (1 + math.sqrt(5)) / 2),
        ("1/&phi;", 1 / ((1 + math.sqrt(5)) / 2)),
        ("&radic;3", math.sqrt(3), 5),
        ("&radic;5", math.sqrt(5), 5),
        ("&tau;", math.tau),
    ]
    for formula, value, *n in constants:
        rows.append((formula, sigfigs(value, *n)))

    # Factorials.
    fact = 1
    for n in range(1, 11):
        fact *= n
        if n >= 5:
            rows.append((f"{n}!", str(fact)))

    # Powers of 3.
    for n in range(5, 9):
        rows.append((f"3^{n}", str(3 ** n)))

    # Powers of 2.
    for n in range(6, 21):
        rows.append((f"2^{n}", str(2 ** n)))

    # Squares (1-10 are times tables).
    for n in range(11, 26):
        rows.append((f"{n}^2", str(n * n)))

    # Inverse powers of 2 (exact terminating decimals), from 2^-2.
    for n in range(2, 9):
        rows.append((f"2^-{n}", format(Decimal(1) / Decimal(2 ** n), "f")))

    # Powers of 5 (same digits as the inverse powers of 2).
    for n in range(4, 9):
        rows.append((f"5^{n}", str(5 ** n)))

    # Fibonacci successors: F_n -> F_(n+1) for F_3 = 2 through F_15 = 610
    # (start at F_3, since "after 1" is ambiguous between F_1 and F_2).
    a, b = 1, 1
    for n in range(1, 16):
        if n >= 3:
            rows.append((f"What is the Fibonacci number after {a}?", str(b)))
        a, b = b, a + b

    # Repeating decimals.
    for n in (6, 7, 9, 11, 13):
        rows.append((f"1/{n}", repeating_decimal(1, n)))
    for k in range(2, 7):
        rows.append((f"{k}/7", repeating_decimal(k, 7)))

    return rows


def main():
    rows = build_rows()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["Front", "Back", "Tags"])
        for front, back in rows:
            writer.writerow([front, back, ""])
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
