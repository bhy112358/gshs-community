from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User


class RegisterForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField("이메일", validators=[DataRequired(), Email()])
    student_id = StringField("학번", validators=[Length(max=30)])
    real_name = StringField("이름", validators=[Length(max=50)])
    school = StringField("학교", validators=[Length(max=100)])
    grade = StringField("학년", validators=[Length(max=20)])
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(min=4, max=50)])
    confirm_password = PasswordField("비밀번호 확인", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("회원가입")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("이미 사용 중인 아이디입니다.")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("이미 사용 중인 이메일입니다.")


class LoginForm(FlaskForm):
    email = StringField("이메일", validators=[DataRequired(), Email()])
    password = PasswordField("비밀번호", validators=[DataRequired()])
    submit = SubmitField("로그인")


class PostForm(FlaskForm):
    content = TextAreaField("내용", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("게시하기")


class CommentForm(FlaskForm):
    content = StringField("댓글", validators=[DataRequired(), Length(max=300)])
    submit = SubmitField("작성")


class ProfileEditForm(FlaskForm):
    bio = TextAreaField("소개", validators=[Length(max=300)])
    school = StringField("학교", validators=[Length(max=100)])
    grade = StringField("학년", validators=[Length(max=20)])
    submit = SubmitField("저장")


class AskForm(FlaskForm):
    content = TextAreaField("질문", validators=[DataRequired(), Length(max=300)])
    is_anonymous = BooleanField("익명으로 보내기", default=True)
    submit = SubmitField("질문 보내기")


class AnswerForm(FlaskForm):
    answer = TextAreaField("답변", validators=[DataRequired(), Length(max=500)])
    is_public = BooleanField("프로필에 공개")
    submit = SubmitField("답변 등록")


class MessageForm(FlaskForm):
    content = TextAreaField("메시지", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("전송")