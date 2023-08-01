

def init_tables():
    if db(db.auth_group.id).count() < 2:
        db.auth_group.insert(role='co admin')
        db.auth_group.insert(role='co user')
        db.auth_group.insert(role='ro admin')
        db.auth_group.insert(role='ro user')
        db.auth_group.insert(role='br admin')
        db.auth_group.insert(role='br user')
        db.auth_group.insert(role='wh supervisor')
        db.auth_group.insert(role='wh assistant')
        db.auth_group.insert(role='cashier')
        db.auth_group.insert(role='sdo')
        db.auth_group.insert(role='sco')

    # initialize regions and branches

    if db(db.region.id).count() < 1:
        db.region.insert(region_name='Region 1 - Ilocos', short_name='Ilocos')
        db.region.insert(region_name='Region 2 - Cagayan Valley', short_name='CVR')
        db.region.insert(region_name='Region 3 - Central Luzon', short_name='CLR')
        db.region.insert(region_name='Region 4 - Southern Tagalog', short_name='STR')
        db.region.insert(region_name='Region 5 - Bicol', short_name='Bicol')
        db.region.insert(region_name='Region 6 - Western Visayas', short_name='WVR')
        db.region.insert(region_name='Region 7 - Central Visayas', short_name='CViR')
        db.region.insert(region_name='Region 8 - Eastern Visayas Region', short_name='EVR')
        db.region.insert(region_name='Region 9 - Western Mindanao', short_name='WMR')
        db.region.insert(region_name='Region 10 - Northeastern Mindanao', short_name='NEMR')
        db.region.insert(region_name='Region 11 - Southeastern Mindanao', short_name='SEMR')
        db.region.insert(region_name='Region 12 - Southern Mindanao', short_name='SMR')
        db.region.insert(region_name='National Capital Region', short_name='NCR')
        db.region.insert(region_name='ARMM', short_name='ARMM')
        db.region.insert(region_name='CARAGA', short_name='CARAGA')

    region2_id = db(db.region.short_name=='CVR').select().first()['id']
    region7_id = db(db.region.short_name=='CViR').select().first()['id']
    region8_id = db(db.region.short_name=='EVR').select().first()['id']

    if db(db.branch.id).count() < 1:
        db.branch.insert(branch_name='Isabela Branch', short_name='ISA', region_id=region2_id)
        db.branch.insert(branch_name='Cagayan Branch', short_name='CAG', region_id=region2_id)
        db.branch.insert(branch_name='Nueva Vizcaya Branch', short_name='NVA', region_id=region2_id)
        db.branch.insert(branch_name='Leyte Branch', short_name='TCN', region_id=region8_id)
        db.branch.insert(branch_name='Samar Branch', short_name='SMR', region_id=region8_id)

    br_leyte_id = db(db.branch.short_name=='TCN').select().first()['id']
    br_samar_id = db(db.branch.short_name=='SMR').select().first()['id']
    # add a few users
    if db(db.auth_user.id).count() < 2:
        db.auth_user.validate_and_insert(email='venus@email.com', first_name='Venus', last_name='Prima', password='Password1', region=region8_id, branch=br_leyte_id)
        db.auth_user.validate_and_insert(email='cebpac@email.com', first_name='Jeff', last_name='Plata', password='Password1', region=region8_id)
        db.auth_user.validate_and_insert(email='enidganda@email.com', first_name='Nadine', last_name='Sandino', password='Password1', region=region8_id, branch=br_leyte_id)
        db.auth_user.validate_and_insert(email='ejconchada@email.com', first_name='Eduard Jayson', last_name='Conchada', password='Password1', region=region8_id)
        db.auth_user.validate_and_insert(email='saldy@email.com', first_name='Salvador', last_name='Ada', password='Password1', region=region8_id, branch=br_samar_id)
        db.auth_user.validate_and_insert(email='reco7@email.com', first_name='RECO of R7', last_name='reco 7', password='Password1', region=region7_id)
        db.auth_user.validate_and_insert(email='reco2@email.com', first_name='RECO of R2', last_name='reco 2', password='Password1', region=region2_id)

    return None


def init_tables_libraries():
    # initialize libraries

    if db(db.commodity.id).count() < 1:
        db.commodity.insert(commodity_name='Local Palay', is_cereal=True)
        db.commodity.insert(commodity_name='Local Rice', is_cereal=True)
        db.commodity.insert(commodity_name='By-products', is_cereal=False)

    if db(db.container.id).count() < 1:
        db.container.insert(container_name='PPR E50', container_shortname='E50', weight=0.095)
        db.container.insert(container_name='PPM G50', container_shortname='G50', weight=0.075)
        # todo: initialize weight capacity

    if db(db.variety.id).count() < 1:
        local_palay = db(db.commodity.commodity_name=='Local Palay').select().first()
        local_rice = db(db.commodity.commodity_name=='Local Rice').select().first()
        db.variety.insert(variety_name='PD1', commodity_id=local_palay)
        db.variety.insert(variety_name='PD3', commodity_id=local_palay)
        db.variety.insert(variety_name='PW1', commodity_id=local_palay)
        db.variety.insert(variety_name='PW3', commodity_id=local_palay)
        db.variety.insert(variety_name='WD1', commodity_id=local_rice)
        db.variety.insert(variety_name='WD2', commodity_id=local_rice)

    if db(db.activity.id).count() < 1:
        db.activity.insert(activity_name='Procurement', applies_to='receipts')
        db.activity.insert(activity_name='Sales', applies_to='issues')
        db.activity.insert(activity_name='Transfer-in', applies_to='receipts')
        db.activity.insert(activity_name='Transfer-out', applies_to='issues')
        db.activity.insert(activity_name='Mechanical Drying', applies_to='any')
        db.activity.insert(activity_name='Solar Drying', applies_to='any')
        db.activity.insert(activity_name='Milling', applies_to='any')

    if db(db.stock_condition.id).count() < 1:
        db.stock_condition.validate_and_insert(condition_name='Good', short_name='GD')
        db.stock_condition.validate_and_insert(condition_name='Infested', short_name='INF')
        db.stock_condition.validate_and_insert(condition_name='Treated', short_name='TD')
        db.stock_condition.validate_and_insert(condition_name='Partially Damaged', short_name='PD')
        db.stock_condition.validate_and_insert(condition_name='Totally Damaged', short_name='TD')

    if db(db.warehouse.id).count() <1:
        branch = db(db.branch.branch_name=='Leyte Branch').select().first()
        branch_id = branch['id']
        region_id = branch['region_id']
        if branch:
            db.warehouse.update_or_insert(warehouse_name='Alangalang WH 1', warehouse_code='1234', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Alangalang WH 2', warehouse_code='1235', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Port Area WH', warehouse_code='1236', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Biliran WH', warehouse_code='1237', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='San Pablo, Ormoc WH', warehouse_code='1238', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Cogon, Ormoc WH', warehouse_code='1239', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Baybay WH', warehouse_code='1240', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Maasin WH', warehouse_code='1241', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='St. Bernard WH', warehouse_code='1242', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Hinunangan WH', warehouse_code='1243', region_id=region_id, branch_id=branch_id)
            db.warehouse.update_or_insert(warehouse_name='Hilongos JICA WH', warehouse_code='1244', region_id=region_id, branch_id=branch_id)

    return None


if db(db.auth_user.id).count() < 1:
    user_id = db.auth_user.validate_and_insert(email="admin@email.com", first_name="admin", last_name="admin", password="Password1")

    redirect(URL('default', 'user/login'))

