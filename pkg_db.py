import sqlite3 as sq

con = None
c = None


def start_db_connection(version):
    global con
    global c
    print(version)
    con = sq.connect(f'D:/D2_Datamining/Package Unpacker/db/{version}.db')
    c = con.cursor()


def get_entries_from_table(pkg_str, column_select='*'):
    global c
    c.execute("SELECT " + column_select + " from " + pkg_str)
    rows = c.fetchall()
    return rows


def get_all_tables():
    c.execute("select * from sqlite_master")
    table_list = c.fetchall()
    return table_list