from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from libraryaccess.forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm
from libraryaccess.models import Student, Author, Genre, Book
import csv

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
