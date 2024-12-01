# import sqlite3
# import pandas as pd
# #
# connection = sqlite3.connect('hahahon.db')
# cursor = connection.cursor()
# #
# # cursor.execute('''
# # CREATE TABLE event_tags (
# # event_id INTEGER PRIMARY KEY,
# # event_name VARCHAR(200),
# # description VARCHAR(600),
# # date DATE,
# # time TIME,
# # place VARCHAR(300),
# # tags VARCHAR(70));
# # ''')
# # connection.commit()
# #
# # cursor.execute('''
# # CREATE TABLE user_event (
# # user_id INTEGER PRIMARY KEY,
# # event_id INTEGER,
# # tags VARCHAR(70),
# # rate INTEGER);''')
# # connection.commit()
# #
# # cursor.execute('''
# # CREATE TABLE user_tags (
# # user_id INTEGER PRIMARY KEY,
# # tags VARCHAR(70));''')
# # connection.commit()
# #
# event_tags=pd.read_excel('event_tags.xlsx')
# # user_tags=pd.read_excel('user_tags.xlsx')
# # user_event=pd.read_excel('user_event.xlsx')
# #
# event_tags.to_sql('event_tags',connection, if_exists = 'replace', index = False)
# # user_tags.to_sql('user_tags',connection, if_exists = 'replace', index = False)
# # user_event.to_sql('user_event',connection, if_exists = 'replace', index = False)
#
