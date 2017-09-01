#
# Copyright 2014-2017 AT&T Intellectual Property
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

"""Group Template Test."""

from tempest import test
from valet.tests.tempest.scenario.scenario_base import ScenarioTestCase


class TestGroupTemplate(ScenarioTestCase):
    """This test case attempts to run the following tests:

     * Create /varying the Group Type
     * Update the Group description  (valid)
     * Update the Group type and level (invalid)
     * Delete the stack and make sure the group is deleted
     * Create / Read / Update and Delete Group
    """

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00120')
    def test_heat_group_create_affinity(self):
        sid, sname = self._one_create("TGrpTmpl_GroupOne",
                                      "affinity", "host", "TestGroup")

    @test.idempotent_id('f61b522b-b84d-458d-b54b-f07f19a00220')
    def test_heat_group_create__diversity(self):
        sid, sname = self._one_create("TGrpTmpl_GroupTwo",
                                      "diversity", "rack", "TestGroup")

    @test.idempotent_id('f16b522b-b84d-458d-b45b-f07f19a00320')
    def test_heat_group_create_exclusivity(self):
        sid, sname = self._one_create("TGrpTmpl_GroupThree",
                                      "exclusivity", "host", "TestGroup")

    @test.idempotent_id('f61c255b-b84d-458d-b45b-f07f19a00400')
    def test_heat_group_update_desc(self):
        base_type = "affinity"
        base_level = "host"
        base_desc = "TestGroup"
        base_name = "TGrpTmpl_GroupFour"
        sid, sname = self._one_create(base_name, base_type,
                                      base_level, base_desc)
        self._one_update(sid, sname, base_name, base_type,
                         base_level, base_desc + "Changed")

    @test.idempotent_id('f61b255b-b84d-458d-b45b-f07f19a00500')
    def test_heat_group_update_name(self):
        # This update will only work because the Group is not used
        # Heat will delete and recreate the Valet Group
        base_type = "exclusivity"
        base_level = "rack"
        base_desc = "TestGroup"
        base_name = "TGrpTmpl_GroupFive"
        sid, sname = self._one_create(base_name, base_type,
                                      base_level, base_desc)
        self._one_update(sid, sname, base_name + "Changed", base_type,
                         base_level, base_desc)

    @test.idempotent_id('f61b255b-b84d-458d-b45b-f07f19a00600')
    def test_heat_group_update_bad_level(self):
        base_type = "affinity"
        base_level = "host"
        base_desc = "TestGroup"
        base_name = "TGrpTmpl_GroupSixLevel"
        sid, sname = self._one_create(base_name, base_type,
                                      base_level, base_desc)
        grpx = self._one_update_bad(sid, sname, base_name,
                                    base_type, "rack", base_desc)
        self._check_group_values(grpx, base_name, base_type,
                                 base_level, base_desc)

    @test.idempotent_id('f61b255b-b44d-458d-b45b-f07f19a00700')
    def test_heat_group_update_bad_type(self):
        base_type = "affinity"
        base_level = "host"
        base_desc = "TestGroup"
        base_name = "TGrpTmpl_GroupSixType"
        sid, sname = self._one_create(base_name, base_type,
                                      base_level, base_desc)
        grpx = self._one_update_bad(sid, sname, base_name,
                                    "exclusivity", base_level, base_desc)
        self._check_group_values(grpx, base_name, base_type,
                                 base_level, base_desc)

    @test.idempotent_id('f61b522b-b84d-458d-b45b-f07f19a00820')
    def test_heat_group_delete(self):
        sid, sname = self._one_create_self_clean("TGrpTmpl_GroupEight",
                                                 "affinity", "host", "TestGroup")
        self._one_delete(sid, "TGrpTmpl_GroupEight")

    @test.idempotent_id('f16b522b-b84d-458d-b45b-f07f19a00920')
    def test_heat_group_crud(self):
        sid, sname = self._one_create_self_clean("TGrpTmpl_GroupNine",
                                                 "affinity", "host",
                                                 "TestGroup")
        grpx = self._select_group("TGrpTmpl_GroupNine")
        self.assertNotEqual(grpx, None)
        self._check_group_values(grpx, "TGrpTmpl_GroupNine",
                                 "affinity", "host", "TestGroup")

        self._one_update(sid, sname, "TGrpTmpl_GroupNine",
                         "affinity", "host", "TestGroup")
        self._one_delete(sid, "TGrpTmpl_GroupNine")

    def _one_create_self_clean(self, xname, xtype, xlevel, xdesc):
        create_template_file = "/templates/group_create_basic.yml"
        xparams = {"group_name": xname, "group_type": xtype,
                   "group_level": xlevel, "group_desc": xdesc}

        stack_id, stack_name = \
            self.create_stack_no_env_self_clean("test_group_create", create_template_file,
                                                params=xparams)

        grpx = self._select_group(xname)
        self.assertNotEqual(grpx, None)
        self._check_group_values(grpx, xname, xtype, xlevel, xdesc)

        return stack_id, stack_name

    def _one_create(self, xname, xtype, xlevel, xdesc):
        create_template_file = "/templates/group_create_basic.yml"
        xparams = {"group_name": xname, "group_type": xtype,
                   "group_level": xlevel, "group_desc": xdesc}

        stack_id, stack_name = \
            self.create_stack_no_env("test_group_create", create_template_file,
                                     params=xparams)

        grpx = self._select_group(xname)
        self.assertNotEqual(grpx, None)
        self._check_group_values(grpx, xname, xtype, xlevel, xdesc)

        return stack_id, stack_name

    def _one_update(self, stack_id, stack_name, xname, xtype, xlevel, xdesc):
        update_template_file = "/templates/group_create_basic.yml"
        xparams = {"group_name": xname, "group_type": xtype,
                   "group_level": xlevel, "group_desc": xdesc}
        self.update_stack_no_env(stack_id, stack_name,
                                 update_template_file,
                                 params=xparams)
        grpx = self._select_group(xname)
        self.assertNotEqual(grpx, None)
        self._check_group_values(grpx, xname,
                                 xtype, xlevel, xdesc)

    def _one_update_bad(self, stack_id, stack_name, xname,
                        xtype, xlevel, xdesc):
        update_template_file = "/templates/group_create_basic.yml"
        xparams = {"group_name": xname, "group_type": xtype,
                   "group_level": xlevel, "group_desc": xdesc}
        try:
            self.update_stack_no_env(stack_id, stack_name,
                                     update_template_file,
                                     params=xparams)
            self.assertEqual("Invalid Update ", "Passed.  Error.")
        except Exception:
            grpx = self._select_group(xname)
            self.assertNotEqual(grpx, None)
            return grpx
        return None

    def _one_delete(self, stack_id, xname):
        self.delete_stack(stack_id)
        grpx = self._select_group(xname)
        self.assertEqual(grpx, None)

    def _check_group_values(self, grpx, xname, xtype, xlevel, xdesc):
        self.assertEqual(xname, grpx['name'])
        self.assertEqual(xtype, grpx['type'])
        self.assertEqual(xlevel, grpx['level'])
        self.assertEqual(xdesc, grpx['description'])

    def _select_group(self, xname):
        for grpx in self.get_list_groups():
            if grpx["name"] == xname:
                return grpx
        return None
