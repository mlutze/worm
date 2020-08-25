#!/usr/bin/env python3

import sys
import ast
import fileinput

# constants
RESULT = "result"
JUMP_LABEL = "jump-label"
ZERO = "zero"
ONE = "one"
STACK_POINTER = "stack-pointer" # always points at next empty slot in stack
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
        if name in self.names:
            id = self.names[name]
        else:
            id = self.add_local()
            self.names[name] = id
        return id

    def add_local(self):
        local_name = f"local-{self.local_count}"
        self.local_count += 1
        self.visitor.registers.add(local_name)
        return local_name 

    def __contains__(self, item):
        return item in self.names

    def __getitem__(self, item):
        return self.names[item]


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.namespaces = {MAIN_SCOPE: Namespace(self)}
        self.scope = MAIN_SCOPE
        self.registers = set([RESULT, ZERO, ONE, JUMP_LABEL, STACK_POINTER])
        self.arg_count = 0
        self.label_count = 0
        self.local_count = 0
        self.lines = []
    
    def add_arg(self):
        arg_name = f"arg-{self.arg_count}"
        self.arg_count += 1
        self.registers.add(arg_name)
        return arg_name

    def add_label(self):
        label_name = f"label-{self.label_count}"
        self.label_count += 1
        return label_name

    def get_func_label(self, name):
        return f"label-{name}"

    def rem_arg(self):
        self.arg_count -= 1

    def rem_local(self):
        self.local_count -= 1

    def get_local_namespace(self):
        if self.scope in self.namespaces:
            return self.namespaces[self.scope]
        else:
            self.namespaces[self.scope] = Namespace(self)
            return self.namespaces[self.scope]

    def get_or_create_name(self, name):
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
            panic("Non-binary boolean operator.", node.lineno) # TODO handle chains
        left, right = node.values
        self.visit(left)
        end_label = self.add_label()
        next_label = self.add_label()
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
        
            
    def visit_Constant(self, node):
        if not(isinstance(node.value, int)):
            panic("Non-integer literal.", node.lineno)
        self.li(RESULT, int(node.value)) 

    def visit_Call(self, node): # will need to handle non-name functions
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
            return_label = self.add_label()
            func_label = self.get_func_label(func)
            for i in range(self.arg_count):
                self.push(f"arg-{i}")
            for i in range(self.local_count):
                self.push(f"local-{i}")
            self.li(JUMP_LABEL, return_label)
            self.push(JUMP_LABEL)
            for arg in node.args:
                self.visit(arg)
                self.push(RESULT)
            self.j_to(func_label)
            self.label(return_label)
            for i in reversed(range(self.local_count)):
                self.pop(f"local-{i}")
            for i in reversed(range(self.arg_count)):
                self.pop(f"arg-{i}")
    
    def visit_Name(self, node):
        namespace = self.get_local_namespace()
        if (node.id not in namespace):
            panic(f"Unknown name: {node.id}", node.lineno)

        reg = namespace[node.id]
        self.cp(RESULT, reg)

    def visit_If(self, node):
        self.visit(node.test)
        false_label = self.add_label()
        end_label = self.add_label()
        
        self.jeqz_to(RESULT, false_label)
        for subnode in node.body:
            self.visit(subnode)
        self.j_to(end_label)
        self.label(false_label)
        for subnode in node.orelse:
            self.visit(subnode)
        self.label(end_label)

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
        start_label = self.add_label()
        end_label = self.add_label()
        
        self.label(start_label)
        self.visit(node.test)
        self.jeqz_to(RESULT, end_label)
        for subnode in node.body:
            if isinstance(subnode, ast.Break): # TODO need to handle break and continue in nested exprs
                self.j_to(end_label)
            elif isinstance(subnode, ast.Continue):
                self.j_to(start_label)
            else:
                self.visit(subnode)
        self.j_to(start_label)
        self.label(end_label)

    def visit_FunctionDef(self, node):
        func_label = self.get_func_label(node.name)
        end_label = self.add_label()
        self.enter_scope(node.name)
        
        self.j_to(end_label) # don't execute when defining function
        self.label(func_label)
        for arg in reversed(node.args.args): # TODO handle kwargs, defaults, etc.
            reg = self.get_or_create_name(arg.arg)
            self.pop(reg)
        for subnode in node.body:
            if isinstance(subnode, ast.Return): # TODO need to handle return in nested exprs
                self.visit(subnode.value)
                self.pop(JUMP_LABEL)
                self.j(JUMP_LABEL)
            else:
                self.visit(subnode)
        self.pop(JUMP_LABEL)
        self.j(JUMP_LABEL)
        self.label(end_label)
        
        self.exit_scope()

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
        allo_regs = ["allocate-registers " + ", ".join(self.registers)]
        loads = [f"li {ZERO}, 0", f"li {ONE}, 1", f"li {STACK_POINTER}, 0"]
        halt = ["halt"]
        return allo_regs + loads + self.lines + halt

def main():
    visitor = Visitor()
    code = read_input()
    tree = ast.parse(code)
    visitor.visit(tree)
    output = visitor.get_code()
    for line in output:
        print(line)
    

if __name__ == "__main__":
    main()

