from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, and_

from config import Config
from extensions import db, login_manager
from models import User, Post, Comment, Like, Question, Message
from forms import (
    RegisterForm, LoginForm, PostForm, CommentForm,
    ProfileEditForm, AskForm, AnswerForm, MessageForm
)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)

with app.app_context():
    db.create_all()


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("관리자만 접근할 수 있습니다.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(6).all()
    public_questions = Question.query.filter_by(is_public=True).order_by(Question.created_at.desc()).limit(4).all()

    if current_user.is_authenticated:
        posts = Post.query.order_by(Post.created_at.desc()).all()
        comment_forms = {post.id: CommentForm(prefix=str(post.id)) for post in posts}
        return render_template(
            "index.html",
            logged_in=True,
            posts=posts,
            comment_forms=comment_forms,
            recent_posts=recent_posts,
            public_questions=public_questions
        )

    return render_template(
        "index.html",
        logged_in=False,
        recent_posts=recent_posts,
        public_questions=public_questions
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            student_id=form.student_id.data,
            real_name=form.real_name.data,
            school=form.school.data,
            grade=form.grade.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("회원가입이 완료되었습니다.")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("로그인되었습니다.")
            return redirect(url_for("index"))
        flash("이메일 또는 비밀번호가 올바르지 않습니다.")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃되었습니다.")
    return redirect(url_for("index"))


@app.route("/post/create", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("게시글이 등록되었습니다.")
        return redirect(url_for("index"))
    return render_template("create_post.html", form=form)


@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm(prefix=str(post.id))
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash("댓글이 등록되었습니다.")
    return redirect(url_for("index"))


@app.route("/post/<int:post_id>/like")
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post.id))

    db.session.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user and not current_user.is_admin:
        flash("삭제 권한이 없습니다.")
        return redirect(url_for("index"))

    db.session.delete(post)
    db.session.commit()
    flash("게시글이 삭제되었습니다.")
    return redirect(url_for("index"))


@app.route("/profile/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    public_questions = Question.query.filter_by(receiver_id=user.id, is_public=True).order_by(Question.created_at.desc()).all()
    return render_template("profile.html", user=user, posts=posts, public_questions=public_questions)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileEditForm()

    if request.method == "GET":
        form.bio.data = current_user.bio
        form.school.data = current_user.school
        form.grade.data = current_user.grade

    if form.validate_on_submit():
        current_user.bio = form.bio.data
        current_user.school = form.school.data
        current_user.grade = form.grade.data
        db.session.commit()
        flash("프로필이 수정되었습니다.")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("edit_profile.html", form=form)


@app.route("/ask/<username>", methods=["GET", "POST"])
@login_required
def ask(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = AskForm()

    if form.validate_on_submit():
        sender_id = None if form.is_anonymous.data else current_user.id
        question = Question(
            content=form.content.data,
            sender_id=sender_id,
            receiver_id=user.id,
            is_anonymous=form.is_anonymous.data
        )
        db.session.add(question)
        db.session.commit()
        flash("질문을 보냈습니다.")
        return redirect(url_for("profile", username=user.username))

    return render_template("ask.html", form=form, user=user)


@app.route("/questions")
@login_required
def my_questions():
    questions = Question.query.filter_by(receiver_id=current_user.id).order_by(Question.created_at.desc()).all()
    return render_template("admin_questions.html", questions=questions, mine=True)


@app.route("/question/<int:question_id>/answer", methods=["GET", "POST"])
@login_required
def answer_question(question_id):
    question = Question.query.get_or_404(question_id)

    if question.receiver_id != current_user.id and not current_user.is_admin:
        flash("권한이 없습니다.")
        return redirect(url_for("index"))

    form = AnswerForm()
    if form.validate_on_submit():
        question.answer = form.answer.data
        question.is_public = form.is_public.data
        db.session.commit()
        flash("답변이 등록되었습니다.")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("ask.html", form=form, question=question, answer_mode=True)


@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    users = []
    if q:
        users = User.query.filter(
            or_(
                User.username.contains(q),
                User.real_name.contains(q),
                User.school.contains(q)
            )
        ).all()
    return render_template("search.html", users=users, q=q)


@app.route("/inbox")
@login_required
def inbox():
    messages = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).all()

    partner_ids = []
    for m in messages:
        other = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        if other not in partner_ids:
            partner_ids.append(other)

    users = User.query.filter(User.id.in_(partner_ids)).all() if partner_ids else []
    return render_template("inbox.html", users=users)


@app.route("/chat/<username>", methods=["GET", "POST"])
@login_required
def chat(username):
    other_user = User.query.filter_by(username=username).first_or_404()
    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(
            content=form.content.data,
            sender_id=current_user.id,
            receiver_id=other_user.id
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for("chat", username=other_user.username))

    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user.id),
            and_(Message.sender_id == other_user.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()

    return render_template("chat.html", other_user=other_user, messages=messages, form=form)


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    user_count = User.query.count()
    post_count = Post.query.count()
    question_count = Question.query.count()
    return render_template(
        "admin_dashboard.html",
        user_count=user_count,
        post_count=post_count,
        question_count=question_count
    )


@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/posts")
@login_required
@admin_required
def admin_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("admin_posts.html", posts=posts)


@app.route("/admin/questions")
@login_required
@admin_required
def admin_questions():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template("admin_questions.html", questions=questions, mine=False)


@app.route("/admin/user/<int:user_id>/delete")
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("자기 자신은 삭제할 수 없습니다.")
        return redirect(url_for("admin_users"))
    db.session.delete(user)
    db.session.commit()
    flash("회원이 삭제되었습니다.")
    return redirect(url_for("admin_users"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)