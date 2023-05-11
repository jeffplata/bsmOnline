# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----

can_view_library = auth.has_permission('view', 'library') or adminuser
can_add_library = auth.has_permission('add', 'library') or adminuser
# can_edit_library = auth.has_permission('edit', 'library') or adminuser
# can_delete_library = auth.has_permission('delete', 'library') or adminuser

def can_modify(r):
    return (r.created_by==me) or\
        (auth.user.branch and (db.auth_user(r.created_by).branch==auth.user.branch)) or\
        ((not auth.user.branch) and auth.user.region and (db.auth_user(r.created_by).region==auth.user.region))

def can_edit_library(r):
    return adminuser or (auth.has_permission('edit', 'library') and can_modify(r))

def can_delete_library(r):
    return adminuser or (auth.has_permission('delete', 'library') and can_modify(r))


@auth.requires(can_view_library)
def warehouse():
    response.view = 'default/library.load'
    title = 'Warehouses'

    query = None
    if auth.has_membership('admin'):
        query = db.warehouse
    elif auth.has_membership('ro admin'):
        if auth.user.region:
            q = db(db.branch.region_id==auth.user.region)._select(db.branch.id)
            query = db.warehouse.branch_id.belongs(q)
    elif auth.has_membership('br admin'):
        if auth.user.branch:
            query = db.warehouse.branch_id==auth.user.branch

    grid = SQLFORM.grid(query, create=can_add_library, editable=can_edit_library, deletable=can_delete_library)
    return locals()


def region():
    response.view = 'default/library.load'
    query = db.region
    grid, title = library(query, 'region|regions',request.args(0), 
        create=can_add_library, editable=can_edit_library, deletable=can_delete_library)

    return locals()


def branch():
    response.view = 'default/library.load'
    query = db.branch
    grid, title = library(query, 'branch|branches',request.args(0), 
        create=can_add_library, editable=can_edit_library, deletable=can_delete_library)

    return locals()


def commodity():
    response.view = 'default/library.load'
    query = db.commodity
    grid, title = library(query, 'commodity|commodities',request.args(0), 
        create=can_add_library, editable=lambda r: can_edit_library(r), deletable=lambda r: can_delete_library(r) )

    return locals()


def container():
    response.view = 'default/library.load'
    query = db.container
    grid, title = library(query, 'container|containers', request.args(0),
        create=can_add_library, editable=can_edit_library, deletable=can_delete_library)

    return locals()


def variety():
    response.view = 'default/library.load'
    query = db.variety
    grid, title = library(query, 'variety|varieties', request.args(0),
        create=can_add_library, editable=can_edit_library, deletable=can_delete_library)

    return locals()


def activity():
    response.view = 'default/library.load'
    query = db.activity
    grid, title = library(query, 'activity|activities', request.args(0),
        create=can_add_library, editable=can_edit_library, deletable=can_delete_library)

    return locals()

    # todo: contextualize edit and delete