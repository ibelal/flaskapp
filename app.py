from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
from dbconnection import connection
from functools import wraps

app  = Flask(__name__)
app.secret_key = 'secret123'

# Mysql Connection


app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = ''
# app.config["MYSQL_PORT"] = ''
app.config["MYSQL_DB"] = 'flaskapp'

# app.config["MYSQL_HOST"] = 'localhost'
# app.config["MYSQL_USER"] = 'sushnzqq_demo' #'root'
# app.config["MYSQL_PASSWORD"] = 'demo@123456' # ''
# # app.config["MYSQL_PORT"] = ''
# app.config["MYSQL_DB"] = 'sushnzqq_demo' #'flaskapp'


app.config["MYSQL_CURSORCLASS"] = 'DictCursor'

# init mysql
mysql = MySQL(app)
	
	
	


#Articles = Articles()

@app.route('/')
def index():
	return render_template('home.html')


@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	con = mysql.connection
	cur = con.cursor()

	result = cur.execute("SELECT * FROM articles")
	articles = cur.fetchall()

	if result > 0:
		return render_template('articles.html', articles=articles)
	else:
		flash("No article found.", 'success')
		return render_template('articles.html')
		cur.close()
		
	return render_template('articles.html')

@app.route('/articles/<string:id>/')
def article(id):
	con = mysql.connection
	cur = con.cursor()

	result = cur.execute("SELECT * FROM articles WHERE id = %s ", [id] )
	article = cur.fetchone()

	if result > 0:
		return render_template('articles.html', article=article)
	else:
		abort(404)

	return render_template('articles.html', article=article)


class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=3, max=50)])
	email = EmailField('Email', [
			validators.DataRequired(),
			validators.Email(message="Enter a valid email"),
			validators.Length(min=5, max=50)
		])
	username = StringField('Username', [validators.Length(min=3, max=50)])
	password = PasswordField('Password', [
			validators.DataRequired(),
			validators.EqualTo('confirm', message='Password do not match')
		])
	confirm = PasswordField('Confirm Password')

	
@app.route('/register', methods=['GET', 'POST'])
def register():
	if session.get('logged_in'):
		if session['logged_in'] == True :
			return redirect(url_for('dashboard'))
	con = mysql.connection
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():

		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))			

		cur = con.cursor()

		result = cur.execute('SELECT username FROM user WHERE username = %s ', [username])

		if result > 0:
			flash('Username already exists, Please go to Login', 'warning')

			return redirect(url_for('register'))
		else:
			cur.execute("INSERT INTO user (name, email, username, password) VALUES (%s,%s,%s,%s)", (name, email, username, password))

			# Commit to DB
			con.commit()

			# Close connection
			cur.close()

			flash('You are now registered and can log in', 'success')

			return redirect(url_for('login'))		

	return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if session.get('logged_in'):
		if session['logged_in'] == True :
			return redirect(url_for('dashboard'))

	con = mysql.connection
	if request.method == 'POST' :
		username = request.form["username"]
		password_candidate = request.form["password"]

		cur = con.cursor()

		result = cur.execute("SELECT * FROM user WHERE username = %s ", [username])

		if result > 0:
			data = cur.fetchone()
			password = data["password"]

			if sha256_crypt.verify(password_candidate, password) :
				
				session["logged_in"] = True
				session["username"] = username			

				flash('You are now logged in.', 'success')
				return redirect(url_for('dashboard'))

			else:				
				error = "Invalid Login."
				return render_template('login.html', error=error)
			cur.close()
		else:
			error = "User not found."
			return render_template('login.html', error=error)


	return render_template('login.html')

# if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorize login', 'danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/logout')
def logout():
	session.clear()
	flash('You are now log out.', 'success')
	return redirect(url_for('login'))



@app.route('/dashboard')
@is_logged_in
def dashboard():
	con = mysql.connection
	cur = con.cursor()

	result = cur.execute("SELECT * FROM articles")
	articles = cur.fetchall()

	if result > 0:
		return render_template('dashboard.html', articles=articles)
	else:
		flash("No article found.", 'success')
		return render_template('dashboard.html')
		cur.close()
		
	return render_template('dashboard.html')	



class ArticleForm(Form):
	title = StringField('Title', [validators.Required(), validators.Length(min=3, max=200)])
	body = TextAreaField('Content', [validators.Required(), validators.Length(min=30)])


# Add Article
@app.route('/add_article', methods = ['GET', 'POST'])
@is_logged_in
def add_article():
	con = mysql.connection
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		cur = con.cursor()

		cur.execute("INSERT INTO articles (title, body, author) VALUES (%s, %s, %s) ", (title, body, session['username']))

		con.commit()

		cur.close()

		flash('Article create.', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods = ['GET', 'POST'])
@is_logged_in
def edit_article(id):
	con = mysql.connection
	cur = con.cursor()

	result = cur.execute("SELECT * FROM articles WHERE id= %s ", [id] )

	article = cur.fetchone()
	cur.close()

	form = ArticleForm(request.form)

	# Populate article form fields
	form.title.data = article['title']
	form.body.data = article['body']

	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		con = mysql.connection

		cur = con.cursor()

		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s ", (title, body, id))

		con.commit()

		cur.close()

		flash('Article updated.', 'success')

		return redirect(url_for('dashboard'))
	# else:
	# 	error = 'Article not updated.'

	# 	return render_template('edit_article.html', error=error) 

	return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>', methods=['GET'])
@is_logged_in
def delete_article(id):
	con = mysql.connection
	cur = con.cursor()

	cur.execute("DELETE FROM articles WHERE id = %s ", [id])

	con.commit()
	cur.close()

	flash('Article Deleted.', 'success')

	return redirect(url_for('dashboard'))




if __name__ == '__main__' :
	
	app.run(debug = True, threaded = True)


