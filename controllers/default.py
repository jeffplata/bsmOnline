# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
def index():
    return locals()

# # ---- Smart Grid (example) -----
# @auth.requires_membership('admin') # can only be accessed by members of admin groupd
# def grid():
#     # response.view = 'generic.html' # use a generic view
#     tablename = request.args(0)
#     if not tablename in db.tables: raise HTTP(403)
#     grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
#     return dict(grid=grid)

# @auth.requires_membership('admin') 
# def library():
#     query = db[request.vars['table']]
#     title = ''
#     if request.vars['table'] == 'auth_user':
#         title = 'User'
#     if request.args(0) in ['view', 'update', 'add']:
#         title = f"{request.args(0).capitalize()} {title}"
#     grid = SQLFORM.grid(query, deletable=False, editable=True, csv=False)
#     return dict(grid=grid, title=title)

@auth.requires_membership('admin') 
def library(table, title=None, action=None):
    query = db[table]
    if not title:
        title = table.capitalize()
    if action in ['view', 'edit', 'add']:
        title = f"{action.capitalize()} {title.lower()}"
    grid = SQLFORM.grid(query, deletable=False, editable=True, csv=False)
    # return dict(grid=grid, title=title)
    return (grid, title)


@auth.requires_membership('admin') 
def user_manage():
    if request.args(0) == 'new':
        db.auth_user.password.readable = False
        db.auth_user.password.writable = False
        db.auth_user.password.default = db.auth_user.password.requires[0]('Password1')[0]

    grid, title = library(db['auth_user'], 'User', request.args(0))
    if grid.update_form:
        grid.update_form.element('#auth_user_email')['_readonly'] = 'readonly'
        grid.update_form.element('#auth_user_password__row')['_hidden'] = 'hidden'
    return dict(grid=grid, title=title)


# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())

