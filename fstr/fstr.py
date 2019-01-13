import six
import sys
import inspect

from .utils import split_format_language, expr_starts_and_stops, raise_syntax_error


class fstr(str):
    """Compile f-string expressions into a formatter.

    Parameters:
        template:
            A string which contains python expressions enclosed in curly-braces {}.
            The python expressions will be evaluated once the returned formatter is
            called. You may reference variables in those expressions that have been
            defined in ``context`` or passed as keyword arguments to the formatter.
        context:
            Variables that are referenced in the template's inner expressions. These
            can be thought of as being "globals" whereas the keyword arguments passed
            to the formatter can be thought of as "locals". In this sense, globals
            remain the same every time you format, but globals can be overwritten
            by locals.

    Examples:
        >>> hello = fstr("Hello {to.title()}!")
        >>> hello(to="world")
        Hello World!
    """

    def __new__(cls, *args, **context):
        return super(fstr, cls).__new__(cls, *args)

    def evaluate(self):
        frame = inspect.currentframe().f_back
        parameters = dict(frame.f_globals, **frame.f_locals)
        return self.format(**parameters)

    if sys.version_info >= (3, 6):  # noqa: C901

        def __init__(self, template, **context):
            self.__context = context
            template = repr(template)
            if r"\'" in template:
                template = template.replace(r"\'", "'")
                if '"""' in template:
                    # this is only possible if backslashed were used.
                    raise SyntaxError("f-string expression cannot contain a backslash.")
                expression = '"""%s"""' % template[1:-1]
            elif r"\"" in template:
                template = template.replace(r"\"", '"')
                if "'''" in template:
                    # this is only possible if backslashed were used.
                    raise SyntaxError("f-string expression cannot contain a backslash.")
                expression = "'''%s'''" % template[1:-1]
            elif r"\n" in template:
                if "'''" in template:
                    expression = '"""%s"""' % template[1:-1]
                else:
                    expression = "'''%s'''" % template[1:-1]
                expression = expression.replace(r"\n", "\n")
            else:
                expression = template
            self.__expression = expression[1:]
            self.__code = compile("f%s" % expression, "<fstr>", "eval")

        def format(self, **context):
            return eval(self.__code, self.__context, context)

        def __repr__(self):
            if self.__context:
                context = ["%s=%r" % item for item in self.__context.items()]
                return "%s(%s, %s)" % ("fstr", self.__expression, ", ".join(context))
            else:
                return "%s(%s)" % ("fstr", self.__expression)

    else:

        def __init__(self, *template, **context):
            self.__context = context or {}

            inside = []
            outside = []
            last = stop = 0
            for start, stop in expr_starts_and_stops(str(self)):
                outside.append(self[last : start - 1])
                inside.append(self[start:stop])
                last = stop + 1
            outside.append(self[last:])

            expressions = []
            template_fstrs = []
            template_parts = [outside[0]]

            index = len(outside[0])  # only used for syntax error info
            for inner, outer in zip(inside, outside[1:]):
                expr, format_lang = split_format_language(inner, self)
                template_parts[-1]
                if "{" in format_lang:
                    # there's an fstring inside the format language
                    template_fstrs.append(fstr(format_lang, **self.__context))
                    template_parts.append(outer)
                else:
                    template_parts.append("{" + format_lang + "}" + outer)
                expr = expr.strip()
                if not expr:
                    msg = "Empty expresion not allowed."
                    raise_syntax_error(self, msg, index + 1)
                expressions.append(expr.strip().replace("\n", ""))
                index += len(inner) + len(outer)

            template_parts = [
                "".join(template_parts[i : i + 2])
                for i in range(0, len(template_parts), 2)
            ]

            self.__template_parts = template_parts
            self.__template_fstrs = template_fstrs
            self.__expressions = expressions
            self.__code = [compile(e, "<fstr>", "eval") for e in expressions]

        def format(self, **context):
            template = ""
            if self.__template_fstrs:
                # there was an fstring inside the format language
                for tp, fs in zip(self.__template_parts, self.__template_fstrs):
                    template += tp + "{" + fs.format(**context) + "}"
            # if no template fstrs join parts otherwise append remaining parts.
            template += "".join(self.__template_parts[len(self.__template_fstrs) :])
            values = []
            for i, c in enumerate(self.__code):
                try:
                    result = eval(c, dict(self.__context, **context))
                except Exception as e:
                    msg = "Could not evaluate %r." % self.__expressions[i]
                    raise six.raise_from(type(e)(msg), e)
                else:
                    values.append(result)
            try:
                return template.format(*values)
            except ValueError as e:
                raise_syntax_error(self, str(e), None)

        def __repr__(self):
            if self.__context:
                context = ["%s=%r" % item for item in self.__context.items()]
                return "%s(%r, %s)" % ("fstr", str(self), ", ".join(context))
            else:
                return "%s(%r)" % ("fstr", str(self))
