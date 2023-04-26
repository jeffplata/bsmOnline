# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# ----------------------------------------------------------------------------------------------------------------------
# this is the main application menu add/remove items as required
# ----------------------------------------------------------------------------------------------------------------------

response.menu = [
    (T('Home'), False, URL('default', 'index'), [])
]

m = ('Library', False, None, [])

if auth.has_permission('manage', 'user', 0):
    m[3].append(('Users', False, URL('default', 'user_manage.load', vars={'table':'auth_user'}, user_signature=True)))

if m[3]:
    response.menu += [m]
