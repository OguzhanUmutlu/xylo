"""Tests for the xylo template engine."""
import pytest
from xylo import xylo, xylo_set_path, xylo_get_path, UserRaisedException


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


class TestInclude:
    def test_include_basic(self, tmp_path):
        """Test basic file inclusion."""
        include_file = tmp_path / "included.sdf"
        include_file.write_text("Hello from included!")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$include("included.sdf")')

        result = xylo(main_file.read_text(), path=str(main_file))
        assert result == "Hello from included!"

    def test_include_with_kwargs(self, tmp_path):
        """Test file inclusion with keyword arguments."""
        include_file = tmp_path / "greet.sdf"
        include_file.write_text("Hello, $(name)! You are $(age) years old.")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$include("greet.sdf", name="Alice", age=30)')

        result = xylo(main_file.read_text(), path=str(main_file))
        assert result == "Hello, Alice! You are 30 years old."

    def test_include_with_expression_args(self, tmp_path):
        """Test file inclusion with expression arguments."""
        include_file = tmp_path / "calc.sdf"
        include_file.write_text("Result: $(x + y)")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$include("calc.sdf", x=10, y=20)')

        result = xylo(main_file.read_text(), path=str(main_file))
        assert result == "Result: 30"

    def test_include_inherits_context(self, tmp_path):
        """Test that included files inherit context."""
        include_file = tmp_path / "use_ctx.sdf"
        include_file.write_text("Greeting: $(greeting)")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$include("use_ctx.sdf")')

        result = xylo(main_file.read_text(), context={"greeting": "Hi there"}, path=str(main_file))
        assert result == "Greeting: Hi there"

    def test_include_kwargs_override_context(self, tmp_path):
        """Test that kwargs override existing context."""
        include_file = tmp_path / "value.sdf"
        include_file.write_text("Value: $(val)")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$include("value.sdf", val=100)')

        result = xylo(main_file.read_text(), context={"val": 50}, path=str(main_file))
        assert result == "Value: 100"

    def test_include_nested(self, tmp_path):
        """Test nested includes."""
        inner_file = tmp_path / "inner.sdf"
        inner_file.write_text("Inner content")

        outer_file = tmp_path / "outer.sdf"
        outer_file.write_text('Outer: $include("inner.sdf")')

        main_file = tmp_path / "main.sdf"
        main_file.write_text('Main: $include("outer.sdf")')

        result = xylo(main_file.read_text(), path=str(main_file))
        assert result == "Main: Outer: Inner content"

    def test_include_without_path_raises_error(self):
        """Test that $include raises error when path is not provided."""
        xylo_set_path(None)
        with pytest.raises(ValueError, match="requires path parameter"):
            xylo('$include("some.sdf")')

    def test_include_file_not_found(self, tmp_path):
        """Test that missing include file raises error."""
        main_file = tmp_path / "main.sdf"
        main_file.write_text('$include("nonexistent.sdf")')

        with pytest.raises(ValueError, match="file not found"):
            xylo(main_file.read_text(), path=str(main_file))

    def test_global_path_set_and_get(self):
        """Test xylo_set_path and xylo_get_path functions."""
        xylo_set_path(None)
        assert xylo_get_path() is None

        xylo_set_path("/some/path/file.sdf")
        assert xylo_get_path() == "/some/path/file.sdf"

        xylo_set_path(None)
        assert xylo_get_path() is None

    def test_include_with_global_path(self, tmp_path):
        """Test $include works with global path set via xylo_set_path."""
        include_file = tmp_path / "included.sdf"
        include_file.write_text("Global path works!")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$include("included.sdf")')

        xylo_set_path(str(main_file))
        try:
            result = xylo(main_file.read_text())
            assert result == "Global path works!"
        finally:
            xylo_set_path(None)

    def test_local_path_overrides_global(self, tmp_path):
        """Test that explicit path parameter overrides global path."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        dir2 = tmp_path / "dir2"
        dir2.mkdir()

        (dir1 / "file.sdf").write_text("From dir1")
        (dir2 / "file.sdf").write_text("From dir2")

        main1 = dir1 / "main.sdf"
        main2 = dir2 / "main.sdf"

        xylo_set_path(str(main1))
        try:
            result = xylo('$include("file.sdf")', path=str(main2))
            assert result == "From dir2"
        finally:
            xylo_set_path(None)


class TestImport:
    def test_import_basic(self, tmp_path):
        """Test basic file import."""
        import_file = tmp_path / "imported.sdf"
        import_file.write_text("Hello from imported!")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$import("imported.sdf")')

        result = xylo(main_file.read_text(), path=str(main_file))
        assert result == "Hello from imported!"

    def test_import_does_not_inherit_context(self, tmp_path):
        """Test that imported files do NOT inherit context (unlike include)."""
        import_file = tmp_path / "use_ctx.sdf"
        import_file.write_text("Value: $if('val' in dir()) $(val) $else undefined $end")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$import("use_ctx.sdf")')

        result = xylo(main_file.read_text(), context={"val": 42}, path=str(main_file))
        assert "undefined" in result

    def test_import_with_kwargs(self, tmp_path):
        """Test that import passes only explicit kwargs."""
        import_file = tmp_path / "greet.sdf"
        import_file.write_text("Hello, $(name)!")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$import("greet.sdf", name="Bob")')

        result = xylo(main_file.read_text(), path=str(main_file))
        assert result == "Hello, Bob!"

    def test_import_vs_include_context_difference(self, tmp_path):
        """Test the difference between import and include regarding context."""
        shared_file = tmp_path / "shared.sdf"
        shared_file.write_text("$if('x' in dir()) x=$(x) $else no-x $end")

        main_file = tmp_path / "main.sdf"

        # Include inherits context
        main_file.write_text('$include("shared.sdf")')
        include_result = xylo(main_file.read_text(), context={"x": 10}, path=str(main_file))
        assert "x=10" in include_result

        # Import does NOT inherit context
        main_file.write_text('$import("shared.sdf")')
        import_result = xylo(main_file.read_text(), context={"x": 10}, path=str(main_file))
        assert "no-x" in import_result

    def test_import_with_global_path(self, tmp_path):
        """Test $import works with global path set via xylo_set_path."""
        import_file = tmp_path / "imported.sdf"
        import_file.write_text("Global import works!")

        main_file = tmp_path / "main.sdf"
        main_file.write_text('$import("imported.sdf")')

        xylo_set_path(str(main_file))
        try:
            result = xylo(main_file.read_text())
            assert result == "Global import works!"
        finally:
            xylo_set_path(None)

    def test_import_without_path_raises_error(self):
        """Test that $import raises error when path is not provided."""
        xylo_set_path(None)
        with pytest.raises(ValueError, match="requires path parameter"):
            xylo('$import("some.sdf")')
