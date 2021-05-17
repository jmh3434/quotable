from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from . import quotes,images
import random

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == "GET":
        return redirect('/')
    errors = User.objects.validate(request.POST)
    if errors:
        for e in errors.values():
            messages.error(request, e)
        return redirect('/')
    else:
        new_user = User.objects.register(request.POST)
        request.session['user_id'] = new_user.id
        messages.success(request, "You have successfully registered!")
        return redirect('/success')

def login(request):
    if request.method == "GET":
        return redirect('/')
    if not User.objects.authenticate(request.POST['email'], request.POST['password']):
        messages.error(request, 'Invalid Email/Password')
        return redirect('/')
    user = User.objects.get(email=request.POST['email'])
    request.session['user_id'] = user.id
    messages.success(request, "You have successfully logged in!")
    return redirect('/success')

def logout(request):
    request.session.clear()
    
    return redirect('/')

def success(request):
    if 'user_id' not in request.session:
        return redirect('/')
    if 'used_quote_ids' not in request.session:
        request.session["used_quote_ids"] = []
        request.session["genre"] = "family"

    request.session["used_quote_ids"].clear()

    user = User.objects.get(id=request.session['user_id'])

    genres = [""]
    context = {
        'user': user,
        'movies': Movie.objects.all(),
        'quotes': Quote.objects.all()
    }
    request.session["result"] = ""
    request.session["score"] = 0
    return render(request, 'success.html', context)


def process_movie(request):
    errors = Movie.objects.validate(request.POST)
    if errors:
        for e in errors.values():
            messages.error(request, e)
        return redirect('/success')

    Movie.objects.create(title=request.POST["title"],genre=request.POST["genre"],image_url=request.POST["image"], poster=User.objects.get(id=request.session['user_id']))
    return redirect('/success')

def add_quote(request):
    errors = Quote.objects.validate(request.POST)
    if errors:
        for e in errors.values():
            messages.error(request, e)
        return redirect('/success')

    movie_submitted = request.POST["movie_id"]
    movie_filtered = Movie.objects.filter(title=movie_submitted)

    movie_id = movie_filtered[0].id

    movie = Movie.objects.get(id=movie_id)
    quote = request.POST["quote"]
    poster = User.objects.get(id=request.session['user_id'])

    Quote.objects.create(quote=quote,poster=poster,movie=movie)

    return redirect('/success')


def getRandom():
    random_quote = Quote.objects.random()
    return random_quote
    

def choose_genre(request):
    request.session["genre"] = request.POST["genre"]
    return redirect('/quiz')

def quiz(request):

    request.session["result"] = ""
   
    if 'user_id' not in request.session:
        return redirect('/')
    if len(Quote.objects.all()) < 1:
        return redirect('/success')

    random_quote = getRandom()


    length = 0

    for quote in Quote.objects.all():
        if quote.movie.genre == request.session["genre"]:
            length+=1
    if length < 1:
        return redirect('/success')

    while True:
        if len(request.session["used_quote_ids"]) == length:
            #print("all have been used")
            random_quote = False
            break
        if random_quote.id in request.session["used_quote_ids"] or random_quote.movie.genre != request.session["genre"]:
            #print("quote has been used, get another")
            random_quote = getRandom()
        else:
            break

        
    if random_quote:
        print("used_quote_ids",request.session["used_quote_ids"])
        print("random_quoteid",random_quote.id)
        request.session['random_quote_id'] = random_quote.id
    else:
        request.session['random_quote_id'] = False

    
    return redirect('/show_quiz')

def show_quiz(request):

    request.session["timer"] = 60
        
    if request.session['random_quote_id']:
        random_quote = Quote.objects.get(id=request.session['random_quote_id'])
    else:
        random_quote = False

    user = User.objects.get(id=request.session['user_id'])
    context = {
        'user': user,
        'movies': Movie.objects.filter(genre=request.session["genre"]),
        'quotes': Quote.objects.all(),
        'random_quote': random_quote,
        'used_quotes':len(request.session["used_quote_ids"]),
        'result': request.session["result"],
        'high_score':user.high_score,

    }
    return render(request, 'quiz.html', context)



def submit_answer(request,quote_id):
    user = User.objects.get(id=request.session['user_id'])
    movie_submitted = request.POST["chosen_movie_id"]

    movie_filtered = Movie.objects.filter(title=movie_submitted)

    if len(movie_filtered) < 1:
        return redirect('/show_quiz')

    chosen_movie_id = movie_filtered[0].id

    for movie in movie_filtered:
        print("filtered",movie.title)

    if request.method == "GET" or movie_submitted == "Choose a movie":
        request.session["result"] = ""
        return redirect('/show_quiz')

    quote = Quote.objects.get(id=quote_id)
    correct_movie_id = quote.movie.id

    # chosen_movie_id = int(movie_submitted)
    favorite = request.POST.getlist("favorite")

    
    if len(favorite) > 0:
        user_liking = User.objects.get(id=request.session['user_id'])
        userquote = UserQuote(user=user_liking,quote=quote)
        userquote.save()

    request.session["used_quote_ids"].append(quote_id)


    movie = Movie.objects.get(id=correct_movie_id)

    if correct_movie_id == chosen_movie_id:
        request.session["correct"] = True
        request.session["score"] += 1
        if request.session["score"] > user.high_score:
            user.high_score = request.session["score"]
            user.save()
    else:
        request.session["correct"] = False
    
    request.session["result"] = f"{movie.title}"
    request.session["image"] = movie.image_url

    return redirect('/show_quiz')

def clear(request):
    user=User.objects.get(id=request.session['user_id'])
    Quote.objects.filter(poster=user).delete()     
    return redirect(f'/profile/{user.id}')

def sample(request):
    all_quotes = quotes.quote_bank
    poster=User.objects.get(id=request.session['user_id'])
    genre="family"
    for key, value in all_quotes.items():
        image = images.images[key]
        movie = Movie.objects.create(title=key, genre=genre, image_url=image, poster=poster)

        for quote in value:
            movie = Movie.objects.get(id=movie.id)
            Quote.objects.create(quote=quote,poster=poster,movie=movie)
    
    return redirect(f'/profile/{poster.id}')


def profile(request,id):
    user = User.objects.get(id=id)
    signed_in_user = User.objects.get(id=request.session['user_id'])
    context = {
        'user': user,
        'signed_in_user':signed_in_user,
        'movies': Movie.objects.filter(poster=user),
        'quotes': Quote.objects.filter(poster=user),
        'high_score':user.high_score,
    }

    return render(request,"profile.html",context)

def delete_quote(request,id):
    user = User.objects.get(id=request.session['user_id'])
    quote = Quote.objects.get(id=id)
    quote.delete()
    return redirect(f"/profile/{user.id}")

def activity(request):
    user = User.objects.get(id=request.session['user_id'])
    signed_in_user = User.objects.get(id=request.session['user_id'])
    context = {
        'user': user,
        'signed_in_user':signed_in_user,
        'users': User.objects.all(),
        'movies': Movie.objects.all(),
        'quotes': Quote.objects.order_by('-updated_at'),
        'user_quotes': UserQuote.objects.all(),
    }

    return render(request,"activity.html",context)


def edit(request,id):
    user = User.objects.get(id=request.session['user_id'])
    quote = Quote.objects.get(id=id)
    if request.method == "GET":
    
        context = {
            "quote":quote,
            'user': user,
        }
        return render(request,"edit.html",context)
    else:
        updated_quote = request.POST["quote"]
        updated_movie_title = request.POST["movie_title"]
        updated_movie_image = request.POST["image_url"]
        updated_movie_genre = request.POST["genre"]

        movie_id = quote.movie.id

        movie = Movie.objects.get(id=movie_id)

        quote.quote = updated_quote

        movie.title = updated_movie_title
        movie.image_url = updated_movie_image
        if updated_movie_genre != "":
            movie.genre = updated_movie_genre

        quote.save()
        movie.save()

        return redirect(f'/profile/{user.id}')


def add_comment(request,id):
    comment = request.POST["comment"]
    poster =  User.objects.get(id=request.session['user_id'])
    quote = Quote.objects.get(id=id)

    Comment.objects.create(comment=comment,poster=poster,quote=quote)

    return redirect('/activity')

def delete_comment(request,id):
    comment = Comment.objects.get(id=id)
    comment.delete()

    return redirect('/activity')


def settings(request,id):
    signed_in_user = User.objects.get(id=request.session['user_id'])

    if request.method == "GET":
        context = {
            'signed_in_user':signed_in_user,
            # 'movies': Movie.objects.filter(poster=user),
            # 'quotes': Quote.objects.filter(poster=user)
        }

        return render(request,"settings.html",context)
    else:
        email = request.POST["email"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        image = request.POST["image"]

        signed_in_user.email = email
        signed_in_user.first_name = first_name
        signed_in_user.last_name = last_name
        signed_in_user.image_url = image

        signed_in_user.save()

        return redirect(f'/settings/{signed_in_user.id}')
