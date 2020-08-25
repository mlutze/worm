#!/usr/bin/env python3

import sys
import ast
import fileinput

# constants
RESULT = "result"
JUMP_LABEL = "jump-label"
ZERO = "zero"

# TODO: update to distinguish input files
def read_input():
    return "".join(line for line in fileinput.input())

def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def panic(message, line):
    error(f"Error on line {line}:")
    error(message)
    exit(1)

class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.registers = set([RESULT, ZERO, JUMP_LABEL])
        self.arg_count = 0
        self.label_count = 0
        self.lines = []
        self.li(ZERO, 0)
    
    def add_arg(self):
        self.arg_count += 1
        arg_name = f"arg-{self.arg_count}"
        self.registers.add(arg_name)
        return arg_name

    def add_label(self):
        self.label_count += 1
        label_name = f"label-{self.label_count}"
        return label_name

    def rem_arg(self):
        self.arg_count -= 1

    def visit_Assign(self, node):
        if (len(node.targets) > 1):
            panic("Multiple assignment targets")
        self.visit(node.value)
        target = node.targets[0].id
        self.registers.add(target)
        self.cp(target, RESULT)

    def visit_AugAssign(self, node):
        self.visit(node.value)
        target = node.target.id
        if isinstance(node.op, ast.Add):
            self.add(target, target, RESULT)
        elif isinstance(node.op, ast.Sub):
            self.sub(target, target, RESULT)
        elif isinstance(node.op, ast.Mult):
            self.mul(target, target, RESULT)
        elif isinstance(node.op, ast.FloorDiv):
            self.div(target, target, RESULT)
        elif isinstance(node.op, ast.Mod):
            self.rem(target, target, RESULT)
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
        self.visit(node.left)
        arg = self.add_arg()
        self.cp(arg, RESULT)
        self.visit(node.right)
        if isinstance(node.op, ast.And):
            pass

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
        self.li(RESULT, node.value) 

    def visit_Call(self, node): # will need to handle non-name functions
        func = node.func.id
        if len(node.args) != 1:
            panic("Non-single print arguments.", node.lineno)
        elif node.keywords != []:
            panic("Print keyword argument.", node.lineno)
        arg = node.args[0]
        if func == "print": 
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
            # push args, locals onto stack
            # move stack pointer
            # set return label
            # jump to function
            # label for return

            # question: should pop off need to happen before or after jump?
            panic("Unsupported function call.", node.lineno)
    
    def visit_Name(self, node):
        if (node.id not in self.registers):
            panic("Unknown name.", node.lineno)
        self.cp(RESULT, node.id)

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
            if isinstance(subnode, ast.Break):
                self.j_to(end_label)
            elif isinstance(subnode, ast.Continue):
                self.j_to(start_label)
            else:
                self.visit(subnode)
        self.j_to(start_label)
        self.label(end_label)

    def visit_FunctionDef(self, node):
        # compile time stuff:
        # map arg names to registers
        
        # run time stuff:
        # pop each arg off stack into registers, in order
        # execute each non-return node

        # for return line:
        # execute body, put result in result reg, jump back to return pointer, reset stack pointer
        
        panic("Unsupported definition.", node.lineno)
        

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


    # not a real instruction
    def jeqz_to(self, src, label):
        self.li(JUMP_LABEL, label)
        self.jeqz(src, JUMP_LABEL)

    # not a real instruction
    def j_to(self, label):
        self.li(JUMP_LABEL, label)
        self.j(JUMP_LABEL)

    # not a real instruction
    def cp(self, dest, src):
        self.add(dest, ZERO, src)

    def do(self, cmd, *args):
        self.lines.append(cmd + " " + ", ".join(str(arg) for arg in args))

    def label(self, name):
        self.lines.append(f"{name}:")
    
    def get_code(self):
        if len(self.registers) > 32:
            panic("Expression stack overflow.", -1)
        allo_regs = ["allocate-registers " + ", ".join(self.registers)]
        halt = ["halt"]
        return allo_regs + self.lines + halt

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

