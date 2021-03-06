# -*- coding: utf-8 -*-
#coding=utf-8

from flask import render_template, redirect, request, url_for, flash, current_app, abort
from flask_login import login_required, current_user

from app import db
from app.decorators import department_required
from app.models.Role import Permission
from app.models.Post import Post
from app.models.Course import Course
from app.models.User import DepartmentUser
from app.models.Arrange import Arrange, ArrangeTime

from datetime import datetime

from . import department
from .forms import PostForm, CourseForm, ArrangeForm, ArrangeTimeSpanForm

# 发布公告
@department.route('/post/add', methods=['GET', 'POST'])
@login_required
@department_required
def post():
    form = PostForm()
    if current_user.username != current_app.config['ADMIN'] and form.validate_on_submit():
        post = Post(
            body=form.body.data,
            author_id=current_user.id,
            title=form.title.data,
            post_time=datetime.utcnow()
        )
        db.session.add(post)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template(
        'department/post_add.html',
        form=form
    )

# 查看公告列表，或者删除公告
@department.route('/post/list', methods=['GET'])
@login_required
@department_required
def post_list():
    return render_template(
        'department/post_list.html',
        posts=Post.query.filter_by(author_id=current_user.id).order_by(Post.post_time.desc()).all()
    )

# 删除公告
@department.route('/post/del/<int:id>', methods=['GET'])
@login_required
@department_required
def del_post(id):
    post = Post.query.filter_by(id=id).first()
    if post:
        db.session.delete(post)
        db.session.commit()
        flash(u'删除成功')
    else:
        flash(u'删除失败，公告已经不存在了')
    return redirect(
        url_for('department.post_list')
    )

# 编辑公告
@department.route('/post/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@department_required
def edit_post(id):
    form = PostForm()
    post = Post.query.filter_by(id=id).first()
    if post is None:
        return abort(404)
    if form.validate_on_submit():
        post.body = form.body.data
        post.title = form.title.data
        post.post_time = datetime.utcnow()
        db.session.add(post)
        db.session.commit()
        flash(u'公告已经成功更改')
        return redirect(url_for('department.post_list'))
    form.body.data = post.body
    form.title.data = post.title
    return render_template(
        'department/post_edit.html',
        form=form
    )

# 添加课程
@department.route('/course/add', methods=['GET', 'POST'])
@login_required
@department_required
def add_course():
    form = CourseForm()
    form.set_choices()
    department_id = DepartmentUser.query.filter_by(id=current_user.id).first().department_id
    if form.validate_on_submit():
        course = Course(
            code=form.code.data,
            name=form.name.data,
            nature=form.nature.data,
            credit=form.credit.data,
            department_id=department_id,
            description=form.description.data
        )
        db.session.add(course)
        db.session.commit()
        flash(u'添加课程成功')
        return redirect(request.args.get('next') or url_for('department.list_course'))
    return render_template('department/add_course.html', form=form)

# 显示课程列表
@department.route('/course/list', methods=['GET'])
@login_required
@department_required
def list_course():
    department_id = DepartmentUser.query.filter_by(id=current_user.id).first().department_id
    courses = Course.query.filter_by(department_id=department_id).all()
    return render_template(
        'department/list_course.html', courses=courses
    )

# 编辑课程
@department.route('/course/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@department_required
def edit_course(id):
    form = CourseForm()
    form.set_choices()
    course = Course.query.filter_by(id=id).first()
    if course is None:
        return abort(404)
    if form.validate_on_submit():
        course.code = form.code.data
        course.name = form.name.data
        course.nature = form.nature.data
        course.credit = form.credit.data
        course.description = form.description.data
        db.session.add(course)
        db.session.commit()
        flash(u'修改课程成功')
        return redirect(url_for('department.list_course'))
    form.code.data = course.code
    form.name.data = course.name
    form.nature.data = course.nature
    form.credit.data = course.credit
    form.description = course.description
    return render_template('department/edit_course.html', form=form)

# 删除课程
@department.route('course/del/<int:id>', methods=['GET', 'POST'])
@login_required
@department_required
def del_course(id):
    course = Course.query.filter_by(id=id).first()
    if course is None:
        return abort(404)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('department.list_course'))


# 安排课程
@department.route('course/arrange', methods=['GET', 'POST'])
@login_required
@department_required
def arrange_course():
    nowdep = DepartmentUser.query.filter_by(id=current_user.id).first()
    form = ArrangeForm()
    form.set_choices(nowdep.department.id)
    if form.validate_on_submit():
        arrange = Arrange(
            year=form.year.data,
            semaster=form.semaster.data,
            course_id=form.course.data,
            teacher_id=form.teacher.data,
            place_id=form.place.data,
            department_id=nowdep.department.id
        )
        db.session.add(arrange)
        db.session.commit()
        flash(u'你已经成功添加了一门课程安排，请为其安排上课时间')
        return redirect(url_for('department.arrange_course_timespan', arrange_id=arrange.id))
    return render_template('department/arrange_course.html', form=form)

# 安排课程时间
@department.route('course/arrange_time/<int:arrange_id>', methods=['GET', 'POST'])
@login_required
@department_required
def arrange_course_timespan(arrange_id):
    form = ArrangeTimeSpanForm()
    form.set_choices(arrange_id=arrange_id)
    if form.validate_on_submit():
        arrange_time = ArrangeTime(
            id = arrange_id,
            timespan_id=form.timespan.data
        )
        db.session.add(arrange_time)
        db.session.commit()
    choosed = ArrangeTime.query.filter_by(id=arrange_id).all()
    return render_template(
        'department/arrange_course_time.html',
        form=form,
        choosed=choosed)

# 删除课程安排时间
@department.route('course/arrange_time/del/<int:arrange_id>/<int:timespan_id>')
@login_required
@department_required
def del_course_timespan(arrange_id, timespan_id):
    result = ArrangeTime.query.filter_by(id=arrange_id, timespan_id=timespan_id).first()
    if result:
        db.session.delete(result)
        db.session.commit()
    return redirect(url_for('department.arrange_course_timespan', arrange_id=arrange_id))

# 显示课程安排列表
@department.route('course/arrange/list', methods=['GET', 'POST'])
@login_required
@department_required
def arrange_list():
    current_department = DepartmentUser.query.filter_by(id=current_user.id).first().department
    arranges = Arrange.query.filter_by(department=current_department).order_by(Arrange.year.desc()).all()
    return render_template(
        'department/arrange_list.html',
        arranges=arranges
    )

# 删除课程安排
@department.route('course/arrange/del/<int:id>', methods=['GET'])
@login_required
@department_required
def del_arrange(id):
    arrange = Arrange.query.filter_by(id=id).first()
    if arrange is not None:
        db.session.delete(arrange)
        db.session.commit()
    return redirect(url_for('department.arrange_list'))
