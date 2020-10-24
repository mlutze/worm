#!/usr/bin/env python3
from worm.interpreter import Interpreter
from worm.console import StaticConsole
from worm.compiler import Compiler
import unittest
from typing import List


def execute_python(script: str, input: str) -> List[str]:
    input_lines = iter(input.splitlines())

    output_lines: List[str] = []
    env = {
        "print": output_lines.append,
        "input": input_lines.__next__
    }
    exec(script, env)
    return [str(i) for i in output_lines]


def execute_worm(script: str, input: str) -> List[str]:
    console = StaticConsole(input)
    compiler = Compiler()
    interpreter = Interpreter(console)

    slim_code = compiler.compile(script)
    interpreter.interpret(slim_code)

    return console.output


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

    def test_multiple_recursion(self):
        script = """
def fib(x):
    if x <= 1:
        return x
    else:
        return fib(x - 1) + fib(x - 2)

print(int(fib(4)))
"""
        self.do_test_script(script, "")

    def test_multiple_recursion_2(self):
        script = """
def fib(x):
    if x <= 1:
        return x
    else:
        a = fib(x - 1)
        b = fib(x - 2)
        return a + b
print(int(fib(4)))
"""
        self.do_test_script(script, "")

    def test_multiple_recursion_3(self):
        script = """
def fib(x):
    if x <= 1:
        return x
    else:
        x1 = x - 1
        x2 = x - 2
        return fib(x1) + fib(x2)

print(int(fib(4)))
"""
        self.do_test_script(script, "")

    def test_multiple_recursion_4(self):
        script = """
def fib(x):
    if x <= 1:
        return x
    else:
        x1 = x - 1
        x2 = x - 2
        a = fib(x1)
        b = fib(x2)
        return a + b
print(int(fib(4)))
"""
        self.do_test_script(script, "")

    def test_multiple_recursion_x(self):
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

    def test_break(self):
        script = """
x = 0
while True:
    print(int(x))
    x += 1
    if x > 5:
        break
"""
        self.do_test_script(script, "")

    def test_nested_break(self):
        script = """
x = 0
y = 0
while True:
    x = 0
    while True:
        print(int(x))
        print(int(y))
        x += 1
        if x > 5:
            break
    if y > 3:
        break
    y += 1
"""
        self.do_test_script(script, "")

    def test_continue(self):
        script = """
x = 0
while x < 9:
    x += 1
    if x % 2 == 0:
        continue
    print(int(x))
"""
        self.do_test_script(script, "")

    def test_nested_continue(self):
        script = """
x = 0
y = 0
while y < 10:
    y += 1
    x = 0
    if y % 3 == 0:
        continue
    while x < 5:
        x += 1
        if x % 2 == 0:
            continue
"""
        self.do_test_script(script, "")

    def test_walrus(self):
        script = """
x = 0
while (x := x + 1) < 10:
    print(int(x))
"""
        self.do_test_script(script, "")


if __name__ == "__main__":
    unittest.main()
