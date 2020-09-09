from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.registration_view, name='registration'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('account/', views.account_view, name='account'),
    path('mycard/', views.card_addition_view, name='cardAddition'),
    path('cardlogin/', views.card_login_view, name='cardLogin'),
    #path('dataadd/', views.load_data, name='dataadd'),#
]
