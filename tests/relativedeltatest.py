import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


if __name__ == '__main__':

    today = date.today()
    print(today)
    this_year = today.year
    start_date = datetime.date(this_year, 1, 1)
    start_date.strftime('%Y-%m-%d')
    end_date = datetime.date(this_year, 1, 31)
    end_date.strftime('%Y-%m-%d')

    while start_date < today:
        print(start_date)
        print(end_date)

        start_date = start_date + relativedelta(months=1)
        end_date = end_date + relativedelta(months=1)
