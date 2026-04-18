import sqlite3
import pandas as pd
import urllib.parse
from flask import Flask, render_template, request, redirect, session, send_file


import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, session, send_file

conn = sqlite3.connect("services.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
except:
    pass

try:
    cursor.execute("ALTER TABLE requests ADD COLUMN status TEXT DEFAULT 'Pending'")
except:
    pass

conn.commit()
conn.close()

app = Flask(__name__)
app.secret_key = "ammar_secret"


# ======================
# 1️⃣ صفحة تسجيل الدخول
# ======================

@app.route("/", methods=["GET", "POST"])
def login_page():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("services.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM users
        WHERE username=? AND password=?
        """, (username, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]   # 🔥 مهم
            session["role"] = user[4]

            return redirect("/services")

        else:
            return render_template("login.html", error="Invalid login ❌")

    return render_template("login.html")

# ======================
#analytics  
# ======================
@app.route("/analytics")
def analytics():

    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT service, COUNT(service)
    FROM requests
    GROUP BY service
    """)

    data = cursor.fetchall()

    services = []
    counts = []

    for row in data:
        services.append(row[0])
        counts.append(row[1])

    conn.close()

    return render_template("analytics.html",
                           services=services,
                           counts=counts)


# ======================
#requests  
# ======================

@app.route("/requests")
def requests():

    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, service, phone, date, status FROM requests")
    rows = cursor.fetchall()

    conn.close()

    return render_template("requests.html", rows=rows)

# ======================
#مايركوست 
# # ======================

@app.route("/my_requests")
def my_requests():

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    cursor.execute(
    "SELECT * FROM requests WHERE name=?",
    (session["username"],)
    )

    data = cursor.fetchall()

    conn.close()

    return render_template("my_requests.html",data=data)

# ======================
#ساين اب 
# # ======================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        phone = request.form.get("phone")

        conn = sqlite3.connect("services.db")
        cursor = conn.cursor()

        # تحقق هل اليوزر موجود
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            conn.close()
            return "Username already exists ❌"

        # تسجيل المستخدم
        cursor.execute("""
        INSERT INTO users (username, password, phone)
        VALUES (?, ?, ?)
        """, (username, password, phone))

        conn.commit()

        # تسجيل دخول تلقائي
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        session["user_id"] = user[0]
        session["role"] = "user"

        conn.close()

        return redirect("/services")

    return render_template("signup.html")

# ======================
# تسجيل الدخول
# ======================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("services.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM users WHERE username=? AND password=?
        """, (username, password))

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[4]   # مهم

            return redirect("/services")

        else:
            return "Invalid login ❌"

    return render_template("login.html")

# ======================
# بروفايل
# ======================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, phone FROM users WHERE id=?", (session["user_id"],))
    user = cursor.fetchone()

    conn.close()

    return render_template("profile.html", user=user)

# ======================
# تغيير كلمة المرور
# ======================

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        conn = sqlite3.connect("services.db")
        cursor = conn.cursor()

        # تحقق من الباسورد القديم
        cursor.execute("SELECT password FROM users WHERE id=?", (session["user_id"],))
        current_password = cursor.fetchone()[0]

        if old_password != current_password:
            conn.close()
            return render_template("change_password.html", error="Wrong password ❌")

        # تحديث
        cursor.execute("UPDATE users SET password=? WHERE id=?",
                       (new_password, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect("/profile")

    return render_template("change_password.html")


# ======================
# تسجيل الخروج
# ======================

@app.route("/logout")
def logout():

    session.pop("admin_access", None)

    return redirect("/login")


# ======================
# 2️⃣ استقبال طلب الخدمة
# ======================


import requests
import sqlite3

@app.route("/submit", methods=["POST"])
def submit():

    name = request.form.get("name")
    service = request.form.get("service")

    country_code = request.form.get("country_code")
    phone = request.form.get("phone")

    if country_code and phone:
        phone = country_code + phone

    # 💾 حفظ
    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO requests (name, service, phone)
    VALUES (?, ?, ?)
    """, (name, service, phone))

    conn.commit()
    conn.close()

    # 🔔 تيليجرام
    BOT_TOKEN = "8686281299:AAGKWfQH49bVkaHn5RAeJZDnJOk-NkfaCDc"
    CHAT_ID = "6946363829"   # ✅ هذا الصح

    message = f"""
🔥 طلب جديد

👤 الاسم: {name}
📦 الخدمة: {service}
📞 الرقم: {phone}

⚡ من موقع Step Services
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

    print(response.text)  # 🔥 مهم للتأكد

    # ✅ صفحة النجاح
    return render_template("success.html")

# ======================
# 2️⃣ تواصل بنا
# ======================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        import requests

        BOT_TOKEN = "******"
        CHAT_ID = "*******"

        text = f"""
📩 New Contact Message

👤 Name: {name}
📧 Email: {email}

💬 Message:
{message}
"""

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        })

        return render_template("contact.html", success=True)

    return render_template("contact.html")

# ======================
# 3️⃣ صفحة الخدمات
# ======================

@app.route("/services")
def services():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("index.html")

# ======================
# 3️⃣ صفحة عننا
# ======================

@app.route("/about")
def about():
    return render_template("about.html")


# ======================
# 4️⃣ لوحة التحكم
# ======================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    # 🔐 admin access logic
    if session.get("role") != "admin" and not session.get("admin_access"):

        if request.method == "POST":
            admin_code = request.form.get("admin_code")

            if admin_code == "9999":
                session["admin_access"] = True
            else:
                return render_template("admin_lock.html", error="رمز غير صحيح ❌")

        else:
            return render_template("admin_lock.html")

    # =====================
    # 📊 البيانات (المشكلة كانت هنا)
    # =====================

    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    # عدد الطلبات
    cursor.execute("SELECT COUNT(*) FROM requests")
    total_requests = cursor.fetchone()[0]

    # عدد المستخدمين
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # أكثر خدمة
    cursor.execute("""
    SELECT service, COUNT(*) as count
    FROM requests
    GROUP BY service
    ORDER BY count DESC
    LIMIT 1
    """)
    most_service = cursor.fetchone()

    # بيانات التشارت
    cursor.execute("""
    SELECT service, COUNT(*) FROM requests GROUP BY service
    """)
    chart_data = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_requests=total_requests,
        total_users=total_users,
        most_service=most_service,
        chart_data=chart_data
    )
# ======================
# تصدير Excel
# ======================

@app.route("/export")
def export():

    conn = sqlite3.connect("services.db")

    df = pd.read_sql_query(
        "SELECT name,service,phone,date FROM requests",
        conn
    )

    conn.close()

    file = "requests.xlsx"

    df.to_excel(file, index=False)

    return send_file(file, as_attachment=True)

# ======================
# تشغيل Done 
# ======================

@app.route("/done/<int:id>")
def done(id):

    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE requests SET status='Done' WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/requests")

# ======================
# تشغيل الحذف 
# ======================

@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("services.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM requests WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/requests")




# ======================
# تشغيل السيرفر
# ======================

if __name__ == "__main__":
    app.run(debug=True)

