# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import textwrap
import unittest

try:
    import pep8
except ImportError:
    import pycodestyle as pep8

from valet.tests.hacking import checks
from valet.tests.unit.valetfixtures import hacking


class BaseStyleChecker(unittest.TestCase):

    def setUp(self):
        super(BaseStyleChecker, self).setUp()
        self.addCleanup(delattr, self, 'code_ex')

    def get_checker(self):
        """Return the checker to be used for tests in this class."""
        raise NotImplementedError('Subclass must provide '
                                  'a real implementation.')

    def get_fixture(self):
        return hacking.HackingCheck()

    def run_check(self, code):
        pep8.register_check(self.get_checker())

        lines = textwrap.dedent(code).strip().splitlines(True)

        # Load all keystone hacking checks, they are of the form Kddd,
        # where ddd can from range from 000-999
        guide = pep8.StyleGuide(select='K')
        checker = pep8.Checker(lines=lines, options=guide.options)
        checker.check_all()
        checker.report._deferred_print.sort()
        return checker.report._deferred_print

    def assert_has_errors(self, code, expected_errors=None):
        actual_errors = [e[:3] for e in self.run_check(code)]
        self.assertItemsEqual(expected_errors or [], actual_errors)
