#coding=utf-8
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, NumberRange
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import ValidationError
from ..models import User, Role
from flask_pagedown.fields import PageDownField

class EditProfileForm(FlaskForm):
	name = StringField(u'真实姓名', validators=[Length(0,64)])
	location = StringField(u'住址', validators=[Length(0,64)])
	about_me = TextAreaField(u'关于我')
	submit = SubmitField(u'提交')

class EditProfileAdiminForm(FlaskForm):
	email = StringField(u'邮箱',validators=[Required(),Length(1,64),Email()])
	username = StringField(u'用户名',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,u'用户名只能使用字母、数字、点或者下划线')])
	confirmed = IntegerField(u'验证',validators=[NumberRange(0,1,u'1代表已验证，0代表未验证')])
	role = SelectField(u'用户组',coerce=int)
	name = StringField(u'真实姓名', validators=[Length(0,64)])
	location = StringField(u'住址', validators=[Length(0,64)])
	about_me = TextAreaField(u'关于我')
	submit = SubmitField(u'提交')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdiminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
		self.user = user 

	def validate_email(self, field):
		if field.data != self.user.email and User.query.filter_by(email=field.data).first():
			raise ValidationError(u'用户名已被注册')

	def validate_username(self, field):
		if field.data != self.user.username and User.query.filter_by(username=field.data).first():
			raise ValidationError(u'用户名已被使用')

class PostForm(FlaskForm):
    body = PageDownField(u'说点什么吧 (>▽<)', validators=[Required()])
    submit = SubmitField(u'提交')

class CommentForm(FlaskForm):
	body = StringField('',validators=[Required()])
	submit = SubmitField(u'提交')

class FileForm(FlaskForm):
	file = FileField(u'选择文件',validators=[FileAllowed(['jpg','png'],u'只能上传图片'),FileRequired(u'文件未选择')])
	submit = SubmitField(u'提交')