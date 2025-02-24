from flask import Flask,request, jsonify,redirect,url_for,render_template,session,flash
import os
import module as module
import Statistics_function as Statistics
import bot_function as bot
from flask_login import login_user, logout_user, login_required
import login as log

app=Flask(__name__)
WHATSAPP_TOKEN="EAAIfUtZBlkpEBO8LldTgRzFZBG0OIvkcrVsFZAqvdmjhRTA3mUaanaxYa5SHJK8HSNf6ZC0tV32kOJyp3BjpU6RxL8HqGym0t8SoiIf4tzK3X7PTBXmevkStog8igu9xvk30DGlgKZBQTc8aADB6HnCFErMakP04CAYH0dNqtNkM2DHXGJkpzZB96QiwzkZAq4TmgZDZD"
PHONE_NUMBER_ID="560613013806982"
VERIFY_TOKEN="1966820c6ab65959244fdc849247dd74f40ba0f632d0b19987ae2bdf292e4810"
app.secret_key = "1966820c6ab65959244fdc849247dd74f40ba0f632d0b19987ae2bdf292e4810"  # 🔐 استخدم مفتاحًا آمنًا للجلسات
log.login_manager.init_app(app)  # تهيئة Flask-Login
@app.route('/')
def d():
    return render_template("login.html")
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':  # تحقق من Webhook
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        return "Verification failed", 403

    elif request.method == 'POST':  # استقبال الرسائل
        data = request.json
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    messages = change.get("value", {}).get("messages", [])
                    if messages:  # إذا كانت هناك رسائل
                        message = messages[0]  # احصل على أول رسالة فقط
                        bot.handle_message(message)  # معالجة الرسالة الواردة
                    else:
                        # إذا لم تكن هناك رسائل في القائمة
                        return "No messages received", 200
        # إذا لم يتم استيفاء شرط "whatsapp_business_account"
        return "EVENT_RECEIVED", 200

    # إذا لم تكن الطريقة GET أو POST
    return "Method not allowed", 405


@app.route('/main', methods=['GET'])
@login_required
def main():
    issues = module.get_All_issues()
    categories=module.get_All_category()
    return render_template('main.html',categories=categories,issues=issues)

# ✅ جلب جميع المشاكل
@app.route('/issues', methods=['GET'])
def get_issues():
    issues = module.get_All_issues()
    return jsonify(issues)

# ✅ جلب المشاكل حسب التصنيف
@app.route('/issues/category/<string:category_name>', methods=['GET'])
def get_issues_by_category(category_name):
    issues = module.get_issues_by_category_name(category_name)
    return jsonify(issues)

# ✅ إضافة تصنيف جديد
@app.route('/add_category', methods=['POST'])
def create_category():
    category_name = request.form.get('category_name')  # Use request.form
    experts_link=request.form.get('experts_link')
    category_name_en=request.form.get('category_name_en')
    if module.add_category(category_name , experts_link , category_name_en):
        return jsonify({"message": "تمت إضافة التصنيف بنجاح"}), 201
    else:
        return jsonify({"error": "فشل إضافة التصنيف"}), 400
# ✅ تحديث التصنيف
@app.route('/category/<int:category_id>', methods=['PUT'])
def modify_category(category_id):
    data = request.json
    module.update_category(category_id, data['new_name'])
    return jsonify({"message": "تم تحديث التصنيف بنجاح"}) ,201

# ✅ حذف التصنيف
@app.route('/category/<int:category_id>', methods=['DELETE'])
def remove_category(category_id):
    module.delete_category(category_id)
    return jsonify({"message": "تم حذف التصنيف بنجاح"}),200

# ✅ إضافة مشكلة جديدة
@app.route('/add_issue', methods=['POST'])
def create_issue():
    category_id = request.form.get('category_id')  # Get category ID
    issue_name = request.form.get('issue_name')    # Get issue name
    issue_link = request.form.get('issue_link')    # Get issue link
    description = request.form.get('description')
    issue_name_en = request.form.get('issue_name_en')
    description_en = request.form.get('description_en')
    if category_id and issue_name and issue_link:  # Ensure all fields are provided
        module.add_issue(category_id, issue_name, issue_link,description ,issue_name_en,description_en)
        return jsonify({"message": "تمت إضافة المشكلة بنجاح"}), 201
    else:
        return jsonify({"error": "يرجى ملء جميع الحقول"}), 400  # Return an error if any field is missing


# ✅ تحديث المشكلة
@app.route('/issue/<int:issue_id>', methods=['PUT'])
def modify_issue(issue_id):
    data = request.json
    module.update_issue(issue_id, data['new_category_id'], data['new_issue_name'], data['new_issue_link'])
    return jsonify({"message": "تم تحديث المشكلة بنجاح"}),201

# ✅ حذف المشكلة
@app.route('/issue/<int:issue_id>', methods=['DELETE'])
def remove_issue(issue_id):
    module.delete_issue(issue_id)
    return jsonify({"message": "تم حذف المشكلة بنجاح"}),201

# ✅ جلب جميع المستخدمين
@app.route('/users', methods=['GET'])
@login_required
def get_users():
    users = module.get_all_users()
    return render_template('user.html',users=users)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    access_kayF = request.form.get('access_kay')
    confirm_password = request.form.get('confirm_password')
    access_key=os.getenv("access_kay")
    if access_kayF==access_key:
     if not username or not password or not confirm_password:
         return jsonify({"message": "يرجى ملء جميع الحقول"}), 400

     if password != confirm_password:
         return jsonify({"message": "كلمتا المرور غير متطابقتين"}), 400

     if module.register_user(username, password):
         return jsonify({"message": "تم تسجيل المستخدم بنجاح"}), 201
     else:
         return jsonify({"message": "اسم المستخدم موجود بالفعل"}), 400
    else:
     return jsonify({"message": "مفتاح الوصول غير صحيح"}), 404


@app.route('/add_error_code', methods=['POST'])
def add_error_code_route():
    code = request.form.get('code')
    action_ar = request.form.get('action_ar')
    action_en = request.form.get('action_en')

    if not code or not action_ar or not action_en:
        return jsonify({"error": "جميع الحقول مطلوبة!"}), 400

    if module.add_error_code(code, action_ar, action_en):
        return jsonify({"message": "✅ تم إضافة رمز الخطأ بنجاح!"}), 201
    else:
        return jsonify({"error": "❌ فشل في الإضافة، قد يكون الكود موجودًا بالفعل!"}), 409

@app.route('/delete_error_code/<code>', methods=['DELETE'])
def delete_error_code_route(code):
    if module.delete_error_code(code):
        return jsonify({"message": "✅ تم حذف رمز الخطأ بنجاح!"}), 200
    else:
        return jsonify({"error": "❌ لم يتم العثور على رمز الخطأ!"}), 404

@app.route('/add_region', methods=['POST'])
def add_region_route():
    name = request.form.get("name")
    
    if not name:
        return jsonify({"error": "❌ يرجى إدخال اسم المنطقة!"}), 400
    
    if module.add_region(name):
        return jsonify({"message": "✅ تم إضافة المنطقة بنجاح!"}), 201
    else:
        return jsonify({"error": "❌ اسم المنطقة موجود بالفعل!"}), 409


@app.route('/delete_region/<int:region_id>', methods=['DELETE'])
def delete_region_route(region_id):
    if module.delete_region(region_id):
        return jsonify({"message": "✅ تم حذف المنطقة بنجاح!"}), 200
    else:
        return jsonify({"error": "❌ لم يتم العثور على المنطقة!"}), 404
#=======================================pages===================================================
@app.route('/register_page', methods=['GET'])
def register_page():
    return render_template('signup.html')

@app.route('/error_code', methods=['GET'])
@login_required
def error_code():
    error=module.get_error_codes()
    return render_template('error_code.html',error_codes=error)

@app.route('/regions', methods=['GET'])
@login_required
def get_regions():
    """إرجاع قائمة المناطق في JSON"""
    connection = module.get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM region")
    regions = cursor.fetchall()
    connection.close()

    return render_template('regions.html',regions=regions )
#==================================== for Statistics ==========================================================
@app.route('/stats', methods=['GET'])
@login_required
def get_statistics():
    stats = {
        "new_users_daily": Statistics.get_new_users_count("daily"),
        "new_users_weekly": Statistics.get_new_users_count("weekly"),
        "new_users_monthly": Statistics.get_new_users_count("monthly"),
        "new_users_yearly": Statistics.get_new_users_count("yearly"),
        "category_requests": Statistics.get_category_request_count(),
        "issue_requests": Statistics.get_issue_request_count(),
        "top_country": Statistics.get_top_cities(),
        "top_users": Statistics.get_top_users(),
        "top_regions": Statistics.get_top_regions(),
        "most_requested_options": Statistics.get_most_requested_options() 
    }    
    return render_template('static.html', stats=stats)

# 🔹 صفحة تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    print("🔄 استقبلنا طلبًا على /login")
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("❌ يرجى إدخال اسم المستخدم وكلمة المرور!", "danger")
            return redirect(url_for("login"))

        user = log.check_login(username, password)

        if user:
            login_user(user)  # ✅ تسجيل الدخول باستخدام Flask-Login
            flash("✅ تسجيل دخول ناجح!", "success")
            return redirect(request.args.get("next") or url_for("main"))  # ✅ إعادة توجيه بعد تسجيل الدخول
        else:
            flash("❌ اسم المستخدم أو كلمة المرور غير صحيحة!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# 🔹 تسجيل الخروج
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("✅ تم تسجيل الخروج بنجاح!", "success")
    return redirect(url_for("login"))
#==============================================================================================================
# ✅ عرض جميع المشرفين
@app.route("/admin_panel")
@login_required
def admin_panel():
    admins = module.get_all_admins()
    return render_template("admin.html", admins=admins)

# ✅ إضافة مشرف جديد
@app.route("/add_admin", methods=["POST"])
@login_required
def add_admin():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("❌ يرجى إدخال اسم المستخدم وكلمة المرور!", "error")
        return redirect(url_for("admin_panel"))

    if module.add_admin(username, password):
        flash("✅ تم إضافة المشرف بنجاح!", "success")
    else:
        flash("❌ اسم المستخدم موجود بالفعل!", "error")

    return redirect(url_for("admin_panel"))

# ✅ تحديث كلمة مرور مشرف
@app.route("/update_admin/<int:admin_id>", methods=["POST"])
@login_required
def update_admin(admin_id):
    new_password = request.form.get("new_password")

    if not new_password:
        flash("❌ يرجى إدخال كلمة المرور الجديدة!", "error")
        return redirect(url_for("admin_panel"))

    module.update_admin_password(admin_id, new_password)
    flash("✅ تم تحديث كلمة المرور بنجاح!", "success")
    return redirect(url_for("admin_panel"))


# ✅ حذف مشرف
@app.route("/delete_admin/<int:admin_id>", methods=["POST"])
@login_required
def delete_admin(admin_id):
    module.delete_admin(admin_id)
    flash("✅ تم حذف المشرف بنجاح!", "success")
    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
