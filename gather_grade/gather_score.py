import requests, csv, json, base64, re, datetime, os

all_files = os.listdir()

default_csv_path = next((s for s in all_files if '-grades-' in s and 'csv_out.csv' in s and '_out' not in s), '')
default_csv_student_name_path = next((s for s in all_files if 'name.csv' in s), '')
default_csv_blackboard_path = next((s for s in all_files if '_column_' in s and '.csv' in s), '')


csv_student_name_path = input('student name csv file (default: ' + default_csv_student_name_path + '): ') or default_csv_student_name_path
csv_blackboard_path = input('Blackboard csv file (default: ' + default_csv_blackboard_path + '): ') or default_csv_blackboard_path
csv_path = input('GitHub Classroom csv file name (default: ' + default_csv_path + '): ') or default_csv_path
csv_classroom_path = csv_path + '_out.csv'

with open(csv_blackboard_path, newline='', encoding='utf-8-sig') as csv_blackboard, \
    open(csv_classroom_path, newline='') as csv_classroom, \
    open(csv_student_name_path, newline='') as csv_student_name, \
    open(csv_blackboard_path + '_upload.csv', 'w') as csv_output:

    name_to_github = csv.DictReader(csv_student_name)
    gitname_to_score = csv.DictReader(csv_classroom)

    reader = csv.DictReader(csv_blackboard)
    header = reader.fieldnames
    score_column = header[-1]
    writer = csv.DictWriter(csv_output, header, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    name_map = [row for row in name_to_github]
    github_score = [row for row in gitname_to_score]
    rows = [row for row in reader]
    
    for row in rows:
        first_name = row['First Name']
        last_name = row['Last Name']
        git_names = [name_row['Github Username'] for name_row in name_map if name_row['First Name'] == first_name and name_row['Last Name'] == last_name]
        if len(git_names) != 1:
            print("error in processing " + first_name + ' ' + last_name)
            print("Git name does not match: " + git_names)
            print('-------- please check it manually --------')
            writer.writerow(row)
            continue
        git_name = git_names[0]
        final_scores = [score_row['final_score'] for score_row in github_score if score_row['github_username'] == git_name]
        if len(final_scores) != 1:
            print("error in processing " + git_name + ' ' + first_name + ' ' + last_name)
            print("Final score does not match: " + str(final_scores))
            print('-------- please check it manually --------')
            writer.writerow(row)
            continue
        final_score = int(float(final_scores[0]))

        row[score_column]       = final_score
        
        writer.writerow(row)
            
