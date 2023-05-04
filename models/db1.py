
# from datetime import datetime, timedelta
# from calendar import monthrange

me = auth.user_id
mdy = '%m/%d/%Y'
mdy_date = IS_DATE(format='%m/%d/%Y')
moneytize = lambda v: '{:,.2f}'.format(v)


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
    Field('weight', 'decimal(8,2)'),
    format='%(container_shortname)s')

db.container.container_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.container.container_name)]
db.container.container_shortname.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.container.container_shortname)]


db.define_table('commodity',
    Field('commodity_name', 'string', length=80, unique=True),
    Field('is_cereal', 'boolean', default=True),
    format='%(commodity_name)s')

db.commodity.commodity_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.commodity.commodity_name)]
db.commodity.is_cereal.default = True


db.define_table('variety',
    Field('variety_name', 'string', length=20, unique=True),
    Field('commodity_id', db.commodity, label='Commodity', ondelete='RESTRICT'),
    format='%(variety_name)s')

db.variety.variety_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.variety.variety_name)]


doc_stamp = db.Table(db, 'doc_stamp',
    Field('doc_date', 'date', default=request.now, requires=IS_DATE(format='%m/%d/%Y') ),
    Field('doc_number', 'string', length=40, unique=True))


db.define_table('WSR',
    doc_stamp,
    Field('warehouse', 'reference warehouse'),
    Field('received_from', 'string')
    )