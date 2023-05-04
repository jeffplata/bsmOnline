
if db(db.warehouse.id).count() <1:
    branch = db(db.branch.branch_name=='Leyte Branch').select().first()['id']
    if branch:
        db.warehouse.update_or_insert(warehouse_name='Alangalang WH 1', warehouse_code='1234', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Alangalang WH 2', warehouse_code='1235', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Port Area WH', warehouse_code='1236', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Biliran WH', warehouse_code='1237', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='San Pablo, Ormoc WH', warehouse_code='1238', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Cogon, Ormoc WH', warehouse_code='1239', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Baybay WH', warehouse_code='1240', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Maasin WH', warehouse_code='1241', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='St. Bernard WH', warehouse_code='1242', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Hinunangan WH', warehouse_code='1243', branch_id=branch)
        db.warehouse.update_or_insert(warehouse_name='Hilongos JICA WH', warehouse_code='1244', branch_id=branch)