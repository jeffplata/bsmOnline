# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# ----------------------------------------------------------------------------------------------------------------------
# this is the main application menu add/remove items as required
# ----------------------------------------------------------------------------------------------------------------------
response.menu = [
    (T('Home'), False, URL('default', 'index'), [])
]

m = ('Users', False, None, [])

if session.adminuser or auth.has_permission('view', 'user'):
    m[3].append(('Users', False, URL('default', 'user_manage.load', vars={'table':'auth_user'}, user_signature=True)))
    m[3].append(('Groups and Permissions', False, URL('default', 'group_manage.load', user_signature=True)))
    m[3].append(('Accountabilities', False, URL('default', 'ws_accountability.load', user_signature=True)))

l = ('Library', False, None, [])

if session.adminuser or auth.has_permission('view', 'library'):
    l[3].append(('Regions', False, URL('library', 'region', user_signature=True)))
    l[3].append(('Branches', False, URL('library', 'branch', user_signature=True)))
    l[3].append(('Warehouses', False, URL('library', 'warehouse', user_signature=True)))
    l[3].append(('Activities', False, URL('library', 'activity', user_signature=True)))
    l[3].append(('Containers', False, URL('library', 'container', user_signature=True)))
    l[3].append(('Commodities', False, URL('library', 'commodity', user_signature=True)))
    l[3].append(('Varieties', False, URL('library', 'variety', user_signature=True)))

d = ('Documents', False, None, [])

if auth.has_permission('view', 'wh docs'):
    d[3].append(('WSR', False, URL('document', 'wsr', user_signature=True)))
    d[3].append(('WSI', False, URL('document', 'wsi', user_signature=True)))

if m[3]:
    response.menu += [m]

if l[3]:
    response.menu += [l]

if d[3]:
    response.menu += [d]
