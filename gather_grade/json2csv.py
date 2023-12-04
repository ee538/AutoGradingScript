


import csv
import requests
import json
import os
from datetime import datetime, timedelta

# Function to make a request to GitHub API
def git_request(url, github_token, retry=3):
    try:
        # Make a GET request to the specified URL with GitHub authorization headers
        return requests.get(url, headers={
            "Accept":"application/vnd.github+json",
            "Authorization": "Bearer " + github_token,
            "X-GitHub-Api-Version": "2022-11-28"}).text
    except:
        # Retry the request if it fails, decrease retry count each time
        return "" if retry < 1 else git_request(url, github_token, retry - 1)

# Function to extract the last segment of a URL
def path_of_url(url):
    return url.split("/")[-1]

# Function to get commit information of a GitHub repository
def get_repo_info(url, github_token):
    # Formulate the API URL and use git_request to fetch data
    return git_request(
        "https://api.github.com/repos/ee538/" + path_of_url(url) + "/commits",
        github_token
    )

# Function to get the date of the last commit of a repository
def get_last_commit_date(url, github_token):
    commits = json.loads(get_repo_info(url, github_token))
    # Return an empty string if there are no commits, else return the date of the latest commit
    return "" if len(commits) == 0 else commits[0]["commit"]["author"]["date"]

# Listing all files in the current directory
all_files = os.listdir()
# Finding the default paths for the CSV and JSON files
default_csv_path = next((s for s in all_files if '-grades-' in s and '.csv' in s and '_out' not in s), '')
default_json_path = next((s for s in all_files if 'output.json' in s), '')

# Prompting for user input for GitHub token and file paths, with defaults provided
github_token = input('github token: ')
json_path = input('output.json (default: ' + default_json_path + '): ') or default_json_path
csv_path = input('GitHub Classroom csv file name (default: ' + default_csv_path + '): ') or default_csv_path
# Defining the path for the output CSV file
csv_classroom_path = csv_path + '_out.csv'

# Reading the JSON file containing GitHub scores
with open(json_path, 'r') as json_file:
    github_scores = json.load(json_file)

# Reading the input CSV file and preparing to write to a new CSV file
with open(csv_path, 'r', newline='') as input_csv, open(csv_classroom_path, 'w', newline='') as output_csv:
    csv_reader = csv.DictReader(input_csv)
    # Adding new fieldnames to the CSV header
    fieldnames = csv_reader.fieldnames + ['totalscore', 'calculated_total', 'final_score', 'submission_date', 'submission_time']
    csv_writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
    csv_writer.writeheader()

    # Iterating through each row in the CSV file
    for row in csv_reader:
        student_repository_url = row['student_repository_url']
        submission_date, submission_time = '', ''

        # Getting the last commit date from the GitHub repository
        last_commit_date = get_last_commit_date(student_repository_url, github_token)
        if last_commit_date:
            # Converting the commit date string into a datetime object
            last_commit_date_time = datetime.strptime(last_commit_date, "%Y-%m-%dT%H:%M:%SZ")

            # Creating a timedelta for Los Angeles timezone offset
            los_angeles_offset = timedelta(hours=-7)

            # Adjusting the commit date to Los Angeles time
            timestamp_los_angeles = last_commit_date_time + los_angeles_offset

            # Extracting the date and time from the timestamp
            submission_date = timestamp_los_angeles.date()
            submission_time = timestamp_los_angeles.time()

        # Retrieving the total score from the JSON data
        totalscore = github_scores.get(student_repository_url, 0)
        calculated_total = totalscore

        # Calculating the final score with a cap of 100
        final_score = min(totalscore, 100)

        # Printing the data for each student repository
        print(student_repository_url, totalscore, final_score, submission_date, submission_time)
        # Updating the row with new data and writing it to the new CSV file
        row.update({'totalscore': totalscore, 'calculated_total': calculated_total, 'final_score': final_score, 'submission_date': submission_date, 'submission_time': submission_time})
        csv_writer.writerow(row)
