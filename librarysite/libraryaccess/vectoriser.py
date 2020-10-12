#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 10 11:27:30 2020

@author: arman
"""

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def recommend_by_description(descriptions, isbns, books_read, recommendation_number):
    if len(books_read) == 0:
        return isbns[:recommendation_number+1]
    else:
        vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', ngram_range=(2, 2), min_df = 1)
        tfidf_matrix = vectorizer.fit_transform(descriptions)
        read_indices = []
        for book in books_read:
            read_indices.append(isbns.index(book))
        required_rows = [tfidf_matrix[i] for i in read_indices]
        if len(required_rows) > 0:
            cumulation = required_rows[0]
            for i in range(len(required_rows)-1):
                cumulation = cumulation+required_rows[i+1]
        else:
            cumulation = []
        sg = cosine_similarity(cumulation, tfidf_matrix)
        sig = list(enumerate(sg[0]))
        sig = sorted(sig, key=lambda x: x[1], reverse=True)
        sig = sig[0:(recommendation_number)+len(books_read)]
        final = []
        for i in range(len(sig)):
            isbn = isbns[sig[i][0]]
            if isbn not in books_read:
                final.append(isbn)
        return(final[:recommendation_number+1])



def recommend_by_genre(genres, isbns, books_read, recommendation_number):
    if len(books_read) == 0:
        return isbns[:recommendation_number+1]
    else:
        vectorizer = CountVectorizer(ngram_range=(1, 3))
        matrix = vectorizer.fit_transform(genres)
        read_indices = []
        for book in books_read:
            read_indices.append(isbns.index(book))
        required_rows = [matrix[i] for i in read_indices]

        if len(required_rows) > 0:
            cumulation = required_rows[0]
            for i in range(len(required_rows)-1):
                cumulation = cumulation+required_rows[i+1]
        else:
            cumulation = []
        sg = cosine_similarity(cumulation, matrix)
        sig = list(enumerate(sg[0]))
        sig = sorted(sig, key=lambda x: x[1], reverse=True)
        sig = sig[:(recommendation_number-1)+len(books_read)]
        final = []
        for i in range(len(sig)):
            isbn = isbns[sig[i][0]]
            if isbn not in books_read:
                final.append(isbn)
        return(final[:recommendation_number])



def combined_recommendation(genre_recommendations, description_recommendations, number_of_recommendations, titles, books_read, isbns):
    full_list = []
    selected_list = []
    counter = 0
    while counter<min([len(genre_recommendations), len(description_recommendations)]) and len(selected_list)<number_of_recommendations:
        if genre_recommendations[counter] not in full_list:
            full_list.append(genre_recommendations[counter])
        elif titles[isbns.index(genre_recommendations[counter])] not in [titles[isbns.index(book_read)] for book_read in books_read]:
            if titles[isbns.index(genre_recommendations[counter])] not in [titles[isbns.index(selected)] for selected in selected_list]:
                selected_list.append(genre_recommendations[counter])
        if description_recommendations[counter] not in full_list:
            full_list.append(description_recommendations[counter])
        elif titles[isbns.index(description_recommendations[counter])] not in [titles[isbns.index(book_read)] for book_read in books_read]:
            if titles[isbns.index(description_recommendations[counter])] not in [titles[isbns.index(selected)] for selected in selected_list]:
                selected_list.append(description_recommendations[counter])
        counter+=1
    if len(selected_list) == number_of_recommendations:
        return(selected_list)
    else:
        remaining = number_of_recommendations - len(selected_list)
        newcounter = 0
        while newcounter < len(full_list) and remaining != 0:
            if full_list[newcounter] not in selected_list:
                if titles[isbns.index(full_list[newcounter])] not in [titles[isbns.index(book_read)] for book_read in books_read]:
                    if titles[isbns.index(full_list[newcounter])] not in [titles[isbns.index(selected)] for selected in selected_list]:
                        selected_list.append(full_list[newcounter])
                        remaining -= 1
            newcounter += 1
        return(selected_list)
