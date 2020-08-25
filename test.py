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
    
    result = subprocess.run(["python3", script_path], input=input, text=True, capture_output=True, timeout=1)
    return result.stdout

def execute_worm(script: str, input: str) -> str:
    script_path = make_temp_file(script)
    compiler_result = subprocess.run(["./compiler.py", script_path], text=True, capture_output=True, timeout=1)

    slim_path = make_temp_file(compiler_result.stdout)
    slim_result = subprocess.run(["./interpreter.py", slim_path], input=input, text=True, capture_output=True, timeout=1)

    return slim_result.stdout

class CompilerTest(unittest.TestCase):

    def do_test_script(self, script: str, input: str) -> None:
        python_result = execute_python(script, input)
        worm_result = execute_worm(script, input)
        self.assertEqual(python_result, worm_result)

    def test_print(self):
        script = "print(123)"
        self.do_test_script(script, "")

    def test_var(self):
        script = """
a = 123
print(a)
"""
        self.do_test_script(script, "")

    def test_binop(self):
        script = "print(1 + 2)"
        self.do_test_script(script, "")

    def test_binop_complex(self):
        script = "print(12 + 34 - 56 * 78 // 90)"
        self.do_test_script(script, "")

    def test_if(self):
        script = """
if 1 == 2:
    print(3)
else:
    print(4)
"""
        self.do_test_script(script, "")


if __name__ == "__main__":
    unittest.main()
