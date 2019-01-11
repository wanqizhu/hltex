from textwrap import dedent
from hltex.translator import Translator


def translate(source):
    translator = Translator(source)
    return translator.translate()


def test_hello():
    source = dedent('''
    \\documentclass{article}
    ===
    Hello?
    ''')
    assert translate(source) == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    Hello?
    \\end{document}\n''')


def test_hello_comments():
    source = dedent('''
    \\documentclass{arti%???
    cle}
    ===
    Hello?
    %bye
    ''')
    assert translate(source) == dedent(
    '''
    \\documentclass{arti%???
    cle}
    \\begin{document}
    Hello?
    %bye
    \\end{document}\n''')


def test_pysplice_multiple_lines():
    source = dedent('''
    \\documentclass{article}
    ===
    Hello?
    \\pysplice:
        h = "hello"
        if True:
            print(h)
        y = "\\this should be ignored%this TOO"
        #_plz
        #\\this too:
        #%wut is dis

            #weird indentation too


    Bye
    ''')
    res = translate(source)
    print(res)
    assert res == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    Hello?
    hello



    Bye
    \\end{document}\n''')


def test_no_starting_newline():
    source = '\\documentclass{article}\n===\nHello?'
    assert translate(source) == '\\documentclass{article}\n\\begin{document}\nHello?\n\\end{document}\n'



# def test_double_document_mark():
#     source = dedent('''
#     \\documentclass{article}
#     ===
#     Hello?
#     ===
#         Goodbye
#     ''')
#     res = translate(source)
#     print(res)
#     assert res == dedent(
#     '''
#     \\documentclass{article}
#     \\begin{document}
#     Hello?
#     ===
#         Goodbye
#     \\end{document}
#     ''')


def test_indented_bad(capsys):
    source = '''
    \\documentclass{article}
    ===
        Hello?
    '''
    res = translate(source)
    assert 'document as a whole must not be indented' in capsys.readouterr().err


def test_equation():
    source = dedent('''
    \\documentclass{article}
    ===
    Here is an equation:
    \\equation:
        f(x) = x^2
    ''')
    res = translate(source)
    assert res == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    Here is an equation:
    \\begin{equation}
        f(x) = x^2
    \\end{equation}
    \\end{document}
    ''')


def test_multiple_equations():
    source = dedent('''
    \\documentclass{article}
    ===
    Here is an equation:
    \\equation:
        f(x) = x^2
    Here is another equation:
    \\equation:
        f(x) = x^3
    Here are some concluding words.
    ''')
    # import pdb; pdb.set_trace()
    res = translate(source)
    assert res == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    Here is an equation:
    \\begin{equation}
        f(x) = x^2
    \\end{equation}
    Here is another equation:
    \\begin{equation}
        f(x) = x^3
    \\end{equation}
    Here are some concluding words.
    \\end{document}
    ''')


def test_multiple_nested_environments():
    source = dedent('''
    \\documentclass{article}
    ===
    Here is an equation:
    \\equation:
        \\split:
            f(x) = x^2
    Here is another equation:
    \\equation:
        \\split:
            f(x) = x^3
    Here are some concluding words.
    ''')
    # import pdb; pdb.set_trace()
    res = translate(source)
    assert res == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    Here is an equation:
    \\begin{equation}
        \\begin{split}
            f(x) = x^2
        \\end{split}
    \\end{equation}
    Here is another equation:
    \\begin{equation}
        \\begin{split}
            f(x) = x^3
        \\end{split}
    \\end{equation}
    Here are some concluding words.
    \\end{document}
    ''')


def test_a_doc_no_docclass():
    source = dedent('''
    ===
    The document environment is the only one which doesn't need to be indented.
    \\section{Some Words}
    Here are some words that are in this section.
    Math is fun, so here's an equation:
    \\eq:
        f(x) = x^2 + 3

    We might want to give our equation a label, like this:
    \\eq[cubic]:
        f(x) = x^3 - 4x^2 + 2
    We can reference our equation with Equation \\ref{eq:cubic}.
    This is automatically joined with the non-breaking space \\verb{~}.
    ''')
    # import pdb; pdb.set_trace()
    res = translate(source)
    print(res)
    assert res == dedent(   # note the weird indentation is for === at start of file
                            # TODO: we should probably throw an error
    '''    \\begin{document}
    The document environment is the only one which doesn't need to be indented.
    \\section{Some Words}
    Here are some words that are in this section.
    Math is fun, so here's an equation:
    \\begin{equation}
        f(x) = x^2 + 3
    \\end{equation}

    We might want to give our equation a label, like this:
    \\begin{equation}\\label{eq:cubic}
        f(x) = x^3 - 4x^2 + 2
    \\end{equation}
    We can reference our equation with Equation \\ref{eq:cubic}.
    This is automatically joined with the non-breaking space \\verb{~}.
    \\end{document}
    ''')


def test_docclass():
    source = dedent('''
    \\docclass{article}
    ===
    Hello?
    ''')
    assert translate(source) == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    Hello?
    \\end{document}\n''')


def test_docclass_options():
    source = dedent('''
    \\docclass[twocolumn,twoside]{article}
    ===
    Hello?
    ''')
    assert translate(source) == dedent(
    '''
    \\documentclass[twocolumn,twoside]{article}
    \\begin{document}
    Hello?
    \\end{document}\n''')



def test_docclass_with_normal_latex_begin_end():
    source = dedent('''
    \\docclass{article}
    ===
    \\begin{document}
    Hello!
    \\end{document}
    ''')
    assert translate(source) == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    \\begin{document}
    Hello!
    \\end{document}
    \\end{document}
    ''')


def test_one_liners():
    source = dedent('''
    \\docclass{article}
    ===
    hi here are some one line equations
    \\eq:    f(x) = oneLiner(whitespace should be kept)
    Or start at the \\textbf{middle} of a \\eq:line(x) = the end
    \\howAboutRandomStuff: hi some stuffz
    ''')

    assert translate(source) == dedent('''
    \\documentclass{article}
    \\begin{document}
    hi here are some one line equations
    \\begin{equation}    f(x) = oneLiner(whitespace should be kept)\\end{equation}
    Or start at the \\textbf{middle} of a \\begin{equation}line(x) = the end\\end{equation}
    \\begin{howAboutRandomStuff} hi some stuffz\\end{howAboutRandomStuff}
    \\end{document}
    ''')


def test_used_to_be_broken():
    source = '\n\\docclass{article}\n\\title{HLTeX Demo}\n\\author{Alex, Wanqi}\n===\n\\section{Introduction}'
    assert translate(source) == dedent(
    '''
    \\documentclass{article}
    \\title{HLTeX Demo}
    \\author{Alex, Wanqi}
    \\begin{document}
    \\section{Introduction}
    \\end{document}
    ''')



def test_commands_in_preamble():
    source = '\n\\eq: f = \\textbf{bold text}\n===\nhello'
    assert translate(source) == dedent(
    '''
    \\begin{equation} f = \\textbf{bold text}\\end{equation}
    \\begin{document}
    hello
    \\end{document}
    ''')



def test_pysplice_in_preamble():
    source = dedent(
    '''
    \\docclass{article}
    \\pysplice:
        print('\\n'.join(['\\\\newcommand{\\cal%s}{\\mathcal{%s}}'
                         % (c, c) for c in ['F', 'G', 'H', 'I', 'D', 'B']]))
    \\title{a Title}
    ===
    hello
    ''')
    assert translate(source) == dedent(
    '''
    \\documentclass{article}
    \\newcommand{\\calF}{\\mathcal{F}}
    \\newcommand{\\calG}{\\mathcal{G}}
    \\newcommand{\\calH}{\\mathcal{H}}
    \\newcommand{\\calI}{\\mathcal{I}}
    \\newcommand{\\calD}{\\mathcal{D}}
    \\newcommand{\\calB}{\\mathcal{B}}

    \\title{a Title}
    \\begin{document}
    hello
    \\end{document}
    ''')


def test_pysplice_generate_file():
    source = dedent('''
    \\pysplice:
        with open('test.txt', 'w') as f:
            f.write('I am a test')
    ===
    ''')
    translator = Translator(source)
    res = translator.translate()
    print('res:', res)
    assert len(translator.generated_files) == 1
    with open(translator.generated_files[0], 'r') as f:
        assert f.read() == 'I am a test'


def test_colon():
    source = dedent('''
    \\documentclass{article}
    ===
    \\textbf{hi}\\colon
    Hello?
    ''')
    assert translate(source) == dedent(
    '''
    \\documentclass{article}
    \\begin{document}
    \\textbf{hi}:
    Hello?
    \\end{document}\n''')
