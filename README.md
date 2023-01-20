# AutoGradingScript
AutoGradingScript for USC EE-538 version 0.2 on 1/19/2023.

### 1. How to Use
Take **Fall22_HW5** as the example:

- 1.1. Start Ubuntu system and go to workspace.

   ```bash
   cd ws
   ```

- 1.2. Clone the assignment repo given from the professor.

   The professor gave us `https://github.com/ourarash/EE538_Fall22_HW5`.

   ```bash
   git clone https://github.com/ourarash/EE538_Fall22_HW5.git
   cd EE538_Fall22_HW5
   ```

- 1.3. **The first step is always checking the ambiguity and the error manually in the code or instructions. Correct them and then proceed.** 

- 1.4. Inside the repo folder, we need to make sure there is no error and **all the tests can pass with the solution provided** through a script.

   Download the script:

   ```bash
   https://github.com/ee538/AutoGradingScript.git
   ```

   Run the script:

   ```bash
   python3 AutoGradingScript/grading_utils.py
   ```

- 1.5. Type the name `Fall22_HW5` for this assignment or type nothing if the default one is correct. Then press the enter key.

- 1.6. The script will run all of the grader tests for several minutes. Please be patient and wait. If you finally see a summary like this:

   ```json
   {
       "1": {
           "passed": 2,
           "failed": 0,
           "error": ""
       },
       "2": {
           "passed": 7,
           "failed": 0,
           "error": ""
       },
       "3": {
           "passed": 17,
           "failed": 0,
           "error": ""
       }
   }
   ================================================================================
   All tests are valid!
   ```

   This means all the grader tests have passed with the solution provided.

- 1.7. Assign some score for each question. You will see a summary like this:

   ```json
   Please enter the full score for each question:
   Q1 (2 test cases): 20
   Q2 (7 test cases): 45
   Q3 (17 test cases): 45
   ================================================================================
   Fall22_HW5_CodingGrader/questions.json
   {
       "q_nums": [
           "1",
           "2",
           "3"
       ],
       "test_cases": {
           "1": 2,
           "2": 7,
           "3": 17
       },
       "full_score": {
           "1": 20,
           "2": 45,
           "3": 45
       }
   }
   ================================================================================
   Fall22_HW5/.github/workflows/config.json
   {
       "q_nums": [
           "1",
           "2",
           "3"
       ],
       "grader_repo": "ee538/Fall22_HW5_CodingGrader"
   }
   ================================================================================
   ```

- 1.8. If we don't want to grade some of the questions with the grading script, please remove them now in the two JSON files. 

   `Fall22_HW5_CodingGrader/questions.json` 

   `Fall22_HW5/.github/workflows/config.json`

- 1.9. Upload the Assignment repo and the Grader repo by typing **yes** if needed.

   Paste the GitHub token to get authentication. Press enter and go the GitHub to check if the two repos have been deployed properly.

- 1.10. Type yes to clean temporary files. Finally remove the `AutoGradingScipt` folder from the repo.

### 2. Repos Needed

To use this grading script, 3 repos are needed.

#### 2.1. Grading Script

This repo (AutoGradingScript) is the **public** grading script repo, where [`coding_grades_total.py`](./coding_grades_total.py) is required.

#### 2.2. Grader Test

A **public** grader test repo is needed with the directory like this:

```shell
@ee538/Fall22_HW3_CodingGrader

.
├── 2
│   ├── BUILD
│   ├── grader_test.cc
│   └── q.h
├── 3
│   ├── BUILD
...
│   ├── grader_test.cc
│   └── q.h
└── questions.json # other files are all from the professor's workspace except this file
```

The professor's workspace directory should be like:

```shell
├── check_all_test.sh # copy this file manually from this repo
├── files
│   ├── 2
│   │   ├── BUILD
│   │   ├── q.cc
│   │   ├── q.h
│   │   └── student_test.cc
│   ├── 3
│   │   ├── BUILD
│   │   ├── q.cc
│   │   ├── q.h
...
│   │   └── student_test.cc
└── sol
    ├── 2
    │   ├── BUILD
    │   ├── grader_test.cc
    │   ├── q.cc
    │   └── q.h
    ├── 3
    │   ├── BUILD
    │   ├── grader_test.cc
    │   ├── q.cc
    ...
        └── q.h
```

where `questions.json` should be like:

```json
{
	"q_nums": ["2", "3", "4", "5"],
	"test_cases": {
		"2": 8,
		"3": 9,
		"4": 16,
		"5": 20
	},
	"full_score": {
		"2": 15,
		"3": 15,
		"4": 40,
		"5": 30
	}
}
```

- `q_nums`: The number the questions needed to be graded by the script.
- `test_cases`: The number of the test cases in `grader_test.cc` for each question.
- `full_score`: Full credits for each question.



To get the number of the test cases for each question and make sure there is no memory misuse or failed test, copy [`check_all_test.sh`](check_all_test.sh) from this repo to the workspace and run the following command in the root folder of the workspace. `2 3 4 5` are the 4 questions under testing.

```shell
./check_all_test.sh 2 3 4 5
```

The outputs may be like: (with errors)

```shell
passed:
"2": 8,
"3": 9,
"4": 16,
"5": 20,
failed:
"2": ,
"3": ,
"4": 4,			# errors
"5": ,
memory misuse:
"2": ,
"3": ,
"4": 1,			# errors
"5": ,
```

After checking and solving all the errors, the outputs should be like this **with no failed or memory misuse cases**:

```shell
passed:
"2": 8,
"3": 9,
"4": 16,
"5": 20,
failed:
"2": ,
"3": ,
"4": ,
"5": ,
memory misuse:
"2": ,
"3": ,
"4": ,
"5": ,
```

After creating the `questions.json` and solving the errors in the grader_test.cc, the preparation for this repo is done.

#### 2.3. Student Repository

```shell
.
├── .bazelrc
├── .github
│   └── workflows
│       ├── classroom.yml	# copy this file manually from this repo
│       └── config.json		# add this file manually
├── .gitignore
├── .vscode
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json
├── README.md
├── WORKSPACE
└── files
    ├── 1
    │   ├── BUILD
    │   ├── README.md
    │   ├── q.cc
    │   └── q.h
    ├── 2
    │   ├── BUILD
    │   ├── q.cc
    │   ├── q.h
    ...
        └── student_test.cc
```

where `config.json` should be like:

```json
{
  "q_nums": ["2", "3", "4", "5"], 
  "grader_repo": "ee538/Fall22_HW3_CodingGrader"
}
```

- `q_nums`: The number the questions needed to be graded by the script.
- `grader_repo`: The location of the **Grader Test repo** prepared from the [previous step](#12-grader-test).

Finally, copy [`classroom.yml`](./classroom.yml) from this repo to the student repo.



### 3. `coding_grades_total.py`

The script should be similar to this:

```python
total_coding_score = 0.0;
q_nums = []
full_score = {}
test_cases = {}

with open('coding_grader/questions.json', encoding='utf-8') as q:
    result = json.load(q)
    q_nums = result.get('q_nums')
    full_score = result.get('full_score')
    test_cases = result.get('test_cases')
```

First, read question information from `questions.json` create in step [1.2.](#12-grader-test). 

- `q_nums`: The number the questions needed to be graded by the script.

- `test_cases`: The number of the test cases in `grader_test.cc` for each question.
- `full_score`: Full credits for each question.

```python
# this line is changed already, this is just a sample
score_per_test = { i: (full_score[i] * 2 // test_cases[i]) / 2 for i in q_nums }
```

Then, set the credits of one test case for each question. 0.5 credits is the minimum scale unit of the credits for one test case.

```python
for q_num in q_nums:
	pass_num = get_ok_num_perq("grades/Q" + q_num + "res_.txt")
	if pass_num < test_cases[q_num]:
		score = pass_num * score_per_test[q_num]
	else:
		score = full_score[q_num]
	print("Q",q_num,": ", pass_num, "/", test_cases[q_num], "passed | score:", score)
	total_coding_score += score

print("Your total score of coding section:", total_coding_score)
```

For each question, **calculate the number of the passed test cases** and compare with the number of all test cases. If not all are passed, score of that question will be the number of the passed test cases multiplied by the credits for one test case. If all are passed, then the score will be full.

Finally `total_coding_score` is calculated.

### 4. `classroom.yml`

The `classroom.yml` file should be similar to this:

```yaml
setup:
    outputs:
      	matrix: ${{ steps.load.outputs.matrix }}
    ...
    run: |
    	data=`cat .github/workflows/config.json | tr '\n' ' ' | tr '\r' ' '`
        echo "::set-output name=matrix::$data"

    ...
testing:
    name: Grading Q${{matrix.q_num}}
    needs: setup
    continue-on-error: true
    timeout-minutes: 3
    strategy:
    	matrix:
    		q_num: ${{ fromJSON(needs.setup.outputs.matrix).q_nums }}
    steps:
    ...
```

First, read question information from `config.json` created in step [1.3.](#13-student-repository) and generate parallel jobs to test each question. Set timeout for each question as 3 minutes and continue on error flag.

```shell
cp files/${{matrix.q_num}}/q.cc coding_grader/${{matrix.q_num}}/
echo "--------- student test ---------"
bazel run --config=asan --ui_event_filters=-info,-stdout,-stderr //files/${{matrix.q_num}}:student_test
if [ $? -ne 0 ] ; then  exit 1; fi
echo "--------- grader test ---------"
bazel run --config=asan --ui_event_filters=-info,-stdout,-stderr //coding_grader/${{matrix.q_num}}:grader_test 2>&1 | tee Q${{matrix.q_num}}res.txt
grep "OK" Q${{matrix.q_num}}res.txt > Q${{matrix.q_num}}res_.txt
chmod 777 ~/.cache/* -R 
```

If the student test is failed, then 0 point will be given for that question and stop running the following tests. Else run the grader test and count the number of passed test cases.

```yaml
- name: Collect result
  uses: actions/download-artifact@v3
  with:
    name: subscore
```

Collecting the result of each question.

```shell
git add ScoresCodingTotal.txt
git commit -m "Add autograding results"
git push origin HEAD:main -f
```

Update `ScoresCodingTotal`.
