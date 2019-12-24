#!/usr/bin/env python
# coding: utf-8

"""Test module to test makemock."""

import logging
import sys
import textwrap
import io

import click.testing
import unittest

import makemock


class CliRunnerTest(unittest.TestCase):
    """Runner tests"""

    def setUp(self):
        """Given the runner."""
        self.runner = click.testing.CliRunner()

    def test_makemock_with_no_argument(self):
        result = self.runner.invoke(makemock.main, [])
        assert result.exit_code == 2
        assert 'Error: Missing argument "INPUT".' in result.output

    def test_makemock_with_input_file(self):
        result = self.runner.invoke(makemock.main, ["invalid"])
        assert result.exit_code == 2
        assert 'Error: Invalid value for "INPUT"' in result.output


class MockMakerTest(unittest.TestCase):
    """Given a MockMaker."""

    input_text = []
    expected_values = []

    @classmethod
    def tearDownClass(cls) -> None:
        """Put a breakpoint here to inspect the list of input processed."""
        print("input tested:", "\n".join(cls.input_text), sep="\n")

    def setUp(self):
        """Create MockMaker and list of input and output."""
        self.mockmaker = makemock.MockMaker()

    def verify(self, in_text, expected, template=None):
        """Factors generated output vs expectation.

        Also stores the input and expected values in input and output lists.

        Args:
            in_text: input text to process.
            expected: expected mocked output.
            template: output template to use.

        """
        self.input_text.append(in_text)
        self.expected_values.append(expected)
        input, output = io.StringIO(in_text), io.StringIO()
        self.mockmaker.make_mock(input, output, template)
        self.assertEqual(expected, output.getvalue())

    def test_simple_make(self):
        """Ignore code that does not need to be in the mock class."""
        self.verify("no changes", "")

    def test_simple_method(self):
        self.verify(
            "virtual int simple_method();",
            "MOCK_METHOD(int, simple_method, (), (override));",
        )

    def test_multiple_arguments(self):
        self.verify(
            "virtual int simple_method_args(int, int);",
            "MOCK_METHOD(int, simple_method_args, (int, int), (override));",
        )

    def test_multiple_lines(self):
        self.verify(
            "virtual int simple_method_args(int,\n"
            "                               int);",
            "MOCK_METHOD(int, simple_method_args, (int, int), (override));",
        )

    def test_multiple_statements(self):
        self.verify(
            "virtual int simple_method_args(int,\n"
            "                               int);\n"
            "virtual int simple_method();",
            "MOCK_METHOD(int, simple_method_args, (int, int), (override));\n"
            "MOCK_METHOD(int, simple_method, (), (override));",
        )

    def test_const_qualifier(self):
        self.verify(
            "virtual int simple_const_method_args(int, int) const;",
            "MOCK_METHOD(int, simple_const_method_args, (int, int), (const, override));",
        )

    def test_const_qualifier_with_named_arguments(self):
        self.verify(
            "virtual int simple_const_method_vals(int x, int y) const;",
            "MOCK_METHOD(int, simple_const_method_vals, (int x, int y), (const, override));",
        )

    def test_templated_return_value(self):
        self.verify(
            "virtual std::pair<bool, int> get_pair();",
            "MOCK_METHOD(std::pair<bool, int>, get_pair, (), (override));",
        )

    def test_templated_arguments(self):
        self.verify(
            "virtual bool check_map(std::map<int, double>, bool);",
            "MOCK_METHOD(bool, check_map, (std::map<int, double>, bool), (override));",
        )

    def test_pointer_argument(self):
        self.verify(
            "virtual bool transform(Gadget * g);",
            "MOCK_METHOD(bool, transform, (Gadget * g), (override));",
        )

    def test_pure_virtual_trailer(self):
        self.verify(
            "virtual bool transform() = 0;",
            "MOCK_METHOD(bool, transform, (), (override));",
        )

    def test_return_type_reference(self):
        self.verify(
            "virtual Bar & GetBar();", "MOCK_METHOD(Bar &, GetBar, (), (override));"
        )

    def test_const_return_type(self):
        self.verify(
            "virtual const Bar & GetBar() const;",
            "MOCK_METHOD(const Bar &, GetBar, (), (const, override));",
        )

    def test_overriden_method(self):
        self.verify(
            "Foo GetFoo() const override;",
            "MOCK_METHOD(Foo, GetFoo, (), (const, override));",
        )

    def test_non_overriden_non_virtual_method_not_mocked(self):
        self.verify("Foo GetFoo() const;", "")


class DefaultDelegationTest(unittest.TestCase):
    """Test generation of method delegation calls."""

    def verify(self, method, expected):
        actual = makemock.generate_default_delegation(method)
        self.assertEqual(expected, actual)

    def test_simple_call(self):
        self.verify(makemock.MockMethod("int", "DoThis", "()", "const"),
                    "ON_CALL(DoThis()).WillByDefault(Return(real->DoThis());")

    def test_with_arg_name(self):
        self.verify(makemock.MockMethod("int", "DoThis", "(int)", "const"),
                    "ON_CALL(DoThis(int p0)).WillByDefault(Return(real->DoThis(p0));")

    def test_without_arg_name(self):
        self.verify(makemock.MockMethod("int", "DoThis", "(int val)", "const"),
                    "ON_CALL(DoThis(int val)).WillByDefault(Return(real->DoThis(val));")

    def test_with_const_arg(self):
        self.verify(makemock.MockMethod("int", "DoThis", "(const int)", "const"),
                    "ON_CALL(DoThis(const int p0)).WillByDefault(Return(real->DoThis(p0));")

    def test_with_const_pointer_arg(self):
        self.verify(makemock.MockMethod("int", "DoThis", "(const char *)", "const"),
                    "ON_CALL(DoThis(const char * p0)).WillByDefault(Return(real->DoThis(p0));")

    def test_with_const_ref_arg(self):
        self.verify(makemock.MockMethod("int", "DoThis", "(const int &)", "const"),
                    "ON_CALL(DoThis(const int & p0)).WillByDefault(Return(real->DoThis(p0));")

    def test_with_namespace(self):
        self.verify(makemock.MockMethod("int", "DoThis", "(const std::string &)", "const"),
                    "ON_CALL(DoThis(const std::string & p0)).WillByDefault(Return(real->DoThis(p0));")

    def test_multiple_arguments(self):
        self.verify(makemock.MockMethod("int", "DoThis", "(const char * str, string &)", "const"),
                    "ON_CALL(DoThis(const char * str, string & p1)).WillByDefault(Return(real->DoThis(str, p1));")


class MockMakerTestWithHeader(unittest.TestCase):
    def setUp(self):
        """Initialize header files."""
        self.mockmaker = makemock.MockMaker()
        header = textwrap.dedent(
            """\
        #include <iostream>
        #include <vector>

        namespace test
        {

        class ProdClass: public ParentClass
        {
        public:
            ProdClass();
            ProdClass(const ProdClass &);
            ProdClass(ProdClass &&);
            ~ProdClass();
            ProdClass & operator=(const ProdClass &);
            ProdClass && operator=(ProdClass &&);

            int DoThis() override;
            virtual std::string DoThat()
            {
                return DoThatOtherThing();
            }       
            void DontMock();
        };
        }
        """
        )

    def notest_default_template(self):
        """Generate mock methods and delegate function."""
        expected = textwrap.dedent("""\
        MOCK_METHOD(int, DoThis, (), (override));
        MOCK_METHOD(std::string, DoThat, (), (override));
        
        void DelegateTo(ProdClass * real)
        {
            ON_CALL(DoThis()).WillByDefault(Return(real->DoThis());
            ON_CALL(DoThat(std::string val)).WillByDefault(Return(real->DoThat(val));
        }
        """)
        self.verify(self.header, expected, template=makemock.get_basic_template())

    def notest_default_template(self):
        """Generate full header using default template."""
        expected = textwrap.dedent(
            """\
        #include "ProdClass.h"
        
        namespace test
        {
        class MockProdClass: public ProdClass
        {
        public:
            MOCK_METHOD(int, DoThis, (), (override));
            MOCK_METHOD(std::string, DoThat, (), (override));
            void DelegateTo(ProdClass * real);
        };
        
        void MockProdClass::DelegateTo(ProdClass * real)
        {
            ON_CALL(DoThis()).WillByDefault(Return(real->DoThis());
            ON_CALL(DoThat(std::string val)).WillByDefault(Return(real->DoThat(val));
        }
        }        
        """
        )
        self.verify(self.header, expected, template=makemock.get_header_template())


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
    try:
        unittest.main(argv=sys.argv)
    finally:
        logging.shutdown()
