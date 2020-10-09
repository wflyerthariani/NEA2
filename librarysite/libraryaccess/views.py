from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from libraryaccess.forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm
from libraryaccess.models import Student, Author, Genre, Book
import csv
from bs4 import BeautifulSoup
import requests
import json
from libraryaccess.get_image_from_isbn import get_imagelink
from libraryaccess.tables import BookTable

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
        form = AccountUpdateForm(initial= {"username": request.user.username, "forename": request.user.forename, "surname": request.user.surname})
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

    return render(request, 'libraryaccess/cardScan.html', context)


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

    return render(request, 'libraryaccess/cardScan.html', context)

def load_data(request):

    context = {}
    with open("libraryaccess/output_1.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            newbook, created = Book.objects.get_or_create(ISBN = row[0], title = row[1].lower(), publisher = row[4], publishDate = row[3], description = row[5], location = '576.8')
            authors = row[2].split(',')
            for author in authors:
                authorname = author.split(' ')
                newauthor, created = Author.objects.get_or_create(forename = ' '.join([authorname[i] for i in range(len(authorname)-1)]), surname = authorname[-1])
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
        table = BookTable(request.user.studentBook.all())
    else:
        return redirect("login")

    return render(request, "libraryaccess/mybooks_list.html", {
        "table": table
    })

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
        else:
            if len(Title) > 0:
                queryset = queryset.filter(title__icontains = Title)
            if len(author) > 0:
                author_names = author.split(' ')
                for name in author_names:
                    authors_forename = Author.objects.all().filter(forename__icontains = name)
                    authors_surname = Author.objects.all().filter(surname__icontains = name)
                    authors = authors_surname | authors_forename
                    queryset = queryset.filter(bookAuthor__in = authors)
            if len(genre) > 0:
                genres = genre.split(', ')
                for genre_name in genres:
                    matches = Genre.objects.all().filter(name__icontains = genre_name)
                    queryset = queryset.filter(bookGenre__in = matches)
        table = BookTable(queryset)
    else:
        queryset = Book.objects.all()
        table = BookTable(queryset)
        table.paginate(page=request.GET.get("page", 1), per_page=25)

    #if len(queryset) > 100:
        #queryset = queryset[0:100]


    context["table"] = table

    return render(request, "libraryaccess/book_search.html", context)
