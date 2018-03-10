###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
import requests
import json
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, IntegerField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/royoke364midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)

api_key='ad9bfe6b914fdcdda7b371656f06ea66'
######################################
######## HELPER FXNS (If any) ########
######################################
def get_movie_info(name):
    if " " in name:
        name.replace(' ','+')
    baseURL = 'https://api.themoviedb.org/3/search/movie?'
    params = {}
    params['query']= name
    params['api_key']=api_key
    data = requests.get(baseURL, params=params)
    return data.text



##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer,primary_key=True)
    user_name = db.Column(db.String (64))

    def __repr__(self):
        return "{} | ID#: {}".format(self.name, self.id)

class Watchlist(db.Model):
    __tablename__="watchlist"
    movie_title = db.Column(db.String (100),primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __repr__(self):
        return "{} | User: {}".format(self.movie_info,self.user_id)

class RemovedMovies(db.Model):
    __tablename__='removedmovies'
    movie_title = db.Column(db.String (100),primary_key=True)
    #user_name = db.Column(db.String (64), db.ForeignKey('users.user_name'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __repr__(self):
        return "{} | User: {} | ID: {}".format(self.movie_title,self.user_name,self.user_id)



###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name (First and Last)",validators=[Required()])
    submit = SubmitField()

    def validate_name(self, field):
        if len(field.data.split()) <= 1:
            raise ValidationError('Please include your first and last name, with spaces!')

class MovieSearchForm(FlaskForm):
    movie = StringField("Name of Movie: ",validators=[Required()])
    submit = SubmitField()

class WatchlistForm(FlaskForm):
    name = StringField("Enter you full name (First and Last) so we know whose watchlist we are working with!: ",validators=[Required()])
    movie = StringField("Enter the name of the movie you would like us to add to your watchlist: ",validators=[Required()])
    submit = SubmitField()
    
    def validate_name(self, field):
        if len(field.data.split()) <= 1:
            raise ValidationError('Please include your first and last name, with spaces!')

class RemoveMoviesForm(FlaskForm):
    name = StringField('Enter you full name (First and Last) so we know whose watchlist we are working with!: ', validators=[Required()])
    movie = StringField('Enter the name of the movie you would like to remove: ', validators=[Required()])
    submit = SubmitField()

    def validate_name(self, field):
        if len(field.data.split()) <= 1:
            raise ValidationError('Please include your first and last name, with spaces!')

#######################
###### VIEW FXNS ######
#######################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/', methods = ['GET','POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name=name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('base.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/movieinfo', methods = ['GET','POST'])
def movie_info():
    return render_template('movieform.html')

@app.route('/movieresults', methods = ['GET','POST'])
def movie_results():
    movie = request.args['movie']
    if movie != '':
        data = get_movie_info(movie)
        obj = json.loads(data)
        return render_template('movieresults.html', movie_dict=obj)
    flash('A movie title is required!')
    return redirect(url_for('movie_info'))

@app.route('/watchlist', methods = ['GET','POST'])
def watchlist():
    form = WatchlistForm()
    if form.validate_on_submit():
        user = form.name.data
        movie = form.movie.data
        u = User.query.filter_by(user_name=user).first()
        if u:
            user = u
        else:
            user = User(user_name=user)
            db.session.add(user)
            db.session.commit()
        m = Watchlist.query.filter_by(movie_title=movie,user_id=user.user_id).first()
        if m:
            flash('You have already added this movie to your watchlist!')
            return redirect(url_for('watchlist'))
        else:
            movie = Watchlist(movie_title=movie,user_id=user.user_id)
            db.session.add(movie)
            db.session.commit()
            flash("{} has been saved to {}'s watchlist!".format(form.movie.data,form.name.data))
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('watchlistform.html',form=form)

@app.route('/viewlist', methods = ['GET','POST'])
def viewlist():
    form = NameForm()
    if form.validate_on_submit():
        all_movies = []
        user = form.name.data
        user_id= User.query.filter_by(user_name=user).first().user_id
        watchlist = Watchlist.query.all()
        for movie in watchlist:
            all_movies.append((movie.movie_title,movie.user_id))
        movie_len = len(all_movies)
        return render_template('viewlist.html',all_movies=all_movies, name=user,user_id=user_id,movie_len=movie_len)
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("There are either no movies in your watchlist or there is a typo. Make sure you are using your first and last name and already have a movie in your watchlist!")
    return render_template('whosewatchlist.html',form=form)

@app.route('/seeremovedmovies',methods = ['GET','POST'])
def see_removed_movies():
    removed_movies = []
    movies = RemovedMovies.query.all()
    for movie in movies:
        removed_movies.append((movie.movie_title,User.query.filter_by(user_id=movie.user_id).first().user_name))
    return render_template('seeremovedmovies.html',removed_movies=removed_movies)

@app.route('/removemovie', methods=['GET','POST'])
def remove_movie():
    form = RemoveMoviesForm()
    if form.validate_on_submit():
        name = form.name.data
        user_id = User.query.filter_by(user_name=name).first().user_id
        movie = form.movie.data
        m = Watchlist.query.filter_by(movie_title=movie,user_id=user_id).first()
        if m:
            db.session.delete(m)
            db.session.commit()
            flash('Your movie has been successfully removed!')

        else:
            flash('You have already removed this movie from you Watchlist!')
        m = RemovedMovies.query.filter_by(movie_title=movie,user_id=user_id).first()
        if not m:
            new_movie = RemovedMovies(movie_title=movie,user_id=user_id)
            db.session.add(new_movie)
            db.session.commit()
        return redirect(url_for('see_removed_movies'))
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('removemovie.html',form=form)





## Code to run the application...
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
