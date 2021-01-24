from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

#Class to specify how to create a new user using relevant information
class MyAccountManager(BaseUserManager):
    #Creating a basic user with the required fields with potential errors
    def create_user(self, email, username, forename, surname, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        if not forename:
            raise ValueError('Users must have a forename')
        if not surname:
            raise ValueError('Users must have a surname')
        #Normalises data for storage in the database
        user = self.model(
			email=self.normalize_email(email),
			username=username,
            forename=forename.lower(),
            surname=surname.lower(),
		)
        #Uses Django's set_password to encrypt password before saving
        user.set_password(password)
        user.save(using=self._db)
        return user
    #Superuser created similar to a normal user except permissions changed
    def create_superuser(self, email, username, forename, surname, password):
        user = self.create_user(
			email=self.normalize_email(email),
			password=password,
			username=username,
            forename=forename.lower(),
            surname=surname.lower(),
		)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

#Defines Author table
class Author(models.Model):
    #Only contains first and last name
    forename                = models.CharField(verbose_name='forename', max_length=30)
    surname                 = models.CharField(verbose_name='surname', max_length=30)
    #Method for displaying forename and surname when object is displayed
    def __str__(self):
        return(self.forename+' '+self.surname)

#Defines Genre table
class Genre(models.Model):
    #In addition to name has a code which is optional
    name                    = models.CharField(verbose_name='name', max_length=50)
    code                    = models.CharField(verbose_name='code', max_length=10, null = True, blank = True)
    #When called, only name is returned
    def __str__(self):
        return(self.name)

#Defines Book table
class Book(models.Model):
    #ISBN set as primary key
    ISBN                    = models.CharField(verbose_name='ISBN', max_length=13, primary_key=True)
    title                   = models.CharField(verbose_name='title', max_length=100)
    #Following are optional fields not used for recommendations
    publisher               = models.CharField(verbose_name='publisher', max_length=50, null = True, blank = True)
    publishDate             = models.IntegerField(verbose_name='publishDate', null = True, blank = True)
    description             = models.CharField(verbose_name='description', max_length=3000, null = True, blank = True)
    location                = models.CharField(verbose_name='code', max_length=10, null = True, blank = True)
    #Built in Django function to create a junction table for many-to-many field
    bookAuthor              = models.ManyToManyField(Author)
    bookGenre               = models.ManyToManyField(Genre)
    inLibrary               = models.BooleanField(default=True)

    #returns title of the book if object is displayed
    def __str__(self):
        return(self.title)

    #Properties used in tables to return a string with all genres/authors
    @property
    def all_authors(self):
        return ', '.join([self.bookAuthor.all()[i].forename+' '+self.bookAuthor.all()[i].surname for i in range(len(self.bookAuthor.all()))])

    @property
    def all_genres(self):
        return ', '.join([self.bookGenre.all()[i].name for i in range(len(self.bookGenre.all()))])

#Student class functions as a user model hence different argument
class Student(AbstractBaseUser):
    #Email and username made to be unique
    email 					= models.EmailField(verbose_name="email", max_length=60, unique=True)
    username 				= models.CharField(max_length=30, unique=True)
    #Date and time added automatically by auto_now
    date_joined				= models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login				= models.DateTimeField(verbose_name='last login', auto_now=True)
    #Sets default values so user is created without admin permissions
    is_admin				= models.BooleanField(default=False)
    book_share				= models.BooleanField(default=False)
    is_active				= models.BooleanField(default=True)
    is_staff				= models.BooleanField(default=False)
    is_superuser			= models.BooleanField(default=False)
    forename                = models.CharField(verbose_name='forename', max_length=30, null = True, blank = True)
    surname                 = models.CharField(verbose_name='surname', max_length=30, null = True, blank = True)
    cardUID                 = models.CharField(verbose_name='cardUID', max_length=8, null = True, blank = True)
    formCode                = models.CharField(verbose_name='formCode', max_length=3, null = True, blank = True)
    yearGroup               = models.IntegerField(verbose_name='yearGroup', null = True, blank = True)
    studentID               = models.IntegerField(verbose_name='studentID', null = True, blank = True)
    studentBook             = models.ManyToManyField(Book)

    #Defines which fields are used for registration and login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'forename', 'surname']

    objects = MyAccountManager()

    #Displays user forename when object is returned
    def __str__(self):
        return self.forename.capitalize()

	# For checking permissions
    def has_perm(self, perm, obj=None):
        return self.is_admin

	# Does this user have permission to view this app
    def has_module_perms(self, app_label):
        return self.is_admin

#Class for each registration into the library
class StudentRegister(models.Model):
    ID                      = models.ForeignKey(Student, on_delete=models.CASCADE)
    signinTime              = models.DateTimeField(verbose_name='signinTime')
    signoutTime             = models.DateTimeField(verbose_name='signoutTime', null = True, blank = True)

    #No support for composite primary keys in django
    #Ensures that both fields are unique when considered together
    class Meta:
        unique_together = ['ID', 'signinTime']
    #Returns Student object, which in turn returns forenmae as specified above
    def __str__(self):
        return(self.ID)
