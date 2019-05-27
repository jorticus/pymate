#
# SQLAlchemy Environment
#
# Usage:
# python -i environment.py
# >>> with session_scope() as s:
# ...     s.query(MxStatus).count()
#

__author__ = 'Jared Sanson <jared@jared.geek.nz>'
__version__ = 'v0.1'

import sqlalchemy as sql
import sqlalchemy.orm
from contextlib import contextmanager
from datetime import datetime
from models import initialize_db, MxStatus, MxLogPage, FxStatus

engine = initialize_db()
Session = sql.orm.sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


