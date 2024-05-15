import firebase_admin
from firebase_admin import credentials, db, firestore
import datetime


# connect to realtime firebase and firestore
def init_db(path_to_db="/"):
    dashboard = db.reference(path_to_db, app=APP)
    dashboard.update({
        "fan_level": 0,
        "humid": 0,
        "lux": 0,
        "temp": 0,
        "air_conditioner": False,
        "light": False,
        "open_door": False
    })
    log_db = firestore.client(app=APP)
    return dashboard, log_db


CRED = credentials.Certificate("accountKey/serviceAccountKey.json")
APP = firebase_admin.initialize_app(CRED, {
    'databaseURL': 'https://fir-ffa0c-default-rtdb.asia-southeast1.firebasedatabase.app/'
})
DASHBOARD, HISTORY = init_db()
is_database_changed = [False]
prev_database = [DASHBOARD.get()]
stop_check_database = [False]


def setup_db(account_key, db_url):
    global CRED, APP
    CRED = credentials.Certificate(account_key)
    APP = firebase_admin.initialize_app(CRED, {
        'databaseURL': db_url
    })


def database_changed():
    global prev_database, is_database_changed, stop_check_database
    while True:
        if not stop_check_database[0]:
            cur_db = DASHBOARD.get()
            if cur_db != prev_database[0]:
                is_database_changed[0] = True
            else:
                is_database_changed[0] = False


def log_activity(activity_name="", actor="Manual",
                 date_time=datetime.datetime.now(tz=datetime.timezone.utc)):
    HISTORY.collection("act").document().set({
        "act": activity_name,
        "actor": actor,
        "time": date_time
    })


def update_dashboard(name=None, value=None):
    if name is None or value is None:
        return
    # validate value for name of field
    if name == "humid" or name == "temp" or name == "lux":
        value = float(value)
        if value < 0:
            return
    if name == "open_door":
        value = True if value == '1' else False
    DASHBOARD.update({name: value})
