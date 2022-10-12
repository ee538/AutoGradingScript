#!/bin/bash

q_nums=( "$@" )
echo "passed:"
for q_num in "${q_nums[@]}"; do echo "\"$q_num\":" `bazel test sol/$q_num:grader_test --test_output=all --config=asan 2>&1 | grep "OK" 2>&1 | sed -n '$='`","; done
echo "failed:"
for q_num in "${q_nums[@]}"; do echo "\"$q_num\":" `bazel test sol/$q_num:grader_test --test_output=all --config=asan 2>&1 | grep "FAIL" 2>&1 | sed -n '$='`","; done
echo "memory misuse:"
for q_num in "${q_nums[@]}"; do echo "\"$q_num\":" `bazel test sol/$q_num:grader_test --test_output=all --config=asan 2>&1 | grep "AddressSanitizer" 2>&1 | sed -n '$='`","; done


