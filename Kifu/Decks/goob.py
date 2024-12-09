# Define the range and file name
start = 0
end = 325
output_file = "even_numbers_with_script.txt"

# Open the file in write mode
with open(output_file, "w") as file:
    for number in range(start, end + 1):
        if number % 2 == 0:  # Check if the number is even
            file.write(f"{number}\tshuusaku.js\n")

print(f"File '{output_file}' has been created with the even numbers and script names.")

