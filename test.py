#!/usr/bin/env python3
import subprocess
import tempfile
import unittest

def make_temp_file(contents: str) -> str:
    _, tmppath = tempfile.mkstemp(dir="/tmp", text=True)
    with open(tmppath, "w") as tmpfile:
        tmpfile.write(contents)
        tmpfile.close()
    return tmppath

def execute_python(script: str, input: str) -> str:
    script_path = make_temp_file(script)
    
    result = subprocess.run(["python3", script_path], input=input, text=True, capture_output=True)
    return result.stdout

def execute_worm(script: str, input: str) -> str:
    script_path = make_temp_file(script)
    compiler_result = subprocess.run(["./compiler.py", script_path], text=True)

    slim_path = make_temp_file(compiler_result.stdout)
    slim_result = subprocess.run(["./interpreter.py", script_path], input=input, text=True, capture_output=True)

    return slim_result.stdout

class CompilerTest(unittest.TestCase):

    def do_test_script(self, script: str, input: str) -> None:
        python_result = execute_python(script, input)
        worm_result = execute_python(script, input)
        self.assertEqual(python_result, worm_result)

    def test_count(self):
        script = """
i = 0
while i < 10:
    print(i)
    i = i + 1
"""
        self.do_test_script(script, "")

    def test_fact(self):
        script = """
i = 1
n = int(input())
product = 1
while i <= n:
    product = product * i
    i += 1
print(product)
"""
        self.do_test_script(script, "10\n")


if __name__ == "__main__":
    unittest.main()
