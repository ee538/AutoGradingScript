import csv
import requests
import json
import os
from datetime import datetime, timedelta

def git_request(url, github_token, retry=3):
    try:
        return requests.get(url, headers={
            "Accept":"application/vnd.github+json",
            "Authorization": "Bearer " + github_token,
            "X-GitHub-Api-Version": "2022-11-28"}).text
    except:
        return "" if retry < 1 else git_request(url, github_token, retry - 1)

def path_of_url(url):
    return url.split("/")[-1]

def get_repo_info(url, github_token):
    return git_request(
        "https://api.github.com/repos/ee538/" + path_of_url(url) + "/commits",
        github_token
    )

def get_last_commit_date(url, github_token):
    commits = json.loads(get_repo_info(url, github_token))
    return "" if len(commits) == 0 else commits[0]["commit"]["author"]["date"]

all_files = os.listdir()
default_csv_path = next((s for s in all_files if '-grades-' in s and '.csv' in s and '_out' not in s), '')
default_json_path = next((s for s in all_files if 'output.json' in s), '')


github_token = input('github token: ')
json_path = input('output.json (default: ' + default_json_path + '): ') or default_json_path
csv_path = input('GitHub Classroom csv file name (default: ' + default_csv_path + '): ') or default_csv_path
csv_classroom_path = csv_path + '_out.csv'

# 读取output.json文件
with open(json_path, 'r') as json_file:
    github_scores = json.load(json_file)

# 读取csv文件并创建新的csv文件
with open(csv_path, 'r', newline='') as input_csv, open(csv_classroom_path, 'w', newline='') as output_csv:
    csv_reader = csv.DictReader(input_csv)
    fieldnames = csv_reader.fieldnames + ['totalscore', 'calculated_total', 'final_score', 'submission_date', 'submission_time']
    csv_writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
    csv_writer.writeheader()

    for row in csv_reader:
        student_repository_url = row['student_repository_url']
        submission_date, submission_time = '', ''

        # 调用git_request函数获取GitHub仓库的最后一次push时间
        last_commit_date = get_last_commit_date(student_repository_url, github_token)
        if last_commit_date:
            last_commit_date_time = datetime.strptime(last_commit_date, "%Y-%m-%dT%H:%M:%SZ")

            # 创建洛杉矶时区的UTC偏移（-07:00）
            los_angeles_offset = timedelta(hours=-7)

            # 将datetime对象加上洛杉矶时区的偏移来获得洛杉矶时间
            timestamp_los_angeles = last_commit_date_time + los_angeles_offset

            # 获取日期和时间部分
            submission_date = timestamp_los_angeles.date()
            submission_time = timestamp_los_angeles.time()


        # 查找totalscore
        totalscore = github_scores.get(student_repository_url, 0)
        calculated_total = totalscore

        # 计算final_score
        final_score = min(totalscore, 100)


        print(student_repository_url, totalscore, final_score, submission_date, submission_time)
        # 更新行数据并写入新的CSV文件
        row.update({'totalscore': totalscore, 'calculated_total': calculated_total, 'final_score': final_score, 'submission_date': submission_date, 'submission_time': submission_time})
        csv_writer.writerow(row)

