# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----

@auth.requires_login()
def index():
    return locals()

can_view_user = auth.has_permission('view', 'user') or session.adminuser
can_add_user = auth.has_permission('add', 'user') or session.adminuser
can_edit_user = auth.has_permission('edit', 'user') or session.adminuser
can_delete_user = auth.has_permission('delete', 'user') or session.adminuser

@auth.requires(session.adminuser or can_view_user)
def user_manage():
    title = 'Users'
    if request.args(0) in ['view', 'edit', 'new']:
        title = f"{request.args(0).capitalize()} user"

    # u = db.auth_user(auth.user_id)
    u = auth.user
    if session.adminuser or auth.has_membership('co admin'):
        query = db['auth_user']
    elif auth.has_membership('ro admin'):
        query = db(db.auth_user.region==u.region)
    elif auth.has_membership('br admin'):
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
        create=can_add_user, 
        editable=can_edit_user,
        deletable=lambda r: ((r.email != 'admin@email.com') and (r.id != me)) and can_delete_user,
        csv=True, formname='user_grid')
    # grid, title = library(db['auth_user'], 'User', request.args(0))
    group_grid = None

    if grid.update_form:
        grid.update_form.element('#auth_user_email')['_readonly'] = 'readonly'
        if auth.has_membership('admin', int(request.args(2)) ):
            grid.update_form.element('#auth_user_region__row')['_hidden'] = 'hidden'
            grid.update_form.element('#auth_user_branch__row')['_hidden'] = 'hidden'
        session.selected_user = int(request.args(2))

    elif grid.view_form:
        groups = db(db.auth_membership.user_id == int(request.args(2))).select(
            join=db.auth_group.on(db.auth_membership.group_id==db.auth_group.id),
            orderby=db.auth_membership.id)
        d = DIV(LABEL('Groups', _class='readonly form-control-label col-sm-3'), 
                DIV([g.auth_group.role+'\n' for g in groups], _class='col-sm-9'),
                _class='form-group row',
                _style='white-space:pre; border-top: 1px solid #eaeaea')

        whses = db(db.user_warehouse.user_id == int(request.args(2))).select(
            join=db.warehouse.on(db.user_warehouse.warehouse_id==db.warehouse.id),
            orderby=db.user_warehouse.id)
        dw = DIV(LABEL('Warehouses', _class='readonly form-control-label col-sm-3'), 
                DIV([w.warehouse.warehouse_name+'\n' for w in whses], _class='col-sm-9'),
                _class='form-group row',
                _style='white-space:pre; border-top: 1px solid #eaeaea')

        grid.view_form[0].append(d)
        if whses:
            grid.view_form[0].append(dw)
        append_record_signature(grid, db.auth_user(request.args(2)))

    return dict(grid=grid, title=title)


@auth.requires(session.adminuser or can_view_user)
def user_group():
    if request.args(0)=='delete':
        db(db.auth_membership.id==request.args(2)).delete()
        redirect(URL('user_group', user_signature=True))
    
    user = db(db.auth_user.id==session.selected_user).select().first()
    curr_user_highest_rank = db(db.auth_membership.user_id==auth.user_id).select(
        join=db.auth_group.on(db.auth_membership.group_id==db.auth_group.id),
        orderby=db.auth_group.ranks
        ).first()['auth_group.ranks']

    def can_delete_group(row):
        admin_group_id = auth.id_group('admin')
        curr_group_rank = db(db.auth_group.id==row.group_id).select().first()['ranks']
        dont_delete = (curr_group_rank==curr_user_highest_rank and user.email==auth.user.email) or\
                      (row.group_id==admin_group_id and user.email=='admin@email.com')
        return not dont_delete

    _link = [ dict(header='', body=lambda r: A('Remove', _class1='button btn btn-default btn-secondary', 
            _href=URL('default','user_group', args=['delete', 'auth_membership', r.id], user_signature=True), cid=request.cid )
            if can_delete_group(r) else ''
            ) ]

    query = db.auth_membership.user_id == session.selected_user
    grid = SQLFORM.grid(query, fields=[db.auth_membership.group_id], 
        create=False, deletable=False , editable=False, details=False, searchable=False, csv=False,
        links=_link,
        )

    user_groups = db(db.auth_membership.user_id==session.selected_user).select()
    ug = [g.group_id for g in user_groups]
    group_options = db(~db.auth_group.id.belongs(ug) & (db.auth_group.ranks>=curr_user_highest_rank))

    db.auth_membership.user_id.default = session.selected_user
    db.auth_membership.group_id.requires = IS_IN_DB(group_options, 'auth_group.id', '%(role)s (%(id)s)', zero=None)
    form = SQLFORM(db.auth_membership, fields=['group_id'], submit_button='Assign group', formname='form_group_add', _id='form_group_add_id')

    return dict(grid=grid, form=form)

def user_group_new():
    group_id = request.vars['group_id']
    fv = {'group_id':group_id, 'user_id':session.selected_user}
    db.auth_membership.insert(**fv)
    force_read = db(db.auth_membership).select().first()
    redirect(URL('user_group', user_signature=True))

def user_warehouse():

    if request.args(0)=='delete':
        db(db.user_warehouse.id==request.args(2)).delete()
        redirect(URL('user_group', user_signature=True))

    _link = [ dict(header='', body=lambda r: A('Remove', 
            _href=URL('default','user_warehouse', args=['delete', 'user_warehouse', r.id], user_signature=True), cid=request.cid )
            ) ]

    query = db.user_warehouse.user_id == session.selected_user
    grid = SQLFORM.grid(query, fields=[db.user_warehouse.warehouse_id],
        create=False, deletable=False , editable=False, details=False, searchable=False, csv=False,
        links=_link,
        )

    user_warehouses = db(db.user_warehouse.user_id==session.selected_user).select()
    uw = [w.warehouse_id for w in user_warehouses]
    warehouse_options = db(~db.warehouse.id.belongs(uw))

    db.user_warehouse.user_id.default = session.selected_user
    db.user_warehouse.warehouse_id.requires =  IS_IN_DB(warehouse_options, 'warehouse.id', '%(warehouse_name)s (%(id)s)', zero=None)
    form = SQLFORM(db.user_warehouse, fields=['warehouse_id'], submit_button='Assign warehouse', formname='form_wh_add', _id='form_wh_add_id')

    return dict(grid=grid, form=form)

def user_warehouse_new():
    warehouse_id = request.vars['warehouse_id']
    fv = {'warehouse_id':warehouse_id, 'user_id':session.selected_user}
    db.user_warehouse.insert(**fv)
    force_read = db(db.user_warehouse).select().first()
    redirect(URL('user_warehouse', user_signature=True))


@auth.requires(session.adminuser or can_view_user)
def group_manage():
    btn_class = 'button btn btn-secondary'
    title = 'Groups'
    query = db['auth_group']
    links = [ dict(header='', body=lambda r: A('Permissions', _class='button btn btn-secondary', 
            _href=URL('default','group_permission', args=[r.id], user_signature=True), cid=request.cid )
            if session.adminuser else '' )
            ]
    grid = SQLFORM.grid(query, orderby=[db.auth_group.ranks],
        create=can_add_user, 
        editable=lambda r: can_edit_user and r.created_by==me,
        deletable=lambda r: (r.role != 'admin') and (session.adminuser or (can_delete_user and r.created_by==me)),
        searchable=False, csv=False,
        formname='group_grid', links=links)
    append_record_signature(grid, db.auth_group(request.args(2)))
    arrange_links = DIV(SPAN('Move item: '), 
        BUTTON('Up', _id='up'), SPAN(' '),
        BUTTON('Down', _id='down'), SPAN(' '),
        BUTTON('Top', _id='top'), SPAN(' '),
        BUTTON('Bottom', _id='bottom'),
        ) if session.adminuser else None
    return dict(title=title, grid=grid, links=arrange_links )


def group_permission():

    # wh docs: wsi wsr wts
    # bsm: ai aap
    # sales: or pr

    group = db.auth_group(request.args(0))
    permissions = db(db.auth_permission.group_id==group.id).select()
    current_permission = [i.name+'|'+i.table_name for i in permissions]
    session.current_permission = current_permission  # <===
    
    actions = ['view','add','edit','delete']
    objects = ['user','library','wh docs','bsm docs','sales docs']

    checked = [
        ['checked' if actions[0]+'|'+objects[i] in current_permission else None for i, v in enumerate(objects)],
        ['checked' if actions[1]+'|'+objects[i] in current_permission else None for i, v in enumerate(objects)],
        ['checked' if actions[2]+'|'+objects[i] in current_permission else None for i, v in enumerate(objects)],
        ['checked' if actions[3]+'|'+objects[i] in current_permission else None for i, v in enumerate(objects)],
        ]

    t = TABLE(
            TR([TH(INPUT(_type='checkbox', _id='object_'+i.replace(' ', ' ')),' '+i) for i in objects]),
            TR([TD((INPUT(_type='checkbox', _name=actions[0]+'|'+objects[i], _checked=checked[0][i])), ' '+actions[0]) for i, v in enumerate(objects)]),
            TR([TD((INPUT(_type='checkbox', _name=actions[1]+'|'+objects[i], _checked=checked[1][i])), ' '+actions[1]) for i, v in enumerate(objects)]),
            TR([TD((INPUT(_type='checkbox', _name=actions[2]+'|'+objects[i], _checked=checked[2][i])), ' '+actions[2]) for i, v in enumerate(objects)]),
            TR([TD((INPUT(_type='checkbox', _name=actions[3]+'|'+objects[i], _checked=checked[3][i])), ' '+actions[3]) for i, v in enumerate(objects)]),
            _class='table table-striped'
            )

    _btn_back = A(SPAN(_class="icon arrowleft icon-arrow-left glyphicon glyphicon-arrow-left"),
        ' Back', _href=URL('group_manage'), 
        cid=request.cid, _class='btn btn-secondary')

    d = DIV(
            _btn_back,
            H5("Group '", STRONG(group.role), "' permission"),
            FORM(
                t,
                DIV(INPUT(_type='submit', _value='Save changes', _class='btn btn-primary'),
                    _class='float-right'),
                _action='group_permission_change.load/'+request.args(0),
                _id='form1',
                # _method='POST',
                ),
            _class='col-md-6'
            )

    return dict(disp=d)


def group_permission_change():
    group_id = request.args(0)
    # session.flash = 'Permission changes saved.'
    if 'current_permission' not in session:
        session.flash = 'Page expired. No changes saved.'
    else:
        selected = list(request.post_vars.keys())
        for v in selected:
            if not v in session.current_permission:
                name_object = list(v.split('|'))
                auth.add_permission(group_id, name_object[0], name_object[1], 0)
        for v in session.current_permission:
            if not v in selected: 
                name_object = list(v.split('|'))
                auth.del_permission(group_id, name_object[0], name_object[1], 0)
    redirect(URL('group_manage', user_signature=True))


def group_rank_change():
    id = request.vars['id']
    next_id = request.vars['next_id']
    direction = request.vars['direction']
    if is_float(next_id):
        this_row = db(db.auth_group.id==id).select().first()
        next_row = db(db.auth_group.id==next_id).select().first()
        if direction in ['up','down']:
            temp = this_row.ranks
            this_row.ranks = next_row.ranks
            next_row.ranks = temp
        elif direction == 'top':
            this_row.ranks = next_row.ranks -1
        else: # 'bottom'
            this_row.ranks = next_row.ranks +1
        this_row.update_record()
        next_row.update_record()
    return


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

