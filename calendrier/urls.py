from django.urls import path
from . import views
from .views import liste_activites

urlpatterns = [
    path('', views.CalendrierView.as_view(), name='calendrier'),
    path('ajouter/', views.ajouter_activite, name='ajouter_activite'),
    path('conflits/', views.verifier_conflit, name='verifier_conflit'),
    path('activites/', liste_activites, name='liste_activites'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('activite/modifier/<int:activite_id>/', views.modifier_activite, name='modifier_activite'),
    path('activite/supprimer/<int:activite_id>/', views.supprimer_activite, name='supprimer_activite'),
]