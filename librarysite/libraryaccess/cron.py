import csv
from libraryaccess.models import Student, Author, Genre, Book

def my_cron_job():
    with open('libraryaccess/recommendation_info.csv', 'w') as recommendation_info:
        all_books = Book.objects.all().filter(inLibrary = True)
        csv.writer(recommendation_info).writerow(list(all_books.values_list('ISBN', flat=True)))
        csv.writer(recommendation_info).writerow(list(all_books.values_list('description', flat=True)))
        csv.writer(recommendation_info).writerow(list(all_books.values_list('title', flat=True)))
        csv.writer(recommendation_info).writerow([' '.join([book.bookGenre.all()[i].name for i in range(len(book.bookGenre.all()))]) for book in all_books])
