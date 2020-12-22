from django.urls import path
from django.contrib.auth import views as auth_views
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
    path('bookview/<str:isbn>/', views.book_view, name='bookDetails'),
    path('mybooks/', views.books_read_view, name='myBooks'),
    path('booksearch/', views.book_search, name='bookSearch'),
    path('recommend/', views.recommendation_view, name='recommend'),
    path('removebook/<str:isbn>/', views.remove_book_view, name='removeBook'),
    path('yeargroup/', views.year_group_view, name='yearGroup'),
    path('studentview/<str:ID>/', views.student_view, name='studentView'),
    path('studentsearch/', views.student_search_view, name='studentSearch'),
    path('bookadd/', views.add_new_book_view, name='bookadd'),
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name = "reset_password.html"), name ='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name = "password_reset_sent.html"), name ='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name = "password_reset_form.html"), name ='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name = "password_reset_done.html"), name ='password_reset_complete'),
    path('confirmreg/', views.confirm_register_view, name='confirm_register'),
]
