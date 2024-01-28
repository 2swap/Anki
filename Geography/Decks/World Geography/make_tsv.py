import os
import re

def extract_and_write(folder_path, output_tsv):
    # Regular expression pattern to find the "name_en":"...something..." part
    name_en_pattern = re.compile(r'"name_en":"([^"]*)"')

    with open(output_tsv, 'w') as tsv_file:
        for filename in os.listdir(folder_path):
            # Check if the file matches the pattern 'geog_*.js'
            if filename.startswith('geog_') and filename.endswith('.js'):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r') as file:
                    for line in file:
                        match = name_en_pattern.search(line)
                        if match:
                            # Extract the ...something... part
                            something = match.group(1)
                            # Write to the TSV file
                            tsv_file.write(f'{something}::{filename[5:-3]}\n')

# Example usage
folder_path = 'media'  # Replace with the path to your folder
output_tsv = 'include.tsv'  # The output TSV file name
extract_and_write(folder_path, output_tsv)

