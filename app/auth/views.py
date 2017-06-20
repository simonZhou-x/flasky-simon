#coding=utf-8
from flask import render_template,redirect, request,url_for,flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm, NewPassword, InputPassword, ResetPassword, ResetEmail
from .. import db
from ..email import send_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

@auth.before_app_request
def before_request():
	if current_user.is_authenticated and current_user.confirmed==0 and request.endpoint and request.endpoint[:5] != 'auth.' and request.endpoint !='static':
		return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
	if current_user.is_anonymous and current_user.confirmed==1:
		return redirect(url_for('main.index'))
	return render_template('auth/unconfirmed.html')

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
			return redirect(request.args.get('next') or url_for('main.index'))
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
		user = User(email=form.email.data,email2=form.email.data,username=form.username.data,password=form.password.data)
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_email(user.email, 'Confirm Your Account','auth/email/confirm',user=user,token=token)
		flash('A confirmation email has been sent to you by email.')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
#保护路由，需要登录才能显示该路由
@login_required
def confirm(token):
	if current_user.confirmed==1:
		return redirect(url_for('main.index'))
	if current_user.reset_email(token):
		current_user.email = current_user.email2
		flash(u'你的新邮箱变更已生效，请用新邮箱登录。')
	elif current_user.confirm(token):
		flash(u'您已验证你的邮箱，谢谢！')
	else:
		flash(u'检查链接无效或已过期。')
	return redirect(url_for('main.index'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
	token = current_user.generate_reset_token()
	if current_user.email2 is not None:
		send_email(current_user.email2,'Confirm Your Account', 'auth/email/confirm',user=current_user, token=token)
		#current_user.email = current_user.email2
		#db.session.add(current_user)
	else:
		send_email(current_user.email,'Confirm Your Account', 'auth/email/confirm',user=current_user, token=token)
	flash(u'验证邮件已发送到您的邮箱，请查看确认。')
	logout_user()
	return redirect(url_for('main.index'))

@auth.route('/repassword',methods=['GET','POST'])
@login_required
def repassword():
	form = NewPassword()
	if form.validate_on_submit():
		if not current_user.verify_password(form.old_password.data):
			flash('password error.')
			return redirect(url_for('auth.repassword'))
		current_user.password = form.newpassword.data
		db.session.add(current_user)
		logout_user()
		flash(u'密码已变更，请使用新密码登录。')
		return redirect(url_for('main.index'))
	return render_template('auth/repassword.html', form=form)

@auth.route('/sendemail',methods=['GET','POST'])
def sendmail():
	form = InputPassword()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None:
			token = user.generate_reset_token()
			send_email(form.email.data,u'重置密码','auth/email/resetpassword',user=user,token=token)
			flash(u'我们已发送一封邮件到您的邮箱.')
			return redirect(url_for('auth.login'))
		else:
			flash(u'邮箱未注册。')
	return render_template('auth/send_email.html',form=form)

@auth.route('/resetpassword/<token>',methods=['GET','POST'])
def resetpassword(token):
	if not current_user.is_anonymous:
		flash(u'用户已登录')
		return redirect(url_for('main.index'))
	form = ResetPassword()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is None:
			flash('aaaa')
			return redirect(url_for('main.index'))
		if user.reset_password(token, form.newpassword.data):
			flash('Your password has been updated.')
			return redirect(url_for('auth.login'))
		else:
			flash('aaaaaa')
			return redirect(url_for('main.index'))
	return render_template('auth/repassword.html', form=form)


@auth.route('/reset_email',methods=['GET','POST'])
@login_required
def reset_email():
	form = ResetEmail()
	if form.validate_on_submit():
		user = current_user.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			token = user.generate_reset_token()
			send_email(form.newemail.data,u'验证邮箱','auth/email/reset_email',user=user,token=token)
			flash(u'已发送邮件到新邮箱.')
			user.email2 = form.newemail.data
			user.confirmed = 0
			db.session.add(user)
			logout_user()
			return redirect(url_for('auth.login'))
		else:
			flash(u'请输入正确的邮箱')
	return render_template('auth/reset_email.html',form=form)

#@auth.route('/reset/email/<token>',methods=['GET','POST'])
#@login_required
#def resetemail(token):
	#if not current_user.is_anonymous:
		#flash(u'用户已登录')
		#return redirect(url_for('main.index'))
	#	if current_user.confirmed==0:
		#	return redirect(url_for('main.index'))
#	s = Serializer(current_user.config['SECRET_KEY'])
#	data = s.lodas(token)
#	id=data.get('reset')
#	user = User.query.filter_by(id=id).first()
#	if user.reset_email(token,current_user.email2):
		#current_user.email = current_user.email2
		#db.session.add(current_user)
#		flash('You have confirmed your account. Thanks!')
#	else:
#		flash('The confirmation link is invalid or has expired.')
#	return redirect(url_for('main.index'))
