
me = auth.user_id
mdy = '%m/%d/%Y'
mdy_date = IS_DATE(format='%m/%d/%Y')
moneytize = lambda v: '{:,.2f}'.format(v)
max_bags = 999999999
adminuser = auth.has_membership('admin')


def is_float(s):
    try:
        float(s)
    except ValueError:
        return False
    return True


def next_month(date, force_day=0):
    today_date = date
    year = today_date.year
    month = today_date.month
    day = today_date.day

    days_in_month = monthrange(year, month)[1]
    next_month = today_date + timedelta(days=days_in_month)
    if next_month.month - month > 1:
        next_month = next_month.replace(month=month+1)
        days_in_month = monthrange(next_month.year, next_month.month)[1]
        next_month = next_month.replace(day=days_in_month)
    days_in_month = monthrange(next_month.year, next_month.month)[1]
    if ((force_day>0) and (days_in_month >= force_day)):
        next_month = next_month.replace(day=force_day)        
    return next_month


# @auth.requires(adminuser or auth.has_permission('view','library'))
# def library(query, title, deletable=True, action=None):
#     t1 = title.split('|')[0]
#     t2 = title.split('|')[1] if '|' in title else t1
#     if action in ['view', 'edit', 'new']:
#         title = f"{action.capitalize()} {t1.lower()}"
#     else:
#         title = t2.capitalize()
#     grid = SQLFORM.grid(query, deletable=deletable, editable=True, csv=False)
#     # return dict(grid=grid, title=title)
#     return (grid, title)

@auth.requires(adminuser or auth.has_permission('view','library'))
def library(query, title, action=None, **kwargs):
    t1 = title.split('|')[0]
    t2 = title.split('|')[1] if '|' in title else t1
    if action in ['view', 'edit', 'new']:
        title = f"{action.capitalize()} {t1.lower()}"
    else:
        title = t2.capitalize()
    grid = SQLFORM.grid(query, csv=False, **kwargs)
    return (grid, title)


# set up auth_membership
db.auth_membership.user_id.label = 'User'
db.auth_membership.group_id.label = 'Group'

# initialize users and groups

if db(db.auth_user.id).count() < 1:
    user = db.auth_user.validate_and_insert(email="admin@email.com", first_name="admin", last_name="admin", password="Password1")
    role = db.auth_group.insert(role="admin", description="admin group")
    db.auth_membership.insert(user_id=user, group_id=role)
    db.auth_permission.insert(group_id=role, name='manage', table_name='auth_user')

if db(db.auth_group.id).count() < 2:
    db.auth_group.insert(role='co admin')
    db.auth_group.insert(role='ro admin')
    db.auth_group.insert(role='br admin')
    db.auth_group.insert(role='co user')
    db.auth_group.insert(role='ro user')
    db.auth_group.insert(role='br user')
    db.auth_group.insert(role='wh supervisor')
    db.auth_group.insert(role='wh asssistant')
    db.auth_group.insert(role='cashier')
    db.auth_group.insert(role='sdo')
    db.auth_group.insert(role='sco')


db.define_table('warehouse',
    Field('warehouse_name', 'string', length=80, unique=True),
    Field('warehouse_code', 'string', length=20, unique=True),
    Field('branch_id', db.branch, label='Branch', ondelete='RESTRICT'),
    format='%(warehouse_name)s')

db.warehouse.warehouse_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.warehouse.warehouse_name)]
db.warehouse.warehouse_code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.warehouse.warehouse_code)]


db.define_table('container',
    Field('container_name', 'string', length=20, unique=True),
    Field('container_shortname', 'string', length=20, unique=True),
    Field('weight', 'decimal(8,4)'),
    auth.signature,
    format='%(container_shortname)s')

db.container.container_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.container.container_name)]
db.container.container_shortname.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.container.container_shortname)]


db.define_table('commodity',
    Field('commodity_name', 'string', length=80, unique=True),
    Field('is_cereal', 'boolean', label='Cereal', default=True),
    auth.signature,
    format='%(commodity_name)s')

db.commodity.commodity_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.commodity.commodity_name)]
db.commodity.is_cereal.default = True


db.define_table('variety',
    Field('variety_name', 'string', length=20, unique=True),
    Field('commodity_id', db.commodity, label='Commodity', ondelete='RESTRICT'),
    auth.signature,
    format='%(variety_name)s')

db.variety.variety_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.variety.variety_name)]


db.define_table('stock_condition',
    Field('condition_name', 'string', length=50, unique=True),
    Field('short_name', 'string', length=5, unique=True),
    )

db.define_table('item',
    Field('item_name', 'string', length=80, unique=True),
    Field('variety_id', db.variety, label='Variety'),
    Field('container_id', db.container, label='Container'),
    Field('selling_price', 'decimal(15,2)'),
    auth.signature,
    format='%(item_name)s')

db.define_table('activity',
    Field('activity_name', 'string', length=80, unique=True),
    Field('applies_to', 'string', length=20, requires=IS_IN_SET(['any', 'receipts', 'issues'], zero=None)),
    auth.signature,
    )

# db.item.item_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.item.item_name)]


doc_stamp = db.Table(db, 'doc_stamp',
    Field('doc_date', 'date', default=request.now, requires=IS_DATE(format='%m/%d/%Y') ),
    Field('doc_number', 'string', length=40, unique=True))


db.define_table('WSR',
    doc_stamp,
    Field('warehouse', 'reference warehouse'),
    Field('received_from', 'string', length=80),
    Field('AI_No', 'string', length=20),
    Field('OR_No', 'string', length=20),
    Field('variety', 'reference variety'),
    Field('container', 'reference container'),
    Field('activity', 'reference activity'),
    Field('received_from', 'string', length=80),
    Field('age', 'string', length=20),
    Field('stock_condition', 'reference stock_condition', label='Condition'),
    Field('MC', 'decimal(8,2)', label='MC %'),
    Field('purity', 'decimal(8,2)', label='Purity %'),
    Field('bags', 'integer', requires=IS_INT_IN_RANGE(0,max_bags)),
    Field('gross_weight', 'decimal(15,3)'),
    Field('net_weight', 'decimal(15,3)'),
    auth.signature,
    )


if db(db.commodity.id).count() < 1:
    db.commodity.insert(commodity_name='Local Palay', is_cereal=True)
    db.commodity.insert(commodity_name='Local Rice', is_cereal=True)

if db(db.container.id).count() < 1:
    db.container.insert(container_name='PPR E50', container_shortname='E50', weight=0.095)
    db.container.insert(container_name='PPM G50', container_shortname='G50', weight=0.075)

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

