import pytest
from sys import version_info

from fstr import fstr


def test_basic():
    template = fstr("{x} + {y} = {x + y}", x=1)
    assert template.format(y=2) == "1 + 2 = 3"
    assert template.format(y=3) == "1 + 3 = 4"


def test_basic_format_language():
    template = fstr("{x!r} + {y!r} = {x + y!r}", x="a")
    assert template.format(y="b") == "'a' + 'b' = 'ab'"
    assert template.format(y="c") == "'a' + 'c' = 'ac'"


_A_GLOBAL = 1


def test_simple_fstr_evaluate():
    a_local = 2  # noqa: F841
    assert fstr("{_A_GLOBAL} {a_local}").evaluate() == "1 2"


def test_format_language_with_inner_fstr():
    template = fstr("{x:{width}}")
    assert template.format(x=10, width=3) == " 10"
    assert template.format(x=3, width=4) == "   3"

    template = fstr("{x:{width}.{precision}}")
    assert template.format(x=1.2345, width=4, precision=2) == " 1.2"


def test_dict():
    d = {'"': "double-quote", "'": "single-quote", "foo": "bar"}
    assert fstr("""{d["'"]}""").format(d=d) == "single-quote"
    assert fstr("""{d['"']}""").format(d=d) == "double-quote"
    assert fstr('{d["foo"]}').format(d=d) == "bar"
    assert fstr("{d['foo']}").format(d=d) == "bar"


def test_format_with_function():
    def add(x, y):
        return x + y

    template = fstr("{add(x, y)}", add=add)
    assert template.format(x=1, y=2) == "3"


def test_even_double_brace_replacement():
    template = fstr("{{}}")
    assert template.format() == "{}"


def test_odd_double_brace_replacement():
    template = fstr("{{{x}}}")
    assert template.format(x=1) == "{1}"


def test_trailing_and_leading_space():
    assert fstr("{   1 + 2}").format() == "3"
    assert fstr("{1 + 2   }").format() == "3"
    assert fstr("{   1 + 2   }").format() == "3"


def dict_inside_braces_with_padding():
    template = fstr("{ {x: y} }", x="a")
    assert template.format(y=1) == "{'a': 1}"


def test_hash_in_string():
    # These aren't comments, since they're in strings.
    d = {"#": "hash"}
    assert fstr("{'#'}").format() == "#"
    assert fstr("{d['#']}").format(d=d) == "hash"


@pytest.mark.parametrize("brace", "])}")
def test_unclosed_braces(brace):
    with pytest.raises(SyntaxError):
        fstr("{%s}" % brace).format()


def test_many_expressions():
    context = {"x": "X", "width": 1}

    def make_template(n, extra=""):
        return fstr(("{x} " + extra) * n)

    for n in range(250, 260):
        make_template(n).format(**context)

    # Test around 256.
    for i in range(250, 260):
        actual = make_template(i).format(**context)
        expected = (context["x"] + " ") * i
        assert actual == expected

    actual = make_template(250, "{x:{width}} ").format(**context)
    expected = (context["x"] + " ") * 500
    assert actual == expected

    # Test lots of expressions and constants.
    assert fstr("{1} {'x'} {'y'} " * 1000).format() == "1 x y " * 1000


_format_specifier_width_precision_templates = [
    "result: {value:{width}.{precision}}",
    "result: {value:{width!r}.{precision}}",
    "result: {value:{width:0}.{precision:1}}",
    "result: {value:{1}{0:0}.{precision:1}}",
    "result: {value:{ 1}{ 0:0}.{ precision:1}}",
]

_format_specifier_expression_expecteds = [
    "result:      12.35",
    "result:      12.35",
    "result:      12.35",
    "result:      12.35",
    "result:      12.35",
    "       0xa",
    "       0xa",
    "      -0xa",
    "      -0xa",
    "       0xa",
]


@pytest.mark.parametrize("template", _format_specifier_width_precision_templates)
def test_format_width_precision_specifier_expressions(template):
    context = {"width": 10, "precision": 4, "value": 12.34567}
    assert fstr(template).format(**context) == "result:      12.35"


_format_hex_specifier_templates = [
    (10, "{value:#{1}0x}"),
    (10, "{value:{'#'}1{0}{'x'}}"),
    (-10, "{value:-{'#'}1{0}x}"),
    (-10, "{value:{'-'}#{1}0{'x'}}"),
    (10, "{value:#{3 != {4:5} and width}x}"),
]


@pytest.mark.parametrize("value, template", _format_hex_specifier_templates)
def test_format_hex_specifier_expressions(value, template):
    expected = "      -0xa" if value < 0 else "       0xa"
    assert fstr(template).format(value=value, width=10) == expected


_invalid_format_specifier_templates = ["{'s'!r{':10'}}", "{4:{/5}}", "{'s'!{'r'}}"]


@pytest.mark.parametrize("template", _invalid_format_specifier_templates)
def test_invalid_format_specifier_expressions(template):
    with pytest.raises(SyntaxError):
        fstr(template).format()


def test_side_effect_order():
    class X:
        def __init__(self):
            self.i = 0

        def __format__(self, spec):
            self.i += 1
            return str(self.i)

    fstr("{x} {x}").format(x=X()) == "1 2"


_bad_missing_expressions = [
    "{}",
    "{ '" " {} ",
    "{!r}",
    "{ !r}",
    "{10:{ }}",
    " { } ",
    # The Python parser ignores also the following
    # whitespace characters in additional to a space.
    "{\t\f\r\n}",
    # Catch the empty expression before the
    #  invalid conversion.
    "{!x}",
    "{ !xr}",
    "{!x:}",
    "{!x:a}",
    "{ !xr:}",
    "{ !xr:a}",
    "{!}",
    "{:}",
    # We find the empty expression before the
    #  missing closing brace.
    "{!",
    "{!s:",
    "{:",
    "{:x",
    "{\xa0}",
]


@pytest.mark.parametrize("template", _bad_missing_expressions)
def test_missing_expression(template):
    with pytest.raises(SyntaxError):
        fstr(template).format()


_bad_parens_in_expressions = ["{,}", "{,}", "{3)+(4}", "{\n}"]


@pytest.mark.parametrize("template", _bad_parens_in_expressions)
def test_bad_parens_in_expressions(template):
    with pytest.raises(SyntaxError):
        fstr(template).format()


_backlashes_in_string_part = [
    ("\t", "\t"),
    (r"\t", "\\t"),
    ("{2}\t", "2\t"),
    ("{2}\t{3}", "2\t3"),
    ("\t{3}", "\t3"),
    ("\u0394", "\u0394"),
    (r"\u0394", "\\u0394"),
    (r"\u0394", "\\u0394"),
    ("{2}\u0394", "2\u0394"),
    ("{2}\u0394{3}", "2\u03943"),
    ("\u0394{3}", "\u03943"),
    ("\x20", " "),
    (r"\x20", "\\x20"),
    (r"\x20", "\\x20"),
    ("{2}\x20", "2 "),
    ("{2}\x20{3}", "2 3"),
    ("\x20{3}", " 3"),
    ("2\x20", "2 "),
    ("2\x203", "2 3"),
    ("\x203", " 3"),
    ("\\{6*7}", "\\42"),
    (r"\{6*7}", "\\42"),
]

if version_info >= (3, 0):
    _backlashes_in_string_part.extend(
        [
            ("\U00000394", "\u0394"),
            (r"\U00000394", "\\U00000394"),
            (r"\U00000394", "\\U00000394"),
            ("{2}\U00000394", "2\u0394"),
            ("{2}\U00000394{3}", "2\u03943"),
            ("\U00000394{3}", "\u03943"),
            ("\N{GREEK CAPITAL LETTER DELTA}", "\u0394"),
            ("{2}\N{GREEK CAPITAL LETTER DELTA}", "2\u0394"),
            ("{2}\N{GREEK CAPITAL LETTER DELTA}{3}", "2\u03943"),
            ("\N{GREEK CAPITAL LETTER DELTA}{3}", "\u03943"),
            ("2\N{GREEK CAPITAL LETTER DELTA}", "2\u0394"),
            ("2\N{GREEK CAPITAL LETTER DELTA}3", "2\u03943"),
            ("\N{GREEK CAPITAL LETTER DELTA}3", "\u03943"),
        ]
    )


@pytest.mark.parametrize("template, expected", _backlashes_in_string_part)
def test_backslashes_in_string_part(template, expected):
    assert fstr(template).format() == expected


_backslashes_in_expression = [r"{\}", r"{\'a\'}", r"{\t3}", "{\n}"]


@pytest.mark.parametrize("template", _backslashes_in_expression)
def test_no_backslashes_in_expression_part(template):
    with pytest.raises(SyntaxError):
        fstr(template).format()


def test_newlines_in_expressions():
    assert fstr("{0}").format() == "0"
    assert (
        fstr(
            """{3+
4}"""
        ).format()
        == "7"  # noqa: W503
    )


_empty_format_specifiers = [
    ("{x}", "test"),
    ("{x:}", "test"),
    ("{x!s:}", "test"),
    ("{x!r:}", "'test'"),
]


@pytest.mark.parametrize("template, expected", _empty_format_specifiers)
def test_empty_format_specifier(template, expected):
    assert fstr(template).format(x="test") == expected


_bad_mismatched_braces = [
    "{{}",
    "{{}}}",
    "}",
    "x}",
    "x}x",
    "{3:}>10}",
    "{3:}}>10}",
    "{3:{{>10}",
    "{3",
    "{3!",
    "{3:",
    "{3!s",
    "{3!s:",
    "{3!s:3",
    "x{",
    "x{x",
    "{x",
    "{3:s",
    "{{{",
    "{{}}{",
    "{",
]


@pytest.mark.parametrize("template", _bad_mismatched_braces)
def test_bad_mismatched_braces(template):
    with pytest.raises(SyntaxError):
        fstr(template).format()


_ok_mismatched_braces = [("{'{'}", "{"), ("{'}'}", "}")]


@pytest.mark.parametrize("template, expected", _ok_mismatched_braces)
def test_ok_mistmatched_braces(template, expected):
    assert fstr(template).format() == expected


_ok_lambdas = [
    ("{(lambda y:x*y)('8')!r}", "'88888'"),
    ("{(lambda y:x*y)('8')!r:10}", "'88888'   "),
    ("{(lambda y:x*y)('8'):10}", "88888     "),
]


@pytest.mark.parametrize("template, expected", _ok_lambdas)
def test_lambda(template, expected):
    assert fstr(template, x=5).format() == expected


_triple_quoted_strings = [
    ("{'''x'''}", "x"),
    ("{'''eric's'''}", "eric's"),
    ('{"x" """eric"s""" "y"}', 'xeric"sy'),
    ('{"x" """eric"s"""}', 'xeric"s'),
    ('{"""eric"s""" "y"}', 'eric"sy'),
    ('{"""x""" """eric"s""" "y"}', 'xeric"sy'),
    ('{"""x""" """eric"s""" """y"""}', 'xeric"sy'),
    ('{r"""x""" """eric"s""" """y"""}', 'xeric"sy'),
]


@pytest.mark.parametrize("template, expected", _triple_quoted_strings)
def test_expressions_with_triple_quoted_strings(template, expected):
    assert fstr(template).format() == expected


def test_missing_variable():
    with pytest.raises(NameError):
        fstr("v:{value}").format()


def test_missing_format_spec():
    class Obj:
        def __format__(self, spec):
            if not spec:
                return "*"
            return spec

    assert fstr("{Obj():x}").format(Obj=Obj) == "x"
    assert fstr("{Obj()}").format(Obj=Obj) == "*"
    assert fstr("{Obj():}").format(Obj=Obj) == "*"

    assert fstr("{3:}").format() == "3"
    assert fstr("{3!s:}").format() == "3"


def test_call():
    def foo(x):
        return "x=" + str(x)

    assert fstr("{foo(10)}").format(foo=foo) == "x=10"


def test_leading_trailing_spaces():
    assert fstr("{ 3}").format() == "3"
    assert fstr("{  3}").format() == "3"
    assert fstr("{3 }").format() == "3"
    assert fstr("{3  }").format() == "3"

    assert fstr("expr={ {x: y for x, y in [(1, 2), ]} }").format() == "expr={1: 2}"
    assert fstr("expr={ {x: y for x, y in [(1, 2), ]}}").format() == "expr={1: 2}"


def test_not_equal():
    # There's a special test for this because there's a special
    # case in the f-string parser to look for != as not ending an
    # expression. Normally it would, while looking for !s or !r.

    assert fstr("{3!=4}").format() == "True"
    assert fstr("{3!=4:}").format() == "True"
    assert fstr("{3!=4!s}").format() == "True"
    assert fstr("{3!=4!s:.3}").format() == "Tru"


def test_conversions():
    assert fstr("{3.14:10.10}").format() == "      3.14"
    assert fstr("{3.14!s:10.10}").format() == "3.14      "
    assert fstr("{3.14!r:10.10}").format() == "3.14      "
    if version_info >= (3, 0):
        assert fstr("{3.14!a:10.10}").format() == "3.14      "

    assert fstr('{"a"}').format() == "a"
    assert fstr('{"a"!r}').format() == "'a'"
    if version_info >= (3, 0):
        assert fstr('{"a"!a}').format() == "'a'"

    # Not a conversion.
    assert fstr('{"a!r"}').format() == "a!r"

    # Not a conversion, but show that ! is allowed in a format spec.
    assert fstr("{3.14:!<10.10}").format() == "3.14!!!!!!"

    bad_conversions = [
        "{3!g}"
        "{3!A}"
        "{3!3}"
        "{3!G}"
        "{3!!}"
        "{3!:}"
        "{3! s}"  # no space before conversion char
        "{x!s{y}}",
        "{3!ss}",
        "{3!ss:}",
        "{3!ss:s}",
    ]

    for bad in bad_conversions:
        with pytest.raises(SyntaxError):
            fstr(bad).format()


_invalid_expressions = ["{a[4)}", "{a(4]}"]


@pytest.mark.parametrize("invalid", _invalid_expressions)
def test_invalid_expressions(invalid):
    with pytest.raises(SyntaxError):
        fstr(invalid).format()


if version_info < (3, 0):
    _causes_errors = [("{1000:j}", SyntaxError)]
elif version_info < (3, 6):
    _causes_errors = [
        ("{(lambda: 0):x}", TypeError),
        ("{(0,):x}", TypeError),
        ("{1000:j}", SyntaxError),
    ]
else:
    _causes_errors = [
        ("{(lambda: 0):x}", TypeError),
        ("{(0,):x}", TypeError),
        ("{1000:j}", ValueError),
    ]


@pytest.mark.parametrize("bad, etype", _causes_errors)
def test_errors(bad, etype):
    with pytest.raises(etype):
        fstr(bad).format()
