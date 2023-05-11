# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# AppConfig configuration made easy. Look inside private/appconfig.ini
# Auth is for authenticaiton and access control
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig
from gluon.tools import Auth

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.15.5":
    raise HTTP(500, "Requires web2py 2.15.5 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
configuration = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(configuration.get('db.uri'),
             pool_size=configuration.get('db.pool_size'),
             migrate_enabled=configuration.get('db.migrate'),
             check_reserved=['all'])
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = [] 
if request.is_local and not configuration.get('app.production'):
    response.generic_patterns.append('*')

# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = 'bootstrap4_inline'
response.form_label_separator = ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=configuration.get('host.names'))

# -------------------------------------------------------------------------
# create all tables needed by auth, maybe add a list of extra fields
# -------------------------------------------------------------------------


# auth.settings.extra_fields['auth_user'] = [
#     Field("middle_name", length=128, default="", map_none=''),
#     Field("region", "reference region", map_none=''),
#     Field("branch", "reference branch", map_none=''),
#     ]
# auth.settings.extra_fields['auth_user'] = []


db.define_table(
    auth.settings.table_user_name,
    Field('first_name', length=128, default=''),
    Field('last_name', length=128, default=''),
    Field('middle_name', length=128, default='', map_none=''),
    Field('email', length=128, default='', unique=True), # required
    Field('password', 'password', length=512,            # required
          readable=False, writable=False, label='Password'),
    Field("region", "integer", map_none=''),
    Field("branch", "integer", map_none=''),

    Field('registration_key', length=512,                # required
          writable=False, readable=False, default=''),
    Field('reset_password_key', length=512,              # required
          writable=False, readable=False, default=''),
    Field('registration_id', length=512,                 # required
          writable=False, readable=False, default=''),
    format='%(first_name)s %(last_name)s (%(id)s)'
    )

## do not forget validators
custom_auth_table = db[auth.settings.table_user_name] # get the custom_auth_table
custom_auth_table.first_name.requires =   IS_NOT_EMPTY(error_message=auth.messages.is_empty)
# custom_auth_table.last_name.requires =   IS_NOT_EMPTY(error_message=auth.messages.is_empty)
# custom_auth_table.password.requires = [IS_STRONG(), CRYPT()]
custom_auth_table.password.requires = [CRYPT()]
custom_auth_table.email.requires = [
  IS_EMAIL(error_message=auth.messages.invalid_email),
  IS_NOT_IN_DB(db, custom_auth_table.email)]

auth.settings.table_user = custom_auth_table # tell auth to use custom_auth_table

# customize auth_group
auth.settings.extra_fields['auth_group'] = [
    Field("ranks", "integer", readable=False, writable=False),
    auth.signature
    ]


auth.define_tables(username=False, signature=False)

db.auth_group._after_insert = [lambda f, i: db(db.auth_group.id==i).update(ranks=i)]

# set up auth_membership
db.auth_membership.user_id.label = 'User'
db.auth_membership.group_id.label = 'Group'

# =======================================================
# Region and Branch

db.define_table("region",
    Field("region_name", "string", requires=IS_NOT_EMPTY(), unique=True),
    Field("short_name", "string", length=20, requires=IS_NOT_EMPTY(), unique=True),
    Field("seq", "integer", readable=False, writable=False),
    auth.signature,
    format="%(region_name)s"
    )
def _region_after_insert(f, i):
    if f: db(db.region.id==i).update(seq=i)
db.region._after_insert = [_region_after_insert]


db.define_table("branch",
    Field("branch_name", "string", requires=IS_NOT_EMPTY(), unique=True),
    Field("short_name", "string", length=20, requires=IS_NOT_EMPTY(), unique=True),
    Field("region_id", "reference region", label="Region", ondelete='RESTRICT'),
    Field("seq", "integer", readable=False, writable=False),
    auth.signature,
    format="%(branch_name)s"
    )
db.branch._after_insert = [lambda f, i: db(db.branch.id==i).update(seq=i)]

# ==============
# set auth_user validation for branch and region

custom_auth_table.region.requires = IS_EMPTY_OR(IS_IN_DB(db, 'region.id', '%(region_name)s'))
custom_auth_table.branch.requires = IS_EMPTY_OR(IS_IN_DB(db, 'branch.id', '%(branch_name)s'))

# initialize users and groups

if db(db.auth_user.id).count() < 1:
    user_id = db.auth_user.validate_and_insert(email="admin@email.com", first_name="admin", last_name="admin", password="Password1")
    user = db(db.auth_user.id==user_id).select().first()
    auth.login_bare(user.email, user.password)

    group_id = db.auth_group.insert(role="admin", description="admin group")
    auth.add_membership(group_id, user_id)

if db(db.auth_group.id).count() < 2:
    db.auth_group.insert(role='co admin')
    db.auth_group.insert(role='co user')
    db.auth_group.insert(role='ro admin')
    db.auth_group.insert(role='ro user')
    db.auth_group.insert(role='br admin')
    db.auth_group.insert(role='br user')
    db.auth_group.insert(role='wh supervisor')
    db.auth_group.insert(role='wh asssistant')
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



# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else configuration.get('smtp.server')
mail.settings.sender = configuration.get('smtp.sender')
mail.settings.login = configuration.get('smtp.login')
mail.settings.tls = configuration.get('smtp.tls') or False
mail.settings.ssl = configuration.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

# -------------------------------------------------------------------------  
# read more at http://dev.w3.org/html5/markup/meta.name.html               
# -------------------------------------------------------------------------
response.meta.author = configuration.get('app.author')
response.meta.description = configuration.get('app.description')
response.meta.keywords = configuration.get('app.keywords')
response.meta.generator = configuration.get('app.generator')
response.show_toolbar = configuration.get('app.toolbar')

# -------------------------------------------------------------------------
# your http://google.com/analytics id                                      
# -------------------------------------------------------------------------
response.google_analytics_id = configuration.get('google.analytics_id')

# -------------------------------------------------------------------------
# maybe use the scheduler
# -------------------------------------------------------------------------
if configuration.get('scheduler.enabled'):
    from gluon.scheduler import Scheduler
    scheduler = Scheduler(db, heartbeat=configuration.get('scheduler.heartbeat'))

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)
