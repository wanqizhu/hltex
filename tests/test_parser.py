from textwrap import dedent

import pytest

from hltex.control import Arg, Command, Environment, resolve_args
from hltex.errors import TranslationError
from hltex.translator import Translator


def prep_translator(source, indent_level=0):
    translator = Translator(source)
    translator.indent_str = "    "
    translator.indent_level = indent_level
    return translator


def test_parse_while():
    source = "aaaaabbbb"
    translator = Translator(source)
    translator.parse_while(lambda c: c == "a")
    assert source[translator.pos] == "b"
    assert translator.pos == 5


def test_parse_while_none():
    source = "aaaaabbbb"
    translator = Translator(source)
    translator.parse_while(lambda c: False)
    assert translator.pos == 0


def test_parse_until():
    source = "aaaaabbbb"
    translator = Translator(source)
    translator.parse_until(lambda c: c == "b")
    assert source[translator.pos] == "b"
    assert translator.pos == 5


def test_parse_until_none():
    source = "aaaaabbbb"
    translator = Translator(source)
    translator.parse_until(lambda c: False)
    assert translator.pos == len(source) + 1  # appended \n


def test_validate_indent_good():
    source = "aaaaabbbb"
    translator = Translator(source)
    translator.validate_indent("    ")
    translator.validate_indent("\t\t\t\t")
    translator.validate_indent("")


def test_validate_indent_bad():
    source = "aaaaabbbb"
    translator = Translator(source)
    with pytest.raises(TranslationError) as excinfo:
        translator.validate_indent("    \t")
    assert "Invalid indentation" in excinfo.value.msg


def test_level_of_indent():
    source = "aaaaabbbb"
    translator = prep_translator(source)
    assert translator.level_of_indent("") == 0
    assert translator.level_of_indent("    ") == 1
    assert translator.level_of_indent("            ") == 3

    with pytest.raises(TranslationError) as excinfo:
        translator.level_of_indent("   ")
    assert "Indentation must be in multiples" in excinfo.value.msg


def test_calc_indent_level_first():
    source = "some text"
    translator = Translator(source)
    assert translator.calc_indent_level() == 0


def test_calc_indent_level_good():
    source = "    some text"
    translator = prep_translator(source)
    assert translator.calc_indent_level() == 1
    assert source[translator.pos] == " "
    assert translator.pos == 0


def test_calc_indent_level_empty():
    source = "    \n    some text"
    translator = prep_translator(source)
    assert translator.calc_indent_level() == 1
    assert source[translator.pos] == " "
    assert translator.pos == 0


def test_calc_indent_level_end():
    source = "    "
    translator = prep_translator(source)
    assert translator.calc_indent_level() == 1  # empty line
    assert translator.pos == 0


def test_calc_indent_level_double():
    source = "        some text"
    translator = prep_translator(source)
    with pytest.raises(TranslationError) as excinfo:
        translator.parse_block()
    assert "Indent Error" in excinfo.value.msg


def test_calc_indent_level_bad():
    source = "   some text"
    translator = prep_translator(source)
    with pytest.raises(TranslationError) as excinfo:
        translator.calc_indent_level()
    assert "multiples of the base" in excinfo.value.msg


def test_parse_empty_good():
    source = "    \n\n    some text"
    translator = Translator(source)
    translator.parse_empty()
    assert translator.pos == 6


def test_parse_empty_stay():
    source = "    some text"
    translator = Translator(source)
    translator.parse_empty()
    assert translator.pos == 0


def test_parse_empty_none():
    source = "    \n\n  \n   \n"
    translator = Translator(source)
    translator.parse_empty()
    assert translator.pos == len(source)


def test_parse_control_seq():
    source = "commandname123"
    translator = Translator(source)
    assert translator.parse_control_seq() == "commandname"
    assert source[translator.pos] == "1"


def test_parse_control_seq_end():
    source = "commandname"
    translator = Translator(source)
    assert translator.parse_control_seq() == "commandname"
    assert translator.pos == len(source)


def test_get_control_symbol():
    source = "!stuff"
    translator = Translator(source)
    assert translator.parse_control_seq() == "!"
    assert source[translator.pos] == "s"


def test_get_control_colon():
    source = ":stuff"
    translator = Translator(source)
    assert translator.parse_control_seq() == ":"
    assert source[translator.pos] == "s"


def test_get_control_symbol_end():
    source = "!"
    translator = Translator(source)
    assert translator.parse_control_seq() == "!"
    assert translator.pos == 1


def test_get_control_colon_end():
    source = ":"
    translator = Translator(source)
    assert translator.parse_control_seq() == ":"
    assert translator.pos == 1


def test_parse_arg():
    source = "my \nargument}some more text"
    translator = Translator(source)
    assert translator.parse_arg() == "my \nargument"
    assert source[translator.pos] == "s"


def test_parse_arg_end():
    source = "my \nargument}"
    translator = Translator(source)
    assert translator.parse_arg() == "my \nargument"
    assert translator.pos == len(source)


def test_parse_arg_opt():
    source = "my \nargument]some more text"
    translator = Translator(source)
    assert translator.parse_arg("]") == "my \nargument"
    assert source[translator.pos] == "s"


def test_parse_arg_opt_end():
    source = "my \nargument]"
    translator = Translator(source)
    assert translator.parse_arg("]") == "my \nargument"
    assert translator.pos == len(source)


def test_parse_arg_command():
    source = "my \\textbf{word}argument}some text"
    translator = Translator(source)
    assert translator.parse_arg() == "my \\textbf{word}argument"
    assert source[translator.pos] == "s"


def test_parse_arg_command_comments():
    source = "my \\textbf{word}a%rgument}some text\nctualArgument}More text"
    translator = Translator(source)
    assert translator.parse_arg() == "my \\textbf{word}actualArgument"
    assert source[translator.pos] == "M"


def test_parse_arg_command_nested():
    source = "my \\textbf{\\command[arg]\n{arg}}argument}some text"
    translator = Translator(source)
    assert translator.parse_arg() == "my \\textbf{\\command[arg]\n{arg}}argument"
    assert source[translator.pos] == "s"


def test_parse_arg_command_crazy():
    source = "my \\textbf{word\\command[arg]{arg} [arg]\n{arg}}{arg }[arg]\n{\\:{\\@{\\@}}}argument}some text"
    translator = Translator(source)
    assert (
        translator.parse_arg()
        == "my \\textbf{word\\command[arg]{arg} [arg]\n{arg}}{arg }[arg]\n{\\:{\\@{\\@}}}argument"
    )
    assert source[translator.pos] == "s"


def test_parse_arg_unmatched():
    source = "my argument"
    translator = Translator(source)
    with pytest.raises(TranslationError) as excinfo:
        translator.parse_arg(required=True)
    assert "Missing closing" in excinfo.value.msg


def test_parse_arg_opt_unmatched():
    source = "my argument\n"
    translator = Translator(source)
    assert translator.parse_arg() is None
    assert translator.pos == len(source)


def test_parse_args():
    source = "{arg1}{arg2}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args()
    assert args == [Arg("arg1"), Arg("arg2")]
    assert argstr == "{arg1}{arg2}"
    assert source[translator.pos] == "s"


def test_parse_args_comments():
    source = "{arg1}{arg%2}\n3}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args()
    assert args == [Arg("arg1"), Arg("arg3")]
    assert argstr == "{arg1}{arg%2}\n3}"
    assert source[translator.pos] == "s"


def test_parse_args_opt():
    source = "{arg1}[arg2]{arg1}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args()
    assert args == [Arg("arg1"), Arg("arg2", optional=True), Arg("arg1")]
    assert argstr == "{arg1}[arg2]{arg1}"
    assert source[translator.pos] == "s"


def test_parse_args_whitespace():
    # NOTE: this is different from standard LaTeX, where newlines don't matter
    # we can still parse standard latex like this, but our commands have to have
    # their arguments on the same line
    source = " {arg1}  [arg2]\n{arg1}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args()
    assert args == [Arg("arg1"), Arg("arg2", optional=True)]
    assert argstr == " {arg1}  [arg2]"
    assert source[translator.pos] == "\n"


def test_parse_args_opt_unmatched():
    source = "{arg1[}[arg2{arg1}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args()
    assert args == [Arg("arg1[")]
    assert argstr == "{arg1[}"
    assert source[translator.pos] == "["
    assert translator.pos == 7


def test_parse_args_only_opt_unmatched():
    source = "[arg2{arg1}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args()
    assert args == []
    assert argstr == ""
    assert source[translator.pos] == "["


def test_parse_args_min_args():
    source = "{arg1}[arg2]some text"
    translator = Translator(source)
    args, argstr = translator.parse_args(min_args=2)
    assert args == [Arg("arg1"), Arg("arg2", optional=True)]
    assert argstr == "{arg1}[arg2]"
    assert source[translator.pos] == "s"


def test_parse_args_min_args_missing():
    source = "{arg1}[arg2]some text"
    translator = Translator(source)
    with pytest.raises(TranslationError) as excinfo:
        translator.parse_args(min_args=3)
    assert "Too few arguments" in excinfo.value.msg


def test_parse_args_unmatched():
    source = "{arg1"
    translator = Translator(source)
    with pytest.raises(TranslationError) as excinfo:
        translator.parse_args()
    assert "Missing closing" in excinfo.value.msg


def test_parse_args_max_args():
    source = "{arg1}  [arg2] {arg1}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args(max_args=4)
    assert args == [Arg("arg1"), Arg("arg2", optional=True), Arg("arg1")]
    assert argstr == "{arg1}  [arg2] {arg1}"
    assert source[translator.pos] == "s"


def test_parse_args_max_args_less():
    source = "{arg1}  [arg2] {arg1}some text"
    translator = Translator(source)
    args, argstr = translator.parse_args(max_args=2)
    assert args == [Arg("arg1"), Arg("arg2", optional=True)]
    assert argstr == "{arg1}  [arg2]"
    assert source[translator.pos] == " "


def test_resolve_args_good():
    assert resolve_args("test", "!!", [Arg("arg1"), Arg("arg2")]) == ["arg1", "arg2"]
    assert resolve_args("test", "", []) == []
    assert resolve_args(
        "test", "??", [Arg("arg1", optional=True), Arg("arg2", optional=True)]
    ) == ["arg1", "arg2"]
    assert resolve_args("test", "??", [Arg("arg1", optional=True)]) == ["arg1", None]
    assert resolve_args("test", "!??", [Arg("arg1"), Arg("arg2", optional=True)]) == [
        "arg1",
        "arg2",
        None,
    ]
    assert resolve_args("test", "?!?", [Arg("arg1", optional=True), Arg("arg2")]) == [
        "arg1",
        "arg2",
        None,
    ]
    assert resolve_args("test", "?!?", [Arg("arg1"), Arg("arg2", optional=True)]) == [
        None,
        "arg1",
        "arg2",
    ]


def test_resolve_args_bad():
    with pytest.raises(TranslationError) as excinfo:
        resolve_args("test", "!!", [Arg("arg1")])
    assert "Missing required" in excinfo.value.msg

    with pytest.raises(TranslationError) as excinfo:
        resolve_args("test", "?!!", [Arg("arg1")])
    assert "Missing required" in excinfo.value.msg

    with pytest.raises(TranslationError) as excinfo:
        resolve_args("test", "!?!", [Arg("arg1")])
    assert "Missing required" in excinfo.value.msg

    with pytest.raises(TranslationError) as excinfo:
        resolve_args("test", "!?!", [Arg("arg1", optional=True)])
    assert "Superfluous optional" in excinfo.value.msg


def test_do_command():
    source = "{arg1}[arg2]{arg1}some text"
    translator = Translator(source)
    res = translator.do_command(Command("test", lambda t, a: "\\textbf{%s}" % a, "!"))
    print(res)
    assert res == "\\textbf{arg1}"
    assert source[translator.pos] == "["


def test_do_command_multiple():
    source = "{arg1}[arg2]{arg1}some text"
    translator = Translator(source)
    res = translator.do_command(
        Command("test", lambda t, a, b: "\\textbf{%s, %s}" % (a, b), "!?")
    )
    print(res)
    assert res == "\\textbf{arg1, arg2}"
    assert source[translator.pos] == "{"
    assert translator.pos == 12


def test_parse_block():
    source = "\n    hello\n    \ngoodbye"
    translator = prep_translator(source)
    assert translator.parse_block() == "\n    hello"
    assert source[translator.pos] == "\n"


def test_parse_block_document():
    source = "\nhello\n\ngoodbye\n"
    translator = prep_translator(source, -1)
    assert translator.parse_block() == "\nhello\n\ngoodbye\n"
    assert translator.pos == len(source)


def test_parse_block_end():
    source = "\n    hello\n    \n"
    translator = prep_translator(source)
    assert translator.parse_block() == "\n    hello"
    assert translator.pos == 10


def test_parse_block_nested():
    source = "\n        hello\n    \n    goodbye"
    translator = prep_translator(source, 1)
    assert translator.parse_block() == "\n        hello"
    assert source[translator.pos] == "\n"
    assert translator.pos == 14


def test_parse_block_nested_end():
    source = "\n        hello\n    \n    "
    translator = prep_translator(source, 1)
    assert translator.parse_block() == "\n        hello"
    assert translator.pos == 14


def test_parse_block_raw_with_indent():
    source = "\nhello\n        weird indentation\n\n    this too\ngoodbye\n"
    translator = prep_translator(source, -1)
    assert (
        translator.parse_block(is_raw=True)
        == "\nhello\n        weird indentation\n\n    this too\ngoodbye\n"
    )
    assert translator.pos == len(source)


def test_parse_block_raw_with_comments():
    source = "\nhello\n    %wha t is \\dis\n\n%this too\ngoodbye\n"
    translator = prep_translator(source, -1)
    assert (
        translator.parse_block(is_raw=True)
        == "\nhello\n    %wha t is \\dis\n\n%this too\ngoodbye\n"
    )
    assert translator.pos == len(source)


def test_parse_block_raw_with_commands():
    source = "\nhello\n    \\ignore_this: \\distoo\n\n\\pysplice too\ngoodbye\n"
    translator = prep_translator(source, -1)
    assert (
        translator.parse_block(is_raw=True)
        == "\nhello\n    \\ignore_this: \\distoo\n\n\\pysplice too\ngoodbye\n"
    )
    assert translator.pos == len(source)


def test_parse_block_environment():
    source = "\n    hello\n    \\environment:\n        nested\ngoodbye\n"
    translator = prep_translator(source)
    block = translator.parse_block()
    assert (
        block
        == "\n    hello\n    \\begin{environment}\n        nested\n    \\end{environment}"
    )
    assert source[translator.pos] == "\n"


def test_parse_block_nonenvironment_bad():
    source = "\n    hello\n    \n    goodbye\n"
    translator = prep_translator(source, -1)
    with pytest.raises(TranslationError) as excinfo:
        translator.parse_block()
    assert "document as a whole must not be indented" in excinfo.value.msg


def test_parse_block_nonenvironment_args():
    source = "\\environment[arg1] { arg2}:\n    contents\n    contents2\ngoodbye\n"
    translator = prep_translator(source, -1)
    block = translator.parse_block()
    assert (
        block
        == "\\begin{environment}[arg1] { arg2}\n    contents\n    contents2\n\\end{environment}\ngoodbye\n"
    )


def test_parse_block_environment_indented():
    source = "\n        hello\n        \\environment:\n            nested\n    goodbye"
    translator = prep_translator(source, 1)
    block = translator.parse_block()
    assert (
        block
        == "\n        hello\n        \\begin{environment}\n            nested\n        \\end{environment}"
    )
    assert source[translator.pos] == "\n"
    assert translator.pos == 55


def test_do_environment():
    source = "\n    hello\n    \ngoodbye"
    translator = prep_translator(source)
    res = translator.do_environment(
        Environment("test", lambda t, b: "\\begin{test}%s\\end{test}" % b, ""),
        [],
        "",
        0,
    )
    print(res)
    assert res == "\\begin{test}\n    hello\n\\end{test}"
    assert source[translator.pos] == "\n"


def test_do_environment_args():
    source = "\n    hello\n    \ngoodbye"
    translator = prep_translator(source)
    res = translator.do_environment(
        Environment(
            "test",
            lambda t, b, a: "\\begin{test}\\textbf{%s}%s\\end{test}" % (a, b),
            "!",
        ),
        [Arg("arg1")],
        "",
        0,
    )
    print(res)
    assert res == "\\begin{test}\\textbf{arg1}\n    hello\n\\end{test}"
    assert source[translator.pos] == "\n"


def test_do_environment_bad():
    source = "\nhello\n\ngoodbye"
    translator = prep_translator(source)
    with pytest.raises(TranslationError) as excinfo:
        translator.do_environment(
            Environment("test", lambda t, b: "\\begin{test}%s\\end{test}" % b, ""),
            [],
            "",
            0,
        )
    assert "indented block on the following line" in excinfo.value.msg


def test_do_environment_nested():
    source = "\n    hello\n    \\environment:\n        nested\ngoodbye"
    translator = prep_translator(source)
    res = translator.do_environment(
        Environment("test", lambda t, b: "\\begin{test}%s\\end{test}" % b, ""),
        [],
        "",
        0,
    )
    print(res)
    assert (
        res
        == "\\begin{test}\n    hello\n    \\begin{environment}\n        nested\n    \\end{environment}\n\\end{test}"
    )
    assert source[translator.pos] == "\n"


def test_do_environment_nested_end():
    source = "\n    hello\n    \\environment:\n        nested\n"
    translator = prep_translator(source)
    res = translator.do_environment(
        Environment("test", lambda t, b: "\\begin{test}%s\\end{test}" % b, ""),
        [],
        "",
        0,
    )
    print(res)
    assert (
        res
        == "\\begin{test}\n    hello\n    \\begin{environment}\n        nested\n    \\end{environment}\n\\end{test}"
    )
    assert translator.pos == len(source) - 1


def test_do_environment_nested_nonewline():
    source = "\n    hello\n    \\environment:\n        nested"
    translator = prep_translator(source)
    res = translator.do_environment(
        Environment("test", lambda t, b: "\\begin{test}%s\\end{test}" % b, ""),
        [],
        "",
        0,
    )
    print(res)
    assert (
        res
        == "\\begin{test}\n    hello\n    \\begin{environment}\n        nested\n    \\end{environment}\n\\end{test}"
    )
    assert translator.pos == len(source)


def test_do_environment_nested_comments():
    source = "\n    hello\n    %IGNORETHIN\\environment:\n    \\realEnvironment:\n        nested\ngoodbye"
    translator = prep_translator(source)
    res = translator.do_environment(
        Environment("test", lambda t, b: "\\begin{test}%s\\end{test}" % b, ""),
        [],
        "",
        0,
    )
    print(res)
    assert (
        res
        == "\\begin{test}\n    hello\n    %IGNORETHIN\\environment:\n    \\begin{realEnvironment}\n        nested\n    \\end{realEnvironment}\n\\end{test}"
    )
    assert source[translator.pos] == "\n"


def test_parse_block_verbatim():
    source = "\n\\verbatim:\n    hiiminverbatim\n    \\pysplice:\n        this should be ignored\n    \\eq{ok}: f(x)\n    this too\n"
    translator = prep_translator(source, -1)
    res = translator.parse_block()
    print(res)
    assert (
        res
        == "\n\\begin{verbatim}\n    hiiminverbatim\n    \\pysplice:\n        this should be ignored\n    \\eq{ok}: f(x)\n    this too\n\\end{verbatim}\n"
    )


def test_parse_verb_command():
    source = "\nstart\\verb{normal%withcomments{wow get out\\}} and some more"
    translator = prep_translator(source, -1)
    res = translator.parse_block()
    print(res)
    assert res == "\nstart\\verb{normal%withcomments{wow get out\\}} and some more\n"


def test_document_begin():
    source = "\n===\n"
    translator = prep_translator(source)
    translator.preamble = True
    assert translator.check_for_document_begin()
    assert translator.pos == len(source) - 1


def test_document_begin_extra_padding():
    source = "\n\n\n   ===  \n"
    translator = prep_translator(source)
    translator.preamble = True
    assert translator.check_for_document_begin()
    assert translator.pos == len(source) - 1


def test_document_begin_comments():
    source = "\n\n\n   %=====  \n"
    translator = prep_translator(source)
    translator.preamble = True
    assert translator.check_for_document_begin() is None
    assert translator.pos == 0


def test_document_begin_extra_equals_and_padding():
    source = "\n\n =======================  \n"
    translator = prep_translator(source)
    translator.preamble = True
    assert translator.check_for_document_begin()
    assert translator.pos == len(source) - 1


def test_document_begin_bad_separator():
    source = "\n\n =  \n"
    translator = prep_translator(source)
    translator.preamble = True
    with pytest.raises(TranslationError) as excinfo:
        translator.check_for_document_begin()
    assert "must be at least '==='" in excinfo.value.msg


def test_document_begin_bad_lines():
    source = "\n\n 1341  \n"
    translator = prep_translator(source)
    translator.preamble = True
    with pytest.raises(TranslationError) as excinfo:
        translator.check_for_document_begin()
    assert "Preamble must consist exclusively" in excinfo.value.msg


def test_one_line_environment():
    source = "\n\\eq:    f(x) = oneLiner(whitespace should be kept)  \n"
    translator = prep_translator(source, -1)
    res = translator.parse_block()
    print(res)
    assert (
        res
        == "\n\\begin{equation}    f(x) = oneLiner(whitespace should be kept)  \\end{equation}\n"
    )


def test_one_line_environment_no_endl():
    source = "\n\\eq:    f(x) = oneLiner(whitespace should be kept)  "
    translator = prep_translator(source, -1)
    res = translator.parse_block()
    print(res)
    assert (
        res
        == "\n\\begin{equation}    f(x) = oneLiner(whitespace should be kept)  \\end{equation}\n"
    )


def test_one_line_environment_with_commands():
    source = "\n\\eq:    f(x) = \\textbf{one}Liner(!) "
    translator = prep_translator(source, -1)
    res = translator.parse_block()
    print(res)
    assert (
        res == "\n\\begin{equation}    f(x) = \\textbf{one}Liner(!) \\end{equation}\n"
    )


def test_one_line_environment_with_hltex_commands():
    # you'd never do this with docclass, but for fun
    source = "\n\\eq:    f(x) = \\docclass{mydoc}wow "
    translator = prep_translator(source, -1)
    res = translator.parse_block()
    print(res)
    assert (
        res
        == "\n\\begin{equation}    f(x) = \\documentclass{mydoc}wow \\end{equation}\n"
    )


def test_one_line_environment_with_comments():
    source = "\n\\eq:    f(x) = %\\docclass{acomment} \n"
    translator = prep_translator(source, -1)
    res = translator.parse_block()
    print(res)
    assert (
        res == "\n\\begin{equation}    f(x) = \\end{equation}%\\docclass{acomment} \n"
    )


def test_missing_end_bracket(capsys):
    source = dedent(
        """
    \\docclass{noend
    ===
    \\eq:
        never an end
    """
    )
    translator = prep_translator(source)
    translator.translate()
    assert "Missing closing " in capsys.readouterr().err
