import sys


class Arg:
    def __init__(self, contents, optional=False):
        self.contents = contents
        self.optional = optional

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def resolve_args(name, params, args):
    '''
    params: a string consisting of `!`s and `?`s, where `!`s represent required arguments
        and `!`s represent optional arguments
    args: a list of `Arg`s to be resolved with the `params` string
    errors: if there is a missing required argument or a superfluous optional argument
    returns: a list of `Arg`s with additional `None`s for missing optional arguments
    raises: Exception if passed more args than params
    '''
    all_args = []
    arg_num = 0
    if len(args) > len(params):
        raise Exception('When would this happen?')  # TODO: be clearer about internal errors
    for param in params:
        if param == '!':
            if arg_num < len(args) and not args[arg_num].optional:
                all_args.append(args[arg_num].contents)
                arg_num += 1
            elif arg_num >= len(args):
                raise TranslationError('Missing required argument for command `{}`'.format(name))
            else:
                raise TranslationError('Superfluous optional argument provided to command `{}`'.format(name))
        else:
            if arg_num < len(args) and args[arg_num].optional:
                all_args.append(args[arg_num].contents)
                arg_num += 1
            else:
                all_args.append(None)
    return all_args

class Command:
    def __init__(self, name, translate_fn, params=''):
        self.name = name
        self.translate_fn = translate_fn
        self.params = params
        assert all([p in '!?' for p in params])

    def translate(self, args):
        return self.translate_fn(*resolve_args(self.name, self.params, args))


class Environment:
    def __init__(self, name, translate_fn, params=''):
        self.name = name
        self.translate_fn = translate_fn
        self.params = params
        assert all([p in '!?' for p in params])

    def translate(self, body, args):
        return self.translate_fn(body, *resolve_args(self.name, self.params, args))


def latex_cmd(name, args):
    return '\\%s%s' % (name, ''.join('{%s}' % arg for arg in args))


def latex_env(name, before='', body='', after='', args=''):
    return '\\begin{%s}%s%s%s%s\\end{%s}' % (name, args, before, body, after, name)


def translate_tbf(args):
    return latex_cmd('textbf', args)


commands = {
    'tbf': Command('tbf', translate_tbf, params='!')
}


def translate_eq(body, label):
    before = ''
    if label is not None:
        before = '\\label{%s}' % label
    return latex_env('equation', before=before, body=body)


environments = {
    'eq': Environment('eq', translate_eq, params='?')
}


class TranslationError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__()


def isnewline(char):
    return char == '\n'


def iswhitespace(char):
    return str.isspace(char) and not isnewline(char)


def is_opt_end(char):
    return char in '#$%^&_{}[]~\\'


class Translator:
    def __init__(self, text):
        self.indent_str = None
        self.indent_level = 0

        self.pos = 0
        self.text = text

        self.in_document = False

    def finished(self):
        return self.pos == len(self.text)

    def not_finished(self):
        return not self.finished()

    def parse_while(self, pred):
        '''
        pred: a boolean-valued function (i.e. a predicate) on a character
        postcondition: `self.pos` is at the first character *not* satisfying `pred`, after the original `self.pos` at call-time,
            or `len(self.text)` if there is no such character
        '''
        # TODO: deal with unexpected EOF
        while self.not_finished() and pred(self.text[self.pos]):
            self.pos += 1

    def parse_until(self, pred):
        '''
        pred: a boolean-valued function (i.e. a predicate) on a character
        postcondition: `self.pos` is at the first character satisfying `pred`, after the original `self.pos` at call-time,
            or `len(self.text)` if there is no such character
        '''
        self.parse_while(lambda c: not pred(c))

    def validate_indent(self, indent):
        '''
        indent: str
        errors: if `indent` is nonempty and isn't either all tabs or all spaces
        '''
        if not (all(s == ' ' for s in indent) or all(s == '\t' for s in indent)):
            self.error('Invalid indentation; must be all spaces or all tabs')  # TODO: more verbose errors

    def level_of_indent(self, indent):
        '''
        indent: str
        precondition: `self.indent_str` is not None
        errors: if `len(indent)` isn't a multiple of `len(self.indent_str)`
        returns: the whole number of non-overlapping `self.indent_str` in `indent`
            (i.e. the indentation level where `self.indent_str` is the base unit of indentation)
        '''
        if not len(indent) % len(self.indent_str) == 0:
            self.error('Indentation must be in multiples of the base indentation `{}`'.format(
                self.indent_str))
        return len(indent) // len(self.indent_str)

    def calc_indent_level(self):
        # TODO: make all functions that don't move self.pos clear from its name (e.g. peek_..., validate_...)
        #assert self.pos == 0 or isnewline(self.text[self.pos - 1]), "pos: {}, text: {}".format(self.pos, self.text[self.pos-1:self.pos+10])
        '''
        precondition: `self.pos` is at the start of a line
        postcondition: `self.pos` is where it started
        errors: if the current line isn't well-indented (e.g. if it is more than one
            deeper than the current level)
        returns: the indentation level of the current line, in terms of `self.indent_str` units
        '''
        indent_start = self.pos
        self.parse_while(iswhitespace)
        indent = self.text[indent_start:self.pos]
        if len(indent) == 0:
            return 0
        self.validate_indent(indent)
        if self.indent_str == None:
            self.indent_str = indent
        indent_level = self.level_of_indent(indent)
        if indent_level > self.indent_level and not indent_level == self.indent_level + 1:
            self.error('You can only indent one level at a time')
        level = self.level_of_indent(indent)
        self.pos = indent_start
        return level

    def parse_empty(self):
        '''
        postcondition: `self.pos` is at the start of the next non-whitespace line (i.e.
            after the preceeding newline), or at `len(self.text)` if there isn't a
            next non-whitespace line
        '''
        # print('parsing empty')
        while self.not_finished():
            # print(self.pos)
            line_end = self.text.find('\n', self.pos)
            if line_end == -1:
                line_end = len(self.text) - 1
            if not str.isspace(self.text[self.pos:line_end + 1]):
                # print('`{}` is not a space'.format(self.text[self.pos:line_end]))
                break
            self.pos = line_end + 1

    def get_control_seq(self):
        '''
        precondition: `self.pos` is at the first character after the escape character ('\\')
        postcondition: `self.pos` is at the first character after the name of the command
            (including for control symbols, commands whose names are single special characters),
            or at `len(self.text)` if there isn't a character after the command name
        returns: the name of the command
        '''
        control_start = self.pos
        self.parse_while(str.isalpha)
        if self.pos == control_start:
            self.pos += 1  # control symbols are only one character long
        # pos should be at the first non-alpha character
        control_seq = self.text[control_start:self.pos]
        return control_seq

    def extract_arg(self, close='}', required=False):
        '''
        close: the closing brace or bracket to the argument
        required: whether to error if no closing brace or bracket is found
        precondition: `self.pos` is at the first character following the opening '{' or '['
        postcondition: `self.pos` is at the first character following the closing '}' or ']',
            or at `len(self.text)` if there is no such character; `extract_arg` ignores
            everything except for other commands inside the braces
        errors: if `required` and the file ends before there is a `close` character
        returns: the substring strictly between the opening and closing curly braces
        '''
        token_start = self.pos
        body = ''
        while self.not_finished():
            self.parse_until(lambda c: c == '\\' or c == close or c == '{')
            if self.not_finished():
                if self.text[self.pos] == '{':
                    body += self.text[token_start:self.pos]
                    self.pos += 1
                    body += '{' + self.extract_arg(required=True) + '}'
                    token_start = self.pos
                elif self.text[self.pos] == '\\':
                    escape_start = self.pos
                    self.pos += 1
                    control_seq = self.get_control_seq()
                    # if self.at_environment():
                    #     self.error('You can\'t start an environment from a command body')
                    body += self.text[token_start:escape_start]
                    if control_seq in commands:
                        body += self.do_command(commands[control_seq])
                    else:
                        _, argstr = self.extract_args()
                        body += '\\' + control_seq + argstr
                        # TODO: issue a warning if the current character is a colon
                    token_start = self.pos
                elif self.text[self.pos] == close:
                    body += self.text[token_start:self.pos]
                    self.pos += 1
                    return body
        if required:
            self.error('Missing closing `{}`'.format(close))
        else:
            return None

    def extract_args(self, min_args=None, max_args=None):
        '''
        min_args: an int representing the minumum number of arguments to parse; None for no minimum
        max_args: an int representing the maximum number of arguments to parse; None for unlimited
        precondition: `self.pos` is at the first character after the name of the command
        postcondition: `self.pos` is at the first character after the last argument's closing brace or bracket
        errors: if there are fewer than `min_args` arguments following the command
        returns: a list of `Arg`s containing the parsed arguments, and a LaTeX string containing
            the arguments in case they are for a LaTeX command
        '''
        if max_args == 0:
            return command.translate([])
        args = []
        argstr = ''
        token_start = self.pos
        nargs = 0
        while True:
            self.parse_while(iswhitespace)
            if self.text[self.pos] == '{':  # TODO: make this less repetitive?
                self.pos += 1
                argstr += self.text[token_start:self.pos]
                token_start = self.pos
                arg = self.extract_arg(close='}', required=True)
                argstr += arg + '}'
                token_start = self.pos
                args.append(Arg(arg, optional=False))
                nargs += 1
            elif self.text[self.pos] == '[':
                arg_start = self.pos
                argstr += self.text[token_start:self.pos]
                self.pos += 1
                arg = self.extract_arg(close=']')
                if arg is not None:
                    token_start = self.pos
                    argstr += '[' + arg + ']'
                    args.append(Arg(arg, optional=True))
                    nargs += 1
                else:
                    self.pos = arg_start
                    break
            else:
                if min_args is not None and nargs < min_args:
                    self.error('Too few arguments provided')
                else:
                    break
            if max_args is not None and nargs >= max_args:
                break
        return args, argstr

    def do_command(self, command):
        '''
        command: `Command` object representing the command to execute
        precondition: `self.pos` is at the first character after the name of the command
            (e.g. a '{', but also possibly some whitespace)
        postcondition: `self.pos` is at the first character after the last argument of the command
            (or after the name for commands with no arguments)
        errors:
            if there are too few arguments
            if the arguments are ill-formed (e.g. contain environments)
        returns: a LaTeX string representing the result of the command
        '''
        if len(command.params) == 0:  # this is just for efficiency
            return command.translate([])
        args, argstr = self.extract_args(max_args=len(command.params))
        return command.translate(args)

    def do_environment(self, environment, args, argstr, outer_indent, for_document=False):
        '''
        environment: either an `Environment` object to do the translation, or a string,
            the name of a LaTeX environment for which to insert a corresponding begin/end
        args: a list of `Arg`s to pass to the environment if it's ours
        argstr: a LaTeX string containing the arguments to pass if it's a LaTeX environment
        outer_indent: indentation level of the enclosing environment, or 0 if unenclosed
        for_document: bool, True if parsing the `document` environment (for the first time), False otherwise
        precondition: `self.pos` is at the first character after the colon
            (e.g. a newline, but also possibly some other whitespace or a non-alph character for one-liners)
        postcondition:
            for one-liner environments, `self.pos` is at the newline at the end of the line
                or at `len(self.text)` if there isn't a trailing newline
            for block environments, `self.pos` is at the first non-whitespace character
                on the (dedented) line following the block, or at `len(self.text)` if
                the block is at the end of the file
        errors:
            if the line opening the environment is empty after the colon, but the following
                line isn't indented and the environment isn't the first `document` environment
            if there is indentation not following the opening of an environment
            if any indentation is ill-formed (e.g. not all tabs or spaces, or
                not a whole repetition of `self.indent_str`)
        returns: a translated LaTeX string for the environment
        '''
        self.parse_while(iswhitespace)
        if self.text[self.pos] == '\n':
            body = self.extract_block(for_environment=True, for_document=for_document)
            if outer_indent > 0:
                body += self.indent_str * outer_indent
        else:
            body_start = self.pos
            body_end = self.text.find('\n', self.pos)
            if body_end == -1:
                body_end = len(self.text)
            self.pos = body_end
            body = self.text[body_start:body_end]
        if isinstance(environment, Environment):
            return environment.translate(body, args)
        else:
            return latex_env(environment, body=body, args=argstr)

    def extract_block(self, for_environment=False, for_document=False):
        # TODO: can this be broken up into smaller methods?
        '''
        for_environment: whether being called from the start of an environment (as opposed
            to the first recursive call, which is outside everything)
        for_document: whether being called from the start of the first `document` environment
        precondition: `self.pos` is at the first newline after the colon for environments,
            or the beginning of the file for the outermost call
        postcondition: `self.pos` is at the start of the line following the block, or at
            `len(self.text)` if the block is at the end of the file
        errors:
            if there is an ill-formed environment (e.g. not indended after and not a one-liner)
            if there is indentation not following the opening of an environment
            if any indentation is ill-formed (e.g. not all tabs or spaces, or
                not a whole repetition of `self.indent_str`)
        returns: the substring containing everything from the original value of `self.pos`
            at calltime through and including the newline before the next non-whitespace
            line, or through the end of the file if the block is at the end of the file
        '''
        body = ''
        # print('starting block at {}, `{}`'.format(self.pos, self.text[self.pos:self.pos+10]))
        token_start = self.pos
        self.parse_empty()
        # print('finished parsing empty')
        indent_level = self.calc_indent_level()
        # print(indent_level)
        if for_environment and not for_document and not indent_level == self.indent_level + 1:
            self.error('You must either put the body of an environment all on one line, or on an indented block on the following line')
        elif not for_environment and not indent_level == 0:
            self.error('The document as a whole must not be indented')
        indented = indent_level == self.indent_level + 1
        #assert indented or not for_environment
        prev_block_indent = self.indent_level
        self.indent_level = indent_level

        while self.not_finished():
            self.parse_until(lambda c: c == '\\' or c == '\n')
            if self.finished():
                break

            if self.text[self.pos] == '\n':
                self.parse_empty()
                line_start = self.pos
                indent_level = self.calc_indent_level()
                # print(indent_level)
                if indent_level > self.indent_level:  # TODO: remove this
                    self.error('Invalid indentation not following the opening of an environment')
                elif indented:
                    if indent_level <= prev_block_indent:
                        body += self.text[token_start:line_start]
                        return body

            elif self.text[self.pos] == '\\':
                # print('Found escape at pos {}'.format(self.pos))
                escape_start = self.pos
                self.pos += 1
                control_seq = self.get_control_seq()
                # print(control_seq)
                body += self.text[token_start:escape_start]
                if control_seq in commands:
                    body += self.do_command(commands[control_seq])
                else:
                    args, argstr = self.extract_args()
                    whitespace_start = self.pos
                    self.parse_while(iswhitespace)
                    if self.text[self.pos] == ':':
                        self.pos += 1
                        # print('at environment')
                        next_for_document = False
                        if not self.in_document and control_seq == 'document':
                            self.in_document = True
                            next_for_document = True
                        # print('Doing environment `{}`'.format(control_seq))
                        if control_seq in environments:
                            environment = environments[control_seq]
                        else:
                            environment = control_seq
                        if indented:
                            outer_indent = prev_block_indent + 1
                        else:
                            outer_indent = 0
                        body += self.do_environment(environment, args, argstr, outer_indent, for_document=next_for_document) + '\n'
                        indent_level = self.calc_indent_level()
                        if indented and indent_level <= prev_block_indent:
                            return body
                        token_start = self.pos
                    else:
                        body += '\\' + control_seq + argstr + self.text[whitespace_start:self.pos]
                token_start = self.pos
        body += self.text[token_start:]
        if body[-1] != '\n':
            body += '\n'
        return body

    def translate(self):
        # import pdb;pdb.set_trace()
        try:
            return self.extract_block()
        except TranslationError as e:
            self.print_error(e.msg)  # XXX: check whether this works (is it .msg?)

    def error(self, msg):
        raise TranslationError(msg)

    def print_error(self, msg):
        sys.stderr.write('{} at char {}'.format(msg, self.pos))  # TODO: better errors
