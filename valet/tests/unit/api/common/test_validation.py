#
# Copyright (c) 2014-2017 AT&T Intellectual Property
#
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

"""Common Validation Helpers"""

from valet.api.common import validation
from valet.tests.unit.api.v1 import api_base


class TestValidation(api_base.ApiBase):
    """Test Harness"""

    uuid = '731056cc-c802-4797-a32b-17eaced354fa'

    def setUp(self):
        """Initializer"""
        super(TestValidation, self).setUp()

    def test_is_valid_uuid4(self):
        """Test with a valid UUID"""
        valid = validation.is_valid_uuid4(self.uuid)
        self.assertTrue(valid)

    def test_is_valid_uuid4_no_hyphens(self):
        """Test with a valid UUID, no hyphens"""
        valid = validation.is_valid_uuid4(self.uuid.replace('-', ''))
        self.assertTrue(valid)

    def test_is_invalid_uuid4(self):
        """Test with an invalid UUID"""
        valid = validation.is_valid_uuid4("not_a_uuid")
        self.assertFalse(valid)
