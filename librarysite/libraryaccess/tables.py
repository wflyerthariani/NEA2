import django_tables2 as tables
from libraryaccess.models import Student, Author, Genre, Book

class BookTable(tables.Table):
    all_authors = tables.Column(verbose_name='Authors')
    go_to_view = tables.TemplateColumn('<a href="/libraryaccess/book_view/{{record.ISBN}}">View</a>')
    class Meta:
        model = Book
        fields = ['ISBN', 'title', 'all_authors']
