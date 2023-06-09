# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------
can_view_wh_docs = auth.has_permission('view', 'wh docs') or session.adminuser
can_add_wh_docs = auth.has_permission('add', 'wh docs') or session.adminuser

def can_modify(r):
    return (r.created_by==me) or\
        (auth.user.branch and (db.auth_user(r.created_by).branch==auth.user.branch)) or\
        ((not auth.user.branch) and auth.user.region and (db.auth_user(r.created_by).region==auth.user.region))

def can_edit_wh_docs(r):
    return session.adminuser or (auth.has_permission('edit', 'wh docs') and can_modify(r))

def can_delete_wh_docs(r):
    return session.adminuser or (auth.has_permission('delete', 'wh docs') and can_modify(r))

@auth.requires(can_view_wh_docs)    
def wsr():
    response.view = 'document/wsr.load'
    title = 'Warehouse Stock Receipt'

    var_container = dict((r.id, r.default_container) for r in db().select(db.variety.ALL))
    cont_capacity = dict((r.id, [r.wt_capacity, r.weight]) for r in db().select(db.container.ALL))

    if request.args(0) == 'new':
        user_whses = db(db.user_warehouse.user_id==auth.user_id).select()
        wh_ids = [i.warehouse_id for i in user_whses]
        if not user_whses:
            if auth.user.branch:
                user_whses = db(db.warehouse.branch_id==auth.user.branch).select()
            elif auth.user.region:
                user_whses = db(db.warehouse.region_id==auth.user.region).select()
            else:
                user_whses = db(db.warehouse).select()
            wh_ids = [i.id for i in user_whses]
        wh_options = db(db.warehouse.id.belongs( wh_ids ))
        db.WSR.warehouse.requires = IS_IN_DB(wh_options, 'warehouse.id', '%(warehouse_name)s', zero=None)

        user_sups = db(db.user_wh_supervisor.user_id == auth.user_id).select()
        ws_ids = [i.wh_supervisor_id for i in user_sups]
        if not user_sups:
            ws_group_id = auth.id_group('wh supervisor')
            user_highest_group = db(db.auth_membership.user_id==auth.user_id).select(db.auth_group.ranks.min().with_alias('highest_group'),
                join=db.auth_group.on(db.auth_membership.group_id==db.auth_group.id))[0].highest_group
            print('highest', user_highest_group)
            # if auth.has_membership('wh supervisor') and (user_highest_group):
            if user_highest_group == ws_group_id:   # rank is wh supervisor
                ws_ids = [auth.user_id]
            elif user_highest_group < ws_group_id:  # rank is higher than a wh supervisor 
                # ws_group_id = auth.id_group('wh supervisor')
                if auth.user.branch:
                    user_sups = db(db.auth_membership.group_id==ws_group_id).select(db.auth_membership.user_id,
                        join=[db.auth_user.on(db.auth_membership.user_id==db.auth_user.id),
                              db.branch.on(db.auth_user.branch==auth.user.branch)
                             ] )
                    ws_ids = [i.user_id for i in user_sups]
                elif auth.user.region:
                    user_sups = db(db.auth_membership.group_id==ws_group_id).select(db.auth_membership.user_id,
                        join=[db.auth_user.on(db.auth_membership.user_id==db.auth_user.id),
                              db.region.on(db.auth_user.region==auth.user.region)
                             ] )
                    ws_ids = [i.user_id for i in user_sups]
                else:
                    ws_ids = [i.id for i in db().select(db.auth_user.id)]
        sups_options = db(db.auth_user.id.belongs( ws_ids ))
        db.WSR.wh_supervisor.requires = IS_IN_DB(sups_options, 'auth_user.id', '%(first_name)s %(last_name)s', zero=None)

        db.WSR.variety.default = list(var_container.keys())[0]
        db.WSR.container.default = list(var_container.values())[0]

    grid = SQLFORM.grid(db.WSR, represent_none='',
        create=can_add_wh_docs, editable=can_edit_wh_docs, deletable=can_delete_wh_docs)
    append_record_signature(grid, db.WSR(request.args(2)))

    return locals()


def wsi():
    response.view = 'default/wh_docs.load'
    title = 'Warehouse Stock Issue'
    grid = SQLFORM.grid(db.WSI)

    return locals()
