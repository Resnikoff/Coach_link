import sqlite3

DATABASE = 'site.db'  

class G:
    _database = None

    @classmethod
    def get_db(cls):
        if cls._database is None:
            cls._database = sqlite3.connect(DATABASE)
            cls._database.row_factory = sqlite3.Row
        return cls._database

    @classmethod
    def close_db(cls, e=None):
        db = cls._database
        if db is not None:
            db.close()
            cls._database = None
