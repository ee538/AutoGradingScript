import requests, csv, json, base64, re, datetime, os

all_files = os.listdir()

default_csv_path = next((s for s in all_files if '-grades-' in s and '.csv' in s and '_out' not in s), '')
default_csv_student_name_path = next((s for s in all_files if 'name.csv' in s), '')
default_csv_blackboard_path = next((s for s in all_files if '_column_' in s and '.csv' in s), '')


csv_student_name_path = input('student name csv file (default: ' + default_csv_student_name_path + '): ') or default_csv_student_name_path
csv_blackboard_path = input('Blackboard csv file (default: ' + default_csv_blackboard_path + '): ') or default_csv_blackboard_path
csv_path = input('GitHub Classroom csv file name (default: ' + default_csv_path + '): ') or default_csv_path
csv_classroom_path = csv_path + '_out.csv'

if not csv_classroom_path in all_files:
    github_token = input('github token: ')
    file_path = 'ScoresCodingTotal.txt'
    with open(csv_path, newline='') as csv_input, open(csv_path + '_out.csv', 'w') as csv_output:
        reader = csv.DictReader(csv_input)
        header = reader.fieldnames + ['totalscore', 'calculated_total', 'final_score', 'submission_date', 'submission_time']
        writer = csv.DictWriter(csv_output, header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        rows = [row for row in reader]
        
        format = '%a %b %d %H:%M:%S %Z %Y'
        subscore_re = re.compile('Q (\d+) .+ score: (\d+)')
        totalscore_re = re.compile('Your total score of coding section: (.+)')
        
        for row in rows:
            repo_name = row['student_repository_name']
            res = requests.get('https://api.github.com/repos/EE538/' + repo_name + '/contents/' + file_path, headers={
                "Accept":"application/vnd.github+json",
                "Authorization": "Bearer " + github_token,
                "X-GitHub-Api-Version": "2022-11-28"
            })
            
            summary = json.loads(res.text)
            content = base64.b64decode(summary['content']).decode("utf-8")
            date_time = datetime.datetime.strptime(content.split('\n')[-2], format)
            
            subscores = subscore_re.findall(content)
            totalscore_match = totalscore_re.findall(content)
            if (len(totalscore_match) == 0 or len(subscores) == 0):
                print("error in processing " + row['github_username'])
                print(content)
                print('-------- please check it manually --------')
                writer.writerow(row)
                continue
            totalscore = float(totalscore_match[0])
            calculated_total = sum([float(subscore[-1]) for subscore in subscores])
            if int(calculated_total) != int(totalscore):
                print("error in processing " + row['github_username'])
                print("Score does not match: " + str(int(calculated_total)) + ' ' + str(int(totalscore)))
                print(content)
                print('-------- please check it manually --------')
                writer.writerow(row)
                continue
            submission_date = str(date_time.date())
            submission_time = str(date_time.time())
            
            print(row['github_username'] + ':\t' + str(totalscore) + '\t' + submission_date)

            row['totalscore']       = totalscore
            row['calculated_total'] = calculated_total
            row['final_score']      = 100 if (calculated_total > 100) else calculated_total
            row['submission_date']  = submission_date
            row['submission_time']  = submission_time
            # for subscore in subscores:
            #    row['subscore Q' + subscore[0]] = subscore[-1]
            
            writer.writerow(row)
            
    input('Press enter to proceed.')

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
            
