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
    Field('last_change', 'string', length=80,           # track outside changes, set manual
        writable=False, readable=False),
    auth.signature,
    format='%(first_name)s %(last_name)s'
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


# initialize users and groups
def user_highest_rank(user_id):
    rank = db(db.auth_membership.user_id==user_id).select(
        join=db.auth_group.on(db.auth_membership.group_id==db.auth_group.id),
        orderby=db.auth_group.ranks
        ).first()['auth_group.ranks']
    return rank

auth.settings.login_onaccept = lambda form: __on_login()
auth.settings.logout_onlogout = lambda user: __on_logout()

def __on_login():
    if db(db.auth_user.id).count() == 1:
        group_id = db.auth_group.insert(role="admin", description="admin group")
        auth.add_membership(group_id, auth.user_id)

    adminuser = auth.has_membership('admin')
    adminusers = adminuser or auth.has_membership('co admin') or auth.has_membership('ro admin') or auth.has_membership('br admin')
    session.adminuser = adminuser
    session.adminusers = adminusers
    session.highest_rank = user_highest_rank(auth.user_id)

    if db(db.auth_user.id).count() == 1:
        init_tables()
        init_tables_libraries()

    return None

def __on_logout():
    session.adminuser = None
    session.adminusers = None
    return None
    