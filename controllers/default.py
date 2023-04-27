# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
def index():
    return locals()


@auth.requires_membership('admin') 
def library(table, title=None, action=None):
    query = db[table]
    if not title:
        title = table.capitalize()
    if action in ['view', 'edit', 'new']:
        title = f"{action.capitalize()} {title.lower()}"
    grid = SQLFORM.grid(query, deletable=False, editable=True, csv=False)
    # return dict(grid=grid, title=title)
    return (grid, title)


@auth.requires(auth.has_permission('manage', 'auth_user'))
def user_manage():
    response.view = 'default/library.load'
    title = 'User'
    if request.args(0) in ['view', 'edit', 'new']:
        title = f"{request.args(0).capitalize()} user"
    query = db['auth_user']
    if request.args(0) == 'new':
        db.auth_user.password.readable = False
        db.auth_user.password.writable = False
        db.auth_user.password.default = db.auth_user.password.requires[0]('Password1')[0]
        if db.auth_user.region:
            db.auth_user.region = db.auth_user.region.default = db.auth_user.region
    fields = 'first_name,last_name,middle_name,email,region,branch'

    grid = SQLFORM.grid(query, 
        fields=[db.auth_user[f] for f in fields.split(',')],
        deletable=False, csv=False)
    # grid, title = library(db['auth_user'], 'User', request.args(0))
    if grid.update_form:
        grid.update_form.element('#auth_user_email')['_readonly'] = 'readonly'
        if auth.has_membership('admin', int(request.args(2)) ):
            grid.update_form.element('#auth_user_region')['_disabled'] = 'disabled'
            grid.update_form.element('#auth_user_branch')['_disabled'] = 'disabled'
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

