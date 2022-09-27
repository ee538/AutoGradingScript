# AutoGradingScript
AutoGradingScript for USC EE-538

**`.github/workflows` should be protected from modified by setting ownership.**

`config.json` should be like:

```json
{"q_num": [1, 2, 3, 4], "grader_repo": "ee538/Summer22_HW5_CodingGrader"}
```

`questions.json` should be like:

```json
{
	"q_nums": ["1", "2", "3", "4"],
	"full_score": {
		"1": 30,
		"2": 30,
		"3": 30,
		"4": 30
	},
	"test_cases": {
		"1": 14,
		"2": 9,
		"3": 7,
		"4": 17
	}
}
```

To get test count, run:

```bash
q_nums=(1 2 3 4 5 7 8)
echo "passed:"
for q_num in "${q_nums[@]}"; do echo "\"$q_num\":" `bazel test sol/$q_num:grader_test --test_output=all --config=asan 2>&1 | grep "OK" 2>&1 | sed -n '$='` ","; done
echo "failed:"
for q_num in "${q_nums[@]}"; do echo "\"$q_num\":" `bazel test sol/$q_num:grader_test --test_output=all --config=asan 2>&1 | grep "FAIL" 2>&1 | sed -n '$='` ","; done
```
`classroom.yml` should be like:

```yaml
name: GitHub Classroom Workflow

on: [push, pull_request]
    
jobs:
  setup:
    name: Loading data
    runs-on: ubuntu-22.04
    outputs:
      matrix: ${{ steps.load.outputs.matrix }}
    steps:
      - uses: actions/checkout@v2 
      - id: load
        name: Load data
        run: |
             data=`cat .github/workflows/config.json`
             echo "::set-output name=matrix::$data"
  testing:
    name: Grading Q${{matrix.q_num}}
    needs: setup
    continue-on-error: true
    runs-on: ubuntu-22.04
    timeout-minutes: 3
    strategy:
        matrix:
            q_num: ${{ fromJSON(needs.setup.outputs.matrix).q_num }}
    steps:
      - uses: actions/checkout@v2 
      - uses: actions/checkout@master
        with:
            repository: ${{ fromJSON(needs.setup.outputs.matrix).grader_repo }}
            path: 'coding_grader'
      - uses: actions/cache@v3
        with:
          path: ~/.cache/bazel
          key: bazel-Q${{matrix.q_num}}
      - name: Clear previous test result
        if: always()
        run: |
            echo "" > Q${{matrix.q_num}}res_.txt
      - name: Prepare for the test result
        uses: actions/upload-artifact@v3
        with:
          name: subscore
          path: Q${{matrix.q_num}}res_.txt
          retention-days: 1
      - name: Test Q${{matrix.q_num}}
        if: always()
        run: |
             cp files/${{matrix.q_num}}/q.cc coding_grader/${{matrix.q_num}}/
             # cp files/${{matrix.q_num}}/{q.cc,q.h} coding_grader/${{matrix.q_num}}/
             echo "--------- student test ---------"
             bazel run --config=asan --ui_event_filters=-info,-stdout,-stderr //files/${{matrix.q_num}}:student_test
             if [ $? -ne 0 ] ; then  exit 1; fi
             echo "--------- grader test ---------"
             bazel run --config=asan --ui_event_filters=-info,-stdout,-stderr //coding_grader/${{matrix.q_num}}:grader_test 2>&1 | tee Q${{matrix.q_num}}res.txt
             grep "OK" Q${{matrix.q_num}}res.txt > Q${{matrix.q_num}}res_.txt
             chmod 777 ~/.cache/* -R 
      - name: Upload result for Q${{matrix.q_num}}
        uses: actions/upload-artifact@v3
        with:
          name: subscore
          path: Q${{matrix.q_num}}res_.txt
          retention-days: 1

  collecting-result:
    name: Collecting result
    needs: [testing, setup]
    runs-on: ubuntu-22.04
    timeout-minutes: 3
    steps:
      - uses: actions/checkout@v2  
      - uses: actions/checkout@master
        with:
            repository: 'ee538/AutoGradingScript'
            path: 'coding_grader'
      - uses: actions/checkout@master
        with:
            repository: ${{ fromJSON(needs.setup.outputs.matrix).grader_repo }}
            path: 'coding_grader'
      - name: Collect result
        uses: actions/download-artifact@v3
        with:
          name: subscore
      - name: Organize the total score (coding questions)
        if: always()
        run: |
             mkdir grades
             mv Q*res_.txt grades
             
             python coding_grader/coding_grades_total.py 2>&1 | tee ScoresCodingTotal.txt
             # clean temporary files
             rm -rf grades
             rm -rf ST_*
             rm -rf coding_grader
             
             TZ='America/Los_Angeles' date >> ScoresCodingTotal.txt
             
             git config --global user.email "ee538.autograder@gmail.com"
             git config --global user.name "AutograderEE538"
             git add ScoresCodingTotal.txt
             
             git commit -m "Add autograding results"
             git push origin HEAD:main -f
```

