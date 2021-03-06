#!/usr/bin/env python3

import sys
import ast
import fileinput
import collections

# constants
RESULT = "result"
JUMP_LABEL = "jump-label"
ZERO = "zero"
ONE = "one"
STACK_POINTER = "stack-pointer"  # always points at next empty slot in stack
MAIN_SCOPE = ""

# TODO: update to distinguish input files


def read_input():
    return "".join(line for line in fileinput.input())


def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def panic(message, line):
    error(f"Error on line {line}:")
    error(message)
    exit(1)


class Namespace:
    def __init__(self, visitor):
        self.visitor = visitor
        self.names = {}
        self.local_count = 0

    def get_or_create_name(self, name):
        """Gets the register for the name, allocating a new one if necessary."""
        if name in self.names:
            id = self.names[name]
        else:
            id = self.add_local()
            self.names[name] = id
        return id

    def add_local(self):
        """Adds an anonymous local variable to the namespace."""

        local_name = self.visitor.local(self.local_count)
        self.local_count += 1
        return local_name

    def __contains__(self, item):
        return item in self.names

    def __getitem__(self, item):
        return self.names[item]

    def __setitem__(self, item, value):
        self.names[item] = value


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.namespaces = {MAIN_SCOPE: Namespace(self)}
        self.scope = MAIN_SCOPE
        self.registers = set([RESULT, ZERO, ONE, JUMP_LABEL, STACK_POINTER])
        self.arg_count = 0
        self.lines = []
        self.break_labels = []
        self.continue_labels = []
        self.label_counts = collections.Counter()

    def arg(self, n):
        """Gets the name for an arg register and allocate it if necessary."""
        arg_name = f"arg-{n}"
        self.registers.add(arg_name)
        return arg_name

    def local(self, n):
        """Gets the name for a local register and allocate it if necessary."""
        local_name = f"local-{n}"
        self.registers.add(local_name)
        return local_name

    def add_arg(self):
        """Gets the name for an anonymous arg and allocate it if necessary."""
        arg_name = self.arg(self.arg_count)
        self.arg_count += 1
        return arg_name

    def add_label(self, name="label"):
        """Gets the name for an anonymous local and allocate it if necessary."""
        self.label_counts[name] += 1
        label_name = f"{name}-{self.label_counts[name]}"
        return label_name

    def get_func_label(self, name):
        """Gets a label pointing to the head of the named function."""
        return f"def-{name}"

    def rem_arg(self):
        """Removes an arg from the arg count."""
        self.arg_count -= 1

    def get_local_namespace(self):
        if self.scope in self.namespaces:
            return self.namespaces[self.scope]
        else:
            self.namespaces[self.scope] = Namespace(self)
            return self.namespaces[self.scope]

    def get_or_create_name(self, name):
        """Get a name from the current namespace, creating it if necessary."""
        namespace = self.get_local_namespace()
        return namespace.get_or_create_name(name)

    def enter_scope(self, name):
        self.scope = name

    def exit_scope(self):
        self.scope = MAIN_SCOPE

    def visit_Assign(self, node):
        if (len(node.targets) > 1):
            panic("Multiple assignment targets")
        self.visit(node.value)
        name = node.targets[0].id

        reg = self.get_or_create_name(name)
        self.cp(reg, RESULT)

    def visit_AugAssign(self, node):
        self.visit(node.value)
        name = node.target.id
        reg = self.get_or_create_name(name)
        if isinstance(node.op, ast.Add):
            self.add(reg, reg, RESULT)
        elif isinstance(node.op, ast.Sub):
            self.sub(reg, reg, RESULT)
        elif isinstance(node.op, ast.Mult):
            self.mul(reg, reg, RESULT)
        elif isinstance(node.op, ast.FloorDiv):
            self.div(reg, reg, RESULT)
        elif isinstance(node.op, ast.Mod):
            self.rem(reg, reg, RESULT)
        else:
            panic("Unsupported binary operator.", node.lineno)

    def visit_BinOp(self, node):
        self.visit(node.left)
        arg = self.add_arg()
        self.cp(arg, RESULT)
        self.visit(node.right)
        if isinstance(node.op, ast.Add):
            self.add(RESULT, arg, RESULT)
        elif isinstance(node.op, ast.Sub):
            self.sub(RESULT, arg, RESULT)
        elif isinstance(node.op, ast.Mult):
            self.mul(RESULT, arg, RESULT)
        elif isinstance(node.op, ast.FloorDiv):
            self.div(RESULT, arg, RESULT)
        elif isinstance(node.op, ast.Mod):
            self.rem(RESULT, arg, RESULT)
        else:
            panic("Unsupported binary operator.", node.lineno)
        self.rem_arg()

    def visit_BoolOp(self, node):
        if (len(node.values) != 2):
            panic("Non-binary boolean operator.",
                  node.lineno)  # TODO handle chains
        left, right = node.values
        self.visit(left)
        end_label = self.add_label("boolop-end")
        next_label = self.add_label("boolop-next")
        if isinstance(node.op, ast.And):
            self.jeqz_to(RESULT, end_label)
            self.visit(right)
        elif isinstance(node.op, ast.Or):
            self.jeqz_to(RESULT, next_label)
            self.j_to(end_label)
            self.label(next_label)
            self.visit(right)
        else:
            panic("Unsupported boolean operator.", node.lineno)
        self.label(end_label)

    def visit_Break(self, node):
        self.j_to(self.break_labels[-1])

    def visit_Compare(self, node):
        if len(node.ops) != 1:
            panic("Chained comparison.", node.lineno)
        self.visit(node.left)
        arg = self.add_arg()
        self.cp(arg, RESULT)
        self.visit(node.comparators[0])
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            self.seq(RESULT, arg, RESULT)
        elif isinstance(op, ast.NotEq):
            self.sne(RESULT, arg, RESULT)
        elif isinstance(op, ast.Lt):
            self.slt(RESULT, arg, RESULT)
        elif isinstance(op, ast.Gt):
            self.sgt(RESULT, arg, RESULT)
        elif isinstance(op, ast.LtE):
            self.sle(RESULT, arg, RESULT)
        elif isinstance(op, ast.GtE):
            self.sge(RESULT, arg, RESULT)
        else:
            panic("Unsupported comparison operator.", node.lineno)
        self.rem_arg()

    def visit_Constant(self, node):
        if not(isinstance(node.value, int)):
            panic("Non-integer literal.", node.lineno)
        self.li(RESULT, int(node.value))

    def visit_Continue(self, node):
        self.j_to(self.continue_labels[-1])

    def visit_Call(self, node):  # will need to handle non-name functions
        func = node.func.id
        if func == "print":
            if len(node.args) != 1:
                panic("Non-single print arguments.", node.lineno)
            elif node.keywords != []:
                panic("Print keyword argument.", node.lineno)
            arg = node.args[0]
            if not(isinstance(arg, ast.Call)):
                panic("Print call not wrapping int.", node.lineno)
            inner_func = arg.func.id
            if (len(arg.args) != 1):
                panic("Multiple print call arguments.", node.lineno)
            elif (arg.keywords != []):
                panic("Print call keyword argument.", node.lineno)
            elif inner_func != "int":
                panic("Print call not wrapping int.", node.lineno)
            self.visit(arg.args[0])
            self.write(RESULT)
        elif func == "int":
            if len(node.args) != 1:
                panic("Non-single int arguments.", node.lineno)
            elif node.keywords != []:
                panic("Int keyword argument.", node.lineno)
            arg = node.args[0]
            if not(isinstance(arg, ast.Call)):
                panic("Int call not wrapping input.", node.lineno)
            inner_func = arg.func.id
            if (arg.args != []):
                panic("Input call argument.", node.lineno)
            elif (arg.keywords != []):
                panic("Input call argument.", node.lineno)
            elif inner_func != "input":
                panic("Int call not wrapping input.", node.lineno)
            self.read(RESULT)
        else:
            return_label = self.add_label("return")
            func_label = self.get_func_label(func)
            for i in range(self.arg_count):
                self.push(self.arg(i))
            for i in range(self.get_local_namespace().local_count):
                self.push(self.local(i))
            self.li(JUMP_LABEL, return_label)
            self.push(JUMP_LABEL)
            for i, arg in enumerate(node.args):
                self.visit(arg)
                self.cp(self.local(i), RESULT)
            self.j_to(func_label)
            self.label(return_label)
            for i in reversed(range(self.get_local_namespace().local_count)):
                self.pop(self.local(i))
            for i in reversed(range(self.arg_count)):
                self.pop(self.arg(i))

    def visit_FunctionDef(self, node):
        func_label = self.get_func_label(node.name)
        end_label = self.add_label(f"end-{node.name}")
        self.enter_scope(node.name)

        self.j_to(end_label)  # don't execute when defining function
        self.label(func_label)
        for arg in node.args.args:  # TODO handle kwargs, defaults, etc.
            # NB: these must be the first names created in this NS
            self.get_or_create_name(arg.arg)
        for subnode in node.body:
            self.visit(subnode)
        self.pop(JUMP_LABEL)
        self.j(JUMP_LABEL)
        self.label(end_label)

        self.exit_scope()

    def visit_Name(self, node):
        namespace = self.get_local_namespace()
        if (node.id not in namespace):
            panic(f"Unknown name: {node.id}", node.lineno)

        reg = namespace[node.id]
        self.cp(RESULT, reg)

    def visit_NamedExpr(self, node):
        self.visit(node.value)
        name = node.target.id

        reg = self.get_or_create_name(name)
        self.cp(reg, RESULT)

    def visit_If(self, node):
        self.visit(node.test)
        false_label = self.add_label("else")
        end_label = self.add_label("end-if")

        self.jeqz_to(RESULT, false_label)
        for subnode in node.body:
            self.visit(subnode)
        self.j_to(end_label)
        self.label(false_label)
        for subnode in node.orelse:
            self.visit(subnode)
        self.label(end_label)

    def visit_Return(self, node):
        self.visit(node.value)
        self.pop(JUMP_LABEL)
        self.j(JUMP_LABEL)

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.UAdd):
            self.visit(node.operand)
        elif isinstance(node.op, ast.USub):
            self.visit(node.operand)
            self.sub(RESULT, ZERO, RESULT)
        elif isinstance(node.op, ast.Not):
            self.visit(node.operand)
            self.seq(RESULT, ZERO, RESULT)
        else:
            panic("Unsupported unary operator.", node.lineno)

    def visit_While(self, node):
        start_label = self.add_label("start-while")
        end_label = self.add_label("end-while")

        self.continue_labels.append(start_label)
        self.break_labels.append(end_label)

        self.label(start_label)
        self.visit(node.test)
        self.jeqz_to(RESULT, end_label)
        for subnode in node.body:
            self.visit(subnode)
        self.j_to(start_label)
        self.label(end_label)

        self.continue_labels.pop()
        self.break_labels.pop()

    # === SLIM Instructions === #

    def add(self, dest, src1, src2):
        self.do("add", dest, src1, src2)

    def sub(self, dest, src1, src2):
        self.do("sub", dest, src1, src2)

    def mul(self, dest, src1, src2):
        self.do("mul", dest, src1, src2)

    def div(self, dest, src1, src2):
        self.do("div", dest, src1, src2)

    # same as div; unused
    def quo(self, dest, src1, src2):
        self.do("quo", dest, src1, src2)

    def rem(self, dest, src1, src2):
        self.do("rem", dest, src1, src2)

    def seq(self, dest, src1, src2):
        self.do("seq", dest, src1, src2)

    def sne(self, dest, src1, src2):
        self.do("sne", dest, src1, src2)

    def slt(self, dest, src1, src2):
        self.do("slt", dest, src1, src2)

    def sgt(self, dest, src1, src2):
        self.do("sgt", dest, src1, src2)

    def sle(self, dest, src1, src2):
        self.do("sle", dest, src1, src2)

    def sge(self, dest, src1, src2):
        self.do("sge", dest, src1, src2)

    def ld(self, dest, addr):
        self.do("ld", dest, addr)

    def st(self, src, addr):
        self.do("st", src, addr)

    def li(self, register, value):
        assert register in self.registers, register
        self.do("li", register, value)

    def read(self, dest):
        self.do("read", dest)

    def write(self, src):
        self.do("write", src)

    def jeqz(self, src, addr):
        self.do("jeqz", src, addr)

    def j(self, addr):
        self.do("j", addr)

    # === Helper "Instructions" === #

    def jeqz_to(self, src, label):
        self.li(JUMP_LABEL, label)
        self.jeqz(src, JUMP_LABEL)

    def j_to(self, label):
        self.li(JUMP_LABEL, label)
        self.j(JUMP_LABEL)

    def cp(self, dest, src):
        self.add(dest, ZERO, src)

    def push(self, src):
        self.st(src, STACK_POINTER)
        self.add(STACK_POINTER, STACK_POINTER, ONE)

    def pop(self, dest):
        self.sub(STACK_POINTER, STACK_POINTER, ONE)
        self.ld(dest, STACK_POINTER)

    def do(self, cmd, *args):
        self.lines.append(cmd + " " + ", ".join(str(arg) for arg in args))

    def label(self, name):
        self.lines.append(f"{name}:")

    def comment(self, text):
        self.lines.append(f";; {text}")

    def get_code(self):
        if len(self.registers) > 32:
            panic("Expression stack overflow.", -1)
        allo_regs = ["allocate-registers " + ", ".join(sorted(self.registers))]
        loads = [f"li {ZERO}, 0", f"li {ONE}, 1", f"li {STACK_POINTER}, 0"]
        halt = ["halt"]
        return allo_regs + loads + self.lines + halt


class Compiler:
    def compile(self, code):
        visitor = Visitor()
        tree = ast.parse(code)
        visitor.visit(tree)
        return "".join(line + "\n" for line in visitor.get_code())


def main():
    output = Compiler().compile(read_input())
    print(output)


if __name__ == "__main__":
    main()
