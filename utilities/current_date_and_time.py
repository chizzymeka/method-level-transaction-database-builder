from datetime import datetime


def get_current_date_and_time():
    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    return str(current_time)
