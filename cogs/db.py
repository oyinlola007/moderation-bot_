import sqlite3

import cogs.config as config

conn = sqlite3.connect(config.DATABASE_NAME)

def initializeDB():
    conn.execute('''CREATE TABLE IF NOT EXISTS MUTED_USERS
                 (DISCORD_ID TEXT,
                 MODERATOR TEXT,
                 START_TIME TEXT,
                 END_TIME TEXT,
                 RULES_BROKEN TEXT,
                 SEVERITY TEXT,
                 PROOF TEXT,
                 ON_MUTE TEXT);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS SEVERITY_TABLE
                 (DISCORD_ID TEXT PRIMARY KEY NOT NULL,
                 SEVERITY TEXT,
                 EXPIRED_SEVERITY TEXT,
                 CHECKPOINT TEXT);''')
    #Checkpoints notes the last time the user severity was reduced,
    # it's checked at intervals and reset to 0 when the elapsed is up to two weeks

    conn.execute('''CREATE TABLE IF NOT EXISTS BANNED_USERS
                 (DISCORD_ID TEXT PRIMARY KEY NOT NULL,
                 MODERATOR TEXT,
                 TIME_STAMP TEXT);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS REMOVED_INDEFINITE_MUTE
                 (DISCORD_ID TEXT PRIMARY KEY NOT NULL,
                 MODERATOR TEXT,
                 TIME_STAMP TEXT);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS INDEFINITE_MUTE
                 (DISCORD_ID TEXT PRIMARY KEY NOT NULL,
                 SEVERITY TEXT,
                 PROOF TEXT);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS REPORTS
                 (REPORTER TEXT,
                 REPORTED TEXT,
                 REASON TEXT,
                 MODERATOR TEXT,
                 TIME_STAMP TEXT);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS VARIABLES
                 (ID TEXT PRIMARY KEY NOT NULL,
                 VALUE TEXT);''')

    try:
        insert_variable("SEVERITY_EXPIRE_DURATION", "14")
        insert_variable("MOD_LOGS_CHANNEL", "928825472207446056")
        insert_variable("BAN_REVIEW_CHANNEL", "928825680890826802")
        insert_variable("REPORTS_CHANNEL", "928825721600753734")
        insert_variable("SEVERITY_LIMIT", "10")
        insert_variable("ADMIN_ROLE", "Admin")
        insert_variable("MOD_ROLE", "Mod Perms")
        insert_variable("SEVERITY_1", "15")
        insert_variable("SEVERITY_2", "120")
        insert_variable("SEVERITY_3", "1440")
        insert_variable("SEVERITY_4", "4320")
        insert_variable("SEVERITY_5", "10080")
        insert_variable("RULE_1", "RULE_1")
        insert_variable("RULE_2", "RULE_2")
        insert_variable("RULE_3", "RULE_3")
        insert_variable("RULE_4", "RULE_4")
        insert_variable("RULE_5", "RULE_5")
        insert_variable("RULE_6", "RULE_6")
        insert_variable("RULE_7", "RULE_7")
        insert_variable("RULE_8", "RULE_8")
        insert_variable("RULE_9", "RULE_9")
        insert_variable("RULE_10", "RULE_10")
        insert_variable("RULE_11", "RULE_11")
        insert_variable("RULE_12", "RULE_12")
        insert_variable("RULE_13", "RULE_13")
        insert_variable("RULE_14", "RULE_14")
        insert_variable("RULE_15", "RULE_15")
        insert_variable("RULE_16", "RULE_16")
        insert_variable("RULE_17", "RULE_17")
        insert_variable("RULE_18", "RULE_18")
        insert_variable("HOURLY_RATE_LIMIT", "5")
    except:
        pass

    conn.commit()

def get_variable(id):
    return conn.execute(f"SELECT VALUE FROM VARIABLES WHERE ID='{id}'").fetchone()[0]

def update_variable(id, value):
    conn.execute(f"UPDATE VARIABLES SET VALUE='{value}' WHERE ID='{id}'")
    conn.commit()

def get_severity_expire_duration():
    return int(get_variable("SEVERITY_EXPIRE_DURATION"))

def get_mod_logs_channel():
    return int(get_variable("MOD_LOGS_CHANNEL"))

def get_ban_review_channel():
    return int(get_variable("BAN_REVIEW_CHANNEL"))

def get_reports_channel():
    return int(get_variable("REPORTS_CHANNEL"))

def get_severity_limit():
    return int(get_variable("SEVERITY_LIMIT"))

def get_admin_role():
    return get_variable("ADMIN_ROLE")

def get_mod_role():
    return get_variable("MOD_ROLE")

def get_severity(severity):
    return int(get_variable(f"SEVERITY_{severity}"))

def get_rule(rule):
    return get_variable(f"RULE_{rule}")

def get_variables():
    return conn.execute("SELECT * FROM VARIABLES")

def get_mod_hourly_rate_limit():
    return int(get_variable("HOURLY_RATE_LIMIT"))

def count_mod_muted(moderator_id, duration):
    return conn.execute(f"SELECT COUNT(MODERATOR) FROM MUTED_USERS WHERE MODERATOR='{moderator_id}' AND START_TIME > datetime('now', '-{duration}')").fetchone()[0]

def count_mod_reports(moderator_id, duration):
    return conn.execute(f"SELECT COUNT(MODERATOR) FROM REPORTS WHERE MODERATOR='{moderator_id}' AND TIME_STAMP > datetime('now', '-{duration}')").fetchone()[0]

def count_mod_removed_indefinite_mute(moderator_id, duration):
    return conn.execute(f"SELECT COUNT(MODERATOR) FROM REMOVED_INDEFINITE_MUTE WHERE MODERATOR='{moderator_id}' AND TIME_STAMP > datetime('now', '-{duration}')").fetchone()[0]

def count_mod_banned(moderator_id, duration):
    return conn.execute(f"SELECT COUNT(MODERATOR) FROM BANNED_USERS WHERE MODERATOR='{moderator_id}' AND TIME_STAMP > datetime('now', '-{duration}')").fetchone()[0]

def count_mod_actions_last_hour(moderator_id):
    return count_mod_muted(moderator_id, "1 hour") + count_mod_reports(moderator_id, "1 hour") + count_mod_removed_indefinite_mute(moderator_id, "1 hour") + count_mod_banned(moderator_id, "1 hour")

def insert_muted_user(discord_id, moderator_id, start_time, end_time, rules_broken, severity, proof):
    sqlite_insert_with_param = """INSERT INTO 'MUTED_USERS'
    ('DISCORD_ID', 'MODERATOR', 'START_TIME', 'END_TIME', 'RULES_BROKEN', 'SEVERITY', 'PROOF', 'ON_MUTE')
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
    data_tuple = (discord_id, moderator_id, start_time, end_time, rules_broken, severity, proof, "1")
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def insert_severity(discord_id, severity, expired_severity, checkpoint):
    sqlite_insert_with_param = """INSERT INTO 'SEVERITY_TABLE'
    ('DISCORD_ID', 'SEVERITY', 'EXPIRED_SEVERITY', 'CHECKPOINT')
    VALUES (?, ?, ?, ?);"""
    data_tuple = (discord_id, severity, expired_severity, checkpoint)
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def insert_banned(discord_id, moderator, time_stamp):
    sqlite_insert_with_param = """INSERT INTO 'BANNED_USERS'
    ('DISCORD_ID', 'MODERATOR', 'TIME_STAMP')
    VALUES (?, ?, ?);"""
    data_tuple = (discord_id, moderator, time_stamp)
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def insert_indefinite_muted(discord_id, severity, proof):
    sqlite_insert_with_param = """INSERT INTO 'INDEFINITE_MUTE'
    ('DISCORD_ID', 'SEVERITY', 'PROOF')
    VALUES (?, ?, ?);"""
    data_tuple = (discord_id, severity, proof)
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def insert_report(reporter, reported, reason, moderator, time_stamp):
    sqlite_insert_with_param = """INSERT INTO 'REPORTS'
    ('REPORTER', 'REPORTED', 'REASON', 'MODERATOR', 'TIME_STAMP')
    VALUES (?, ?, ?, ?, ?);"""
    data_tuple = (reporter, reported, reason, moderator, time_stamp)
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def insert_removed_indefinite_mute(discord_id, moderator, time_stamp):
    sqlite_insert_with_param = """INSERT INTO 'REMOVED_INDEFINITE_MUTE'
    ('DISCORD_ID', 'MODERATOR', 'TIME_STAMP')
    VALUES (?, ?, ?);"""
    data_tuple = (discord_id, moderator, time_stamp)
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def insert_variable(id, value):
    sqlite_insert_with_param = """INSERT INTO 'VARIABLES'
    ('ID', 'VALUE')
    VALUES (?, ?);"""
    data_tuple = (id, value)
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def get_severity_from_severity_table(discord_id):
    return conn.execute(f"SELECT SEVERITY FROM SEVERITY_TABLE WHERE DISCORD_ID='{discord_id}'").fetchone()[0]

def get_all_severity():
    return conn.execute(f"SELECT * FROM SEVERITY_TABLE")

def update_severity_table(discord_id, severity, expired_severity, checkpoint):
    conn.execute(f"UPDATE SEVERITY_TABLE SET SEVERITY='{severity}', EXPIRED_SEVERITY='{expired_severity}', CHECKPOINT='{checkpoint}' WHERE DISCORD_ID='{discord_id}'")
    conn.commit()

def get_severity_table(discord_id):
    return conn.execute(f"SELECT * FROM SEVERITY_TABLE WHERE DISCORD_ID='{discord_id}'").fetchone()

def update_severity_point(discord_id, severity):
    conn.execute(f"UPDATE SEVERITY_TABLE SET SEVERITY='{severity}' WHERE DISCORD_ID='{discord_id}'")
    conn.commit()

def delete_from_indefinite_mute(discord_id):
    conn.execute(f"DELETE FROM INDEFINITE_MUTE WHERE DISCORD_ID='{discord_id}'")
    conn.commit()

def get_active_muted_users():
    return conn.execute("SELECT * FROM MUTED_USERS WHERE ON_MUTE='1'")

def get_all_indefinite_muted():
    return conn.execute("SELECT * FROM INDEFINITE_MUTE")

def get_active_muted_user(discord_id):
    return conn.execute(f"SELECT * FROM MUTED_USERS WHERE DISCORD_ID='{discord_id}' AND ON_MUTE='1'").fetchone()

def update_end_time(discord_id, end_time):
    conn.execute(f"UPDATE MUTED_USERS SET END_TIME='{end_time}' WHERE DISCORD_ID='{discord_id}'")
    conn.commit()

def update_muted_status(discord_id):
    conn.execute(f"UPDATE MUTED_USERS SET ON_MUTE='0' WHERE DISCORD_ID='{discord_id}'")
    conn.commit()

