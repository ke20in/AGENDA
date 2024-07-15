from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.views import generic
from django.utils.safestring import mark_safe
from datetime import datetime, date, timedelta
from django.db.models import Q
from .models import Activite
from .utils import Calendrier
from .forms import ActiviteForm
import calendar
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils.encoding import smart_str
from django.utils.formats import date_format
import os
import mimetypes
from django.utils import translation
from django.utils import timezone
import random




class CalendrierView(generic.ListView):
    model = Activite
    template_name = 'calendrier/calendrier.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        d = self.get_date(self.request.GET.get('month', None))
        cal = Calendrier(year=d.year, month=d.month)
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = self.prev_month(d)
        context['next_month'] = self.next_month(d)
        return context

    def get_date(self, req_month):
        if req_month:
            year, month = (int(x) for x in req_month.split('-'))
            return date(year, month, day=1)
        return date.today()

    def prev_month(self, d):
        first = d.replace(day=1)
        prev_month = first - timedelta(days=1)
        month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
        return month

    def next_month(self, d):
        days_in_month = calendar.monthrange(d.year, d.month)[1]
        last = d.replace(day=days_in_month)
        next_month = last + timedelta(days=1)
        month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
        return month


def ajouter_activite(request):
    if request.method == 'POST':
        form = ActiviteForm(request.POST)
        if form.is_valid():
            activite = form.save()
            return redirect('calendrier')
    else:
        form = ActiviteForm()
    return render(request, 'calendrier/ajouter_activite.html', {'form': form})


def verifier_conflit(request):
    creneaux_disponibles = []
    conflits = []
    date_recherche = request.GET.get('date_recherche')
    heure_recherche = request.GET.get('heure_recherche')
    duree = int(request.GET.get('duree', 60))  # Durée en minutes, par défaut 60

    if date_recherche and heure_recherche:
        date_heure_debut = timezone.make_aware(
            datetime.strptime(f"{date_recherche} {heure_recherche}", "%Y-%m-%d %H:%M"))
        date_heure_fin = date_heure_debut + timedelta(minutes=duree)

        # Vérifier les conflits
        activites_en_conflit = Activite.objects.filter(
            Q(date_debut__lt=date_heure_fin, date_fin__gt=date_heure_debut)
        ).order_by('date_debut')

        if activites_en_conflit.exists():
            conflits = list(activites_en_conflit)

        # Trouver des créneaux disponibles
        creneaux_disponibles = trouver_creneaux_libres(date_heure_debut.date(), duree, activites_en_conflit)

    context = {
        'creneaux_disponibles': creneaux_disponibles[:10],  # Limiter à 10 créneaux
        'conflits': conflits,
        'date_recherche': date_recherche,
        'heure_recherche': heure_recherche,
        'duree': duree
    }
    return render(request, 'calendrier/conflits.html', context)


def trouver_creneaux_libres(date, duree_minutes, activites_en_conflit):
    creneaux_disponibles = []
    debut_jour = timezone.make_aware(datetime.combine(date, datetime.min.time())).replace(hour=8, minute=0)
    fin_jour = debut_jour.replace(hour=18, minute=0)

    toutes_activites = Activite.objects.filter(
        date_debut__date=date
    ).order_by('date_debut')

    plages_occupees = [(a.date_debut, a.date_fin) for a in toutes_activites]
    plages_occupees.sort(key=lambda x: x[0])

    plages_libres = []
    heure_actuelle = debut_jour

    for debut, fin in plages_occupees:
        if heure_actuelle < debut:
            plages_libres.append((heure_actuelle, debut))
        heure_actuelle = max(heure_actuelle, fin)

    if heure_actuelle < fin_jour:
        plages_libres.append((heure_actuelle, fin_jour))

    for debut, fin in plages_libres:
        while debut + timedelta(minutes=duree_minutes) <= fin:
            if debut >= debut_jour and debut + timedelta(minutes=duree_minutes) <= fin_jour:
                creneaux_disponibles.append((debut, debut + timedelta(minutes=duree_minutes)))
            debut += timedelta(minutes=30)

    return creneaux_disponibles

def liste_activites(request):
    today = timezone.now().date()
    activites_list = Activite.objects.all()

    # Recherche
    search_query = request.GET.get('search')
    if search_query:
        activites_list = activites_list.filter(
            Q(activite__icontains=search_query) |
            Q(object__icontains=search_query)
        )

    # Filtrage par date
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    if date_debut:
        activites_list = activites_list.filter(date_debut__gte=date_debut)
    if date_fin:
        activites_list = activites_list.filter(date_fin__lte=date_fin)

    # Tri
    activites_list = activites_list.order_by('-date_debut')

    # Vérifier les conflits
    for activite in activites_list:
        conflits = Activite.objects.filter(
            Q(date_debut__lt=activite.date_fin, date_fin__gt=activite.date_debut)
        ).exclude(id=activite.id)
        activite.conflit = conflits.exists()

    paginator = Paginator(activites_list, 10)  # 10 activités par page
    page = request.GET.get('page')
    activites = paginator.get_page(page)

    context = {
        'activites': activites,
        'today': today,
        'search_query': search_query,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    return render(request, 'calendrier/liste_activites.html', context)

# modifier et suprimer du tableau

def modifier_activite(request, activite_id):
    activite = get_object_or_404(Activite, pk=activite_id)

    # Vérifier si l'activité est dans le futur
    if activite.date_debut.date() < timezone.now().date():
        return redirect('liste_activites')  # Rediriger si l'activité est dans le passé

    if request.method == 'POST':
        form = ActiviteForm(request.POST, instance=activite)
        if form.is_valid():
            form.save()
            return redirect('liste_activites')
    else:
        form = ActiviteForm(instance=activite)

    return render(request, 'calendrier/modifier_activite.html', {'form': form, 'activite': activite})


def supprimer_activite(request, activite_id):
    activite = get_object_or_404(Activite, pk=activite_id)
    if activite.date_debut.date() >= timezone.now().date():
        activite.delete()
    return redirect('liste_activites')

# transformer en pdf
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(smart_str(html).encode("UTF-8")), result, encoding='UTF-8')
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@translation.override('fr')
def event_detail(request, event_id):
    activite = get_object_or_404(Activite, pk=event_id)
    activite.date_debut_formatted = date_format(activite.date_debut, format="l j F Y à H:i", use_l10n=True)
    activite.date_fin_formatted = date_format(activite.date_fin, format="l j F Y à H:i", use_l10n=True)

    if request.GET.get('pdf'):
        pdf = render_to_pdf('calendrier/event_detail_pdf.html', {'activite': activite})
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"activite_{activite.id}.pdf"
            content = f"inline; filename='{filename}'"
            download = request.GET.get("download")
            if download:
                content = f"attachment; filename='{filename}'"
            response['Content-Disposition'] = content
            return response

    if request.GET.get('voir_document') and activite.document:
        chemin_fichier = activite.document.path
        if os.path.exists(chemin_fichier):
            type_fichier, encoding = mimetypes.guess_type(chemin_fichier)
            if type_fichier is None:
                type_fichier = 'application/octet-stream'

            try:
                response = FileResponse(open(chemin_fichier, 'rb'), content_type=type_fichier)
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(chemin_fichier)}"'
                return response
            except IOError:
                return HttpResponse("Erreur lors de l'ouverture du fichier", status=404)

    context = {
        'activite': activite,
    }
    return render(request, 'calendrier/event_detail.html', context)
