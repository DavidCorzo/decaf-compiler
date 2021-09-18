from datetime import datetime, date, time, timedelta

d0 = date(2000, 2, 8)
d1 = date(2021, 9, 18)
day_hash = str((d1 - d0).days).zfill(5)
time_hash = str(timedelta(hours=23, minutes=59, seconds=59).seconds).zfill(5)


print(day_hash + time_hash)
