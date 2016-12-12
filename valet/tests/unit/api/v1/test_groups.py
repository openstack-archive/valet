
import mock
import pecan
from valet.api.db.models.music.groups import Group
from valet.api.db.models.music import Query, Results
import valet.api.v1.controllers.groups as groups
from valet.api.v1.controllers.groups import GroupsController, MembersController, GroupsItemController, MembersItemController
from valet.tests.unit.api.v1.api_base import ApiBase


class TestGroups(ApiBase):
    ''' Unit tests for valet.api.v1.controllers.groups '''

    def setUp(self):
        super(TestGroups, self).setUp()
        self.tenant_id = "testprojectid"

        # core.state = mock.MagicMock()

        # Testing class GroupsController
        self.groups_controller = GroupsController()

        # Testing class MembersController
        self.members_controller = MembersController()

        # Testing class GroupsItemController
        self.groups_item_controller = self.init_GroupsItemController()

        # Testing class MembersItemController
        self.members_item_controller = self.init_MembersItemController()

    @mock.patch.object(groups, 'request')
    @mock.patch.object(Query, 'filter_by')
    def init_GroupsItemController(self, mock_filter, mock_request):
        mock_request.context = {}
        mock_filter.return_value = Results([Group("test_name", "test_description", "test_type", None)])
        contrler = GroupsItemController("group_id")

        self.validate_test("test_name" == groups.request.context['group'].name)
        return contrler

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    def test_init_GroupsItemController_unhappy(self):
        GroupsItemController("group_id")
        self.validate_test("Group not found" in TestGroups.response)

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    @mock.patch.object(groups, 'request')
    def init_MembersItemController(self, mock_request):
        grp = Group("test_member_item_name", "test_description", "test_type", None)
        grp.members = ["demo members"]
        mock_request.context = {'group': grp}

        MembersItemController("member_id")
        self.validate_test("Member not found in group" in TestGroups.response)

        contrler = MembersItemController("demo members")
        self.validate_test("test_member_item_name" == groups.request.context['group'].name)
        return contrler

    def test_allow(self):
        self.validate_test(self.groups_controller.allow() == 'GET,POST')

        self.validate_test(self.members_controller.allow() == 'PUT,DELETE')

        self.validate_test(self.groups_item_controller.allow() == "GET,PUT,DELETE")

        self.validate_test(self.members_item_controller.allow() == "GET,DELETE")

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    @mock.patch.object(groups, 'request')
    def test_index(self, mock_request):
        mock_request.method = "HEAD"
        self.groups_controller.index()
        self.validate_test("The HEAD method is not allowed" in TestGroups.response)

        mock_request.method = "GET"
        self.members_controller.index()
        self.validate_test("The GET method is not allowed" in TestGroups.response)

        mock_request.method = "POST"
        self.groups_item_controller.index()
        self.validate_test("The POST method is not allowed" in TestGroups.response)

        mock_request.method = "PUT"
        self.members_item_controller.index()
        self.validate_test("The PUT method is not allowed" in TestGroups.response)

    @mock.patch.object(groups, 'request')
    def index_put(self, mock_request):
        pecan.conf.identity.engine.is_tenant_list_valid.return_value = True

        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        r = self.members_controller.index_put(members=[self.tenant_id])

        self.validate_test(groups.response.status == 201)
        self.validate_test(r.members[0] == self.tenant_id)

        return r

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    @mock.patch.object(groups, 'request')
    def test_index_put_unhappy(self, mock_request):
        pecan.conf.identity.engine.is_tenant_list_valid.return_value = False

        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        self.members_controller.index_put(members=[self.tenant_id])

        self.validate_test("Member list contains invalid tenant IDs" in TestGroups.response)

    @mock.patch.object(groups, 'tenant_servers_in_group')
    @mock.patch.object(groups, 'request')
    def test_index_put_delete(self, mock_request, mock_func):
        grp_with_member = self.index_put()

        mock_request.context = {'group': grp_with_member}
        mock_func.return_value = None
        self.members_controller.index_delete()

        self.validate_test(groups.response.status == 204)
        self.validate_test(grp_with_member.members == [])

    @mock.patch.object(groups, 'tenant_servers_in_group')
    @mock.patch.object(groups, 'request')
    def test_index_delete_member_item_controller(self, mock_request, mock_func):
        grp = Group("test_name", "test_description", "test_type", None)
        grp.members = ["demo members"]

        mock_request.context = {'group': grp, 'member_id': "demo members"}
        mock_func.return_value = None

        self.members_item_controller.index_delete()

        self.validate_test(groups.response.status == 204)
        self.validate_test(grp.members == [])

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    @mock.patch.object(groups, 'tenant_servers_in_group')
    @mock.patch.object(groups, 'request')
    def test_index_delete_member_item_controller_unhappy(self, mock_request, mock_func):
        grp = Group("test_name", "test_description", "test_type", None)
        grp.members = ["demo members"]

        mock_request.context = {'group': grp, 'member_id': "demo members"}
        mock_func.return_value = None

        self.members_item_controller.index_delete()

        self.validate_test("Member not found in group" in TestGroups.response)

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    @mock.patch.object(groups, 'tenant_servers_in_group')
    @mock.patch.object(groups, 'request')
    def test_index_delete_unhappy(self, mock_request, mock_func):
        grp_with_member = self.index_put()

        mock_request.context = {'group': grp_with_member}
        mock_func.return_value = "Servers"
        self.members_controller.index_delete()

        self.validate_test("has servers in group" in TestGroups.response)

    @mock.patch.object(groups, 'request')
    def test_index_put_groups_item_controller(self, mock_request):
        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        r = self.groups_item_controller.index_put(description="new description")

        self.validate_test(groups.response.status == 201)
        self.validate_test(r.description == "new description")

        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        r = self.groups_item_controller.index_put()

        self.validate_test(groups.response.status == 201)
        self.validate_test(r.description == "test_description")

    @mock.patch.object(groups, 'request')
    def test_index_delete_groups_item_controller(self, mock_request):
        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        self.groups_item_controller.index_delete()

        self.validate_test(groups.response.status == 204)

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    @mock.patch.object(groups, 'request')
    def test_index_delete_groups_item_controller_unhappy(self, mock_request):
        grp = Group("test_name", "test_description", "test_type", None)
        grp.members = ["demo members"]
        mock_request.context = {'group': grp}
        self.groups_item_controller.index_delete()

        self.validate_test(groups.response.status == 204)
        self.validate_test("Unable to delete a Group with members." in TestGroups.response)

    @mock.patch.object(groups, 'request')
    @mock.patch.object(Query, 'all')
    def test_index_get(self, mock_all, mock_request):
        all_groups = ["group1", "group2", "group3"]
        mock_all.return_value = all_groups
        response = self.groups_controller.index_get()

        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        item_controller_response = self.groups_item_controller.index_get()

        self.members_item_controller.index_get()
        self.validate_test(groups.response.status == 204)

        self.validate_test("test_name" in item_controller_response["group"].name)
        self.validate_test(len(response) == 1)
        self.validate_test(len(response["groups"]) == len(all_groups))
        self.validate_test(all_groups == response["groups"])

    def test_index_post(self):
        group = self.groups_controller.index_post(name="testgroup", description="test description", type="testtype")

        self.validate_test(groups.response.status == 201)
        self.validate_test(group.name == "testgroup")

    @mock.patch.object(groups, 'error', ApiBase.mock_error)
    def test_index_post_unhappy(self):
        pecan.conf.music = None
        self.groups_controller.index_post(name="testgroup", description="test description", type="testtype")

        self.validate_test("Unable to create Group" in TestGroups.response)

    def test_index_options(self):
        self.groups_item_controller.index_options()
        self.validate_test(groups.response.status == 204)

        self.members_item_controller.index_options()
        self.validate_test(groups.response.status == 204)
