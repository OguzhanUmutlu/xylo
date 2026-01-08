import re

DEFAULT_MAX_ITERATIONS = 1000

KEYWORD_FOR = "for"
KEYWORD_WHILE = "while"
KEYWORD_IF = "if"
KEYWORD_ELIF = "elif"
KEYWORD_ELSE = "else"
KEYWORD_END = "end"
KEYWORD_BREAK = "break"
KEYWORD_CONTINUE = "continue"
KEYWORD_RETURN = "return"
KEYWORD_TRY = "try"
KEYWORD_CATCH = "catch"
KEYWORD_RAISE = "raise"
KEYWORD_ASSERT = "assert"
KEYWORD_SWITCH = "switch"
KEYWORD_CASE = "case"
KEYWORD_DEFAULT = "default"
KEYWORD_FUNCTION = "function"
KEYWORD_CALL = "call"
KEYWORD_WITH = "with"
KEYWORD_EXEC = "exec"
xml_globals = globals()


def _find_matching_paren(text, start):
    depth = 0
    i = start
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        if escape_next:
            escape_next = False
            i += 1
            continue

        if char == "\\":
            escape_next = True
            i += 1
            continue

        if char == "\"":
            in_string = not in_string
        elif not in_string:
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    return i
                depth -= 1

        i += 1

    return -1


def _find_matching_end(text, start):
    depth = 1
    i = start

    while i < len(text):
        if (re.match(r"\$" + KEYWORD_FOR + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_WHILE + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_IF + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_TRY + r"\s", text[i:]) or
                re.match(r"\$" + KEYWORD_SWITCH + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_FUNCTION + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_WITH + r"\s*\(", text[i:])):
            depth += 1
        elif text[i:i + len("$" + KEYWORD_END)] == "$" + KEYWORD_END:
            depth -= 1
            if depth == 0:
                return i
        i += 1

    return -1


def _find_catch_block(text, start, end_pos):
    i = start
    depth = 0

    while i < end_pos:
        if (re.match(r"\$" + KEYWORD_FOR + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_WHILE + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_IF + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_TRY + r"\s", text[i:]) or
                re.match(r"\$" + KEYWORD_SWITCH + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_FUNCTION + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_WITH + r"\s*\(", text[i:])):
            depth += 1
            i += 1
            continue
        elif text[i:i + len("$" + KEYWORD_END)] == "$" + KEYWORD_END:
            depth -= 1
            i += 4
            continue

        if depth == 0:
            catch_match = re.match(r"\$" + KEYWORD_CATCH + r"\s*\(", text[i:])
            if catch_match:
                return i

        i += 1

    return -1


def _find_conditional_branches(text, start, end_pos):
    branches = []
    i = start
    depth = 0

    while i < end_pos:
        if re.match(r"\$" + KEYWORD_IF + r"\s*\(", text[i:]):
            depth += 1
            i += 1
            continue
        elif text[i:i + len("$" + KEYWORD_END)] == "$" + KEYWORD_END:
            depth -= 1
            i += 4
            continue

        if depth == 0:
            elif_match = re.match(r"\$" + KEYWORD_ELIF + r"\s*\(", text[i:])
            if elif_match:
                branches.append(("elif", i))
            elif text[i:i + len("$" + KEYWORD_ELSE)] == "$" + KEYWORD_ELSE:
                branches.append(("else", i))

        i += 1

    return branches


def _find_switch_branches(text, start, end_pos):
    branches = []
    i = start
    depth = 0

    while i < end_pos:
        if (re.match(r"\$" + KEYWORD_FOR + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_WHILE + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_IF + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_TRY + r"\s", text[i:]) or
                re.match(r"\$" + KEYWORD_SWITCH + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_FUNCTION + r"\s*\(", text[i:]) or
                re.match(r"\$" + KEYWORD_WITH + r"\s*\(", text[i:])):
            depth += 1
            i += 1
            continue
        elif text[i:i + len("$" + KEYWORD_END)] == "$" + KEYWORD_END:
            depth -= 1
            i += len("$" + KEYWORD_END)
            continue

        if depth == 0:
            case_match = re.match(r"\$" + KEYWORD_CASE + r"\s*\(", text[i:])
            if case_match:
                branches.append(("case", i))
            elif text[i:i + len("$" + KEYWORD_DEFAULT)] == "$" + KEYWORD_DEFAULT:
                branches.append(("default", i))

        i += 1

    return branches


class UserRaisedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def xylo(text, context=None, max_iterations=DEFAULT_MAX_ITERATIONS):
    """
    Process a xylo template string and return the rendered result.

    Args:
        text: The template string to process.
        context: Optional dictionary of variables available in the template.
        max_iterations: Maximum iterations for while loops (default: 1000).

    Returns:
        The rendered string result.

    Example:
        >>> from xylo import xylo
        >>> xylo("text $(1 + 5)")
        'text 6'
    """
    if context is None:
        context = dict()
    result = []
    i = 0
    control_flow = {"break": False, "continue": False, "return": False}

    while i < len(text):
        if text[i:i + len("$" + KEYWORD_BREAK)] == "$" + KEYWORD_BREAK:
            control_flow["break"] = True
            return "".join(result), control_flow

        if text[i:i + len("$" + KEYWORD_CONTINUE)] == "$" + KEYWORD_CONTINUE:
            control_flow["continue"] = True
            return "".join(result), control_flow

        if text[i:i + len("$" + KEYWORD_RETURN)] == "$" + KEYWORD_RETURN:
            control_flow["return"] = True
            return "".join(result), control_flow

        raise_match = re.match(r"\$" + KEYWORD_RAISE + r"\s*\(", text[i:])
        if raise_match:
            paren_end = _find_matching_paren(text, i + raise_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_RAISE} statement parenthesis")

            code = text[i + raise_match.end():paren_end].strip()

            try:
                value = eval(code, xml_globals, context)
                if isinstance(value, str):
                    raise UserRaisedException(value)
                elif isinstance(value, Exception):
                    raise value
                else:
                    raise UserRaisedException(str(value))
            except Exception as e:
                raise

        assert_match = re.match(r"\$" + KEYWORD_ASSERT + r"\s*\(", text[i:])
        if assert_match:
            paren_end = _find_matching_paren(text, i + assert_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_ASSERT} statement parenthesis")

            assert_content = text[i + assert_match.end():paren_end].strip()

            comma_pos = -1
            depth = 0
            in_string = False
            escape_next = False
            for idx, char in enumerate(assert_content):
                if escape_next:
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    continue
                if char == "\"":
                    in_string = not in_string
                elif not in_string:
                    if char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                    elif char == "," and depth == 0:
                        comma_pos = idx
                        break

            if comma_pos != -1:
                condition_expr = assert_content[:comma_pos].strip()
                message_expr = assert_content[comma_pos + 1:].strip()
            else:
                condition_expr = assert_content
                message_expr = None

            try:
                condition_result = eval(condition_expr, xml_globals, context)
            except Exception as e:
                raise ValueError(f"Error evaluating ${KEYWORD_ASSERT} condition '{condition_expr}': {e}")

            if not condition_result:
                if message_expr:
                    try:
                        message = eval(message_expr, xml_globals, context)
                    except Exception as e:
                        raise ValueError(f"Error evaluating ${KEYWORD_ASSERT} message '{message_expr}': {e}")
                    raise AssertionError(str(message))
                else:
                    raise AssertionError(f"Assertion failed: {condition_expr}")

            i = paren_end + 1
            continue

        try_match = re.match(r"\$" + KEYWORD_TRY + r"\s", text[i:])
        if try_match:
            end_pos = _find_matching_end(text, i + try_match.end())
            if end_pos == -1:
                raise ValueError(f"Unmatched ${KEYWORD_TRY} statement")

            catch_pos = _find_catch_block(text, i + try_match.end(), end_pos)

            if catch_pos is None:
                try_body = text[i + try_match.end():end_pos]
                try:
                    body_result, body_control = xylo(try_body, context, max_iterations)
                    result.append(body_result)
                    if body_control["break"] or body_control["continue"] or body_control["return"]:
                        return "".join(result), body_control
                except Exception:
                    raise
            else:
                catch_match = re.match(r"\$" + KEYWORD_CATCH + r"\s*\(", text[catch_pos:])
                catch_paren_end = _find_matching_paren(text, catch_pos + catch_match.end())
                if catch_paren_end == -1:
                    raise ValueError(f"Unmatched ${KEYWORD_CATCH} statement parenthesis")

                var_name = text[catch_pos + catch_match.end():catch_paren_end].strip()

                try_body = text[i + try_match.end():catch_pos]
                catch_body = text[catch_paren_end + 1:end_pos]

                try:
                    body_result, body_control = xylo(try_body, context, max_iterations)
                    result.append(body_result)
                    if body_control["break"] or body_control["continue"] or body_control["return"]:
                        return "".join(result), body_control
                except Exception as e:
                    catch_context = context.copy()
                    catch_context[var_name] = e
                    body_result, body_control = xylo(catch_body, catch_context, max_iterations)
                    result.append(body_result)
                    if body_control["break"] or body_control["continue"] or body_control["return"]:
                        return "".join(result), body_control

            i = end_pos + len("$" + KEYWORD_END)
            continue

        function_match = re.match(r"\$" + KEYWORD_FUNCTION + r"\s*\(", text[i:])
        if function_match:
            paren_end = _find_matching_paren(text, i + function_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_FUNCTION} statement parenthesis")

            func_signature = text[i + function_match.end():paren_end].strip()

            parts = []
            current = ""
            depth = 0
            in_string = False
            escape_next = False
            for char in func_signature:
                if escape_next:
                    current += char
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    current += char
                    continue
                if char == "\"":
                    in_string = not in_string
                    current += char
                elif not in_string:
                    if char == "(":
                        depth += 1
                        current += char
                    elif char == ")":
                        depth -= 1
                        current += char
                    elif char == "," and depth == 0:
                        parts.append(current.strip())
                        current = ""
                    else:
                        current += char
                else:
                    current += char
            if current.strip():
                parts.append(current.strip())

            if len(parts) < 1:
                raise ValueError(f"Invalid ${KEYWORD_FUNCTION} syntax: expected at least function name")

            func_name = parts[0]
            func_params = parts[1:] if len(parts) > 1 else []

            end_pos = _find_matching_end(text, paren_end + 1)
            if end_pos == -1:
                raise ValueError(f"Unmatched ${KEYWORD_FUNCTION} statement")

            func_body = text[paren_end + 1:end_pos]

            if "__functions__" not in context:
                context["__functions__"] = {}
            context["__functions__"][func_name] = {
                "params": func_params,
                "body": func_body
            }

            i = end_pos + len("$" + KEYWORD_END)
            continue

        call_match = re.match(r"\$" + KEYWORD_CALL + r"\s*\(", text[i:])
        if call_match:
            paren_end = _find_matching_paren(text, i + call_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_CALL} statement parenthesis")

            call_content = text[i + call_match.end():paren_end].strip()

            parts = []
            current = ""
            depth = 0
            in_string = False
            escape_next = False
            for char in call_content:
                if escape_next:
                    current += char
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    current += char
                    continue
                if char == "\"":
                    in_string = not in_string
                    current += char
                elif not in_string:
                    if char == "(":
                        depth += 1
                        current += char
                    elif char == ")":
                        depth -= 1
                        current += char
                    elif char == "," and depth == 0:
                        parts.append(current.strip())
                        current = ""
                    else:
                        current += char
                else:
                    current += char
            if current.strip():
                parts.append(current.strip())

            if len(parts) < 1:
                raise ValueError(f"Invalid ${KEYWORD_CALL} syntax: expected at least function name")

            func_name = parts[0]
            arg_exprs = parts[1:] if len(parts) > 1 else []

            if "__functions__" not in context or func_name not in context["__functions__"]:
                raise ValueError(f"Undefined function: {func_name}")

            func_def = context["__functions__"][func_name]
            func_params = func_def["params"]
            func_body = func_def["body"]

            if len(arg_exprs) != len(func_params):
                raise ValueError(f"Function {func_name} expects {len(func_params)} arguments, got {len(arg_exprs)}")

            call_context = context.copy()
            for param, arg_expr in zip(func_params, arg_exprs):
                try:
                    arg_value = eval(arg_expr, xml_globals, context)
                    call_context[param] = arg_value
                except Exception as e:
                    raise ValueError(f"Error evaluating ${KEYWORD_CALL} argument '{arg_expr}': {e}")

            body_result, body_control = xylo(func_body, call_context, max_iterations)
            result.append(body_result)
            if body_control["break"] or body_control["continue"] or body_control["return"]:
                return "".join(result), body_control

            i = paren_end + 1
            continue

        switch_match = re.match(r"\$" + KEYWORD_SWITCH + r"\s*\(", text[i:])
        if switch_match:
            paren_end = _find_matching_paren(text, i + switch_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_SWITCH} statement parenthesis")

            switch_expr = text[i + switch_match.end():paren_end].strip()

            end_pos = _find_matching_end(text, paren_end + 1)
            if end_pos == -1:
                raise ValueError(f"Unmatched ${KEYWORD_SWITCH} statement")

            try:
                switch_value = eval(switch_expr, xml_globals, context)
            except Exception as e:
                raise ValueError(f"Error evaluating ${KEYWORD_SWITCH} expression '{switch_expr}': {e}")

            branches = _find_switch_branches(text, paren_end + 1, end_pos)
            branch_positions = [paren_end + 1] + [pos for _, pos in branches] + [end_pos]

            executed = False
            default_branch_idx = None

            for idx, (branch_type, branch_pos) in enumerate(branches):
                if executed:
                    break

                if branch_type == "case":
                    case_match = re.match(r"\$" + KEYWORD_CASE + r"\s*\(", text[branch_pos:])
                    case_paren_end = _find_matching_paren(text, branch_pos + case_match.end())
                    case_expr = text[branch_pos + case_match.end():case_paren_end].strip()

                    try:
                        case_value = eval(case_expr, xml_globals, context)
                    except Exception as e:
                        raise ValueError(f"Error evaluating ${KEYWORD_CASE} expression '{case_expr}': {e}")

                    if switch_value == case_value:
                        body_start = case_paren_end + 1
                        next_branch_idx = idx + 2
                        body_end = branch_positions[next_branch_idx] if next_branch_idx < len(
                            branch_positions) else end_pos
                        body = text[body_start:body_end]
                        body_result, body_control = xylo(body, context, max_iterations)
                        result.append(body_result)
                        if body_control["break"] or body_control["continue"] or body_control["return"]:
                            return "".join(result), body_control
                        executed = True

                elif branch_type == "default":
                    default_branch_idx = idx

            if not executed and default_branch_idx is not None:
                default_pos = branches[default_branch_idx][1]
                body_start = default_pos + len("$" + KEYWORD_DEFAULT)
                next_branch_idx = default_branch_idx + 2
                body_end = branch_positions[next_branch_idx] if next_branch_idx < len(branch_positions) else end_pos
                body = text[body_start:body_end]
                body_result, body_control = xylo(body, context, max_iterations)
                result.append(body_result)
                if body_control["break"] or body_control["continue"] or body_control["return"]:
                    return "".join(result), body_control

            i = end_pos + len("$" + KEYWORD_END)
            continue

        with_match = re.match(r"\$" + KEYWORD_WITH + r"\s*\(", text[i:])
        if with_match:
            paren_end = _find_matching_paren(text, i + with_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_WITH} statement parenthesis")

            with_content = text[i + with_match.end():paren_end].strip()

            as_match = re.match(r"(.+?)\s+as\s+(\w+)\s*$", with_content)
            if not as_match:
                raise ValueError(
                    f"Invalid ${KEYWORD_WITH} syntax: expected 'expression as variable', got '{with_content}'")

            cm_expr = as_match.group(1).strip()
            var_name = as_match.group(2).strip()

            end_pos = _find_matching_end(text, paren_end + 1)
            if end_pos == -1:
                raise ValueError(f"Unmatched ${KEYWORD_WITH} statement")

            body = text[paren_end + 1:end_pos]

            try:
                cm = eval(cm_expr, xml_globals, context)
            except Exception as e:
                raise ValueError(f"Error evaluating ${KEYWORD_WITH} expression '{cm_expr}': {e}")

            try:
                enter_result = cm.__enter__()
            except AttributeError:
                raise ValueError(f"${KEYWORD_WITH} expression '{cm_expr}' is not a context manager")

            with_context = context.copy()
            with_context[var_name] = enter_result

            exc_info = (None, None, None)
            try:
                body_result, body_control = xylo(body, with_context, max_iterations)
                result.append(body_result)
            except Exception as e:
                import sys
                exc_info = sys.exc_info()
                if not cm.__exit__(*exc_info):
                    raise
            else:
                cm.__exit__(*exc_info)
                if body_control["break"] or body_control["continue"] or body_control["return"]:
                    return "".join(result), body_control

            i = end_pos + len("$" + KEYWORD_END)
            continue

        if_match = re.match(r"\$" + KEYWORD_IF + r"\s*\(", text[i:])
        if if_match:
            paren_end = _find_matching_paren(text, i + if_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_IF} statement parenthesis")

            condition_expr = text[i + if_match.end():paren_end].strip()

            end_pos = _find_matching_end(text, paren_end + 1)
            if end_pos == -1:
                raise ValueError(f"Unmatched ${KEYWORD_IF} statement")

            branches = _find_conditional_branches(text, paren_end + 1, end_pos)

            branch_positions = [paren_end + 1] + [pos for _, pos in branches] + [end_pos]

            try:
                condition_met = eval(condition_expr, xml_globals, context)
            except Exception as e:
                raise ValueError(f"Error evaluating ${KEYWORD_IF} condition '{condition_expr}': {e}")

            executed = False

            if condition_met:
                body_start = paren_end + 1
                body_end = branch_positions[1] if len(branch_positions) > 2 else end_pos
                body = text[body_start:body_end]
                body_result, body_control = xylo(body, context, max_iterations)
                result.append(body_result)
                if body_control["break"] or body_control["continue"] or body_control["return"]:
                    return "".join(result), body_control
            else:
                for idx, (branch_type, branch_pos) in enumerate(branches):
                    if executed:
                        break

                    if branch_type == "elif":
                        elif_match = re.match(r"\$" + KEYWORD_ELIF + r"\s*\(", text[branch_pos:])
                        elif_paren_end = _find_matching_paren(text, branch_pos + elif_match.end())
                        elif_condition = text[branch_pos + elif_match.end():elif_paren_end].strip()

                        try:
                            elif_result = eval(elif_condition, xml_globals, context)
                        except Exception as e:
                            raise ValueError(f"Error evaluating ${KEYWORD_ELIF} condition '{elif_condition}': {e}")

                        if elif_result:
                            body_start = elif_paren_end + 1
                            next_branch_idx = idx + 2
                            body_end = branch_positions[next_branch_idx] if next_branch_idx < len(
                                branch_positions) else end_pos
                            body = text[body_start:body_end]
                            body_result, body_control = xylo(body, context, max_iterations)
                            result.append(body_result)
                            if body_control["break"] or body_control["continue"] or body_control["return"]:
                                return "".join(result), body_control
                            executed = True

                    elif branch_type == "else":
                        body_start = branch_pos + len("$" + KEYWORD_ELSE)
                        body_end = end_pos
                        body = text[body_start:body_end]
                        body_result, body_control = xylo(body, context, max_iterations)
                        result.append(body_result)
                        if body_control["break"] or body_control["continue"] or body_control["return"]:
                            return "".join(result), body_control
                        executed = True

            i = end_pos + len("$" + KEYWORD_END)
            continue

        while_match = re.match(r"\$" + KEYWORD_WHILE + r"\s*\(", text[i:])
        if while_match:
            paren_end = _find_matching_paren(text, i + while_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_WHILE} statement parenthesis")

            condition_expr = text[i + while_match.end():paren_end].strip()

            end_pos = _find_matching_end(text, paren_end + 1)
            if end_pos == -1:
                raise ValueError(f"Unmatched ${KEYWORD_WHILE} statement")

            body = text[paren_end + 1:end_pos]

            iteration_count = 0
            while True:
                if iteration_count >= max_iterations:
                    raise ValueError(f"${KEYWORD_WHILE} loop exceeded maximum iterations ({max_iterations})")

                try:
                    condition_met = eval(condition_expr, xml_globals, context)
                except Exception as e:
                    raise ValueError(f"Error evaluating ${KEYWORD_WHILE} condition '{condition_expr}': {e}")

                if not condition_met:
                    break

                body_result, body_control = xylo(body, context, max_iterations)
                result.append(body_result)

                if body_control["break"]:
                    break

                iteration_count += 1

            i = end_pos + len("$" + KEYWORD_END)
            continue

        for_match = re.match(r"\$" + KEYWORD_FOR + r"\s*\(", text[i:])
        if for_match:
            paren_end = _find_matching_paren(text, i + for_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched ${KEYWORD_FOR} statement parenthesis")

            for_statement = text[i + for_match.end():paren_end].strip()

            in_match = re.match(r"(.+?)\s+in\s+(.+)", for_statement, re.DOTALL)
            if not in_match:
                raise ValueError(f"Invalid ${KEYWORD_FOR} syntax: expected 'var in iterable', got '{for_statement}'")

            var_part = in_match.group(1).strip()
            iterable_expr = in_match.group(2).strip()

            end_pos = _find_matching_end(text, paren_end + 1)
            if end_pos == -1:
                raise ValueError(f"Unmatched ${KEYWORD_FOR} statement")

            body = text[paren_end + 1:end_pos]

            try:
                iterable = eval(iterable_expr, xml_globals, context)
            except Exception as e:
                raise ValueError(f"Error evaluating ${KEYWORD_FOR} iterable '{iterable_expr}': {e}")

            for value in iterable:
                loop_context = context.copy()

                try:
                    exec(f"{var_part} = value", {"value": value}, loop_context)
                except Exception as e:
                    raise ValueError(f"Error unpacking ${KEYWORD_FOR} variable '{var_part}': {e}")

                body_result, body_control = xylo(body, loop_context, max_iterations)
                result.append(body_result)

                if body_control["break"]:
                    break

            i = end_pos + len("$" + KEYWORD_END)
            continue

        if text[i:i + len("$" + KEYWORD_END)] == "$" + KEYWORD_END:
            raise ValueError(f"Unmatched ${KEYWORD_END} statement")

        exec_match = re.match(r"\$(" + KEYWORD_EXEC + r")?\s*\(", text[i:])
        if exec_match:
            paren_end = _find_matching_paren(text, i + exec_match.end())
            if paren_end == -1:
                raise ValueError(f"Unmatched {exec_match.group(0)} statement parenthesis")
            code = text[i + exec_match.end():paren_end]
            is_exec = exec_match.group(1) is not None
            try:
                if is_exec:
                    exec(code, xml_globals, context)
                else:
                    value = eval(code, xml_globals, context)
                    result.append(str(value))
            except Exception as e:
                raise ValueError(f"Error evaluating {'code' if is_exec else 'expression'} '{code}': {e}")
            i = paren_end + 1
            continue

        result.append(text[i])
        i += 1

    return "".join(result), control_flow

