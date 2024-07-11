import os
import re

def extract_and_write(folder_path, output_tsv):
    # Regular expression pattern to find the "name_en":"...something..." part
    name_en_pattern = re.compile(r'"name_en": *"([^"]*)"')

    with open(output_tsv, 'w') as tsv_file:
        sounds = ""
        for filename in os.listdir(folder_path):
            sounds += f'[sound:{filename}]'
            # Check if the file matches the pattern 'geog_*.js'
            if filename.startswith('geog_') and filename.endswith('.js'):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r') as file:
                    for line in file:
                        if line.startswith("//"):
                            continue
                        match = name_en_pattern.search(line)
                        if match:
                            # Extract the ...something... part
                            something = match.group(1)
                            # Write to the TSV file
                            tsv_file.write(f'{something}::{filename[5:-3]}\n')
        tsv_file.write(f'This card contains all map data for the deck - suspend it, but dont delete it!::{sounds}\n')

# Example usage
folder_path = 'media'  # Replace with the path to your folder
output_tsv = 'include.tsv'  # The output TSV file name

# Remove the output TSV file if it exists
if os.path.exists(output_tsv):
    os.remove(output_tsv)

# Call the function
extract_and_write(folder_path, output_tsv)

