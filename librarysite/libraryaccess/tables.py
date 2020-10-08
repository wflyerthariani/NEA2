import django_tables2 as tables
from libraryaccess.models import Student, Author, Genre, Book

class BookTable(tables.Table):
    class Meta:
        model = Book
        fields = ['ISBN', 'title']
