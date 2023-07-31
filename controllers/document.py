# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------
can_view_wh_docs = auth.has_permission('view', 'wh docs') or session.adminuser
can_add_wh_docs = auth.has_permission('add', 'wh docs') or session.adminuser

def select_accountability():
    response.view = 'document/select_accountability.load'
    title = 'Select accountability:'
    s = "margin: 0px 5px 3px 0px;"
    lc = 'form-check-label'
    cc = 'form-check-input'
    dc = 'form-check'
    form = FORM(
        DIV(
            INPUT(_type='radio', _class=cc, _name='acc', _id='acc0', _checked='checked'),
            LABEL('Jobet Atienza, Tacloban Port Area, 1/1/2021', _class=lc),
            _class=dc),
        DIV(
            INPUT(_type='radio', _class=cc, _name='acc', _id='acc1'),
            LABEL('Jobet Atienza, Baybay, 8/1/2023', _class=lc),
            _class=dc),
        INPUT(_type='submit', _value='Continue', _class='btn button btn-primary'),
        _name="select_accountability_form", method='GET', _class="xxxform-inline", _style="margin: 5px 0px")
    if form.process().accepted:
        print('accepted')
        session.accountability = 0
        redirect(URL('wsr', args=['new','WSR'], user_signature=True))

    return dict(title=title, form=form)


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

    s = "margin: 0px 5px 3px 0px;"
    account_filter = FORM(
        LABEL('Accountability:', _style=s),
        SELECT('','Jobet Atienza, Tacloban Port Area, 1/1/2021', 'Jobet Atienza, Baybay, 8/1/2023'),
        _name="account_filter_form", method='GET', _class="form-inline", _style="margin: 5px 0px")

    if request.vars:
        # print(request.vars)
        if 'keywords' in request.vars:
            print('keyword in request.vars')
            request.vars.acc_id = request.vars.acc_id[0]
            request.vars.ws_id = request.vars.ws_id[0]
            request.vars.wh_id = request.vars.wh_id[0]
            print(request.vars)
    else:
        print('no request.vars')

    if request.args(0) == 'new':

        # user_accountabilities = db(db.ws_accountability.ws_id == auth.user_id).select()
        # if len(user_accountabilities) > 1:
        #     redirect()
        # if session.accountability == None:
        #     redirect(URL('select_accountability', user_signature=True))

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
    else:
        if session.accountability:
            del session.accountability

    # from pydal.helpers.methods import smart_query
    # def search_with_this(fields, keywords):
    #     key = keywords.strip()
    #     if key and not '"' in key:
    #         SEARCHABLE_TYPES = ('string', 'text', 'list:string')
    #         sfields = [field for field in fields if field.type in SEARCHABLE_TYPES]
    #         if False: # settings.global_settings.web2py_runtime_gae:
    #             return reduce(lambda a,b: a|b, [field.contains(key) for field in sfields])
    #         else:
    #             queries = [db.WSR.id>0]
    #             queries.append((db.WSR.doc_number.contains(key))
    #                 )
    #             return reduce(lambda a,b:a&b,[
    #                     reduce(lambda a,b: a|b, [
    #                             field.contains(k) for field in sfields]
    #                            ) for k in key.split()])

    #     else:
    #         return smart_query(fields, key)

    db.WSR.age.listable = False
    db.WSR.stock_condition.listable = False
    db.WSR.MC.listable = False
    db.WSR.purity.listable = False
    # grid = SQLFORM.grid(db.WSR, represent_none='', searchable=search_with_this,
    grid = SQLFORM.grid(db.WSR, represent_none='', 
        create=can_add_wh_docs, editable=can_edit_wh_docs, deletable=can_delete_wh_docs)
    append_record_signature(grid, db.WSR(request.args(2)))

    return locals()


def wsi():
    response.view = 'default/wh_docs.load'
    title = 'Warehouse Stock Issue'
    grid = SQLFORM.grid(db.WSI)

    return locals()
