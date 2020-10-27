#!/usr/bin/env python3

import pathlib
import unittest
from typing import List

from worm.slim.interpreter import Interpreter
from worm.util.console import StaticConsole


def get_test_file(name: str) -> str:
    path = pathlib.Path(__file__).parent.joinpath("resources").joinpath(name)
    return path.read_text()


class InterpreterTest(unittest.TestCase):

    def do_test(self, file_name: str, in_lines: List[str], out_lines: List[str], out_errors: List[str] = None) -> None:
        code = get_test_file(file_name)
        console = StaticConsole(in_lines)
        interpreter = Interpreter(console)
        interpreter.interpret(code)
        self.assertEqual(console.output, out_lines)
        self.assertEqual(console.error, out_errors or [])

    def test_count_to_ten(self):
        expected = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        self.do_test("count-to-ten.slim", [], expected)

    def test_write_larger_1(self):
        in_lines = ["1", "2"]
        expected = ["2"]
        self.do_test("write-larger.slim", in_lines, expected)

    def test_write_larger_2(self):
        in_lines = ["2", "1"]
        expected = ["2"]
        self.do_test("write-larger.slim", in_lines, expected)

    def test_iterative_factorial(self):
        in_lines = ["5"]
        expected = ["120"]
        self.do_test("iterative-factorial.slim", in_lines, expected)

    def test_two_factorials(self):
        in_lines = ["5"]
        expected = ["3628920"]
        self.do_test("two-factorials.slim", in_lines, expected)

    def test_double_factorial(self):
        in_lines = ["3"]
        expected = ["720"]
        self.do_test("double-factorial.slim", in_lines, expected)

    def test_recursive_factorial(self):
        in_lines = ["5"]
        expected = ["120"]
        self.do_test("recursive-factorial.slim", in_lines, expected)

    def test_overflow(self):
        expected = ["-2147483648"]
        self.do_test("overflow.slim", [], expected)

    def test_unknown_opcode(self):
        expected = [
            "Unknown opcode 'do' in line 3.",
            "Unknown opcode 'loop' in line 4.",
        ]
        self.do_test("unknown-opcode.slim", [], [], expected)

    def test_unknown_name(self):
        expected = [
            "Unknown name 'reg' in line 1."
        ]
        self.do_test("unknown-name.slim", [], [], expected)

    def test_missing_argument(self):
        expected = [
            "Missing argument in line 3."
        ]
        self.do_test("missing-argument.slim", [], [], expected)

    def test_too_many_arguments(self):
        expected = [
            "Too many arguments in line 3."
        ]
        self.do_test("too-many-arguments.slim", [], [], expected)

    def test_no_commas(self):
        expected = ["3"]
        self.do_test("no-commas.slim", [], expected)

    def test_extra_commas(self):
        expected = ["3"]
        self.do_test("extra-commas.slim", [], expected)

    def test_allocate_registers_comma(self):
        expected = ["Unknown opcode 'allocate-registers' in line 1."]
        self.do_test("allocate-registers-comma.slim", [], [], expected)

    def test_negative_dividend(self):
        expected = ["-1"]
        self.do_test("negative-dividend.slim", [], expected)

    def test_negative_divisor(self):
        expected = ["1"]
        self.do_test("negative-divisor.slim", [], expected)
