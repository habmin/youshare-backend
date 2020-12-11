from peewee import *;
from playhouse.sqlite_ext import JSONField;
from playhouse.db_url import connect
import os;

import datetime;

if 'ON_HEROKU' in os.environ:
    DATABASE = connect(os.environ.get('DATABASE_URL'));
else:
    DATABASE = connect('postgres://vqqpuuhxyearva:b28ef10f4c23ade1113e33f014fcd97a8e8ecf43b808cff5ed93845d2b0b0975@ec2-3-216-129-140.compute-');
    #DATABASE = SqliteDatabase('sessions.sqlite');

class Session(Model):
    room_name = CharField(unique = True);
    playlist = JSONField(null= True);
    created_at = DateTimeField(default = datetime.datetime.now);

    class Meta:
        database = DATABASE;
    
def initialize():
    DATABASE.connect();
    DATABASE.create_tables([Session], safe = True);
    print("SQLITE Tables created");
    DATABASE.close();
