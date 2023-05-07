# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----

def warehouse():
    response.view = 'default/library.load'
    title = 'Warehouses'

    if auth.has_membership('admin'):
        query = db.warehouse
    elif auth.has_membership('ro admin'):
        if auth.user.region:
            q = db(db.branch.region_id==auth.user.region)._select(db.branch.id)
            query = db.warehouse.branch_id.belongs(q)

    # m_g_id = auth.id_group('member')
    # qm = db(db.auth_membership.group_id==m_g_id)._select(db.auth_membership.user_id)
    # query = ~db.auth_user.id.belongs(qm)

    grid = SQLFORM.grid(query)
    return locals()