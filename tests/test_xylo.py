"""Tests for the xylo template engine."""
import pytest
from xylo import xylo, UserRaisedException


class TestBasicExpressions:
    def test_simple_expression(self):
        assert xylo("text $(1 + 5)") == "text 6"

    def test_arithmetic(self):
        assert xylo("$(2 + 5)") == "7"

    def test_string_expression(self):
        assert xylo('$("hello")') == "hello"


class TestExec:
    def test_exec_variable(self):
        assert xylo("$exec(x = 10) $(x)") == " 10"


class TestConditionals:
    def test_if_else_equal(self):
        assert xylo("$if(2 > 2) Greater $elif(3 < 2) Lesser $else Equal $end") == " Equal "

    def test_if_true(self):
        assert xylo("$if(5 > 3) Yes $end") == " Yes "

    def test_if_false(self):
        assert xylo("$if(3 > 5) Yes $end") == ""


class TestLoops:
    def test_while_max_iterations(self):
        with pytest.raises(ValueError, match=f"exceeded maximum iterations"):
            xylo("$while(1 < 2) hi $end")

    def test_while_break(self):
        assert xylo("$while(1 < 2) hi $break $end") == " hi "

    def test_while_continue(self):
        assert xylo("$exec(x = 0) $while(x < 2) hi$(x) $exec(x += 1) $continue hi2 $end") == "  hi0   hi1  "

    def test_for_loop(self):
        assert xylo("$for(x in range(3)) $(x) $end") == " 0  1  2 "

    def test_for_tuple_unpacking(self):
        assert xylo("$for((i, val) in enumerate(['a', 'b', 'c'])) $(i): $(val) $end") == " 0: a  1: b  2: c "

    def test_for_zip(self):
        assert xylo("$for((a, b) in zip([1, 2, 3], ['x', 'y', 'z'])) $(a)-$(b) $end") == " 1-x  2-y  3-z "

    def test_for_nested_unpacking(self):
        assert xylo("$for((i, (x, y)) in enumerate([(1, 2), (3, 4)])) $(i): $(x),$(y) $end") == " 0: 1,2  1: 3,4 "


class TestExceptions:
    def test_raise(self):
        with pytest.raises(UserRaisedException, match="Test error!"):
            xylo("$raise('Test error!')")

    def test_try_catch(self):
        result = xylo("$try $(1 / 0) $catch(e) Caught error: $(e) $end")
        assert "Caught error:" in result
        assert "division by zero" in result


class TestAssert:
    def test_assert_pass(self):
        assert xylo("$assert(1 == 1) Passed") == " Passed"

    def test_assert_fail(self):
        with pytest.raises(AssertionError, match="Assertion failed: 1 == 2"):
            xylo("$assert(1 == 2)")

    def test_assert_custom_message(self):
        with pytest.raises(AssertionError, match="Custom message"):
            xylo('$assert(1 == 2, "Custom message")')


class TestSwitch:
    def test_switch_case_match(self):
        assert xylo(
            "$exec(x = 2) $switch(x) $case(1) One $case(2) Two $case(3) Three $default Unknown $end") == "  Two "

    def test_switch_default(self):
        assert xylo("$exec(x = 5) $switch(x) $case(1) One $case(2) Two $default Unknown $end") == "  Unknown "

    def test_switch_string(self):
        assert xylo('$switch("hello") $case("hi") Hi $case("hello") Hello $end') == " Hello "


class TestFunctions:
    def test_simple_function(self):
        assert xylo('$function(greet, name) Hello, $(name)! $end $call(greet, "World")') == "  Hello, World! "

    def test_function_with_expression(self):
        assert xylo("$function(add, a, b) $(a + b) $end Result: $call(add, 3, 5)") == " Result:  8 "

    def test_function_with_loop(self):
        assert xylo(
            '$function(repeat, text, count) $for(i in range(count)) $(text) $end $end $call(repeat, "hi", 3)') == "   hi  hi  hi  "

    def test_function_early_return(self):
        assert xylo("$function(early, x) $if(x > 5) Big $return $end Small $end $call(early, 10)") == "   Big "
        assert xylo("$function(early, x) $if(x > 5) Big $return $end Small $end $call(early, 3)") == "   Small "


class TestContext:
    def test_context_variable(self):
        assert xylo("Hello $(name)!", {"name": "World"}) == "Hello World!"

    def test_context_function(self):
        assert xylo("$(double(5))", {"double": lambda x: x * 2}) == "10"


class TestComplexCases:
    def test_nested_loops(self):
        result = xylo('hi $(2 + 5) $for(x in range(3)) $for(y in range(3)) hi $(x),$(y) $end $end $("hi)))\\"")')
        expected = "hi 7   hi 0,0  hi 0,1  hi 0,2    hi 1,0  hi 1,1  hi 1,2    hi 2,0  hi 2,1  hi 2,2   hi)))\""
        assert result == expected


class TestLine:
    def test_line(self):
        assert xylo("$for(x in [\n1])$end") == ""
