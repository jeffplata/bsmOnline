# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
@auth.requires_login()
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
    title = 'User'
    if request.args(0) in ['view', 'edit', 'new']:
        title = f"{request.args(0).capitalize()} user"

    query = db['auth_user']
    u = db.auth_user(auth.user_id)
    if auth.has_membership('br admin'):
        query = db(db.auth_user.branch==u.branch)
    if request.args(0) == 'new':
        db.auth_user.password.readable = False
        db.auth_user.password.writable = False
        db.auth_user.password.default = db.auth_user.password.requires[0]('Password1')[0]
        if u.region:
            db.auth_user.region.default = u.region
            region_ops = db(db.region.id==u.region)
            db.auth_user.region.requires = IS_IN_DB(region_ops, 'region.id', '%(region_name)s', zero=None )
        if u.branch:
            db.auth_user.branch.default = u.branch
            branch_ops =  db(db.branch.id==u.branch)
            db.auth_user.branch.requires = IS_IN_DB(branch_ops, 'branch.id', '%(branch_name)s', zero=None)
    fields = 'first_name,last_name,middle_name,email,region,branch'

    grid = SQLFORM.grid(query, 
        fields=[db.auth_user[f] for f in fields.split(',')],
        deletable=False, csv=False, formname='user_grid')
    # grid, title = library(db['auth_user'], 'User', request.args(0))
    group_grid = None
    if grid.update_form:
        grid.update_form.element('#auth_user_email')['_readonly'] = 'readonly'
        if auth.has_membership('admin', int(request.args(2)) ):
            grid.update_form.element('#auth_user_region__row')['_hidden'] = 'hidden'
            grid.update_form.element('#auth_user_branch__row')['_hidden'] = 'hidden'
        session.selected_user = int(request.args(2))
    return dict(grid=grid, title=title)


def user_group():

    user = db(db.auth_user.id==session.selected_user).select().first()
    def can_delete_group(row):
        admin_group_id = auth.id_group('admin')
        return not (row.group_id==admin_group_id and user.email=='admin@email.com')

    user_groups = db(db.auth_membership.user_id==session.selected_user).select()
    ug = [g.group_id for g in user_groups]
    group_options = db(~db.auth_group.id.belongs(ug))
    db.auth_membership.group_id.requires = IS_IN_DB(group_options, 'auth_group.id', '%(role)s (%(id)s)', zero=None)

    query = db.auth_membership.user_id == session.selected_user
    grid = SQLFORM.grid(query, fields=[db.auth_membership.group_id], 
        create=False, deletable=can_delete_group , editable=False, details=False, searchable=False, csv=False,
        )
    form = SQLFORM(db.auth_membership, fields=['group_id'], submit_button='Assign group', formname='form_group_add')

    if form.process(dbio=False).accepted:
        gid = form.vars['group_id']
        fv = {'group_id':gid, 'user_id':session.selected_user}
        db.auth_membership.insert(**fv)
        redirect(URL('user_group', user_signature=True))

    return dict(grid=grid, form=form)

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

