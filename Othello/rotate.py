import csv

# Mapping for flipping columns and rows
flip_col = {a: b for a, b in zip("ABCDEFGH", "HGFEDCBA")}
flip_row = {str(i): str(9 - i) for i in range(1, 9)}

def rotate_coord(coord: str) -> str:
    """Rotate a coordinate like C4 → F5 (180° rotation)."""
    if len(coord) != 2:
        return coord
    col, row = coord[0].upper(), coord[1]
    return flip_col.get(col, col) + flip_row.get(row, row)

def rotate_sequence(seq: str) -> str:
    """Rotate an entire sequence like C4c3D3c5 → F5f6E6f4."""
    seq = seq.strip()
    moves = [seq[i:i+2] for i in range(0, len(seq), 2)]
    return "".join(rotate_coord(m) for m in moves)

input_file = "openings.tsv"
output_file = "openings_rotated.tsv"

with open(input_file, "r", encoding="utf-8") as infile, \
     open(output_file, "w", encoding="utf-8", newline="") as outfile:
    reader = csv.reader(infile, delimiter="\t")
    writer = csv.writer(outfile, delimiter="\t")
    
    for row in reader:
        if not row or len(row) < 2:
            continue
        sequence, name = row[0].strip(), row[1].strip()
        rotated = rotate_sequence(sequence)
        writer.writerow([rotated, name])

print(f"✅ Rotated openings written to {output_file}")

