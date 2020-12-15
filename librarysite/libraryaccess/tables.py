import django_tables2 as tables
from libraryaccess.models import Student, Author, Genre, Book

class BookTable(tables.Table):
    all_authors = tables.Column(verbose_name='Authors', order_by=("bookAuthor.surname"))
    go_to_view = tables.TemplateColumn('<a href="/libraryaccess/bookview/{{record.ISBN}}">View</a>')
    class Meta:
        model = Book
        fields = ['ISBN', 'title', 'all_authors']

class MyBookTable(tables.Table):
    all_authors = tables.Column(verbose_name='Authors', order_by=("bookAuthor.surname"))
    go_to_view = tables.TemplateColumn('<a href="/libraryaccess/bookview/{{record.ISBN}}">View</a>')
    delete_book = tables.TemplateColumn('<a href="/libraryaccess/removebook/{{record.ISBN}}">Remove</a>')
    class Meta:
        model = Book
        fields = ['ISBN', 'title', 'all_authors']

class StudentTable(tables.Table):
    go_to_view = tables.TemplateColumn('<a href="/libraryaccess/studentview/{{record.pk}}">View</a>')
    class Meta:
        model = Student
        fields = ['forename', 'surname']
