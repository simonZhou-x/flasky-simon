#coding=utf-8
import os
from flask import abort, render_template,redirect, request,url_for,flash,current_app, make_response
from . import main
from ..models import User, Role, Permission, Post, Comment
from .. import db
from .forms import FileForm, EditProfileForm, EditProfileAdiminForm, PostForm, CommentForm
from flask_login import login_required, current_user
from ..decorators import admin_required
from ..decorators import permission_required
from flask_sqlalchemy import get_debug_queries
import random

@main.after_app_request
def after_request(response):
	for query in get_debug_queries():
		if query.duration >= 0.5:
			current_app.logger.warning('Slow query:%s\nParameters:%s\nDuration:%fs\nContext:%s\n'%(query.statement,query.parameters,query.duration,query.context))
	return response

@main.route('/', methods=['GET', 'POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		post = Post(body=form.body.data, author=current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	show_followed = False
	if current_user.is_authenticated:
		show_followed = bool(request.cookies.get('show_followed',''))
	if show_followed:
		query = current_user.followed_posts
	else:
		query = Post.query
	pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=int(current_app.config['FLASKY_POSTS_PER_PAGE']),error_out=False)
	posts = pagination.items
	#comments = Comment.query.filter_by(post_id=post.id).all()
	a = 0
	return render_template('index.html', form=form, posts=posts,show_followed=show_followed, pagination=pagination,a=a)

@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed','',max_age=30*24*60*60)
	return resp
	
@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed','1',max_age=30*24*60*60)
	return resp

@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	posts = user.posts.order_by(Post.timestamp.desc()).all()
	return render_template('user.html', user=user, posts=posts, img=user.img)

@main.route('/edit-profile', methods=['GET','POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		flash(u'你的资料已更新。')
		return redirect(url_for('.user',username=current_user.username))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', form=form, user=current_user)

@main.route('/edit-profile/<int:id>', methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdiminForm(user=user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		flash(u'资料已更新')
		return redirect(url_for('.user', username=user.username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form=form, user=user)

@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.body.data,post=post,author=current_user._get_current_object())
		db.session.add(comment)
		flash(u'你的评论已发布')
		return redirect(url_for('.post', id=post.id, page=-1))
	page = request.args.get('page',1,type=int)
	if page == -1:
		page = (post.comments.count() -1)/current_app.config['FLASKY_COMMENTS_PER_PAGE'] +1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
	comments = pagination.items
	return render_template('post.html', posts=[post],form=form,comments=comments,pagination=pagination)

@main.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		flash(u'帖子已更新')
		return redirect(url_for('.post',id=post.id))
	form.body.data = post.body
	return render_template('edit_post.html',form=form, post=post)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash(u'用户不存在')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		flash(u'你已经关注了此用户')
		return redirect(url_for('.user',username=username))
	current_user.follow(user)
	flash(u'你现在关注了 %s.'% username)
	return redirect(url_for('.user', username=username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash(u'用户不存在')
		return redirect(url_for('.index'))
	current_user.unfollow(user)
	flash(u'你已经取消了对此用户的关注')
	return redirect(url_for('.user',username=username))

@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash(u'用户不存在')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.paginate(page, per_page=int(current_app.config['FLASKY_FOLLOWERS_PER_PAGE']),error_out=False)
	follows = [{'user':item.follower, 'timestamp':item.timestamp} for item in pagination.items]
	return render_template('followers.html',user=user,title=u'的关注者',endpoint='.followers',pagination=pagination,follows=follows)

@main.route('/followed_by/<username>')
def followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash(u'用户不存在')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followed.paginate(page, per_page=int(current_app.config['FLASKY_FOLLOWERS_PER_PAGE']),error_out=False)
	follows = [{'user':item.followed, 'timestamp':item.timestamp} for item in pagination.items]
	return render_template('followers.html',user=user,title=u'关注的用户',endpoint='.followers',pagination=pagination,follows=follows)

@main.route('/delete_posts/<int:id>')
@login_required
def delete_posts(id):
	posts = Post.query.filter_by(id=id).first()
	if posts is None:
		flash(u'帖子不存在')
		return redirect(url_for('.index'))
	else:
		db.session.delete(posts)
		flash(u'帖子已删除')
		return redirect(url_for('.index'))

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page=int(current_app.config['FLASKY_POSTS_PER_PAGE']),error_out=False)
	comments = pagination.items
	return render_template('moderate.html', comments=comments, pagination=pagination)

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def disable(id):
	comment = Comment.query.filter_by(id=id).first()
	if comment is None:
		flash(u'帖子不存在')
		return redirect(url_for('.moderate'))
	else:
		comment.disabled = True
		db.session.add(comment)
		flash(u'帖子已隐藏')
		return redirect(url_for('.moderate'))


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def enable(id):
	comment = Comment.query.filter_by(id=id).first()
	if comment is None:
		flash(u'帖子不存在')
		return redirect(url_for('.moderate'))
	else:
		comment.disabled = False
		db.session.add(comment)
		flash(u'帖子已显示')
		return redirect(url_for('.moderate'))

@main.route('/user/file',methods=['GET','POST'])
@login_required
def file():
	form = FileForm()
	if form.validate_on_submit():
		file = form.file.data
		filename = random.randint(0,999999)
		file.save('app/static/images/%s.jpg'%filename)
		if current_user.img:
			os.remove('app/static/%s'%current_user.img)
		current_user.img = 'images/%s.jpg' %filename
		db.session.add(current_user)
		flash(u'头像修改成功')
		return redirect(url_for('.user',username=current_user.username))
	return render_template('file_form.html',form=form)
