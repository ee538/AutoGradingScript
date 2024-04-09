#!/usr/bin/env python3

import os, json, subprocess
# from unittest import TestResult

def exec_cmd(cmd):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    # print(text)
    return text

def bazel_test(task):
    # test_cmd = 'bazel test coding_grader/' + q_num + ':grader_test --test_output=all --config=asan 2>&1'
    test_cmd = [
        'bazel',
        'test',
        task,
        '--test_output=all',
        '--test_timeout=90',
        '--config=asan'
    ]
    test_output = ''
    error_msg = ''
    try:
        test_output = subprocess.check_output(test_cmd, stderr=subprocess.STDOUT, timeout=120).decode()
    except subprocess.TimeoutExpired as e:
        test_output = e.output.decode()
        error_msg = 'ERROR: Timeout expired!'
    except subprocess.CalledProcessError as e:
        test_output = e.output.decode()
        if 'AddressSanitizer' in test_output:
            error_msg = 'ERROR: Memory misuse detected!'
        elif 'TIMEOUT' in test_output:
            error_msg = 'ERROR: Timeout expired!'
        elif 'FAILED TO BUILD' in test_output:
            error_msg = 'ERROR: Bazel build error!'
        else:
            error_msg = 'Partially Incorrect...'
    except Exception as e:
        test_output = str(e)
        error_msg = 'ERROR: Unknown error!'

    return [test_output, error_msg]

def run_test(path_q_num, student_test=False, return_all=False):
    
    tasks = [path_q_num + ':grader_test']

    # os.system('cp ../submission/files/' + q_num + '/q.cc coding_grader/' + q_num + '/')
    if student_test:
        # os.system('cp ../submission/files/' + q_num + '/student_test.cc coding_grader/' + q_num + '/')
        tasks = [path_q_num + ':student_test'] + tasks
    print('================================================================================\n')
    print(path_q_num + ' testing:')
    for task in tasks:
        test_output, error_msg = bazel_test(task)
        print(test_output + error_msg)
        if task != tasks[-1] and error_msg != '':
            res = {
                'passed':   0,
                'failed':   0,
                'error':    'Student test ' + error_msg,
            }
            if return_all:
                res.update({"test_output": test_output})
            return res
    res = {
        'passed':           test_output.count('[       OK ]'),
        'failed':           test_output.count('FAIL'),
        'error':            error_msg,
    }
    if return_all:
        res.update({"test_output": test_output})
    return res

# def output_json(score_obj):
#     # reference: https://gradescope-autograders.readthedocs.io/en/latest/specs/#output-format
#     dict_obj = {
#         'visibility':       'after_published',
#         'stdout_visibility':'after_published',
#         'tests':            score_obj,
#     }
#     if not os.path.exists('../results/'):
#         os.mkdir('../results/')
#     with open('../results/results.json', "w") as outfile:
#         outfile.writelines(json.dumps(dict_obj, indent = 4))


def output_json(dict_obj: dict, file_path: str, disp: bool=False) -> None:
    json_str = json.dumps(dict_obj, indent = 4)
    
    if file_path != '':
        (folder_name, _) = os.path.split(file_path)
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        with open(file_path, "w") as outfile:
            outfile.writelines(json_str)
            
    if disp:
        print('================================================================================')
        print(file_path + '\n' + json_str)

def generate_coding_grader(coding_grader_name):
    all_files = sorted(os.listdir('sol'))
    ungrading_q_nums = list(filter(lambda file:(not os.path.isfile('sol/' + file)), all_files))
    q_nums = list(filter(lambda file:(os.path.isfile('sol/' + file + '/grader_test.cc')), ungrading_q_nums))
    
    # execute all the grader tests for all the questions and get the testing results
    test_results = { q_num: run_test('sol/' + q_num) for q_num in q_nums }
    output_json(test_results, '', True)
    
    # if some of the test are not passed, then exit
    failed_test = [test_results[q_num]['failed'] for q_num in test_results]
    error_test = [test_results[q_num]['error'] for q_num in test_results]
    if any(failed_test) or any(error_test):
        print("Error detected in some test cases!")
        exit()
        
    # copy the 'sol' folder as coding_grader_name, remove the solutions
    exec_cmd('rm -rf ' + coding_grader_name)
    exec_cmd('mkdir ' + coding_grader_name)
    [exec_cmd('cp -r sol/' + str(q_num) + " " + coding_grader_name + "/" + str(q_num)) for q_num in q_nums]
    exec_cmd('rm -rf `find ' + coding_grader_name + ' -name q.cc -o -name student_test.cc -o -name *.csh`')
    
    # count the number of test cases for each question using the number of passed tests
    test_cases = { q_num: test_results[q_num]['passed'] for q_num in q_nums }
    
    # input how many points should be allocated for each question
    print('================================================================================')
    print('All tests are valid!')
    print('Please enter the full score for each question (coding part):')
    full_score = {}
    for q_num in q_nums:
        score = input('Q' + q_num + ' (' + str(test_cases[q_num]) + ' test cases): ')
        if score == '':
            score = 0
        full_score[q_num] = int(score)
        
    output_json({
        'q_nums': q_nums,
        'test_cases': test_cases,
        'full_score': full_score
    }, coding_grader_name + '/questions.json', disp=True)
    
def generate_assignment(hw_name):
    coding_grader_name = hw_name + '_CodingGrader'
    all_files = sorted(os.listdir('files'))
    ungrading_q_nums = list(filter(lambda file:(not os.path.isfile('sol/' + file)), all_files))
    q_nums = list(filter(lambda file:(os.path.isfile('sol/' + file + '/grader_test.cc')), ungrading_q_nums))
        
    file_list = [
        '.vscode',
        'files',
        '.bazelrc',
        '.gitignore',
        'README.md',
        'WORKSPACE'
    ]
    
    # copy files in file_list to assignment folder
    exec_cmd('rm -rf ' + hw_name)
    exec_cmd('mkdir -p ' + hw_name + '/.github/workflows')
    for file in file_list:
        exec_cmd('cp -r ' + file + ' ' + hw_name)
    for q_num in q_nums:
        exec_cmd('cp sol/' + q_num + '/grader_test.cc ' + hw_name + '/files/' + q_num + '/')
    # exec_cmd('cp AutoGradingScript/classroom.yml ' + hw_name + '/.github/workflows/')
        
    output_json({
        'q_nums': q_nums,
        'grader_repo': 'ee538/' + coding_grader_name
    }, hw_name + '/.github/workflows/config.json', disp=True)

def git_upload(dir: str, token: str='', private: str='true', repo: str='') -> None:
    if repo == '':
        repo = dir
    cwd = os.getcwd()
    os.chdir(dir)
    exec_cmd('curl -X POST -H "Accept: application/vnd.github+json" -H "Authorization: Bearer ' + token + '" -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/orgs/ee538/repos -d \'{"name":"' + repo + '","description":"","private":' + private + ',"has_issues":true,"has_projects":true,"has_wiki":true}\'')
    exec_cmd('git init')
    exec_cmd('git add ./')
    exec_cmd('git commit -m fcm')
    exec_cmd('git branch -M main')
    exec_cmd('git remote add origin https://github.com/ee538/' + repo)
    exec_cmd('git branch --set-upstream-to=origin/main main')
    exec_cmd('git push -u origin main')
    exec_cmd('git pull origin main')
    exec_cmd('git push -u origin main')
    os.chdir(cwd)
    
if __name__ == '__main__':
    default_name = '_'.join(os.path.split(os.getcwd())[-1].split('_')[1:])
    hw_name = input('Please enter the name of this assignment (default: ' + default_name + '): ')
    if hw_name == '':
        hw_name = default_name
    coding_grader_name = hw_name + '_CodingGrader'
        
    generate_coding_grader(coding_grader_name)
    generate_assignment(hw_name)
    
    print('================================================================================')
    key_in = ''
    key_in = input('Do you want to upload the two repo? [ (Y)es / (N)o ]: ')
    if key_in == 'y' or key_in == 'Y' or key_in == 'yes' or key_in == 'Yes':
        git_token = input('github token: ')
        git_upload(hw_name, git_token, 'true')
        git_upload(coding_grader_name, git_token, 'false')
        
    print('================================================================================')
    key_in = ''
    key_in = input('Do you want to clean the two repo? [ (Y)es / (N)o ]: ')
    if key_in == 'y' or key_in == 'Y' or key_in == 'yes' or key_in == 'Yes':
        exec_cmd('rm -rf ' + hw_name)
        exec_cmd('rm -rf ' + coding_grader_name)

# if __name__ == '__main__':
    
#     os.chdir('./source/')
#     total_coding_score = 0.0
#     q_nums = []
#     full_score = {}
#     test_cases = {}
#     total_result = []
#     visible_list = []
#     student_test_list = []

#     with open('questions.json', encoding='utf-8') as q:
#         questions = json.load(q)
#         q_nums = questions.get('q_nums')
#         q_nums = [str(q_num) for q_num in q_nums]
#         full_score = questions.get('full_score')
#         test_cases = questions.get('test_cases')
#         visible_list = questions.get('visible_list')
#         student_test_list = questions.get('student_test_list')
    
#     score_per_test = { q_num: (full_score[q_num] * 2 // test_cases[q_num]) / 2 for q_num in q_nums }
#     for q_num in q_nums:
#         test_result = run_test(q_num, q_num in student_test_list)
#         score = 0.0

#         if test_result['passed'] < test_cases[q_num]:
#             score = test_result['passed'] * score_per_test[q_num]
#         elif test_result['passed'] == test_cases[q_num]:
#             score = full_score[q_num]
#         else:                   # if this happens, student might cheat
#             score = 0.0

#         if 'ERROR' in test_result['error']:       # score will be deducted by 50%
#             score = (score * 2 + 1) // 2 / 2
#         elif test_result['passed'] >= test_cases[q_num] and test_result['failed'] != 0:    # if this happens, student might cheat 
#             score = 0.0

#         total_result.append({
#             'score':        score,
#             'max_score':    full_score[q_num],
#             'number':       q_num,
#             'visibility':   'visible' if q_num in visible_list else 'after_due_date',
#             'output':       test_result['error']
#         })

#     output_json(total_result)
