# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

def wsr():
    response.view = 'document/wsr.load'
    title = 'Warehouse Stock Receipt'

    var_container = dict((r.id, r.default_container) for r in db().select(db.variety.ALL))

    if request.args(0) == 'new':
        user_whses = db(db.user_warehouse.user_id==auth.user_id).select()
        # uw = [i.warehouse_id for i in user_whses]
        wh_options = db(db.warehouse.id.belongs( [i.warehouse_id for i in user_whses] ))
        db.WSR.warehouse.requires = IS_IN_DB(wh_options, 'warehouse.id', '%(warehouse_name)s', zero=None)
        db.WSR.variety.default = list(var_container.keys())[0]
        db.WSR.container.default = list(var_container.values())[0]
    grid = SQLFORM.grid(db.WSR)

    return locals()


def wsi():
    response.view = 'default/library.load'
    title = 'Warehouse Stock Issue'
    grid = SQLFORM.grid(db.WSI)

    return locals()
