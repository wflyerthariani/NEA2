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
    path('dataadd/', views.load_data, name='dataadd'),
    path('book_view/<str:isbn>/', views.book_view, name='bookDetails'),
    path('mybooks/', views.books_read_view, name='myBooks'),
    path('booksearch/', views.book_search, name='book_search'),
    path('recommend/', views.recommendation_view, name='recommend')
]
