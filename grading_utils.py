#!/usr/bin/env python3

import os, json, subprocess, argparse, re, shutil, sys, platform
from pathlib import Path
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

GRADER_PLATFORM_LABELS = {
    'macos-arm64': 'macos/arm64',
    'linux-amd64': 'linux/amd64',
}

GRADER_PLATFORM_ALIASES = {
    'arm64': 'macos-arm64',
    'darwin-arm64': 'macos-arm64',
    'mac-arm64': 'macos-arm64',
    'macos-arm64': 'macos-arm64',
    'macos-aarch64': 'macos-arm64',
    'linux-amd64': 'linux-amd64',
    'linux-x86-64': 'linux-amd64',
    'linux-x64': 'linux-amd64',
    'amd64': 'linux-amd64',
    'x86-64': 'linux-amd64',
    'x64': 'linux-amd64',
}

def normalize_grader_platform(value: str | None) -> str | None:
    if value is None or value == '':
        return None

    normalized = value.strip().lower().replace('/', '-').replace('_', '-')
    platform_key = GRADER_PLATFORM_ALIASES.get(normalized)
    if platform_key is None:
        allowed = ', '.join(sorted(GRADER_PLATFORM_LABELS.values()))
        raise SystemExit(f'Unknown grader platform "{value}". Expected one of: {allowed}.')
    return platform_key

def infer_current_grader_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == 'darwin' and machine in ('arm64', 'aarch64'):
        return 'macos-arm64'
    if system == 'linux' and machine in ('x86_64', 'amd64'):
        return 'linux-amd64'
    raise SystemExit(
        f'Unsupported grader build host: {platform.system()} {platform.machine()}. '
        'Use macos/arm64 or linux/amd64.'
    )

def docker_linux_amd64_hint() -> str:
    return (
        "docker run --rm --platform linux/amd64 -v \"$PWD\":/work -w /work "
        "gcr.io/bazel-public/bazel:8.4.2 bash -lc "
        "'python3 AutoGradingScript/grading_utils.py --hide-grader --grader-platform linux/amd64'"
    )

def validate_host_for_grader_platform(grader_platform: str) -> None:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if grader_platform == 'macos-arm64':
        if system == 'darwin' and machine in ('arm64', 'aarch64'):
            return
        raise SystemExit('macos/arm64 grader binaries must be generated on Apple Silicon macOS.')

    if grader_platform == 'linux-amd64':
        if system == 'linux' and machine in ('x86_64', 'amd64'):
            return
        raise SystemExit(
            'linux/amd64 grader binaries must be generated in a linux/amd64 environment.\n'
            'On Apple Silicon macOS, run:\n' + docker_linux_amd64_hint()
        )

def file_description(path: Path) -> str:
    try:
        return subprocess.check_output(['file', str(path)], text=True).strip()
    except Exception as e:
        raise SystemExit(f'Unable to inspect {path}: {e}')

def verify_grader_binary_platform(path: Path, grader_platform: str) -> None:
    description = file_description(path)
    print(description)

    if grader_platform == 'macos-arm64':
        ok = 'Mach-O' in description and 'arm64' in description
    elif grader_platform == 'linux-amd64':
        ok = 'ELF 64-bit' in description and ('x86-64' in description or 'x86_64' in description)
    else:
        ok = False

    if not ok:
        expected = GRADER_PLATFORM_LABELS[grader_platform]
        raise SystemExit(f'{path} is not a {expected} grader binary.')

def prompt_grader_platform() -> str:
    print('================================================================================')
    print('Please choose the hidden grader binary platform:')
    print('  1) linux/amd64  - for GitHub Classroom on ubuntu-22.04')
    print('  2) macos/arm64  - for local Apple Silicon testing only')
    choice = input('Platform [1=linux/amd64, 2=macos/arm64] (default: 1): ').strip()
    if choice == '' or choice == '1':
        return 'linux-amd64'
    if choice == '2':
        return 'macos-arm64'
    return normalize_grader_platform(choice)

def run_test(path_q_num, student_test=False, return_all=False, hide_grader=False, grader_platform=None):
    grader_platform = normalize_grader_platform(grader_platform)
    if hide_grader:
        grader_platform = grader_platform or infer_current_grader_platform()
        validate_host_for_grader_platform(grader_platform)

    tasks = [path_q_num + ':grader_test']

    # os.system('cp ../submission/files/' + q_num + '/q.cc coding_grader/' + q_num + '/')
    if student_test:
        # os.system('cp ../submission/files/' + q_num + '/student_test.cc coding_grader/' + q_num + '/')
        tasks = [path_q_num + ':student_test'] + tasks
    print('================================================================================\n')
    print(path_q_num + ' testing:')
    for task in tasks:
        if hide_grader:
            bazel_entry = [
                'cc_binary(\n',
                '    name="libgrader_test.so",\n',
                '    srcs=["grader_test.cc", "q.h"],\n',
                '    copts=["--std=c++17"],\n',
                '    deps=[\n',
                '        "@com_google_googletest//:gtest",\n',
                '    ],\n',
                '    linkshared=True,\n',
                '    linkstatic=False,\n',
                ')\n'
            ]
            if sys.platform == 'darwin':
                bazel_entry.insert(-2, '    linkopts=["-Wl,-undefined,dynamic_lookup"],\n')

            with open(os.path.join(path_q_num, "BUILD"), 'r') as f:
                text = f.read()
                source_build_text = text.replace("libgrader_test.so", "grader_test.cc")
                text = source_build_text.replace("grader_test.cc", "libgrader_test.so")
            with open(os.path.join(path_q_num, "BUILD"), 'w') as f:
                f.write(text)
                f.writelines(bazel_entry)

        test_output, error_msg = bazel_test(task)
        print(test_output + error_msg)

        if hide_grader:
            if error_msg != '':
                with open(os.path.join(path_q_num, "BUILD"), 'w') as f:
                    f.write(source_build_text)
                continue

            built_grader = Path('bazel-bin') / path_q_num / 'libgrader_test.so'
            hidden_grader = Path(path_q_num) / 'libgrader_test.so'
            if hidden_grader.exists():
                hidden_grader.unlink()
            if built_grader.exists():
                shutil.copy2(built_grader, hidden_grader)
                verify_grader_binary_platform(hidden_grader, grader_platform)
            else:
                raise SystemExit(f'ERROR: {built_grader} not found.')

            with open(os.path.join(path_q_num, "BUILD"), 'r') as f:
                lines = f.readlines()
            with open(os.path.join(path_q_num, "BUILD"), 'w') as f:
                f.writelines(lines[:-len(bazel_entry)])

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

RULES_CC_LOAD = 'load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library", "cc_test")'
CC_RULES = ("cc_binary(", "cc_library(", "cc_test(")
CC_LIBRARY_BLOCK = re.compile(r'cc_library\(\n.*?^\)', flags=re.MULTILINE | re.DOTALL)
CC_TEST_BLOCK = re.compile(r'cc_test\(\n.*?^\)', flags=re.MULTILINE | re.DOTALL)

def ensure_cpplib_alwayslink(text: str) -> str:
    def add_alwayslink(match):
        block = match.group(0)
        if not re.search(r'name\s*=\s*"CPPLib"', block) or 'alwayslink' in block:
            return block

        lines = block.splitlines(keepends=True)
        insert_at = next((i for i, line in enumerate(lines) if 'visibility' in line), len(lines) - 1)
        lines.insert(insert_at, '    alwayslink = True,\n')
        return ''.join(lines)

    return CC_LIBRARY_BLOCK.sub(add_alwayslink, text)

def remove_grader_test_rule(text: str) -> str:
    def drop_grader_test(match):
        block = match.group(0)
        if re.search(r'name\s*=\s*"grader_test"', block):
            return ''
        return block

    text = CC_TEST_BLOCK.sub(drop_grader_test, text)
    return re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'

def strip_staff_notes(text: str) -> str:
    return re.split(r'\n## Staff Notes\n', text, maxsplit=1)[0].rstrip() + '\n'

def copy_path(src: Path, dst: Path, ignore_names=()):
    if src.is_dir():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*ignore_names))
    else:
        shutil.copy2(src, dst)

def require_absent(path: Path) -> None:
    if path.exists():
        raise SystemExit(
            f'{path} already exists. Please move or delete it manually before regenerating.'
        )

def set_bazel_dep(text: str, dep_name: str, replacement: str) -> str:
    dep_pattern = re.compile(
        r'\n?bazel_dep\(\s*name\s*=\s*"' + re.escape(dep_name) + r'".*?\)\s*\n?',
        flags=re.DOTALL,
    )
    text = dep_pattern.sub('\n', text)
    return text.rstrip() + '\n' + replacement + '\n'

def normalize_bazel_compatibility(repo_root: str='.') -> None:
    """Keep generated repos compatible with Bazel 9 and Bazelisk defaults."""
    root = Path(repo_root)
    module_file = root / 'MODULE.bazel'
    if module_file.exists():
        text = module_file.read_text()
        text = set_bazel_dep(text, 'rules_cc', 'bazel_dep(name = "rules_cc", version = "0.2.8")')
        text = set_bazel_dep(
            text,
            'googletest',
            'bazel_dep(name = "googletest", version = "1.17.0.bcr.2", repo_name = "com_google_googletest")',
        )
        module_file.write_text(text)

    bazelversion_file = root / '.bazelversion'
    bazelversion_file.write_text('8.4.2\n')

    for build_file in list(root.glob('files/*/BUILD')) + list(root.glob('sol/*/BUILD')) + list(root.glob('*/BUILD')):
        text = build_file.read_text()
        if not any(rule in text for rule in CC_RULES):
            continue

        if '@rules_cc//cc:defs.bzl' in text:
            text = re.sub(
                r'^load\("@rules_cc//cc:defs\.bzl".*\)\n\n?',
                RULES_CC_LOAD + '\n\n',
                text,
                count=1,
                flags=re.MULTILINE)
        else:
            text = RULES_CC_LOAD + '\n\n' + text
        text = ensure_cpplib_alwayslink(text)
        build_file.write_text(text)

def generate_coding_grader(coding_grader_name, hide_grader=False, grader_platform=None):
    normalize_bazel_compatibility()
    grader_platform = normalize_grader_platform(grader_platform)
    if hide_grader:
        grader_platform = grader_platform or infer_current_grader_platform()
        validate_host_for_grader_platform(grader_platform)
        print('Hidden grader platform: ' + GRADER_PLATFORM_LABELS[grader_platform])

    all_files = sorted(os.listdir('sol'))
    ungrading_q_nums = list(filter(lambda file:(not os.path.isfile('sol/' + file)), all_files))
    q_nums = list(filter(lambda file:(os.path.isfile('sol/' + file + '/grader_test.cc')), ungrading_q_nums))

    # execute all the grader tests for all the questions and get the testing results
    test_results = {
        q_num: run_test('sol/' + q_num, hide_grader=hide_grader, grader_platform=grader_platform)
        for q_num in q_nums
    }
    output_json(test_results, '', True)

    # if some of the test are not passed, then exit
    failed_test = [test_results[q_num]['failed'] for q_num in test_results]
    error_test = [test_results[q_num]['error'] for q_num in test_results]
    if any(failed_test) or any(error_test):
        print("Error detected in some test cases!")
        exit()

    # copy the 'sol' folder as coding_grader_name, remove the solutions
    coding_grader_path = Path(coding_grader_name)
    require_absent(coding_grader_path)
    coding_grader_path.mkdir()
    ignored = ['q.cc', 'student_test.cc', '*.csh']
    if hide_grader:
        ignored.append('grader_test.cc')
    for q_num in q_nums:
        copy_path(Path('sol') / str(q_num), coding_grader_path / str(q_num), ignored)

    normalize_bazel_compatibility(coding_grader_name)

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
        'full_score': full_score,
        'grader_platform': GRADER_PLATFORM_LABELS.get(grader_platform, 'source'),
    }, coding_grader_name + '/questions.json', disp=True)

def generate_assignment(hw_name, hide_grader=False, grader_platform=None):
    normalize_bazel_compatibility()
    grader_platform = normalize_grader_platform(grader_platform)

    coding_grader_name = hw_name + '_CodingGrader'
    all_files = sorted(os.listdir('files'))
    ungrading_q_nums = list(filter(lambda file:(not os.path.isfile('sol/' + file)), all_files))
    if hide_grader:
        q_nums = list(filter(lambda file:(os.path.isfile('sol/' + file + '/libgrader_test.so')), ungrading_q_nums))
    else:
        q_nums = list(filter(lambda file:(os.path.isfile('sol/' + file + '/grader_test.cc')), ungrading_q_nums))
    file_list = [
        '.vscode',
        'files',
        '.bazelrc',
        '.gitignore',
        '.bazelversion',
        'MODULE.bazel',
        'MODULE.bazel.lock',
        'README.md',
        'WORKSPACE'
    ]

    # copy files in file_list to assignment folder
    hw_path = Path(hw_name)
    require_absent(hw_path)
    (hw_path / '.github' / 'workflows').mkdir(parents=True)
    for file in file_list:
        src = Path(file)
        if not src.exists():
            continue
        ignored = ['grader_test.cc'] if hide_grader and file == 'files' else []
        copy_path(src, hw_path / file, ignored)
    if hide_grader:
        readme_file = hw_path / 'README.md'
        if readme_file.exists():
            readme_file.write_text(strip_staff_notes(readme_file.read_text()))
    if not hide_grader:
        for q_num in q_nums:
            shutil.copy2(Path('sol') / q_num / 'grader_test.cc', hw_path / 'files' / q_num / 'grader_test.cc')
    else:
        for build_file in (hw_path / 'files').glob('*/BUILD'):
            if build_file.exists():
                build_file.write_text(remove_grader_test_rule(build_file.read_text()))
    shutil.copy2(Path('AutoGradingScript') / 'classroom.yml', hw_path / '.github' / 'workflows' / 'classroom.yml')

    normalize_bazel_compatibility(hw_name)

    output_json({
        'q_nums': q_nums,
        'grader_repo': 'ee538/' + coding_grader_name,
        'grader_platform': GRADER_PLATFORM_LABELS.get(grader_platform, 'source'),
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
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--hide-grader',
        action='store_true',
        help='Hide grader test cases')
    argparser.add_argument(
        '--grader-platform',
        default='',
        help='Hidden grader binary platform: linux/amd64 or macos/arm64')

    args = argparser.parse_args()
    hide_grader = args.hide_grader
    grader_platform = normalize_grader_platform(args.grader_platform)
    if hide_grader:
        grader_platform = grader_platform or prompt_grader_platform()
        validate_host_for_grader_platform(grader_platform)

    default_name = '_'.join(os.path.split(os.getcwd())[-1].split('_')[1:])
    hw_name = input('Please enter the name of this assignment (default: ' + default_name + '): ')
    if hw_name == '':
        hw_name = default_name
    coding_grader_name = hw_name + '_CodingGrader'

    generate_coding_grader(coding_grader_name, hide_grader, grader_platform)
    generate_assignment(hw_name, hide_grader, grader_platform)

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
        print('Please remove generated folders and libgrader_test.so files manually if needed.')
        print('Generated folders: ' + hw_name + ', ' + coding_grader_name)

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
