from peewee import *
from playhouse.sqlite_ext import JSONField
from playhouse.db_url import connect
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

if os.getenv("DEBUG") == "1":
    print('DEV Address Used')
    DATABASE = SqliteDatabase('sessions.sqlite')
else:
    print('DEPLOY Address Used')
    DATABASE = connect(os.environ.get('DATABASE_URL'))

class Session(Model):
    room_name = CharField(unique = True)
    playlist = JSONField(null= True)
    created_at = DateTimeField(default = datetime.datetime.now)

    class Meta:
        database = DATABASE
    
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([Session], safe = True)
    print("SQLITE Tables created")
    DATABASE.close()
