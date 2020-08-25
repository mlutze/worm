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
        script = "print(int(123))"
        self.do_test_script(script, "")

    def test_var(self):
        script = """
a = 123
print(int(a))
"""
        self.do_test_script(script, "")

    def test_augassign(self):
        script = """
a = 10
a += 5
print(int(a))
"""
        self.do_test_script(script, "")

    def test_unaryop(self):
        script = """
a = 99
b = -a
print(int(b))
"""
        self.do_test_script(script, "")

    def test_binop(self):
        script = "print(int(1 + 2))"
        self.do_test_script(script, "")

    def test_binop_complex(self):
        script = "print(int(12 + 34 - 56 * 78 // 90))"
        self.do_test_script(script, "")

    def test_bool(self):
        script = "print(int(True))"
        self.do_test_script(script, "")

    def test_boolop(self):
        script = "print(int(False or True))"
        self.do_test_script(script, "")

    def test_boolop_complex(self):
        script = "print(int(not(12 and 34 or False)))"
        self.do_test_script(script, "")

    def test_if(self):
        script = """
if 1 == 2:
    print(int(3))
else:
    print(int(4))
"""
        self.do_test_script(script, "")

    def test_while(self):
        script = """
i = 10
while i > 0:
    print(int(i))
    i -= 1
"""
        self.do_test_script(script, "")

    def test_func(self):
        script = """
def f(x):
    return 5

print(int(f(3)))
"""
        self.do_test_script(script, "")

    @unittest.skip
    def test_recursion(self):
        script = """
def fact(x):
    if x == 1:
        return 1
    else:
        return x * fact(x - 1)

print(int(fact(10)))
"""
        self.do_test_script(script, "")

    @unittest.skip
    def test_multiple_recursion(self):
        script = """
def choose(n, k):
    if (k == 0):
        return 1
    elif (k == n):
        return 1
    else:
        return choose(n - 1, k - 1) + choose(n - 1, k)
print(int(choose(10, 4)))
"""
        self.do_test_script(script, "")

if __name__ == "__main__":
    unittest.main()
