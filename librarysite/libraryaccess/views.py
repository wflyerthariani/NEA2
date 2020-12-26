from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.core.mail import send_mail
from libraryaccess.forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm
from libraryaccess.models import Student, Author, Genre, Book, StudentRegister
import csv
from bs4 import BeautifulSoup
import requests
import json
from libraryaccess.get_info_from_isbn import get_imagelink, get_details
from libraryaccess.tables import BookTable, MyBookTable, StudentTable
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from libraryaccess.vectoriser import recommend_by_description, recommend_by_genre, combined_recommendation
from django_tables2 import RequestConfig
import datetime

def index(request):
    context = {}
    return render(request, 'libraryaccess/home.html', context)


def registration_view(request):
    context = {}
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(email=email, password=raw_password)
            login(request, account)
            return redirect('index')
        else:
            context['registration_form'] = form
    else:
        form = RegistrationForm()
        context['registration_form'] = form
    return render(request, 'libraryaccess/registration.html', context)


def logout_view(request):
    logout(request)
    return redirect('index')


def login_view(request):
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect('index')

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)

            if user:
                login(request, user)
                return redirect('index')
    else:
        form = AccountAuthenticationForm()

    context['login_form'] = form
    return render(request, 'libraryaccess/login.html', context)


def account_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = AccountUpdateForm(initial= {"username": request.user.username, "forename": request.user.forename, "surname": request.user.surname, "formCode": request.user.formCode, "studentID": request.user.studentID, "yearGroup": request.user.yearGroup})
    context['account_form'] = form
    return render(request, 'libraryaccess/account.html', context)


def card_addition_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    context = {'error':''}
    code = request.POST.get("cardScan", "")
    if len(code) == 8:
        if len(Student.objects.raw('SELECT * FROM libraryaccess_Student WHERE libraryaccess_Student.cardUID = %s', [code])) == 0:
            request.user.cardUID = code
            request.user.save()
            return redirect("index")
        else:
            if Student.objects.raw('SELECT * FROM libraryaccess_Student WHERE libraryaccess_Student.cardUID = %s', [code])[0].id == request.user.id:
                return redirect("index")
            else:
                context['error'] = 'Card belongs to someone else'
    elif len(code) > 0:
        context['error'] = 'Invalid Card'

    return render(request, 'libraryaccess/cardscan.html', context)


def card_login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    context = {'error':''}
    if request.POST:
        code = request.POST.get("cardScan", "")
        if len(code) == 8:
            if len(Student.objects.raw('SELECT * FROM libraryaccess_Student WHERE libraryaccess_Student.cardUID = %s', [code])) == 0:
                context['error'] = 'No account associated with this card'
            else:
                user = Student.objects.get(cardUID = code)
                login(request, user)
                return redirect("index")
        elif len(code) > 0:
            context['error'] = 'Invalid Card'

    return render(request, 'libraryaccess/cardscan.html', context)


def load_data(request):
    context = {}
    with open("libraryaccess/output_1.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            newbook, created = Book.objects.get_or_create(ISBN = row[0], title = row[1], publisher = row[4], publishDate = row[3], description = row[5], location = '576.8')
            authors = row[2].split(',')
            for author in authors:
                authorname = author.split(' ')
                newauthor, created = Author.objects.get_or_create(forename = ' '.join([authorname[i].lower().capitalize() for i in range(len(authorname)-1)]), surname = authorname[-1].lower().capitalize())
                if newauthor not in newbook.bookAuthor.all():
                    newbook.bookAuthor.add(newauthor)
                    newbook.save()
            genres = row[6].split(',')
            for genre in genres:
                newgenre, created = Genre.objects.get_or_create(name = genre)
                if newgenre not in newbook.bookGenre.all():
                    newbook.bookGenre.add(newgenre)
                    newbook.save()

    return render(request, 'libraryaccess/dataadd.html', context)


def book_view(request, isbn):
    context = {}
    book = get_object_or_404(Book, ISBN=str(isbn))

    if request.user.is_authenticated:
        context['authenticated'] = True
        if book in request.user.studentBook.all():
            context['added'] = 'added'
        else:
            if request.POST:
                if request.POST.get("added", "") == 'add':
                    request.user.studentBook.add(book)
                    context['added'] = 'added'
                else:
                    context['added'] = 'addable'
            else:
                context['added'] = 'addable'

    else:
        context['authenticated'] = False
        context['added'] = 'unaddable'

    context['title'] = book.title
    context['description'] = book.description
    context['author'] = book.all_authors
    try:
        context['imagelink'] = get_imagelink(isbn)
    except:
        context['imagelink'] = None
    context['location'] = book.location
    context['in_library'] = book.inLibrary
    context['publisher'] = book.publisher
    context['publish_year'] = book.publishDate
    context['genre'] = book.all_genres
    return render(request, 'libraryaccess/bookview.html', context)


def books_read_view(request):
    if request.user.is_authenticated:
        table = MyBookTable(request.user.studentBook.all())
    else:
        return redirect("login")

    return render(request, "libraryaccess/mybooks.html", {"table": table})


def book_search(request):
    context = {}
    if request.POST:
        isbn = request.POST.get("ISBN", "")
        Title = request.POST.get("Title", "")
        author = request.POST.get("Author", "")
        genre = request.POST.get("Genre", "")
        queryset = Book.objects.all()
        if len(isbn) > 0:
            if len(queryset.filter(ISBN = isbn)) == 1:
                return redirect('bookDetails', isbn=isbn)
            else:
                queryset = Book.objects.all()
                table = BookTable(queryset, orderable = True)
        else:
            if len(Title) > 0:
                queryset = queryset.filter(title__icontains = Title)
                table = BookTable(queryset, orderable = False)
            if len(author) > 0:
                author_names = author.split(' ')
                for name in author_names:
                    authors_forename = Author.objects.all().filter(forename__icontains = name)
                    authors_surname = Author.objects.all().filter(surname__icontains = name)
                    authors = authors_surname | authors_forename
                    queryset = queryset.filter(bookAuthor__in = authors)
                    table = BookTable(queryset, orderable = False)
            if len(genre) > 0:
                genres = genre.split(', ')
                for genre_name in genres:
                    matches = Genre.objects.all().filter(name__icontains = genre_name)
                    queryset = queryset.filter(bookGenre__in = matches)
                    table = BookTable(queryset, orderable = False)
            elif len(author) == 0 and len(Title) == 0:
                queryset = Book.objects.all()
                table = BookTable(queryset, orderable = True)
    else:
        queryset = Book.objects.all()
        table = BookTable(queryset)
        RequestConfig(request).configure(table)
        table.paginate(page=request.GET.get("page", 1), per_page=25)
    context["table"] = table
    return render(request, "libraryaccess/booksearch.html", context)


def recommendation_view(request):
    context = {}
    if not request.user.is_authenticated:
        return redirect("login")

    books_in_library = Book.objects.all().filter(inLibrary = True)
    read_books = request.user.studentBook.all()
    all_books = books_in_library | read_books
    all_isbns = [book.ISBN for book in all_books]
    all_descriptions = [book.description for book in all_books]
    all_genres = [' '.join([book.bookGenre.all()[i].name for i in range(len(book.bookGenre.all()))]) for book in all_books]
    all_titles = [book.title for book in all_books]
    read_isbns = [book.ISBN for book in read_books]
    result_isbns_description = recommend_by_description(all_descriptions, all_isbns, read_isbns, 100)
    result_isbns_genre = recommend_by_genre(all_genres, all_isbns, read_isbns, 100)
    result_isbns = combined_recommendation(result_isbns_genre, result_isbns_description, 5, all_titles, read_isbns, all_isbns)
    book_suggestions = Book.objects.filter(ISBN__in=result_isbns)
    table = BookTable(book_suggestions)
    context["table"] = table
    return render(request, "libraryaccess/recommend.html", context)


def remove_book_view(request, isbn):
    if request.user.is_authenticated:
        if request.user.studentBook.filter(ISBN = isbn):
            request.user.studentBook.filter(ISBN = isbn).delete()
        return redirect('myBooks')
    else:
        return redirect('index')


def year_group_view(request):
    context = {}
    if not request.user.is_authenticated:
        return redirect("login")

    year_group = request.user.yearGroup
    if year_group == None:
        return redirect("account")
    else:
        students = Student.objects.all().filter(yearGroup = year_group)
        books = Book.objects.all()
        numbers = [book.student_set.all().count() for book in books]
        enumerated_numbers = list(enumerate(numbers))
        sorted_numbers = sorted(enumerated_numbers, key=lambda x:x[1])
        if len(sorted_numbers) > 5:
            top_five = [item[0] for item in sorted_numbers[-5::]]
            top_five.reverse()
        else:
            top_five = [item[0] for item in sorted_numbers]
            top_five.reverse()
        queryset = []
        for index in top_five:
            queryset.append(books[index])
        table = BookTable(queryset)
        RequestConfig(request).configure(table)
        context["table"] = table
        return render(request, "libraryaccess/yeargroup.html", context)

def student_search_view(request):
    context = {}
    queryset = Student.objects.all()
    if request.POST:
        Forename = request.POST.get("Forename", "")
        Surname = request.POST.get("Surname", "")
        if len(Forename) > 0:
            queryset = queryset.filter(forename = Forename)
        if len(Surname) > 0:
            queryset = queryset.filter(surname = Surname)

    table = StudentTable(queryset)
    RequestConfig(request).configure(table)
    context["table"] = table
    return render(request, "libraryaccess/studentsearch.html", context)

def student_view(request, ID):
    context = {}
    student = get_object_or_404(Student, pk=int(ID))

    context["forename"] = (student.forename).capitalize()
    context["surname"] = (student.surname).capitalize()

    if student.book_share == True:
        queryset = student.studentBook.all()
    else:
        queryset = []
    table = BookTable(queryset)
    RequestConfig(request).configure(table)
    context["table"] = table
    return render(request, "libraryaccess/studentview.html", context)

def add_new_book_view(request):
    context = {"error":''}
    if request.POST:
        isbn = request.POST.get("ISBN", "")
        try:
            Title, Authors, publishedDate, Description, Genres = get_details(str(isbn))
        except:
            context["error"] = 'Book Details Not Found'
            return render(request, "libraryaccess/bookadd.html", context)
        if isbn in Book.objects.values_list('ISBN', flat=True):
            context["error"] = 'Book already in library'
            return render(request, "libraryaccess/bookadd.html", context)
        newbook, created = Book.objects.get_or_create(ISBN = isbn, publishDate = int(publishedDate), title = Title, description = Description, inLibrary = False)
        for author in Authors:
            authorname = author.split(' ')
            newauthor, created = Author.objects.get_or_create(forename = ' '.join([authorname[i].lower().capitalize() for i in range(len(authorname)-1)]), surname = authorname[-1].lower().capitalize())
            newbook.bookAuthor.add(newauthor)
            newbook.save()
        for genre in Genres:
            newgenre, created = Genre.objects.get_or_create(name = genre)
            newbook.bookGenre.add(newgenre)
            newbook.save()
        return redirect('index')
    else:
        return render(request, "libraryaccess/bookadd.html", context)

def confirm_register_view(request):
    context = {"error":''}
    if request.POST:
        valid = False
        password = request.POST.get("password", '')
        comparisons = Student.objects.all().filter(is_admin = True)
        for comparison in comparisons.values_list('password', flat=True):
            if check_password(password, comparison):
                valid = True
        if valid:
            request.session['valid_register'] = True
            return redirect("libraryRegister")
        else:
            context["error"] = 'Not valid password'
            request.session['valid_register'] = False
    return render(request, "libraryaccess/confirmreg.html", context)

def register_view(request):
    if 'valid_register' in request.session:
        if request.session['valid_register']:
            logout(request)
            request.session['valid_register'] = True
            context = {'error':''}
            if request.POST:
                form = AccountAuthenticationForm()
                code = request.POST.get("cardScan", "")
                if len(code) <= 0:
                    email = request.POST['email']
                    password = request.POST['password']
                    user = authenticate(email=email, password=password)

                    if user:
                        start_date = timezone.now().date()
                        end_date = start_date + datetime.timedelta(days=1)
                        user_registers = StudentRegister.objects.all().filter(signinTime__range=(start_date, end_date))
                        if len(user_registers) == 0:
                            new_register = StudentRegister(ID=user, signinTime=timezone.now(), signoutTime=None)
                            new_register.save()
                            context['error'] = (user.forename.capitalize()+' has been signed in.')
                        else:
                            latest_register = user_registers.latest('signinTime')
                            if latest_register.signoutTime == None:
                                latest_register.signoutTime = timezone.now()
                                latest_register.save()
                                context['error'] = (user.forename.capitalize()+' has been signed out.')
                            else:
                                new_register = StudentRegister(ID=user, signinTime=timezone.now(), signoutTime=None)
                                new_register.save()
                                context['error'] = (user.forename.capitalize()+' has been signed in.')
                    else:
                        context['error'] = 'Invalid login'

                else:
                    if len(code) == 8:
                        if len(Student.objects.raw('SELECT * FROM libraryaccess_Student WHERE libraryaccess_Student.cardUID = %s', [code])) == 0:
                            context['error'] = 'No account associated with this card'
                        else:
                            user = Student.objects.get(cardUID = code)
                            start_date = timezone.now().date()
                            end_date = start_date + datetime.timedelta(days=1)
                            user_registers = StudentRegister.objects.all().filter(signinTime__range=(start_date, end_date)).filter(ID=user)
                            if len(user_registers) == 0:
                                new_register = StudentRegister(ID=user, signinTime=timezone.now(), signoutTime=None)
                                new_register.save()
                                context['error'] = (user.forename.capitalize()+' has been signed in.')
                            else:
                                latest_register = user_registers.latest('signinTime')
                                if latest_register.signoutTime == None:
                                    latest_register.signoutTime = timezone.now()
                                    latest_register.save()
                                    context['error'] = (user.forename.capitalize()+' has been signed out.')
                                else:
                                    new_register = StudentRegister(ID=user, signinTime=timezone.now(), signoutTime=None)
                                    new_register.save()
                                    context['error'] = (user.forename.capitalize()+' has been signed in.')

                    elif len(code) > 0:
                        context['error'] = 'Invalid Card'
                    else:
                        context['error'] = 'User not found, try again'

            else:
                form = AccountAuthenticationForm()

            context['login_form'] = form
            return render(request, 'libraryaccess/register.html', context)
    return redirect('confirm_register')

def close_register(request):
    request.session['valid_register'] = False
    return redirect('index')

@user_passes_test(lambda u: u.is_admin)
def mail_register(request):
    start_date = timezone.now().date()
    end_date = start_date + datetime.timedelta(days=1)
    queryset = StudentRegister.objects.all().filter(signinTime__range=(start_date, end_date))
    names = queryset.values_list('ID__surname', 'ID__forename')
    names = '\n'.join([j.capitalize()+' '+i.capitalize() for (i, j) in names])
    send_mail('Library Register', 'The following students have been registered today:\n'+names, None, ['wflyerthariani@gmail.com'])
    return redirect('index')
