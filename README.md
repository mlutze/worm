# Worm
A small subset of Python compiling to SLIM assembly, the language interpreted by a hypothetical machine as described in [Concrete Abstractions](https://gustavus.edu/mcs/max/concrete-abstractions.html) by Max Hailperin, Barbara Kaiser, and Karl Knight.

# Data Types
SLIM assembly only supports the integer data type. As such, floating-points and strings are not valid in Worm.
Integer values are handled as normal; boolean values are implicitly promoted to integers.

# Built-in functions
Worm supports two of Python's built-in functions, albeit clumsily: `print` and `input`.

Due to the datatype limitation, each of these function's calling must use `int` casting:
* `print(int(x))`
* `int(input())`

Neither function may take other arguments.

# Language features
Function definitions and calls are supported, using only named positional arguments.

```
def f(x, y):
    return x * 2 + y
```

While-loops are also supported:

```
x = 0
while x < 10:
    print(int(x))
```

Boolean operators evaluate as in Python, though all output is represented as integers.

```
print(int(5 and False)) # writes 0
```

