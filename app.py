import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify
)

import psycopg2

from psycopg2.extras import RealDictCursor

from datetime import datetime



app = Flask(__name__)

app.secret_key = "ri_studio_secret_key"



# =====================
# АДМИНЫ
# =====================

ADMINS = {

    8019907955: "Иван",

    975812111: "Никита",

    820298635: "Никита"

}





# =====================
# DATABASE
# =====================


def db():

    return psycopg2.connect(

        os.environ.get("DATABASE_URL"),

        cursor_factory=RealDictCursor

    )





def init_db():


    con = db()

    cur = con.cursor()



    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets(

        id SERIAL PRIMARY KEY,

        user_name TEXT,

        title TEXT,

        reason TEXT,

        description TEXT,

        status TEXT,

        created TEXT

    )
    """)



    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(

        id SERIAL PRIMARY KEY,

        ticket_id INTEGER,

        sender TEXT,

        text TEXT,

        created TEXT

    )
    """)




    cur.execute("""
    CREATE TABLE IF NOT EXISTS ratings(

        id SERIAL PRIMARY KEY,

        ticket_id INTEGER,

        rating INTEGER,

        created TEXT

    )
    """)



    con.commit()

    cur.close()

    con.close()







# =====================
# ГЛАВНАЯ
# =====================


@app.route("/")
def index():

    return render_template(
        "index.html"
    )





# =====================
# СОЗДАНИЕ ТИКЕТА
# =====================


@app.route("/create")
def create_page():

    return render_template(
        "create.html"
    )





@app.route(
"/create_ticket",
methods=["POST"]
)
def create_ticket():


    con = db()

    cur = con.cursor()



    cur.execute(
    """
    INSERT INTO tickets

    (
    user_name,
    title,
    reason,
    description,
    status,
    created
    )

    VALUES(%s,%s,%s,%s,%s,%s)

    RETURNING id

    """,

    (

    request.form["user"],

    request.form["title"],

    request.form["reason"],

    request.form["description"],

    "Открыт",

    str(datetime.now())

    )

    )



    ticket_id = cur.fetchone()["id"]





    cur.execute(
    """
    INSERT INTO messages

    (
    ticket_id,
    sender,
    text,
    created
    )

    VALUES(%s,%s,%s,%s)

    """,

    (

    ticket_id,

    "Система",

    "🎫 Тикет создан",

    str(datetime.now())

    )

    )



    con.commit()


    cur.close()

    con.close()



    print(
        f"🔔 Новый тикет #{ticket_id}"
    )



    return redirect(
        f"/ticket/{ticket_id}"
    )







# =====================
# ПОЛЬЗОВАТЕЛЬСКИЙ ЧАТ
# =====================


@app.route(
"/ticket/<int:id>",
methods=["GET","POST"]
)
def ticket(id):


    con=db()

    cur=con.cursor()



    cur.execute(
    """
    SELECT *

    FROM tickets

    WHERE id=%s

    """,

    (id,)

    )



    ticket=cur.fetchone()



    if not ticket:

        return "Тикет не найден"





    if request.method=="POST":



        if ticket["status"]=="Закрыт":

            return "closed"




        cur.execute(
        """
        INSERT INTO messages

        (
        ticket_id,
        sender,
        text,
        created
        )

        VALUES(%s,%s,%s,%s)

        """,

        (

        id,

        "Пользователь",

        request.form["text"],

        str(datetime.now())

        )

        )



        con.commit()



        return "ok"





    cur.close()

    con.close()



    return render_template(
        "ticket.html",
        ticket=ticket
    )








# =====================
# СООБЩЕНИЯ
# =====================


@app.route(
"/messages/<int:id>"
)
def messages(id):


    con=db()

    cur=con.cursor()



    cur.execute(
    """
    SELECT *

    FROM messages

    WHERE ticket_id=%s

    ORDER BY id

    """,

    (id,)

    )



    data=cur.fetchall()



    cur.close()

    con.close()



    return jsonify(data)







# =====================
# ОЦЕНКА
# =====================


@app.route(
"/rate/<int:id>",
methods=["POST"]
)
def rate(id):


    con=db()

    cur=con.cursor()



    cur.execute(
    """
    INSERT INTO ratings

    (
    ticket_id,
    rating,
    created
    )

    VALUES(%s,%s,%s)

    """,

    (

    id,

    request.form["rating"],

    str(datetime.now())

    )

    )



    con.commit()


    cur.close()

    con.close()



    return redirect(
        f"/ticket/{id}"
    )







# =====================
# LOGIN ADMIN
# =====================


@app.route(
"/admin/login",
methods=["GET","POST"]
)
def admin_login():


    if request.method=="POST":


        admin_id=int(
            request.form["id"]
        )


        if admin_id in ADMINS:


            session["admin"]=admin_id


            return redirect(
                "/admin"
            )



    return render_template(
        "admin_login.html"
    )







# =====================
# ADMIN PANEL
# =====================


@app.route("/admin")
def admin():


    if "admin" not in session:

        return redirect(
            "/admin/login"
        )



    con=db()

    cur=con.cursor()



    cur.execute(
    """
    SELECT *

    FROM tickets

    ORDER BY id DESC

    """
    )



    tickets=cur.fetchall()



    return render_template(

        "admin.html",

        tickets=tickets,

        admin_name=ADMINS[
            session["admin"]
        ]

    )







# =====================
# ADMIN TICKET
# =====================


@app.route(
"/admin/ticket/<int:id>",
methods=["GET","POST"]
)
def admin_ticket(id):


    if "admin" not in session:

        return redirect(
            "/admin/login"
        )



    con=db()

    cur=con.cursor()



    if request.method=="POST":


        cur.execute(
        """
        INSERT INTO messages

        (
        ticket_id,
        sender,
        text,
        created
        )

        VALUES(%s,%s,%s,%s)

        """,

        (

        id,

        ADMINS[
            session["admin"]
        ],

        request.form["text"],

        str(datetime.now())

        )

        )



        con.commit()



        return "ok"




    cur.execute(
    """
    SELECT *

    FROM tickets

    WHERE id=%s

    """,

    (id,)

    )



    ticket=cur.fetchone()



    return render_template(

        "admin_ticket.html",

        ticket=ticket

    )







# =====================
# CLOSE TICKET
# =====================


@app.route(
"/admin/close/<int:id>"
)
def close(id):


    if "admin" not in session:

        return redirect(
            "/admin/login"
        )



    con=db()

    cur=con.cursor()



    cur.execute(
    """
    UPDATE tickets

    SET status='Закрыт'

    WHERE id=%s

    """,

    (id,)

    )




    cur.execute(
    """
    INSERT INTO messages

    (
    ticket_id,
    sender,
    text,
    created
    )

    VALUES(%s,%s,%s,%s)

    """,

    (

    id,

    "Система",

    "🔒 Чат закрыт. Спасибо за обращение! Заходите ещё 🙂",

    str(datetime.now())

    )

    )



    con.commit()



    return redirect(
        f"/admin/ticket/{id}"
    )







# =====================
# STATS
# =====================


@app.route("/admin/stats")
def stats():


    if "admin" not in session:

        return redirect(
            "/admin/login"
        )



    con=db()

    cur=con.cursor()



    cur.execute(
    "SELECT COUNT(*) FROM tickets"
    )

    tickets=cur.fetchone()["count"]



    cur.execute(
    """
    SELECT COUNT(DISTINCT user_name)

    FROM tickets
    """
    )

    users=cur.fetchone()["count"]




    cur.execute(
    """
    SELECT COUNT(*)

    FROM tickets

    WHERE status='Закрыт'

    """
    )

    closed=cur.fetchone()["count"]




    return render_template(

        "stats.html",

        users=users,

        tickets=tickets,

        closed=closed

    )






init_db()

if __name__=="__main__":


    init_db()


    app.run(
        host="0.0.0.0",
        port=5000
    )
