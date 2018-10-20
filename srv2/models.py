
from matenet.mx import MXStatusPacket, MXLogPagePacket
import sqlalchemy as sql
import sqlalchemy.orm
from sqlalchemy.engine.url import URL
from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from base64 import b64encode, b64decode

import dateutil.parser

Base = declarative_base()


class MxStatus(Base):
    __tablename__ = "mx_status"

    id = Column(sql.Integer, primary_key=True)
    timestamp = Column(sql.DateTime)
    tzoffset = Column(sql.Integer)
    raw_packet = Column(sql.LargeBinary)

    pv_current = Column(sql.Float)
    bat_current = Column(sql.Float)
    pv_voltage = Column(sql.Float)
    bat_voltage = Column(sql.Float)
    amp_hours = Column(sql.Float)
    kw_hours = Column(sql.Float)
    watts = Column(sql.Float)

    status = Column(sql.Integer)
    errors = Column(sql.Integer)

    def __init__(self, js):
        data = b64decode(js['data'])  # To bytestr

        self.timestamp = dateutil.parser.parse(js['ts'])
        self.tzoffset = int(js['tz'])
        self.raw_packet = data

        status = MXStatusPacket.from_buffer(data)
        self.pv_current = float(status.pv_current)
        self.bat_current = float(status.bat_current)
        self.pv_voltage = float(status.pv_voltage)
        self.bat_voltage = float(status.bat_voltage)
        self.amp_hours = float(status.amp_hours)
        self.kw_hours = float(status.kilowatt_hours)
        self.watts = float(js['extra']['chg_w'])
        self.status = int(status.status)
        self.errors = int(status.errors)

        print("Status:", status)

    def to_json(self):
        d = {key: getattr(self, key) for key in self.__dict__ if key[0] != '_'}
        d['raw_packet'] = b64encode(d['raw_packet'])
        return d

    @property
    def local_timestamp(self):
        return self.timestamp


class MxLogPage(Base):
    __tablename__ = "mx_logpage"

    id = Column(sql.Integer, primary_key=True)
    timestamp = Column(sql.DateTime)
    tzoffset = Column(sql.Integer)
    raw_packet = Column(sql.LargeBinary)

    date = Column(sql.Date)

    bat_min = Column(sql.Float)
    bat_max = Column(sql.Float)
    volts_peak = Column(sql.Float)
    amps_peak = Column(sql.Float)
    amp_hours = Column(sql.Float)
    kw_hours = Column(sql.Float)
    absorb_time = Column(sql.Float)
    float_time = Column(sql.Float)

    def __init__(self, js):
        data = b64decode(js['data'])

        self.timestamp = dateutil.parser.parse(js['ts'])
        self.tzoffset = int(js['tz'])
        self.raw_packet = data

        self.date = dateutil.parser.parse(js['date']).date()

        logpage = MXLogPagePacket.from_buffer(data)
        self.bat_min = float(logpage.bat_min)
        self.bat_max = float(logpage.bat_max)
        self.volts_peak = float(logpage.volts_peak)
        self.amps_peak = float(logpage.amps_peak)
        self.amp_hours = float(logpage.amp_hours)
        self.kw_hours = float(logpage.kilowatt_hours)
        self.absorb_time = float(logpage.absorb_time)  # Minutes
        self.float_time = float(logpage.float_time)  # Minutes

        print("Log Page:", logpage)

    def to_json(self):
        d = {key: getattr(self, key) for key in self.__dict__ if key[0] != '_'}
        d['raw_packet'] = b64encode(d['raw_packet'])
        return d

def initialize_db():
    import settings

    print("Create DB Engine")
    engine = sql.create_engine(URL(**settings.DATABASE))
    Base.metadata.create_all(engine)

    return engine