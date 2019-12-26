#!/usr/bin/env python
# encoding: utf-8

"""A regex based mock generator from .h header files."""

import re
import logging
import collections
import textwrap
import string

import click

__version__ = "0.5"  # UPDATE setup.py when changing version.
__author__ = "elmotec"
__license__ = "MIT"


log = logging.getLogger(__name__)
MockMethod = collections.namedtuple("MockMetod", "ret_type name parameters qualifiers")


def generate_mock_method(method):
    """Generate MOCK_METHOD google macro."""
    return (
        f"MOCK_METHOD({method.ret_type}, {method.name}, "
        f"{method.parameters}, ({method.qualifiers}));"
    )


def generate_default_delegation(method):
    """Generate ON_CALL default delegation statement."""
    arg_pholders, arg_names, arg_type_and_names = [], [], []
    for index, arg in enumerate(
        method.parameters.replace("(", "").replace(")", "").split(",")
    ):
        m = re.match(
            r"^\s*(?P<arg_type>(?:const\s+)?[:\w]+(?:\s*[\*\&])?)\s*(?P<arg_name>\w+)?\s*(= 0)?\s*$",
            arg,
        )
        if not m:
            continue
        arg_name = f"p{index}"
        arg_is_matched = m.lastindex >= 2
        if arg_is_matched:
            arg_name = m.group("arg_name")
        arg_type_and_name = f"{m.group('arg_type')} {arg_name}"
        arg_type_and_names.append(arg_type_and_name)
        arg_names.append(arg_name)
        arg_pholders.append("_")
    body = "{ " + f"return real->{method.name}({', '.join(arg_names)});" + " }"
    return f"ON_CALL(*this, {method.name}({', '.join(arg_pholders)})).WillByDefault(Invoke([]({', '.join(arg_type_and_names)}) {body}));"


class BraceCounter:
    """Counts braces as it processes statements."""

    def __init__(self):
        self.count = 0

    def process(self, statement):
        """Look for opening and closing braces and update count."""
        self.count += statement.count("{")
        self.count -= statement.count("}")


class MockMaker:
    """Makes a mock file from a C++ header file."""

    method_decl_re = re.compile(
        r"^\s*(?P<virtual>virtual)?\s*(?P<ret_type>[\w:<>,\s&*]+)\s+(?P<name>\w+)(?P<params>\([^\)]*\))(?P<qualifiers>(?:\s*\w+)*)(\s*=.*)?"
    )

    def __init__(self, target_class=None, indent=None):
        """Initialize MockMaker."""
        self.target_class = target_class

    def parse_method(self, match):
        """Process match from the regular expression."""
        ret_type = match.group("ret_type")
        name = match.group("name")
        params = match.group("params")
        quals = match.group("qualifiers").split()
        if "override" not in quals and not match.group("virtual"):
            return
        if "override" not in quals:
            quals.append("override")
        if "final" in quals:
            return
        params = re.sub(r"\s+", " ", params)
        params = re.sub(r"\s*=\s*\w+", "", params)
        return MockMethod(ret_type, name, params, ", ".join(quals))

    def find_methods_to_mock(self, input):
        """Makes the mock."""
        content = input.read()
        methods = []
        brace_counter = BraceCounter()
        class_brace_level, content_of_interest = None, []
        if self.target_class is not None:
            for line in content.split("\n"):
                brace_counter.process(line)
                if class_brace_level is None:
                    if 'class' not in line and self.target_class not in line:
                        continue
                    offset = 1
                    if '{' in line:
                        offset = 0
                    class_brace_level = brace_counter.count + offset
                    continue
                elif brace_counter.count < class_brace_level:
                    break
                content_of_interest.append(line)
            content = "\n".join(content_of_interest)
        for statement in re.split(r"[;{}]", content):
            match = self.method_decl_re.match(statement)
            if not match:
                continue
            method = self.parse_method(match)
            if not method:
                continue
            methods.append(method)
        return methods

    def make_mock(self, input, output, template=None):
        """Makes the mock.

        Args:
            input: input header or snippet of code.
            output: output mock .cpp.
            template: template to use for output.

        """
        methods = self.find_methods_to_mock(input)
        mock_methods = "\n".join(generate_mock_method(method) for method in methods)
        generated = mock_methods
        output.write(generated)

    def __call__(self, *args, **kwargs):
        return self.make_mock(*args, **kwargs)


@click.command()
@click.argument("input", type=click.File("r"))
@click.option("-o", "--output", type=click.File("w"), default="-", help="output file")
@click.option("-c", "--target-class", type=str, help="target class name")
def main(input, output, target_class=None):
    """Process a C++ header file and generate a mock class based on it.

    This tool is regex based and does not handle all c++, notably:
    - no support for operators.
    - (TBD)

    """
    mockmaker = MockMaker(target_class=target_class)
    mockmaker.make_mock(input, output)
    return 0


if __name__ == "__main__":
    main()
