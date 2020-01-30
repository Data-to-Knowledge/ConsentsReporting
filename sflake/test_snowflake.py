# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 13:49:10 2020

@author: MichaelEK
"""
import pandas as pd
import snowflake
from sqlalchemy import create_engine
from pdsql import snowflake as sf
from pdsql import create_snowflake_engine

username='mikeek'
password='Pumpkins2u'
account='ru48422.australia-east.azure'
database = 'waterdatarepo'
schema = 'public'
table = 'Consents_Permit_Source'

# Gets the version
ctx = snowflake.connector.connect(
    user=username,
    password=password,
    account=account
    )
cs = ctx.cursor()
try:
    cs.execute("SELECT current_version()")
    one_row = cs.fetchone()
    print(one_row[0])
finally:
    cs.close()
    ctx.close()


engine = create_engine(
    'snowflake://{user}:{password}@{account}/'.format(
        user=username,
        password=password,
        account=account,
    )
)
try:
    connection = engine.connect()
    results = connection.execute('select current_version()').fetchone()
    print(results[0])
finally:
    connection.close()
    engine.dispose()

engine = create_snowflake_engine(username, password, account, database, schema)

stmt = 'SELECT * FROM "Consents_Permit_Source"'

with engine.connect() as cs:
    cs.execute(stmt)
    df1 = cs.fetch_pandas_all()

t1 = sf.read_table(username, password, account, database, schema, 'SELECT * FROM "Consents_Permit_Source"')




ctx = snowflake.connector.connect(
    user=username,
    password=password,
    account=account,
    database=database,
    schema=schema,
#    warehouse='compute_wh'
    )
cs = ctx.cursor()
try:
    cs.execute(stmt)
    df1 = cs.fetch_pandas_all()
finally:
    cs.close()
    ctx.close()


def fetch_pandas_sqlalchemy(stmt):
    lst1 = []
    for chunk in pd.read_sql_query(stmt, engine, chunksize=50000):
        lst1.append(chunk)
    df1 = pd.concat(lst1)

    return df1




engine = create_snowflake_engine(p['username'], p['password'], p['account'], p['database'], p['schema'])

df1 = pd.read_sql_table('ConsentedAllocation', engine, 'Curated', chunksize=5000)

rv4.to_sql(name='test1', con=engine, if_exists='append', chunksize=5000, index=False)


sf.read_table(p['username'], p['password'], p['account'], p['database'], p['schema'], stmt)
















