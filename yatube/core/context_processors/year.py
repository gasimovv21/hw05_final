from datetime import datetime


def year(request):
    date = datetime.today().year
    return {
        'year': date
    }
