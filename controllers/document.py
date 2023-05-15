# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

def wsr():
    response.view = 'default/library.load'
    title = 'Warehouse Stock Receipt'
    grid = SQLFORM.grid(db.WSR)

    return locals()
