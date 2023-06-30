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
can_edit_user = session.adminuser or auth.has_permission('edit', 'user')
can_delete_user = session.adminuser or (auth.has_permission('delete', 'user') and session.adminusers)

def branch_options():
    options = ''
    if request.vars.region_id:
        branches = db(db.branch.region_id==request.vars.region_id).select(db.branch.ALL)
        ops1 = [f"<option value={i['id']}>{i.branch_name}</option>" for i in branches]
        options = ["<option value=></option>"] + ops1
    return options

@auth.requires(session.adminuser or can_view_user)
def user_manage():
    title = 'Users'
    if request.args(0) in ['view', 'edit', 'new']:
        title = f"{request.args(0).capitalize()} user"

    if request.args(0) == 'me':
        # query = db(db.auth_user.id == me)
        query = (db.auth_user.id == me)
    elif request.args(0) == 'my_branch':
        # query = db(db.auth_user.branch == auth.user.branch)
        query = (db.auth_user.branch == auth.user.branch)
    elif request.args(0) == 'my_region':
        # query = db(db.auth_user.region == auth.user.region)
        query = (db.auth_user.region == auth.user.region)
    else:
        # query = db(db.auth_user)
        query = (db.auth_user.id > 0)

    # m_g_id = auth.id_group('member')
    # qm = db(db.auth_membership.group_id==m_g_id)._select(db.auth_membership.user_id)
    # query = ~db.auth_user.id.belongs(qm)

    # qm = db(db.auth_user)._select(left=db.region.on(db.region.id==db.auth_user.region))

    
    if request.args(0) == 'new':
        db.auth_user.password.readable = False
        db.auth_user.password.writable = False
        db.auth_user.password.default = db.auth_user.password.requires[0]('Password1')[0]
        if auth.user.branch:
            branch_ops =  db(db.branch.id==auth.user.branch)
            db.auth_user.branch.requires = IS_IN_DB(branch_ops, 'branch.id', '%(branch_name)s', zero=None)
        if auth.user.region:
            region_ops = db(db.region.id==auth.user.region)
            db.auth_user.region.requires = IS_IN_DB(region_ops, 'region.id', '%(region_name)s', zero=None )
            if not auth.user.branch:
                branch_ops = db(db.branch.region_id==auth.user.region)
                db.auth_user.branch.requires = IS_IN_DB(branch_ops, 'branch.id', '%(branch_name)s')

    if request.args(0) == 'edit':
        if auth.user.branch:
            b_ops = db(db.branch.id == auth.user.branch)
            db.auth_user.branch.requires = IS_IN_DB(b_ops, db.branch.id, '%(branch_name)s', zero=None )
        if auth.user.region:
            r_ops = db(db.region.id == auth.user.region)
            db.auth_user.region.requires = IS_IN_DB(r_ops, db.region.id, '%(region_name)s', zero=None )
            if not auth.user.branch:
                b_ops = db(db.branch.region_id == auth.user.region)
                db.auth_user.branch.requires = IS_IN_DB(b_ops, db.branch.id, '%(branch_name)s' )

    fields = [db.auth_user.first_name,db.auth_user.last_name,db.auth_user.middle_name,db.auth_user.email,\
             db.region.region_name,db.branch.branch_name, db.region.id, db.branch.id, db.auth_user.created_by,
             ]

    min_val = db.auth_group.ranks.min()
    user_highest_ranks = dict((i.auth_user.id, i._extra[min_val]) \
        for i in db( (query) &
                     (db.auth_membership.user_id==db.auth_user.id) &
                     (db.auth_group.id==db.auth_membership.group_id) ).select(
                        db.auth_user.id, min_val, groupby=db.auth_user.id
            )
        )

    curr_user_highest_rank = db(db.auth_membership.user_id==auth.user_id).select(
        join=db.auth_group.on(db.auth_membership.group_id==db.auth_group.id),
        orderby=db.auth_group.ranks
        ).first()['auth_group.ranks']

    wh_group_id = auth.id_group('wh supervisor')
    wh_ast_group_id = auth.id_group('wh assistant')

    def same_branch_or_region(r):
        return ((auth.user.branch and (auth.user.branch==r.branch.id)) or
                (auth.user.region and not auth.user.branch and (auth.user.region==r.region.id)))

    def can_delete(r):
        if hasattr(r, 'auth_user'):
            if r.auth_user.email=='admin@email.com':
                return False
            elif session.adminuser:
                return True
            else:
                return can_delete_user and\
                    (
                        ((r.auth_user.id != me) or (r.auth_user.created_by==me)) and
                        (same_branch_or_region(r) and
                          ((r.auth_user.id not in user_highest_ranks.keys()) or (user_highest_ranks[r.auth_user.id] >= curr_user_highest_rank))
                        )
                    )
        # todo: can delete if:
        #   same branch or same region
        #   lower in rank
        # current can delete test is wrong

    def can_edit(r):
        if hasattr(r, 'auth_user'):
            if session.adminuser:
                return True
            elif (r.auth_user.id == me) and can_edit_user:
                return True
            elif curr_user_highest_rank == wh_group_id: # warehouse supervisor
                return can_edit_user and ((r.auth_user.id in user_highest_ranks.keys()) and \
                    (user_highest_ranks[r.auth_user.id] == wh_ast_group_id) and same_branch_or_region(r))
            elif curr_user_highest_rank >= wh_ast_group_id: # wh assistant, sco, sdo
                return can_edit_user and (r.auth_user.id == me)
            else:
                return can_edit_user and\
                    (
                        (r.auth_user.created_by==me) or
                        (same_branch_or_region(r) and
                          ((r.auth_user.id not in user_highest_ranks.keys()) or (user_highest_ranks[r.auth_user.id] >= curr_user_highest_rank))
                        ) #or (r.auth_user.id == me)
                    ) 
    db.region.id.listable = False
    db.branch.id.listable = False
    grid = SQLFORM.grid(query, 
        fields=fields,
        create=can_add_user, 
        editable=lambda r: can_edit(r),
        deletable=lambda r: can_delete(r),
        left=[db.region.on(db.auth_user.region==db.region.id), 
              db.branch.on(db.auth_user.branch==db.branch.id)],
        represent_none='',
        csv=True, formname='user_grid', maxtextlength=60)

    if grid.update_form:
        _links = CAT(A('groups', _href='#user_group_div'),
                  A('warehouses', _href='#user_warehouse_div'),
                  A('supervisors', _href='#user_wh_supervisor_div') )
        grid.element('.form_header').append(_links)
        grid.update_form.element('#auth_user_email')['_readonly'] = 'readonly'
        if auth.has_membership('admin', int(request.args(2)) ):
            grid.update_form.element('#auth_user_region__row')['_hidden'] = 'hidden'
            grid.update_form.element('#auth_user_branch__row')['_hidden'] = 'hidden'
        session.selected_user = int(request.args(2))

    # todo: be descriptive on view form with brancha and region
    elif grid.view_form:
        # e = grid.view_form.element('#auth_user_region__row .col-sm-9')['textContent'] = 'xxx'
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

        sups = db(db.user_wh_supervisor.user_id == int(request.args(2))).select(
            join=db.auth_user.on(db.user_wh_supervisor.wh_supervisor_id==db.auth_user.id),
            orderby=db.user_wh_supervisor.id)
        ds = DIV(LABEL('Supervisors', _class='readonly form-control-label col-sm-3'), 
                DIV([s.auth_user.first_name+' '+s.auth_user.last_name+'\n' for s in sups], _class='col-sm-9'),
                _class='form-group row',
                _style='white-space:pre; border-top: 1px solid #eaeaea')

        grid.view_form[0].append(d)
        if whses:  grid.view_form[0].append(dw)
        if sups: grid.view_form[0].append(ds)
        append_record_signature(grid, db.auth_user(request.args(2)))

    elif grid.create_form:
        pass
    else:
        # todo: prevent break of link text on smaller screen
        _filter_links = CAT(
            A('me', _href=URL('default', 'user_manage', args=['me'], user_signature=True), cid=request.cid),
            A('my branch', _href=URL('default', 'user_manage', args=['my_branch'], user_signature=True), cid=request.cid)
                if auth.user.branch else SPAN('my branch', _style='padding: 6px 12px;'),
            A('my region', _href=URL('default', 'user_manage', args=['my_region'], user_signature=True), cid=request.cid)
                if auth.user.region else SPAN('my region', _style='padding: 6px 12px;'),
            )
        grid.element('.web2py_console').append(_filter_links)

    return dict(grid=grid, title=title)


@auth.requires(session.adminuser or can_view_user)
def user_group():
    if request.args(0)=='delete':
        db(db.auth_membership.id==request.args(2)).delete()
        db(db.auth_user.id==session.selected_user).update(last_change=f'removed from group')
        response.js = "jQuery('#user_wh_supervisor_div').get(0).reload()"   # reload the wh_supervisor component
    
    if request.args(0)=='new':
        group_id = request.vars['group_id']
        fv = {'group_id':group_id, 'user_id':session.selected_user}
        db.auth_membership.insert(**fv)
        force_read = db(db.auth_membership).select().first()
        db(db.auth_user.id==session.selected_user).update(last_change=f"assigned to group {group_id}")
        response.js = "jQuery('#user_wh_supervisor_div').get(0).reload()"   # reload the wh_supervisor component

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
        create=False, deletable=False , editable=False, details=False, searchable=False, csv=False, sortable=False,
        links=_link if session.adminusers else None, headers={'auth_membership.group_id':'Assigned groups'},  maxtextlength=40,
        )
    grid.element('thead', replace=None)

    if session.adminusers:
        user_groups = db(db.auth_membership.user_id==session.selected_user).select()
        ug = [g.group_id for g in user_groups]
        group_options = db(~db.auth_group.id.belongs(ug) & (db.auth_group.ranks>=curr_user_highest_rank))

        db.auth_membership.user_id.default = session.selected_user
        db.auth_membership.group_id.requires = IS_IN_DB(group_options, 'auth_group.id', '%(role)s (%(id)s)')
        form = SQLFORM(db.auth_membership, fields=['group_id'], submit_button='Assign group', formname='form_group_add', _id='form_group_add_id')
    else:
        form = None
        grid.append(DIV(STRONG('* You are not authorized to change assigned groups.')))

    return dict(grid=grid, form=form)


@auth.requires(session.adminuser or can_view_user)
def user_warehouse():
    if request.args(0)=='delete':
        db(db.user_warehouse.id==request.args(2)).delete()
        db(db.auth_user.id==session.selected_user).update(last_change=f"removed warehouse")

    if request.args(0)=='new':
        warehouse_id = request.vars['warehouse_id']
        fv = {'warehouse_id':warehouse_id, 'user_id':session.selected_user}
        db.user_warehouse.insert(**fv)
        force_read = db(db.user_warehouse).select().first()
        db(db.auth_user.id==session.selected_user).update(last_change=f"assigned warehouse {warehouse_id}")

    _link = [ dict(header='', body=lambda r: A('Remove', 
            _href=URL('default','user_warehouse', args=['delete', 'user_warehouse', r.id], user_signature=True), cid=request.cid )
            ) ]

    query = db.user_warehouse.user_id == session.selected_user
    grid = SQLFORM.grid(query, fields=[db.user_warehouse.warehouse_id],
        create=False, deletable=False , editable=False, details=False, searchable=False, csv=False, sortable=False,
        links=_link, maxtextlength=40,
        )
    grid.element('thead', replace=None)

    u = auth.user
    if u.branch:
        warehouses = db(db.warehouse.branch_id==u.branch).select()
    elif u.region:
        warehouses = db(db.warehouse.region_id==u.region).select()
    else:
        warehouses = db().select(db.warehouse.id)
    warehouse_ids = [w.id for w in warehouses]

    user_warehouses = db(db.user_warehouse.user_id==session.selected_user).select()
    uw = [w.warehouse_id for w in user_warehouses]
    if warehouse_ids: 
        [(warehouse_ids.remove(x) if x in warehouse_ids else None) for x in uw]
        warehouse_options = db(db.warehouse.id.belongs(warehouse_ids))
    else:
        warehouse_options = db(~db.warehouse.id.belongs(uw))

    db.user_warehouse.user_id.default = session.selected_user
    db.user_warehouse.warehouse_id.requires =  IS_IN_DB(warehouse_options, 'warehouse.id', '%(warehouse_name)s (%(id)s)')
    form = SQLFORM(db.user_warehouse, fields=['warehouse_id'], submit_button='Assign warehouse', formname='form_wh_add', _id='form_wh_add_id')

    return dict(grid=grid, form=form)


@auth.requires(session.adminuser or can_view_user)
def user_wh_supervisor():
    if request.args(0)=='delete':
        db(db.user_wh_supervisor.id==request.args(2)).delete()
        db(db.auth_user.id==session.selected_user).update(last_change=f"removed supervisor")

    if request.args(0)=='new':
        wh_supervisor_id = request.vars['wh_supervisor_id']
        fv = {'wh_supervisor_id':wh_supervisor_id, 'user_id':session.selected_user}
        db.user_wh_supervisor.insert(**fv)
        force_read = db(db.user_wh_supervisor).select().first()
        db(db.auth_user.id==session.selected_user).update(last_change=f"assigned supervisor {wh_supervisor_id}")

    _link = [ dict(header='', body=lambda r: A('Remove', 
            _href=URL('default','user_wh_supervisor', args=['delete', 'user_wh_supervisor', r.id], user_signature=True), cid=request.cid )
            ) ]

    query = db.user_wh_supervisor.user_id == session.selected_user
    grid = SQLFORM.grid(query, fields=[db.user_wh_supervisor.wh_supervisor_id],
        create=False, deletable=False , editable=False, details=False, searchable=False, csv=False, sortable=False,
        links=_link, maxtextlength=40,
        )
    grid.element('thead', replace=None)

    join_query = [db.auth_membership.on(db.auth_user.id==db.auth_membership.user_id),
                  db.auth_group.on((db.auth_membership.group_id==db.auth_group.id) & (db.auth_group.role=='wh supervisor')) ]
    
    if auth.user.branch:
        sups = db(db.auth_user.branch==auth.user.branch).select(join=join_query)
    elif auth.user.region:
        sups = db(db.auth_user.region==auth.user.region).select(join=join_query)
    else:
        sups = db().select(db.auth_user.id,join=join_query)
    sup_ids = [s.id for s in sups]

    user_wh_supervisors = db(db.user_wh_supervisor.user_id==session.selected_user).select()
    uws = [ws.wh_supervisor_id for ws in user_wh_supervisors]

    [(sup_ids.remove(x) if x in sup_ids else None) for x in uws]
    wh_supervisor_options = db(db.auth_user.id.belongs(sup_ids))
    # else:
    #     wh_supervisor_options = db(~db.auth_user.id.belongs(uws))

    db.user_wh_supervisor.user_id.default = session.selected_user
    # db.user_wh_supervisor.wh_supervisor_id.requires = IS_IN_DB(wh_supervisor_options, 'auth_user.id', '%(first_name)s (%(last_name)s)', zero=None)
    db.user_wh_supervisor.wh_supervisor_id.requires = IS_IN_DB(wh_supervisor_options, 'auth_user.id', '%(first_name)s (%(last_name)s)')
    form = SQLFORM(db.user_wh_supervisor, fields=['wh_supervisor_id'], submit_button='Assign supervisor', formname='form_wh_sup_add', _id='form_wh_sup_add_id')

    return dict(grid=grid, form=form)


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


def ws_accountability():
    title = 'Accountabilities'
    query = db.accountability
    grid = SQLFORM.grid(query, represent_none = '')

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

    if request.args(0) == 'profile':
        if auth.user.region:
            r_ops = db(db.region.id == auth.user.region)
            db.auth_user.region.requires = IS_IN_DB(r_ops, db.region.id, '%(region_name)s', zero=None )
        if auth.user.branch:
            b_ops = db(db.branch.id == auth.user.branch)
            db.auth_user.branch.requires = IS_IN_DB(b_ops, db.branch.id, '%(branch_name)s', zero=None )

    return dict(form=auth())
