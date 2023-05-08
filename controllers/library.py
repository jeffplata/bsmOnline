# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----

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

    grid = SQLFORM.grid(query)
    return locals()


def commodity():
    response.view = 'default/library.load'
    query = db.commodity
    grid, title = library(query, 'commodity|commodities', False, request.args(0))

    return locals()


def container():
    response.view = 'default/library.load'
    query = db.container
    grid, title = library(query, 'container|containers', False, request.args(0))

    return locals()


def variety():
    response.view = 'default/library.load'
    query = db.variety
    grid, title = library(query, 'variety|varieties', False, request.args(0))

    return locals()


def activity():
    response.view = 'default/library.load'
    query = db.activity
    grid, title = library(query, 'activity|activities', False, request.args(0))

    return locals()