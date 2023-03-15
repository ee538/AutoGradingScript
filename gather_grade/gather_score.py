import requests, csv, json, base64, re, datetime


github_token = input('github token: ')
csv_path = input('csv file name: ')

file_path = 'ScoresCodingTotal.txt'

with open(csv_path, newline='') as csv_input, open(csv_path + '_out.csv', 'w') as csv_output:
    reader = csv.DictReader(csv_input)
    header = reader.fieldnames + ['totalscore', 'calculated_total', 'submission_date', 'submission_time']
    writer = csv.DictWriter(csv_output, header)
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
        if len(totalscore_match) == 0 or len(subscores) == 0:
        	print("error in processing " + row['github_username'])
        	print(content)
        	print('-------- please check it manually --------')
        	continue
        totalscore = totalscore_match[0]
        calculated_total = sum([float(subscore[-1]) for subscore in subscores])
        submission_date = str(date_time.date())
        submission_time = str(date_time.time())
        
        print(row['github_username'] + ':\t' + totalscore + '\t' + submission_date)

        row['totalscore'] = totalscore
        row['calculated_total'] = calculated_total
        row['submission_date'] = submission_date
        row['submission_time'] = submission_time
        # for subscore in subscores:
        #    row['subscore Q' + subscore[0]] = subscore[-1]
        
        writer.writerow(row)
            
        
            
        
        
        
