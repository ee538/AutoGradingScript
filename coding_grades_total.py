from __future__ import print_function
import json


def get_ok_num_perq(tresfile):
    file = open(tresfile,"r")
    cnt = 0
    f = file.read()
    lists = f.split("\n")
    
    for i in lists:
        if i:
            cnt += 1
    
    return cnt




if __name__ == '__main__':
	
	total_coding_score = 0.0;
	q_nums = []
	full_score = {}
	test_cases = {}

	with open('questions.json', encoding='utf-8') as q:
	    result = json.load(q)
	    q_nums = result.get('q_nums')
	    full_score = result.get('full_score')
	    test_cases = result.get('test_cases')

	score_per_test = { i: (full_score[i] * 2 // test_cases[i]) / 2 for i in q_nums }

	for q_num in q_nums:
		pass_num = get_ok_num_perq("grades/Q" + q_num + "res_.txt")
		if pass_num < test_cases[q_num]:
			score = pass_num * score_per_test[q_num]
		else:
			score = full_score[q_num]
		print("Q",q_num,": ", pass_num, "/", test_cases[q_num], "passed | score:", score)
		total_coding_score += score


	print("-----------------------------------------")
	print("Your total score of coding section:", total_coding_score)
	print("-----------------------------------------")
