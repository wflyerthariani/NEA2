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

#View defines how to render the home page
def index(request):
    #Nothing needs to be passed to the page
    context = {}
    #The html file is rendered with the user's request and the context to be passed
    return render(request, 'libraryaccess/home.html', context)

#View for the sign-up page
def registration_view(request):
    #Context will contain the form defined in the forms file as well as errors
    context = {}
    #Check for POST request to ensure it is only processed when a form is submit
    if request.POST:
        #Gets the required form from the forms file
        form = RegistrationForm(request.POST)
        #Only processes data if the form is valid
        if form.is_valid():
            #Saves the changes to the database
            form.save()
            #Logs in the user after they register using Django's built-in func
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(email=email, password=raw_password)
            login(request, account)
            #Redirects the user to the home page
            return redirect('index')
        #If a post request is not received, the form will be passed to the page
        else:
            context['registration_form'] = form
    else:
        form = RegistrationForm()
        context['registration_form'] = form
    return render(request, 'libraryaccess/registration.html', context)

#View for logging-out
def logout_view(request):
    #Logs out the user's session and redirects to the home page with no rendering
    logout(request)
    return redirect('index')

#View for the login page
def login_view(request):
    #Context will include the login form as well as errors
    context = {}
    #If the user is already logged in, they will be redirected to the home page
    user = request.user
    if user.is_authenticated:
        return redirect('index')
    #If the user is not logged in the post request will indicate form submission
    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        #Determines validity of form and logs user in similar to sign-up
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)
            #If a user exists with the given credentials
            if user:
                login(request, user)
                return redirect('index')
    else:
        form = AccountAuthenticationForm()
    #Passes the login form to the page via context
    context['login_form'] = form
    return render(request, 'libraryaccess/login.html', context)

#View to see details of account and make changes
def account_view(request):
    #Redirects if no user is logged in
    if not request.user.is_authenticated:
        return redirect("login")
    #Passes and saves a form similar to above
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
    else:
        #Additional parameters used to set initial values in form fields
        form = AccountUpdateForm(initial= {"username": request.user.username, "forename": request.user.forename, "surname": request.user.surname, "formCode": request.user.formCode, "studentID": request.user.studentID, "yearGroup": request.user.yearGroup})
    context['account_form'] = form
    return render(request, 'libraryaccess/account.html', context)

#View to add or update a card
def card_addition_view(request):
    #Redirects user if they are not logged in
    if not request.user.is_authenticated:
        return redirect("login")
    #Gives the context an error field if card is already in use or invalid
    context = {'error':''}
    #Gets the card scan from the form defined in the html file
    code = request.POST.get("cardScan", "")
    #Chacks the length of the card matches the school's standard
    if len(code) == 8:
        #Check if nobody has the card assigned to them before assigning it
        if len(Student.objects.all().filter(cardUID=code)) == 0:
            request.user.cardUID = code
            request.user.save()
            return redirect("index")
        #If the user inputs the existing card it redirects to the home page
        else:
            if Student.objects.get(cardUID=code).id == request.user.id:
                return redirect("index")
            #If the card value matches another person, an error message is displayed
            else:
                context['error'] = 'Card belongs to someone else'
    elif len(code) > 0:
        #If the card is not the correct type, it returns an error message
        context['error'] = 'Invalid Card'
    #context containing errors is passed to display them on the page
    return render(request, 'libraryaccess/cardscan.html', context)

#View for logging in with a card
def card_login_view(request):
    #Redirect if user is already logged in
    if request.user.is_authenticated:
        return redirect("index")
    #Similar to above, errors are passed through context
    context = {'error':''}
    if request.POST:
        code = request.POST.get("cardScan", "")
        #Checks if the card exists in the database and returns relevant error
        if len(code) == 8:
            if len(Student.objects.all().filter(cardUID=code)) == 0:
                context['error'] = 'No account associated with this card'
            #If it matches a user, the user is logged in as before
            else:
                user = Student.objects.get(cardUID = code)
                login(request, user)
                return redirect("index")
        elif len(code) > 0:
            context['error'] = 'Invalid Card'

    return render(request, 'libraryaccess/cardscan.html', context)

#View to see the book details
def book_view(request, isbn):
    context = {}
    #Attempts to get book from isbn in url
    #If object is not found a 404 error is returned
    book = get_object_or_404(Book, ISBN=str(isbn))
    #If the user is logged in they have the option to add the book to their list
    #If the user has already added it, the 'added' value changes to prevent readding
    #If the 'added' value is 'added' then the button will be deactivated
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

    #Passes in all book information as separate values in context dictionary
    #Attempts to get the image from the function in get_info_from_isbn file
    context['title'] = book.title
    context['description'] = book.description
    context['author'] = book.all_authors
    #If the image is not be found using the google books api, a None value is used
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

#View for user to see books that they have added
def books_read_view(request):
    #If user is logged in their books are passed into a table
    #Tables are defined in tables file and passed via context to be rendered
    if request.user.is_authenticated:
        table = MyBookTable(request.user.studentBook.all())
    else:
        return redirect("login")

    return render(request, "libraryaccess/mybooks.html", {"table": table})

#View to search for a book
def book_search(request):
    context = {}
    #If the user submits a search the following will be carried out
    if request.POST:
        #Attempts to get all search fields from the html form
        isbn = request.POST.get("ISBN", "")
        Title = request.POST.get("Title", "")
        author = request.POST.get("Author", "")
        genre = request.POST.get("Genre", "")
        queryset = Book.objects.all()
        #Checks if each field has an input to filter by
        #ISBN field redirects to the book view if it exists
        if len(isbn) > 0:
            if len(queryset.filter(ISBN = isbn)) == 1:
                return redirect('bookDetails', isbn=isbn)
            else:
                queryset = Book.objects.all()
                table = BookTable(queryset, orderable = True)
        #Other fields filter the queryset to obtain only desired data
        else:
            #If title has been used, searches for all titles containing term
            #__icontains checks if title contains term instead of being the same
            if len(Title) > 0:
                queryset = queryset.filter(title__icontains = Title)
                table = BookTable(queryset, orderable = False)
            #If authors are input then it has to check both forename and surname
            if len(author) > 0:
                author_names = author.split(' ')
                for name in author_names:
                    authors_forename = Author.objects.all().filter(forename__icontains = name)
                    authors_surname = Author.objects.all().filter(surname__icontains = name)
                    #Joins both querysets
                    authors = authors_surname | authors_forename
                    queryset = queryset.filter(bookAuthor__in = authors)
                    table = BookTable(queryset, orderable = False)
            #For genres, students can search multiple Genres
            if len(genre) > 0:
                #Splits input by comma to allow multiple genres to be searched for
                genres = genre.split(', ')
                for genre_name in genres:
                    #Identifies distinct objects that match the search
                    matches = Genre.objects.all().filter(name__icontains = genre_name)
                    queryset = queryset.filter(bookGenre__in = matches)
                    table = BookTable(queryset.distinct(), orderable = False)
    #If no search was made then it returns the entire list of books
            elif len(author) == 0 and len(Title) == 0:
                queryset = Book.objects.all()
                table = BookTable(queryset, orderable = True)
    else:
        queryset = Book.objects.all()
        table = BookTable(queryset)
        RequestConfig(request).configure(table)
        #Allows the user to browse the table in a paginated form
        table.paginate(page=request.GET.get("page", 1), per_page=25)
    context["table"] = table
    return render(request, "libraryaccess/booksearch.html", context)

#View for seeing a students recommendations
def recommendation_view2(request):
    #Requires user to be logged in otherwise user is redirected to login page
    context = {}
    if not request.user.is_authenticated:
        return redirect("login")
    #The books read by the student are obtained as objects
    read_books = request.user.studentBook.all()
    #The books not in the library are not stored in the csv
    #This means all these books must have each attribute as a list
    not_in_lib = request.user.studentBook.all().filter(inLibrary = False)
    not_in_lib_isbns = list(not_in_lib.values_list('ISBN', flat=True))
    not_in_lib_descriptions = list(not_in_lib.values_list('description', flat=True))
    not_in_lib_genres = [' '.join([book.bookGenre.all()[i].name for i in range(len(book.bookGenre.all()))]) for book in not_in_lib]
    not_in_lib_titles = list(not_in_lib.values_list('title', flat=True))
    #The respective isbns are used to pass into the recommendation algorithm
    read_isbns = list(read_books.values_list('ISBN', flat=True))
    #The data for each book in the library is retrieved from the csv for speed
    with open('libraryaccess/recommendation_info.csv') as reading_info:
        csv_reader = csv.reader(reading_info, delimiter=',')
        #Each line in the csv is a different attribute's list
        for i, l in enumerate(csv_reader):
            if i == 0:
                isbns = l
            elif i == 1:
                descriptions = l
            elif i == 2:
                titles = l
            else:
                genres = l
    #All the lists are joined to be processed simultaneously
    all_isbns = isbns+not_in_lib_isbns
    all_descriptions = descriptions+not_in_lib_descriptions
    all_genres = genres+not_in_lib_genres
    all_titles = titles+not_in_lib_titles
    #The values are passed into the two recommendation algorithms
    result_isbns_description = recommend_by_description(all_descriptions, all_isbns, read_isbns, 100)
    result_isbns_genre = recommend_by_genre(all_genres, all_isbns, read_isbns, 100)
    #The result of the algorithms are joined to obtain the best matches
    result_isbns = combined_recommendation(result_isbns_genre, result_isbns_description, 5, all_titles, read_isbns, all_isbns)
    #The respective book objects are fetched using their isbn number
    book_suggestions = Book.objects.filter(ISBN__in=result_isbns)
    #The books are passed into a table
    table = BookTable(book_suggestions)
    context["table"] = table
    return render(request, "libraryaccess/recommend.html", context)

#View to remove a book from the reading list
#Function takes in isbn as an argument passed in the url
def remove_book_view(request, isbn):
    #If the user is authenticated and have the book in their list, it is removed
    if request.user.is_authenticated:
        if request.user.studentBook.filter(ISBN = isbn):
            request.user.studentBook.filter(ISBN = isbn).delete()
        #User is redirected to their reading list
        return redirect('myBooks')
    #Otherwise the user is redirected to the home page
    else:
        return redirect('index')

#View to see the most read books in the year group
def year_group_view(request):
    #First ensures that the user is logged in
    context = {}
    if not request.user.is_authenticated:
        return redirect("login")
    #As inputting year group is optional, it has to be checked
    year_group = request.user.yearGroup
    if year_group == None:
        return redirect("account")
    #If the user has input their year group, the entire year group is processed
    else:
        #Number of students reading each book is counted
        students = Student.objects.all().filter(yearGroup = year_group)
        books = Book.objects.all()
        numbers = [book.student_set.all().count() for book in books]
        #These numbers are enumerated so the isbns can be obtained after sorting
        enumerated_numbers = list(enumerate(numbers))
        sorted_numbers = sorted(enumerated_numbers, key=lambda x:x[1])
        #If the number of results is more than 5, the top 5 are used
        if len(sorted_numbers) > 5:
            top_five = [item[0] for item in sorted_numbers[-5::]]
            top_five.reverse()
        #If there are less than 5, all of them are used
        else:
            top_five = [item[0] for item in sorted_numbers]
            top_five.reverse()
        #The book objects are added to the queryset
        queryset = []
        for index in top_five:
            queryset.append(books[index])
        #A table is made from the result
        table = BookTable(queryset)
        RequestConfig(request).configure(table)
        context["table"] = table
        return render(request, "libraryaccess/yeargroup.html", context)

#View to search for other students
def student_search_view(request):
    context = {}
    #Sets the queryset to include all students
    queryset = Student.objects.all()
    #If the user inputs names, the queryset is filtered to include them
    if request.POST:
        Forename = request.POST.get("Forename", "")
        Surname = request.POST.get("Surname", "")
        if len(Forename) > 0:
            queryset = queryset.filter(forename = Forename)
        if len(Surname) > 0:
            queryset = queryset.filter(surname = Surname)
    #The resulting data is passed into table which links to student_view
    table = StudentTable(queryset)
    RequestConfig(request).configure(table)
    context["table"] = table
    return render(request, "libraryaccess/studentsearch.html", context)

#View for seeing another student's reading
def student_view(request, ID):
    #Uses the id number passed into the url to get a student object
    context = {}
    student = get_object_or_404(Student, pk=int(ID))
    #Finds both the forename and surname of the student from the object
    #This is put in the context so it can be displayed
    context["forename"] = (student.forename).capitalize()
    context["surname"] = (student.surname).capitalize()
    #If the student agrees to share their books then a queryset of books is made
    if student.book_share == True:
        queryset = student.studentBook.all()
    else:
        queryset = []
    #The wuery set is put in a book table and returned
    table = BookTable(queryset)
    RequestConfig(request).configure(table)
    context["table"] = table
    return render(request, "libraryaccess/studentview.html", context)

#View to add a new book that is not in the library
def add_new_book_view(request):
    #Creates an error key in the context to return if there is an error
    context = {"error":''}
    #Takes the isbn that has been input
    if request.POST:
        isbn = request.POST.get("ISBN", "")
        #Tries to use the function I created to use google books to get data
        try:
            Title, Authors, publishedDate, Description, Genres = get_details(str(isbn))
        except:
            #If the function is unsuccessful the following error is used
            context["error"] = 'Book Details Not Found'
            return render(request, "libraryaccess/bookadd.html", context)
        #if the book is already in the library it returns another error
        if isbn in Book.objects.values_list('ISBN', flat=True):
            context["error"] = 'Book already in library'
            return render(request, "libraryaccess/bookadd.html", context)
        #Uses django get or create to ensure no errrors when creating object
        newbook, created = Book.objects.get_or_create(ISBN = isbn, publishDate = int(publishedDate), title = Title, description = Description, inLibrary = False)
        #Adds each author and genre individually
        #First checks if author or genre exists and gets it or creates it
        for author in Authors:
            authorname = author.split(' ')
            newauthor, created = Author.objects.get_or_create(forename = ' '.join([authorname[i].lower().capitalize() for i in range(len(authorname)-1)]), surname = authorname[-1].lower().capitalize())
            newbook.bookAuthor.add(newauthor)
            newbook.save()
        for genre in Genres:
            newgenre, created = Genre.objects.get_or_create(name = genre)
            newbook.bookGenre.add(newgenre)
            newbook.save()
        newbook.save()
        #If the user is logged in the book is added to their reading list
        if request.user.is_authenticated:
            request.user.studentBook.add(newbook)
        return redirect('index')
    else:
        return render(request, "libraryaccess/bookadd.html", context)

#View for logging in with an admin passowrd to activate the register
def confirm_register_view(request):
    #Takes the password and compares it to admin accounts
    context = {"error":''}
    if request.POST:
        valid = False
        password = request.POST.get("password", '')
        comparisons = Student.objects.all().filter(is_admin = True)
        for comparison in comparisons.values_list('password', flat=True):
            if check_password(password, comparison):
                valid = True
        #If password is valid, session variable is changed to true
        #This prevents user from being logged in so students cant access admin
        if valid:
            request.session['valid_register'] = True
            return redirect("libraryRegister")
        else:
            context["error"] = 'Not valid password'
            request.session['valid_register'] = False
    return render(request, "libraryaccess/confirmreg.html", context)

#View for the library register
def register_view(request):
    #First the session variable is checked and the user is logged out
    if 'valid_register' in request.session:
        if request.session['valid_register']:
            logout(request)
            request.session['valid_register'] = True
            context = {'error':''}
            #When either the login fields are submitted or a card is scanned
            if request.POST:
                form = AccountAuthenticationForm()
                code = request.POST.get("cardScan", "")
                #First the lenght of the input card UID is checked
                #If there is no card, the login fields are used
                if len(code) <= 0:
                    email = request.POST['email']
                    password = request.POST['password']
                    user = authenticate(email=email, password=password)
                    #If a user is found, their registers for the day are checked
                    if user:
                        start_date = timezone.now().date()
                        end_date = start_date + datetime.timedelta(days=1)
                        user_registers = StudentRegister.objects.all().filter(signinTime__range=(start_date, end_date))
                        #If the user hasn't been registered on the day
                        #Creates a new register
                        if len(user_registers) == 0:
                            new_register = StudentRegister(ID=user, signinTime=timezone.now(), signoutTime=None)
                            new_register.save()
                            context['error'] = (user.forename.capitalize()+' has been signed in.')
                        #If there is a register for the day
                        else:
                            #Checks if the latest register has a sign out time
                            latest_register = user_registers.latest('signinTime')
                            if latest_register.signoutTime == None:
                                #Sets the signout time to the current time
                                latest_register.signoutTime = timezone.now()
                                latest_register.save()
                                context['error'] = (user.forename.capitalize()+' has been signed out.')
                            #Otherwise creates a new register
                            else:
                                new_register = StudentRegister(ID=user, signinTime=timezone.now(), signoutTime=None)
                                new_register.save()
                                context['error'] = (user.forename.capitalize()+' has been signed in.')
                    #If the input fields are not valid an error is returned
                    else:
                        context['error'] = 'Invalid login'
                #If it does not have a typed input it checks the card scanned
                #Card is deemed valid if the code is 8 characters
                else:
                    if len(code) == 8:
                        #Determines if an account is associated with it
                        if len(Student.objects.all().filter(cardUID=code)) == 0:
                            context['error'] = 'No account associated with this card'
                        #Same process as above is sued to add to the register
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
                    #Errors returned for different situations
                    elif len(code) > 0:
                        context['error'] = 'Invalid Card'
                    else:
                        context['error'] = 'User not found, try again'
            #Uses authentication form like login for error generation
            else:
                form = AccountAuthenticationForm()

            context['login_form'] = form
            return render(request, 'libraryaccess/register.html', context)
    #If the register was not confirmed user is redirected
    return redirect('confirm_register')

#View to redirect user to home after closing register and changing session
def close_register(request):
    request.session['valid_register'] = False
    return redirect('index')

#Only allows admin to access this view
#View to send email with register of students to school Admin
#Email can be changed for future use
@user_passes_test(lambda u: u.is_admin)
def mail_register(request):
    #Selects all registers for current day
    start_date = timezone.now().date()
    end_date = start_date + datetime.timedelta(days=1)
    queryset = StudentRegister.objects.all().filter(signinTime__range=(start_date, end_date))
    #Gets list of forenames and surnames to append to email before sending
    names = list(set(queryset.values_list('ID__surname', 'ID__forename')))
    names = '\n'.join([j.capitalize()+' '+i.capitalize() for (i, j) in names])
    send_mail('Library Register', 'The following students have been registered today:\n'+names, None, ['wflyerthariani@gmail.com'])
    #Redirects user to home page
    return redirect('index')
