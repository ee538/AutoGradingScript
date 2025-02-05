from __future__ import print_function
import json
import os

# count the number of lines in the tresfile
def get_ok_num_perq(tresfile):
    # Check if the file exists before opening
    if not os.path.exists(tresfile):
        return 0  # Return 0 if file is missing

    with open(tresfile, "r") as file:
        lists = file.read().split("\n")

    return sum(bool(x.strip()) for x in lists)  # Strip removes extra spaces


if __name__ == '__main__':

    total_coding_score = 0.0;       # final total score for all questions
    q_nums = []                     # questions need to be graded
    full_score = {}                 # full score for each question
    test_cases = {}                 # the number of test cases for each questions

    # read the json file to acquire the four variables above
    with open('coding_grader/questions.json', encoding='utf-8') as q:
        result = json.load(q)
        q_nums = result.get('q_nums')
        full_score = result.get('full_score')
        test_cases = result.get('test_cases')

    score_per_test = { q_num: (full_score[q_num] / test_cases[q_num]) for q_num in q_nums }

    # start grading each question
    for q_num in q_nums:
        # count the lines with "OK"s for the current question
        pass_num = get_ok_num_perq("grades/Q" + q_num + "res_.txt")
        
        # calculate score for the current question
        if pass_num < test_cases[q_num]:
            score = pass_num * score_per_test[q_num]
        else:
            score = full_score[q_num]
        score = int(score)
        
        print("Q", q_num,": ", pass_num, "/", test_cases[q_num], "passed | score:", score)
        
        # add the score of the current question to the final total score
        total_coding_score += score

    print("-----------------------------------------")
    print("Your total score of coding section:", total_coding_score)
    print("-----------------------------------------")
