def split_format_language(string):
    depths = {"{}": 0, "[]": 0, "()": 0}

    quotations = {"'": False, '"': False}

    index = 0
    for index, char in enumerate(string):
        for enclosure in depths:
            if char == enclosure[0]:
                depths[enclosure] += 1
            elif char == enclosure[1]:
                depths[enclosure] -= 1
        for quote, inside in quotations.items():
            if char == quote:
                quotations[quote] = not inside
        if not (any(depths.values()) or any(quotations.values())):
            if char == "!" and string[index : index + 2] != "!=":
                break
            elif char == ":":
                break
    else:
        index = len(string)

    expression = string[:index]
    formatting = string[index:].rstrip()

    if "{" in formatting.split(":")[0]:
        raise SyntaxError("fstr may only be in the format specification.")

    return expression, formatting


def expr_starts_and_stops(string):
    index = 0
    brace_depth = 0
    expression_starts = []
    expression_stops = []
    in_single_quote = False
    in_double_quote = False
    in_triple_quote = False

    while index < len(string):
        char = string[index]
        if brace_depth > 0:
            if char == "'" and not in_double_quote:
                if string[index + 1 : index + 3] == "''":
                    in_triple_quote = not in_triple_quote
                elif not in_triple_quote:
                    in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                if string[index + 1 : index + 3] == '""':
                    in_triple_quote = not in_triple_quote
                elif not in_triple_quote:
                    in_double_quote = not in_double_quote
        if char == "{":
            if brace_depth > 0:
                if not (in_double_quote or in_single_quote):
                    # increment open count to verify ballanced braces at end
                    brace_depth += 1
            else:
                j = 0
                for j, c in enumerate(string[index + 1 :]):
                    if c != "{":
                        break
                index += j
                if j % 2 == 0:
                    # encountered odd number of open braces
                    expression_starts.append(index + 1)
                    brace_depth += 1
        elif not (in_double_quote or in_single_quote) and char == "}":
            if brace_depth > 1:
                brace_depth -= 1
            elif brace_depth == 1:
                j = 0
                for j, c in enumerate(string[index + 1 :] + " "):
                    if c != "}":
                        break
                if j % 2 == 0:
                    # encountered odd number of open braces
                    expression_stops.append(index)
                    brace_depth -= 1
                index += j
        index += 1

    if brace_depth:
        raise SyntaxError("Mismatched braces in f-string %r." % string)

    return list(zip(expression_starts, expression_stops))
