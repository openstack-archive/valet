# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ast

import six

import valet.tests.unit.valetfixtures import hacking as valet_hacking


class BaseASTChecker(ast.NodeVisitor):
    """Provides a simple framework for writing AST-based checks.

    Subclasses should implement visit_* methods like any other AST visitor
    implementation. When they detect an error for a particular node the
    method should call ``self.add_error(offending_node)``. Details about
    where in the code the error occurred will be pulled from the node
    object.

    Subclasses should also provide a class variable named CHECK_DESC to
    be used for the human readable error message.

    """

    def __init__(self, tree, filename):
        self._tree = tree
        self._errors = []

    def run(self):
        self.visit(self._tree)
        return self._errors

    def add_error(self, node, message=None):
        message = message or self.CHECK_DESC
        error = (node.lineno, node.col_offset, message, self.__class__)
        self._errors.append(error)


class CheckForAssertingNoneEquality(BaseASTChecker):

        CHECK_DESC = ('V001 Use self.assertIsNone(...) when comparing '
                      'against None')
        CHECK_DESC_NOT = ('V002 Use self.assertIsNotNone(...) when comparing '
                          'against None')

        def visit_Call(self, node):

            def _is_None(node):
                if six.PY3:
                    return (isinstance(node, ast.NameConstant)
                            and node.value is None)
                else:
                    return isinstance(node, ast.Name) and node.id == 'None'

            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "assertEqual":
                    for arg in node.args:
                        if _is_None(arg):
                            self.add_error(node, message=self.CHECK_DESC)
                elif node.func.attr == "assertNotEqual":
                    for arg in node.args:
                        if _is_None(arg):
                            self.add_error(node, message=self.CHECK_DESC_NOT)

            super(CheckForAssertingNoneEquality, self).generic_visit(node)


def factory(register):
    register(CheckForAssertingNoneEquality)
