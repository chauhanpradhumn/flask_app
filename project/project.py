from flask import Flask, render_template, url_for, redirect, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField , PasswordField , SubmitField
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import DataRequired, Length , Email, EqualTo
from datetime import datetime, UTC, date, timedelta
#---------configurations---------

app = Flask( __name__ )
app.config['SECRET_KEY'] = 'my-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
db=SQLAlchemy(app)

#----------- models --------------

class user(db.Model):
   id=db.Column(db.Integer(),primary_key=True)
   username=db.Column(db.String(length=30),nullable=False)
   email=db.Column(db.String(),nullable=False,unique=True)
   pass_hash=db.Column(db.String(length=255), nullable=False)
   habits=db.relationship('habit')

class habit(db.Model):
   id=db.Column(db.Integer(),primary_key=True)
   name=db.Column(db.String(),nullable=False)
   description=db.Column(db.Text)
   created_at=db.Column(db.Date , nullable=False)
   user_id=db.Column(db.Integer,  db.ForeignKey('user.id'), nullable=False)
   habits_data=db.relationship('habitlog')

class habitlog(db.Model):
   id=db.Column(db.Integer(),primary_key=True)
   date=db.Column(db.Date, nullable=False)
   habit_id=db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)


#----------- forms ---------------

class registeration_form(FlaskForm):
    username=StringField(label="Username :", validators=[DataRequired(), Length(min=6 , max=20)])
    email=StringField(label="Enter Email :", validators=[DataRequired(), Email()])
    password=PasswordField(label="Password :", validators=[DataRequired(), Length(min=8, max=15)])
    passwrod2=PasswordField(label="Confirm Password :", validators=[DataRequired(),Length(min=8, max=15), EqualTo('password')])
    submit=SubmitField(label='Create account :') 

class login_form(FlaskForm):
   email=StringField(label='Enter Email :', validators=[DataRequired(), Email()])
   password=PasswordField(label='Password :', validators=[DataRequired(), Length(min=8,max=15)])
   submit=SubmitField(label='Login :') 

class createhabit_form(FlaskForm):
   name=StringField(label='habit name :', validators=[DataRequired(), Length(min=5,max=15)])
   description=StringField(label='describe your habit :', validators=[Length(min=5,max=50)])
   submit=SubmitField(label='create habit :')

#--------------routes------------

@app.route('/')
def home():
   return  render_template('home.html')

@app.route("/register", methods=['GET','POST'])
def register():
   form=registeration_form()
   if form.validate_on_submit():
      duplicate=user.query.filter(user.email==form.email.data).first()
      if duplicate is None:
         hashed_password = generate_password_hash(form.password.data)
         new_user=user(username=form.username.data, email=form.email.data, pass_hash=hashed_password)

         db.session.add(new_user)
         db.session.commit()
         flash('user registered successfully')
         return redirect(url_for('home'))
      else:
         flash('emial alredy exists')
   return render_template('register.html',form=form)
   
@app.route('/login',methods=['GET','POST'])
def Login():
   form=login_form()
   if form.validate_on_submit():
      found_user=user.query.filter_by(email=form.email.data).first()
      if found_user is None:
         flash('invalid email or password')
      elif check_password_hash(found_user.pass_hash, form.password.data):
         flash('login successful')
         session['user_id']=found_user.id
         return redirect(url_for('dashboard'))
      else:
         flash('invalid email or password')
      return redirect(url_for('Login'))

   return render_template('login.html',form=form)

@app.route('/dashboard')
def dashboard():
   curr_user=session['user_id']
   customer=user.query.filter(user.id==curr_user).first()
   return render_template('dashboard.html',customer=customer)

@app.route('/habits')
def habitspage():
   curr_user=session['user_id']
   customer=user.query.filter(user.id==curr_user).first()
   habit=customer.habits
   return render_template('habits.html',habits=habit)


@app.route('/createhabit', methods=['GET','POST'])
def create_habit():
   form=createhabit_form()
   if form.validate_on_submit():
      userid=session['user_id']
      new_habit=habit(name=form.name.data, description=form.description.data, user_id=userid, created_at=datetime.now(UTC))
      db.session.add(new_habit)
      db.session.commit()
      return redirect(url_for('habitspage'))
   return render_template('create_habit.html',form=form)

@app.route('/logout')
def logout():
   session.pop('user_id', None)
   return redirect(url_for('home'))

@app.route('/delete/<int:habit_id>')
def delete(habit_id):
   del_habit=habit.query.filter(habit.id==habit_id).first()
   db.session.delete(del_habit)
   db.session.commit()
   return redirect(url_for('habitspage'))

@app.route('/edit/<int:habit_id>', methods=['GET', 'POST'])
def edit_habit(habit_id):
   habit_edit=habit.query.filter(habit.id==habit_id).first()
   form=createhabit_form()
   if form.validate_on_submit():
      habit_edit.name=form.name.data
      habit_edit.description=form.description.data
      db.session.commit()
      return redirect(url_for('habitspage'))
   form.name.data=habit_edit.name
   form.description.data=habit_edit.description
   return render_template('edit_habit.html', form=form)

@app.route('/complete_habit/<int:habit_id>', methods=['GET','POST'])
def complete_habit(habit_id):
   logs=habitlog.query.filter(habit_id==habitlog.id).all()
   crr_date=date.today()
   exits=False
   for log in logs:
      if log.date==crr_date:
         exits=True
   if exits==False:
      new_log=habitlog(habit_id=habit_id, date=crr_date)
      db.session.add(new_log)
      db.session.commit()
   return redirect(url_for('habitspage'))

@app.route('/streaks/<int:habit_id>')
def streaks(habit_id):
   logs=habitlog.query.filter(habit_id==habit_id).all()
   date_list=[]
   for log in logs:
      date_list=date_list+[log.date]
   date_list.sort()
   current=1
   best=1
   for i in range(1,len(date_list)):
      if date_list[i]-date_list[i-1] == timedelta(days=1):
         current=current+1
         best=max(best,current)
      else:
         current=1
   return render_template('streaks.html',varc=current,varb=best)
      






with app.app_context():
    db.create_all()
if __name__=="__main__":
   app.run(debug=False)
