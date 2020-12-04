from flask import Flask,render_template,url_for, request, redirect, flash, session 
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from functools import wraps
import random
import datetime
import os
from werkzeug.utils import secure_filename


app = Flask(__name__ , template_folder='template')
app.config["MONGO_URI"] = "mongodb://localhost:27017/article"
app.config['UPLOAD_FOLDER'] = "C:\\Users\\Admin\\Documents\\Article\\static\\profile_images"


mongo = PyMongo(app)
bcrypt = Bcrypt(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fname' in session:
            return f(*args, **kwargs)

        else:
            flash("You have to login first","warning")
            return redirect('login')    
            
    return decorated_function



@app.route("/")
def index():
    if 'fname' in session:
        fname = session['fname']
        print(fname)
    
    return render_template("index.html")



@app.route('/signup',methods =["POST","GET"])
def signup():
    if request.method == "POST":
        First_name = request.form["First_name"]
        Last_name = request.form["Last_name"]
        Email = request.form["Email"]
        Password = request.form["Password"]

        pw_hash = bcrypt.generate_password_hash(Password).decode( 'utf-8' )
        
        mongo.db.users.insert_one(
             {
                 "fname": First_name,
                 "lname": Last_name,
                 "email": Email,
                 "password": pw_hash,
            
             }
          )
     
        flash("account created successfuly!","success")  
        return redirect(url_for('login'))     
    return render_template("signup.html")
    
   
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
         Email = request.form["Email"]
         Password = request.form["Password"]
         
         found_user = mongo.db.users.find_one({"email": Email})
         if found_user:
             if bcrypt.check_password_hash(found_user['password'], request.form['Password']):
                 session['fname'] = found_user['fname']
                 session['lname'] = found_user['lname']
                 session['email'] = found_user['email']
 
                 flash("Successful Login","success")
                 return redirect(url_for("index"))
             else:
                 flash("Login failed. Please try again!","danger")
         else:
             flash("Sorry user not found","danger")
    return render_template("login.html")   


@app.route('/articles')
def articles():
    articles = mongo.db.articles.find()

    return render_template("articles.html" , articles = articles)

@app.route('/view_article/<int:article_id>')
def view_article(article_id):


    article = mongo.db.articles.find_one({ 'article_id': article_id })
    

    return render_template("view_article.html",article = article)



@app.route('/add_article' , methods=['POST','GET'])
@login_required
def add_article():
    
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        article_id = random.randint(1111,9999)

        mongo.db.articles.insert_one({
            'title': title,
            'content': content,
            'article_id':article_id,
            'created_at': datetime.datetime.now(),
            'owner':{
                'name':session['fname'] + ' ' + session['lname'],
                'email':session['email']
            }
        })
        

        flash("Article addes successfully","success")
    return render_template('add_article.html' , articles = articles)


@app.route('/dashboard')
def dashboard():
    articles = mongo.db.articles.find({'owner.email':session['email']})
    return render_template("dashboard.html",articles = articles)

@app.route('/edit_article/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):


    article = mongo.db.articles.find_one({'article_id':article_id, 'owner.email':session['email']})

    if article is None:
        flash("Article not found!/not allowed!","danger")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        mongo.db.articles.update_one( {'article_id':article_id} ,{'$set': { 'title':request.form['title'] , 'content':request.form['content']} } ,upsert= False )
        flash("Article updated successfully","success")
        
        return redirect(url_for('edit_article',article_id=article_id))

    return render_template("edit_article.html",article=article)


@app.route('/delete_article/<int:article_id>')
@login_required
def delete_article(article_id):
    mongo.db.articles.remove({ 'article_id':article_id,'owner.email':session['email'] })

    flash("Article deleted successfully","success")

    return redirect(url_for('dashboard'))

@app.route('/search', methods=['POST','GET'] )
def search():
    if request.method == "POST":
        search_query = request.form['search_query']
        search_results = mongo.db.articles.find( { '$text': {'$search':search_query } } )

        result_count = int(search_results.count())


    return render_template("search.html", result_count = result_count , search_results = search_results)


@app.route('/profile',methods = ['POST','GET'] )
def profile():
    if request.method == "POST":
        mongo.db.users.update_one({'email':session['email']},{'$set':{
            'fname':request.form['First_name'],
            'lname':request.form['Last_name'],
            'email':request.form['Email']
        }})
        session['fname'] = request.form['First_name']
        session['lname'] = request.form['Last_name']
        session['email'] = request.form['Email']
        flash("Successfuly updated profile","success")    
    return render_template('profile.html')   

@app.route('/update_picture', methods=['GET','POST'])
def update_picture():
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash("No image selected","danger")
            return redirect(url_for('profile')) 
    file = request.files['photo']          
    filename =secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    mongo.db.users.update_one({'email':session['email']},{'$set':{
        'pro_pic': '/profile_images/'+filename
    }})  
    session['pro_pic'] = '/profile_images/'+filename

    flash("Successfuly uploaded image","success")

    return redirect(url_for('profile')) 

    


@app.route('/logout')
def logout():
    session.clear()
    flash("Successfuly logged out!" , "success")
    return redirect(url_for('login'))





if __name__=="__main__":
    app.secret_key = "asdtc"
    app.run(debug=True)