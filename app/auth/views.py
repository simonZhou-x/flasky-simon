#coding=utf-8
from flask import render_template,redirect, request,url_for,flash
from flask_login import login_user, logout_user, login_required
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm
from .. import db

@auth.route('/login', methods=['GET','POST'])
def login():
	form = LoginForm()
	#判断用户是否点击了submit按钮
	if form.validate_on_submit():
		#查询数据库，判断用户是否存在，如果存在函数返回用户名，如果不存在，返回None
		user = User.query.filter_by(email=form.email.data).first()
		#verify_password函数接受表单中password数据，如果与用户名匹配则返回True
		if user is not None and user.verify_password(form.password.data):
			#此函数标记登录的用户，登录用户为第一个参数，第二个参数由表单中的复选框给予，已判断是否记住用户
			login_user(user, form.remember_me.data)
			#重定向到主页，由于上面已经标记了登录用户，所以页面为登录状态
			return redirect(url_for('main.index'))
		flash('Invalid username or password.')
	return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been loged out.')
	return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data,username=form.username.data,password=form.password.data)
		db.session.add(user)
		flash('You can now login.')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form=form)