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

import sys

import fixtures


class HackingCheck(fixtures.Fixture):

    asserting_none_equality = {
        'code': """
            class Test(object):

                def test(self):
                    self.assertEqual('', '')
                    self.assertEqual(None, '')
                    self.assertEqual('', None)
                    self.assertNotEqual(None, '')
                    self.assertNotEqual('', None)
                    self.assertNotEqual(None, '') # noqa
                    self.assertNotEqual('', None) # noqa
        """,
        'expected_errors': [
            (5, 8, 'V001'),
            (6, 8, 'V001'),
            (7, 8, 'V002'),
            (8, 8, 'V002')
        ]}
