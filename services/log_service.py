from database.db import get_connection

def log_activity(user_id, aktivitas):
    db = get_connection()
    c = db.cursor()
    c.execute("""INSERT INTO log_aktivitas_user (user_id, aktivitas)
                 VALUES (%s,%s)""",(user_id, aktivitas))
    db.commit()
