# fstr

<a href="https://travis-ci.org/rmorshea/fstr"><img alt="Build Status" src="https://travis-ci.org/rmorshea/fstr.svg?branch=master"></a>
<a href="https://pypi.org/project/fstr/"><img alt="PyPI" src="https://img.shields.io/pypi/v/fstr.svg"></a>
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/rmorshea/fstr/blob/master/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-purple.svg"></a>

**1. Use f-string syntax in Python 2:**

```python
import fstr

x = 1
y = 2

template = fstr("{x} + {y} = {x + y}")

print(template.evaluate())
```

```
1 + 2 = 3
```

**2. Use f-string syntax instead of `str.format` in both Python 2 and 3:**

```python
import fstr

common_error_message = fstr("function {function.__name__!r} failed because {error}")

def add(x, y):
    try:
        return x + y
    except Exception as e:
        msg = common_error_message.format(function=add, error=e)
        print(msg)

def sub(x, y):
    try:
        return x + y
    except Exception as e:
        msg = common_error_message.format(function=sub, error=e)
        print(msg)

add(1, "2")
sub("5", 3)
```

```
function 'add' failed because unsupported operand type(s) for +: 'int' and 'str'
function 'sub' failed because can only concatenate str (not "int") to str
```


# Full [PEP-498](https://www.python.org/dev/peps/pep-0498) Compliance

Other backward compatibility libraries for f-string syntax in Python 2 only implement some of the capabilities defined in the PEP's [specification](https://www.python.org/dev/peps/pep-0498/#specification). The test cases for `fstr` were even lifted (with minor changes) from [CPython's test suite](https://github.com/python/cpython/blob/master/Lib/test/test_fstring.py).


## Format Specifiers

Format specifiers may contain evaluated expressions.

```python
import fstr
import decimal

width = 10
precision = 4
value = decimal.Decimal('12.34567')

fstr("result: {value:{width}.{precision}}").evaluate()
```

```
'result:      12.35'
```

Once expressions in a format specifier are evaluated (if necessary), format specifiers are not interpreted by the f-string evaluator. Just as in `str.format()`, they are merely passed in to the `__format__()` method of the object being formatted.


## Lambdas In Expressions

```python
import fstr

fstr("{(lambda x: x*2)(3)}").format()
```

```
'6'
```

## Error Handling

Exact messages will vary depending on whether you are using Python<3.6 or not.

---

```python
import fstr

fstr("x={x")
```

```
File "fstr", line 1
  x={x
      ^
SyntaxError: Mismatched braces in f-string.
```

---

```python
import fstr

fstr("x={!x}")
```

```
File "fstr", line 1
  x={!x}
    ^
SyntaxError: Empty expresion not allowed.
```


# Performance Considerations

`fstr` is not meant to be a replacement for python's f-string syntax. Rather it serves primarily as a slightly slower, but more convenient way to do string formatting in the
cases where you might otherwise use `str.format`. Additionally Python's f-string syntax is able to make performance optimizations at compile time that are not afforded to either `str.format` or `fstr.format`. Given this we only compare `fstr.format` to `str.format`.

The performance of `fstr` differs depending on whether you:

+ Use Python<3.6 or not.
+ Define your f-string template ahead of time.

For example, this will be **significantly** slower

```python
for i in range(10):
   s = fstr("{i}**2 = {i**2}").format(i=i)
```

than if you define your template outside the loop:

```python
template = fstr("{i}**2 = {i**2}")

for i in range(10):
   s = template.format(i=i)
```

## `str.format` vs `fstr.format`

```python
from timeit import timeit

str_setup = "template = '{x}' * 10"
fstr_setup = "import fstr\ntemplate = fstr('{x}' * 10)"

str_result = timeit("template.format(x=1)", setup=str_setup, number=1000000)
fstr_result = timeit("template.format(x=1)", setup=fstr_setup, number=1000000)

print("str.format() : %s seconds" % str_result)
print("fstr.format() : %s seconds" % fstr_result)
```

### Python < 3.6

```
str.format() : 0.741672992706 seconds
fstr.format() : 6.77992010117 seconds
```

### Python >= 3.6

```
str.format: 0.7007193689933047 seconds
fstr.format: 0.9083925349987112 seconds
```
