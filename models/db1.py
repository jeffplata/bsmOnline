
me = auth.user_id
mdy = '%m/%d/%Y'
mdy_date = IS_DATE(format='%m/%d/%Y')
moneytize = lambda v: '{:,.2f}'.format(v)
max_bags = 999999999


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


def get_next_number(table, next_number, number_format):
    fld = db[table][next_number]
    db.executesql('update %s set %s=%s+1;' % (table, next_number, next_number))
    r = db.executesql('select %s, %s from %s' % (next_number, number_format, table))
    nxn = r[0][0]
    fmt = r[0][1]
    fmt = datetime.now().strftime(fmt)
    nph = re.search('\[0+\]', fmt)
    nph = re.sub('[\[\]]', '', nph[0])
    if len(nxn) >= len(nph):
        nph = nxn
    else:
        nph = nph[0:len(nph)-len(nxn)] + nxn
    nxn = re.sub('\[0+\]', nph, fmt)
    return nxn


def record_signature(r):
    created_by = db.auth_user(r.created_by)
    modified_by = created_by if r.created_by==r.modified_by else db.auth_user(r.modified_by)
    created_by_name = created_by.first_name+ ' '+ created_by.last_name if created_by else 'None'
    modified_by_name =  modified_by.first_name+ ' '+ modified_by.last_name if modified_by else 'None'
    s = ''
    if created_by:
        s = 'Created by '+ created_by_name+ ' on '+ r.created_on.strftime("%m/%d/%Y, %H:%M:%S") +'\n'
    if modified_by:
        s = s + 'Modified by '+ modified_by_name+ ' on '+ r.modified_on.strftime("%m/%d/%Y, %H:%M:%S") 
    return s

def append_record_signature(grid, r):
    if grid.view_form and session.adminusers:
        d = DIV(record_signature(r), _style='white-space:pre; border-top: 1px solid #eaeaea', _class='text-muted')
        grid.view_form[0].append(d)
    return None

@auth.requires(session.adminuser or auth.has_permission('view','library'))
def library(query, title, action=None, **kwargs):
    t1 = title.split('|')[0]
    t2 = title.split('|')[1] if '|' in title else t1
    if action in ['view', 'edit', 'new']:
        title = f"{action.capitalize()} {t1.lower()}"
    else:
        title = t2.capitalize()
    grid = SQLFORM.grid(query, maxtextlength=80, csv=False, **kwargs)
    return (grid, title)


db.define_table('warehouse',
    Field('warehouse_name', 'string', length=80, unique=True),
    Field('warehouse_code', 'string', length=20, unique=True),
    Field('region_id', db.region, label='Region', ondelete='RESTRICT'),
    Field('branch_id', db.branch, label='Branch', ondelete='RESTRICT'),
    auth.signature,
    format='%(warehouse_name)s')

# db.warehouse.warehouse_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.warehouse.warehouse_name)]
# db.warehouse.warehouse_code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.warehouse.warehouse_code)]


db.define_table('ws_accountability',
    Field('ws_id', db.auth_user, label='Supervisor', ondelete='RESTRICT'),
    Field('wh_id', db.warehouse, label='Warehouse', ondelete='RESTRICT'),
    Field('period_start', 'date', requires=IS_DATE(format='%m/%d/%Y')),
    Field('period_end', 'date', requires=IS_EMPTY_OR(IS_DATE(format='%m/%d/%Y'))),
    auth.signature,
    )

db.define_table('user_warehouse',
    Field('user_id', db.auth_user, label='User', ondelete='RESTRICT'),
    Field('warehouse_id', db.warehouse, label='Warehouse', ondelete='RESTRICT'),
    auth.signature,
    )

db.define_table('user_wh_supervisor',
    Field('user_id', db.auth_user, label='User', ondelete='RESTRICT'),
    Field('wh_supervisor_id', db.auth_user, label='Warehouse Supervisor', ondelete='RESTRICT'),
    auth.signature,
    )

db.define_table('container',
    Field('container_name', 'string', length=20, unique=True),
    Field('container_shortname', 'string', length=20, unique=True),
    Field('weight', 'decimal(15,4)'),
    Field('wt_capacity', 'decimal(15,4)', label='Wt capacity (kg)', requires=IS_DECIMAL_IN_RANGE(1,99999, error_message='Wt capacity must be greater than zero.')),
    auth.signature,
    format='%(container_shortname)s')

# db.container.container_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.container.container_name)]
# db.container.container_shortname.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.container.container_shortname)]


db.define_table('commodity',
    Field('commodity_name', 'string', length=80, unique=True),
    Field('is_cereal', 'boolean', label='Cereal', default=True),
    auth.signature,
    format='%(commodity_name)s')

# db.commodity.commodity_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.commodity.commodity_name)]
db.commodity.is_cereal.default = True


db.define_table('variety',
    Field('variety_name', 'string', length=20, unique=True),
    Field('commodity_id', db.commodity, label='Commodity', ondelete='RESTRICT'),
    Field('default_container', db.container, ondelete='RESTRICT'),
    auth.signature,
    format='%(variety_name)s')

# db.variety.variety_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.variety.variety_name)]


db.define_table('stock_condition',
    Field('condition_name', 'string', length=50, unique=True),
    Field('short_name', 'string', length=5, unique=True),
    auth.signature,
    format='%(condition_name)s'
    )

db.define_table('item',
    Field('item_name', 'string', length=80, unique=True),
    Field('variety_id', db.variety, label='Variety', ondelete='RESTRICT'),
    Field('container_id', db.container, label='Container', ondelete='RESTRICT'),
    Field('selling_price', 'decimal(15,2)'),
    auth.signature,
    format='%(item_name)s')

db.define_table('activity',
    Field('activity_name', 'string', length=80, unique=True),
    Field('applies_to', 'string', length=20, requires=IS_IN_SET(['any', 'receipts', 'issues'], zero=None)),
    auth.signature,
    format='%(activity_name)s'
    )

# db.item.item_name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, db.item.item_name)]

db.define_table('user_doc_no',
    Field('user_id', db.auth_user),
    Field('docu', 'string'),
    Field('lastno', 'string')
    )

doc_stamp = db.Table(db, 'doc_stamp',
    Field('doc_date', 'date', default=request.now, requires=IS_DATE(format='%m/%d/%Y') ),
    Field('doc_number', 'string', length=40, unique=True))

db.define_table('WSR',
    doc_stamp,
    Field('wh_supervisor', db.auth_user, label='Warehouse Supervisor'),
    Field('warehouse', 'reference warehouse', requires=IS_IN_DB(db, db.warehouse.id, '%(warehouse_name)s', zero=None)),
    Field('received_from', 'string', length=80),
    Field('reference_doc', 'string', length=20),
    Field('variety', 'reference variety', ondelete='RESTRICT', requires=IS_IN_DB(db, db.variety.id, '%(variety_name)s', zero=None)),
    Field('container', 'reference container', ondelete='RESTRICT', requires=IS_IN_DB(db, db.container.id, '%(container_shortname)s', zero=None)),
    Field('bags', 'integer', requires=IS_INT_IN_RANGE(0,max_bags)),
    Field('gross_weight', 'decimal(15,3)'),
    Field('net_weight', 'decimal(15,3)'),
    Field('activity', 'reference activity', ondelete='RESTRICT'),
    Field('age', 'string', length=20),
    Field('stock_condition', 'reference stock_condition', label='Condition', ondelete='RESTRICT'),
    Field('MC', 'decimal(8,2)', label='MC %'),
    Field('purity', 'decimal(8,2)', label='Purity %'),
    auth.signature,
    )

db.define_table('WSI',
    doc_stamp,
    Field('warehouse', 'reference warehouse'),
    Field('issued_to', 'string', length=80),
    Field('AI_No', 'string', label='AI No', length=20),
    Field('OR_No', 'string', label='OR No', length=20),
    Field('variety', 'reference variety', ondelete='RESTRICT'),
    Field('container', 'reference container', ondelete='RESTRICT'),
    Field('bags', 'integer', requires=IS_INT_IN_RANGE(0,max_bags)),
    Field('gross_weight', 'decimal(15,3)'),
    Field('net_weight', 'decimal(15,3)'),
    Field('activity', 'reference activity', ondelete='RESTRICT'),
    Field('age', 'string', length=20),
    Field('stock_condition', 'reference stock_condition', label='Condition', ondelete='RESTRICT'),
    Field('MC', 'decimal(8,2)', label='MC %'),
    Field('purity', 'decimal(8,2)', label='Purity %'),
    auth.signature,
    )
