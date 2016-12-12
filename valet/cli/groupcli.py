#!/usr/bin/python
import argparse
import json
from oslo_config import cfg
import requests
from valet.api.conf import register_conf, set_domain

CONF = cfg.CONF


class ResponseError(Exception):
    pass


class ConnectionError(Exception):
    pass


def print_verbose(verbose, url, headers, body, rest_cmd, timeout):
    if verbose:
        print("Sending Request:\nurl: %s\nheaders: %s\nbody: %s\ncmd: %s\ntimeout: %d\n"
              % (url, headers, body, rest_cmd.__name__ if rest_cmd is not None else None, timeout))


def pretty_print_json(json_thing, sort=True, indents=4):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


def add_to_parser(service_sub):
    parser = service_sub.add_parser('group', help='Group Management',
                                    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30,
                                                                                        width=120))
    parser.add_argument('--version', action='version', version='%(prog)s 1.1')
    parser.add_argument('--timeout', type=int, help='Set request timeout in seconds (default: 10)')
    parser.add_argument('--host', type=str, help='Hostname or ip of valet server')
    parser.add_argument('--port', type=str, help='Port number of valet server')
    parser.add_argument('--os-tenant-name', type=str, help='Tenant name')
    parser.add_argument('--os-user-name', dest='os_username', type=str, help='Username')
    parser.add_argument('--os-password', type=str, help="User's password")
    parser.add_argument('--verbose', '-v', help='Show details', action="store_true")
    subparsers = parser.add_subparsers(dest='subcmd', metavar='<subcommand>')

    # create group
    parser_create_group = subparsers.add_parser('create', help='Create new group.')
    parser_create_group.add_argument('name', type=str, help='<GROUP_NAME>')
    parser_create_group.add_argument('type', type=str, help='<GROUP_TYPE> (exclusivity)')
    parser_create_group.add_argument('--description', type=str, help='<GROUP_DESCRIPTION>')

    # delete group
    parser_delete_group = subparsers.add_parser('delete', help='Delete specified group.')
    parser_delete_group.add_argument('groupid', type=str, help='<GROUP_ID>')

    # delete group member
    parser_delete_group_member = subparsers.add_parser('delete-member', help='Delete members from specified group.')
    parser_delete_group_member.add_argument('groupid', type=str, help='<GROUP_ID>')
    parser_delete_group_member.add_argument('memberid', type=str, help='<MEMBER_ID>')

    # delete all group members
    parser_delete_all_group_members = subparsers.add_parser('delete-all-members', help='Delete all members from '
                                                                                       'specified group.')
    parser_delete_all_group_members.add_argument('groupid', type=str, help='<GROUP_ID>')

    # list group
    subparsers.add_parser('list', help='List all groups.')

    # show group details
    parser_show_group_details = subparsers.add_parser('show', help='Show details about the given group.')
    parser_show_group_details.add_argument('groupid', type=str, help='<GROUP_ID>')

    # update group
    parser_update_group = subparsers.add_parser('update', help='Update group description.')
    parser_update_group.add_argument('groupid', type=str, help='<GROUP_ID>')
    parser_update_group.add_argument('--description', type=str, help='<GROUP_DESCRIPTION>')

    parser_update_group_members = subparsers.add_parser('update-member', help='Update group members.')
    parser_update_group_members.add_argument('groupid', type=str, help='<GROUP_ID>')
    parser_update_group_members.add_argument('members', type=str, help='<MEMBER_ID>')

    return parser


def cmd_details(args):
    if args.subcmd == 'create':
        return requests.post, ''
    elif args.subcmd == 'update':
        return requests.put, '/%s' % args.groupid
    elif args.subcmd == 'update-member':
        return requests.put, '/%s/members' % args.groupid
    elif args.subcmd == 'delete':
        return requests.delete, '/%s' % (args.groupid)
    elif args.subcmd == 'delete-all-members':
        return requests.delete, '/%s/members' % (args.groupid)
    elif args.subcmd == 'delete-member':
        return requests.delete, '/%s/members/%s' % (args.groupid, args.memberid)
    elif args.subcmd == 'show':
        return requests.get, '/%s' % (args.groupid)
    elif args.subcmd == 'list':
        return requests.get, ''


def get_token(timeout, args):
    # tenant_name = args.os_tenant_name if args.os_tenant_name else os.environ.get('OS_TENANT_NAME')
    tenant_name = args.os_tenant_name if args.os_tenant_name else CONF.identity.project_name
    auth_name = args.os_username if args.os_username else CONF.identity.username
    password = args.os_password if args.os_password else CONF.identity.password
    headers = {
        'Content-Type': 'application/json',
    }
    url = '%s/tokens' % CONF.identity.uth_url
    data = '''
    {
    "auth": {
        "tenantName": "%s",
        "passwordCredentials": {
            "username": "%s",
            "password": "%s"
            }
        }
    }''' % (tenant_name, auth_name, password)
    print_verbose(args.verbose, url, headers, data, None, timeout)
    try:
        resp = requests.post(url, timeout=timeout, data=data, headers=headers)
        if resp.status_code != 200:
            raise ResponseError(
                'Failed in get_token: status code received {}'.format(
                    resp.status_code))
        return resp.json()['access']['token']['id']
    except Exception as e:
        message = 'Failed in get_token'
        # logger.log_exception(message, str(e))
        print(e)
        raise ConnectionError(message)


def populate_args_request_body(args):
    body_args_list = ['name', 'type', 'description', 'members']
    # assign values to dictionary (if val exist). members will be assign as a list
    body_dict = {}
    for body_arg in body_args_list:
        if hasattr(args, body_arg):
            body_dict[body_arg] = getattr(args, body_arg) if body_arg != 'members' else [getattr(args, body_arg)]
    # remove keys without values
    filtered_body_dict = dict((k, v) for k, v in body_dict.iteritems() if v is not None)
    # check if dictionary is not empty, convert body dictionary to json format
    return json.dumps(filtered_body_dict) if bool(filtered_body_dict) else None


def run(args):
    register_conf()
    set_domain(project='valet')
    args.host = args.host or CONF.server.host
    args.port = args.port or CONF.server.port
    args.timeout = args.timeout or 10
    rest_cmd, cmd_url = cmd_details(args)
    args.url = 'http://%s:%s/v1/groups' % (args.host, args.port) + cmd_url
    auth_token = get_token(args.timeout, args)
    args.headers = {
        'content-type': 'application/json',
        'X-Auth-Token': auth_token
    }
    args.body = populate_args_request_body(args)

    try:
        print_verbose(args.verbose, args.url, args.headers, args.body, rest_cmd, args.timeout)
        if args.body:
            resp = rest_cmd(args.url, timeout=args.timeout, data=args.body, headers=args.headers)
        else:
            resp = rest_cmd(args.url, timeout=args.timeout, headers=args.headers)
    except Exception as e:
        print(e)
        exit(1)

    if not 200 <= resp.status_code < 300:
        content = resp.json() if resp.status_code == 500 else ''
        print('API error: %s %s (Reason: %d)\n%s' % (rest_cmd.func_name.upper(), args.url, resp.status_code, content))
        exit(1)
    try:
        if resp.content:
            rj = resp.json()
            pretty_print_json(rj)
    except Exception as e:
        print (e)
        exit(1)
