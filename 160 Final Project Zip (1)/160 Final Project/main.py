from flask import Flask, render_template, request, redirect, session
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
#Needs password below
conn_str = "mysql://root:PASSWORD@localhost/160finaldb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


@app.route("/")
def get_index():
    return render_template("index.html", loggedin=session.get("username"), success=None)


@app.route("/login", methods=["GET"])
def get_login_template():
    session["username"] = None
    session["acct_type"] = None
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    try:
        user = conn.execute(
            text(f"SELECT username FROM accounts WHERE password = :password AND username = :email_or_username OR email = :email_or_username"),
            request.form
        )
        user = "".join(user.first())
        session["username"] = user
        acct_type = conn.execute(
            text(f"SELECT acct_type FROM accounts WHERE username = '{session.get('username')}'")).first()
        acct_type = "".join(acct_type)
        session["acct_type"] = acct_type
        return redirect("/")
    except Exception:
        error = "Incorrect login information"
        return render_template("login.html", error=error)


@app.route("/logout", methods=["GET"])
def logout():
    session["username"] = None
    session["acct_type"] = None
    return redirect("/")


@app.route("/register", methods=["GET"])
def get_register_template():
    session["username"] = None
    session["acct_type"] = None
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    if request.form.get("password") == request.form.get("password-confirm"):
        try:
            conn.execute(
                text(f"INSERT INTO accounts (email, username, password, acct_type) VALUES (:email, :username, :password, :radio)"),
                request.form
            )
            conn.commit()
            session["username"] = request.form.get("username")
            session["acct_type"] = request.form.get("radio")
            return render_template("index.html", success="Account created successfully!", loggedin=session.get("username"))
        except Exception:
            return render_template("register.html", error="Unexpected error encountered", succes=None)
    else:
        return render_template("register.html", error="Passwords do not match", success=None)


@app.route("/tests", methods=["GET"])
def get_test_taking_template():
    tests = conn.execute(text("SELECT * FROM tests"))
    return render_template("test_list.html", loggedin=session.get("username"), tests=tests, acct_type=session.get("acct_type"))


@app.route("/tests/<test>")
def take_test(test):
    if conn.execute(text(f"SELECT * FROM test_results WHERE test_name = '{test}' AND student_name = '{session.get('username')}'")).all():
        return render_template("index.html", loggedin=session.get("username"), success=f"You've already taken {test}")
    else:
        questions = conn.execute(text(f"SELECT question FROM test_questions WHERE test_name = '{test}'"))
        return render_template("testing.html", test=test, questions=questions, loggedin=session.get("username"), acct_type=session.get("acct_type"))


@app.route("/tests/<test>", methods=["POST"])
def submit_test(test):
    num_questions = conn.execute(text(f"SELECT num_questions FROM tests WHERE test_name = '{test}'")).first()
    for i in range(0, num_questions[0]):
        conn.execute(text(f"INSERT INTO test_results (student_name, test_name, question_num, answer)"
                          f"VALUES ('{session.get('username')}', '{test}', {i + 1}, '{request.form.get(f'question-{i + 1}')}')"))
    conn.commit()
    return render_template("index.html", loggedin=session.get("username"), success="Results recorded")


@app.route("/tests_and_grades", methods=["GET"])
def get_manage_tests_template():
    tests = conn.execute(text("SELECT * FROM tests"))
    return render_template("manage_tests.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), tests=tests, success=None)


@app.route("/update_tests/<test>", methods=["GET"])
def get_update_test_template(test):
    creator = conn.execute(text(f"SELECT created_by FROM tests WHERE test_name = '{test}'")).first()
    creator = "".join(creator)
    questions = conn.execute(text(f"SELECT question FROM test_questions WHERE test_name = '{test}'"))
    test = conn.execute(text(f"SELECT * FROM tests WHERE test_name = '{test}'")).first()
    return render_template("update.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), questions=questions, test=test, creator=creator)


@app.route("/update_tests/<test>", methods=["POST"])
def update(test):
    try:
        num_question = conn.execute(text(f"SELECT num_questions FROM tests WHERE test_name = '{test}'")).first()
        questions = conn.execute(text(f"SELECT question FROM test_questions WHERE test_name = '{test}'")).all()
        conn.execute(text(f"UPDATE tests SET test_name = '{request.form.get('test-name')}' WHERE test_name = '{test}'"))
        for i in range(0, num_question[0]):
            conn.execute(text(f"UPDATE test_questions SET question = '{request.form.get(f'question-{i + 1}')}' WHERE question = '{''.join(questions[i])}' AND test_name = '{test}'"))
        conn.execute(text(f"UPDATE test_questions SET test_name = '{request.form.get('test-name')}' WHERE test_name = '{test}'"))
        conn.commit()
        return render_template("index.html", loggedin=session.get("username"), success="Test updated successfully!")
    except Exception:
        return render_template("create_test.html", error="Unexpected error encountered", acct_type=session.get("acct_type"), loggedin=session.get("username"))


@app.route("/create_new_test", methods=["GET"])
def get_creation_template():
    return render_template("create_test.html", error=None, acct_type=session.get("acct_type"), loggedin=session.get("username"))


@app.route("/create_new_test", methods=["POST"])
def create_test():
    try:
        conn.execute(
            text(f"INSERT INTO tests (created_by, test_name, date_created, num_questions) "
                 f"VALUES ('{session.get("username")}', '{request.form.get("test_name")}',"
                 f" CURDATE(), {int(request.form.get('num_questions'))})"))
        for i in range(0, int(request.form.get("num_questions"))):
            conn.execute(text(f"INSERT INTO test_questions (question, test_name)"
                              f"VALUES ('{request.form.get(f'question-{i + 1}')}', '{request.form.get("test_name")}')"))
        conn.commit()
        return render_template("index.html", loggedin=session.get("username"), success="Test created successfully!")
    except Exception:
        error = "Error encountered"
        return render_template("create_test.html", error=error)


@app.route("/delete/<test>", methods=["GET"])
def delete_test_template(test):
    test = conn.execute(text(f"SELECT * FROM tests WHERE test_name = '{test}'")).first()
    return render_template("delete_test.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), test=test)


@app.route("/delete/<test>", methods=["POST"])
def delete_test(test):
    if request.form.get("radio") == "delete":
        conn.execute(text(f"DELETE FROM tests WHERE test_name = '{test}'"))
        conn.execute(text(f"DELETE FROM test_questions WHERE test_name = '{test}'"))
        conn.commit()
        return render_template("index.html", loggedin=session.get("username"), success="Test deleted successfully")
    else:
        tests = conn.execute(text("SELECT * FROM tests"))
        return render_template("manage_tests.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), tests=tests, success=None)


@app.route("/manage_grades", methods=["GET"])
def get_grades_template():
    students = conn.execute(text("SELECT * FROM accounts WHERE acct_type = 'student'")).all()
    return render_template("students.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), students=students, grades=None)


@app.route("/students/grades/<student>", methods=["GET"])
def get_student_grades(student):
    grades = conn.execute(text(f"SELECT * FROM grades WHERE student_name = '{student}'")).all()
    return render_template("students.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), grades=grades)


@app.route("/students/<student>", methods=["GET"])
def get_student_info(student):
    tests_taken = conn.execute(text(f"SELECT test_name FROM test_results WHERE student_name = '{student}'")).all()
    return render_template("student_info.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), student=student, tests_taken=tests_taken, results=None)


@app.route("/students/<student>/<test>", methods=["GET"])
def get_grade_info(student, test):
    results = conn.execute(text(f"SELECT * FROM test_results WHERE student_name = '{student}' AND test_name = '{test}'")).all()
    questions = conn.execute(text(f"SELECT question FROM test_questions WHERE test_name = '{test}'")).all()
    return render_template("student_info.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), questions=questions, student=student, tests_taken=None, results=results, test=test)


@app.route("/students/<student>/<test>", methods=["POST"])
def post_grade(student, test):
    if conn.execute(text(f"SELECT * FROM grades WHERE test_name = '{test}' AND graded_by = '{session.get('username')}' AND student_name = '{student}'")):
        conn.execute(text(f"DELETE FROM grades WHERE test_name = '{test}' AND graded_by = '{session.get('username')}' AND student_name = '{student}'"))
    conn.execute(text(f"INSERT INTO grades (test_name, grade, student_name, graded_by, time_graded)"
                      f"VALUES ('{test}', '{request.form.get('grade')} / {request.form.get('max-points')}', '{student}', '{session.get('username')}', CURRENT_TIMESTAMP())"))
    conn.commit()
    return render_template("index.html", loggedin=session.get("username"), success="Grade posted successfully!")


@app.route("/tests/info/<test>", methods=["GET"])
def get_test_info(test):
    test_vals = conn.execute(text(f"SELECT * FROM tests WHERE test_name = '{test}'")).first()
    num_of_students = conn.execute(text("SELECT COUNT(DISTINCT student_name) FROM test_results")).first()
    grades = conn.execute(text(f"SELECT * FROM grades WHERE test_name = '{test}'")).all()
    return render_template("test_info.html", loggedin=session.get("username"), acct_type=session.get("acct_type"), test_vals=test_vals, num_of_students=num_of_students, grades=grades)


if __name__ == "__main__":
    app.run(debug=True)
