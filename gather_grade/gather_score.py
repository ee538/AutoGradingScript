# Importing necessary libraries
import requests, csv, json, base64, re, datetime, os

# Listing all files in the current directory
all_files = os.listdir()

# Identifying default file paths based on naming conventions
default_csv_path = next((s for s in all_files if '-grades-' in s and 'csv_out.csv' in s), '')
default_csv_student_name_path = next((s for s in all_files if 'name.csv' in s), '')
default_csv_blackboard_path = next((s for s in all_files if '_column_' in s and '.csv' in s), '')

# Prompting for user input to specify file paths with defaults provided
csv_student_name_path = input('student name csv file (default: ' + default_csv_student_name_path + '): ') or default_csv_student_name_path
csv_blackboard_path = input('Blackboard csv file (default: ' + default_csv_blackboard_path + '): ') or default_csv_blackboard_path
csv_classroom_path = input('GitHub Classroom csv file name (default: ' + default_csv_path + '): ') or default_csv_path

# Opening the specified CSV files in read mode and one in write mode
with open(csv_blackboard_path, newline='', encoding='utf-8-sig') as csv_blackboard, \
    open(csv_classroom_path, newline='') as csv_classroom, \
    open(csv_student_name_path, newline='') as csv_student_name, \
    open(csv_blackboard_path + '_upload.csv', 'w') as csv_output:

    # Reading the CSV files using the csv.DictReader
    name_to_github = csv.DictReader(csv_student_name)
    gitname_to_score = csv.DictReader(csv_classroom)
    reader = csv.DictReader(csv_blackboard)

    # Extracting header information and the name of the score column
    header = reader.fieldnames
    score_column = header[-1]

    # Creating a csv.DictWriter to write into the output CSV file
    writer = csv.DictWriter(csv_output, header, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    # Converting CSV data to lists for easier processing
    name_map = [row for row in name_to_github]
    github_score = [row for row in gitname_to_score]
    rows = [row for row in reader]
    
    # Looping through each row in the Blackboard CSV file
    for row in rows:
        # Extracting first and last name from the current row
        first_name = row['First Name']
        last_name = row['Last Name']

        # Finding the corresponding GitHub username for the student
        git_names = [name_row['Github Username'] for name_row in name_map if name_row['First Name'] == first_name and name_row['Last Name'] == last_name]

        # Handling cases where the GitHub username does not match exactly one entry
        if len(git_names) != 1:
            print("error in processing (GitName):" + first_name + ' (Student Name):' + last_name)
            print("Git name does not match: " + git_names)
            print('-------- please check it manually --------')
            writer.writerow(row)
            continue

        git_name = git_names[0]

        # Finding the corresponding final score for the GitHub username
        final_scores = [score_row['final_score'] for score_row in github_score if score_row['github_username'] == git_name]

        # Handling cases where the final score does not match exactly one entry
        if len(final_scores) != 1:
            print("error in processing (GitName):" + git_name + ' (Student Name):' + first_name + ' ' + last_name)
            print("Final score does not match: " + str(final_scores))
            print('-------- please check it manually --------')
            writer.writerow(row)
            continue

        final_score = int(float(final_scores[0]))

        # Updating the score column in the current row
        row[score_column] = final_score
        
        # Writing the updated row to the output CSV file
        writer.writerow(row)
