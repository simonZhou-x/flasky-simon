#coding=utf-8
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
	email = StringField(u'邮箱',validators=[Required(), Length(1,64),Email()])
	password = PasswordField(u'密码',validators=[Required()])
	remember_me = BooleanField(u'记住我')
	submit = SubmitField(u'登录')

class RegistrationForm(FlaskForm):
	email = StringField(u'邮箱', validators=[Required(), Length(1,64),Email()])
	username = StringField(u'用户名', validators=[Required(), Length(1,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, ''numbers, dots or underscores')])
	password = PasswordField(u'密码', validators=[Required(),EqualTo('password2', message='Password must match.')])
	password2 = PasswordField(u'确认密码', validators=[Required()])
	submit = SubmitField(u'注册')

	#验证用户所使用的邮箱能否在数据库检索到，如果返回True，则说明邮箱已注册，返回错误信息
	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError(u'此邮箱已注册。')


	#同上，验证用户名
	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError(u'用户名已存在。')

class NewPassword(FlaskForm):
	
	old_password = PasswordField(u'原密码',validators=[Required()])
	newpassword = PasswordField(u'新密码', validators=[Required(),EqualTo('newpassword2',message='Password must match.')])
	newpassword2 = PasswordField(u'确认新密码', validators=[Required()])
	submit = SubmitField(u'提交')

	
class InputPassword(FlaskForm):
	email = StringField(u'邮箱',validators=[Required(),Length(1,64),Email()])
	submit = SubmitField(u'提交')

class ResetPassword(FlaskForm):
	email = StringField(u'邮箱', validators=[Required(), Length(1, 64),Email()])
	newpassword=PasswordField(u'新密码', validators=[Required(),EqualTo('newpassword2',message='Password must match.')])
	newpassword2 = PasswordField(u'确认密码',validators=[Required()])
	submit = SubmitField(u'提交')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first() is None:
			raise ValidationError(u'邮箱地址无效。')

class ResetEmail(FlaskForm):
	email = StringField(u'邮箱',validators=[Required(),Length(1,64),Email()])
	password = PasswordField(u'密码', validators=[Required()])
	newemail = StringField(u'新邮箱',validators=[Required(),Length(1,64),Email()])
	submit = SubmitField(u'提交')

	def validate_newemail(self,field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError(u'这个邮箱已经被注册啦。')



