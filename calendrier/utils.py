from calendar import HTMLCalendar
from .models import Activite
from datetime import date, datetime
from django.db.models import Q
from django.urls import reverse


class Calendrier(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        self.today = date.today()
        self.colors = {
            'past': '#FFF3E0',
            'today': '#FFB74D',
            'future': '#E8F5E9',
            'conflict': '#FFCDD2'
        }
        super(Calendrier, self).__init__()

    def formatday(self, day, weekday, activites):
        if day != 0:
            current_date = date(self.year, self.month, day)
            activites_par_jour = activites.filter(date_debut__date=current_date)
            d = ''
            cell_style = ''

            for activite in activites_par_jour:
                conflits = activites.filter(
                    Q(date_debut__lt=activite.date_fin, date_fin__gt=activite.date_debut)
                ).exclude(id=activite.id)

                if conflits.exists():
                    d += f'<li style="color: #D32F2F;"><a href="{reverse("event_detail", args=[activite.id])}">{activite.activite} ({activite.date_debut.strftime("%H:%M")} - {activite.date_fin.strftime("%H:%M")})</a></li>'
                    cell_style = f'style="background-color: {self.colors["conflict"]};"'
                else:
                    d += f'<li><a href="{reverse("event_detail", args=[activite.id])}">{activite.activite} ({activite.date_debut.strftime("%H:%M")} - {activite.date_fin.strftime("%H:%M")})</a></li>'

                    if current_date < self.today:
                        cell_style = f'style="background-color: {self.colors["past"]};"'
                    elif current_date == self.today:
                        cell_style = f'style="background-color: {self.colors["today"]};"'
                    else:
                        cell_style = f'style="background-color: {self.colors["future"]};"'

            if d:
                return f"<td {cell_style}><span class='date'>{day}</span><ul>{d}</ul></td>"
            return f"<td><span class='date'>{day}</span></td>"
        return '<td></td>'

    # ... le reste de la classe reste inchangé

    def formatweek(self, theweek, activites):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, weekday, activites)
        return f'<tr> {week} </tr>'

    def formatmonth(self, withyear=True):
        activites = Activite.objects.filter(date_debut__year=self.year, date_debut__month=self.month)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, activites)}\n'
        return cal