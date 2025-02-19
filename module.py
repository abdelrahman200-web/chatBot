import sqlite3
import os
import bcrypt
import datetime
# إنشاء اتصال بقاعدة البيانات
def get_db_connection():
    db_path = os.getenv("DB_PATH", "whatsapp_bot")  # تحديد اسم قاعدة البيانات أو مسارها
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # تمكين الوصول إلى الصفوف كقواميس
    return conn
#=======================for bot===============================
def update_user_region(phone_number, region_name):
    """تحديث المنطقة الخاصة بالمستخدم بعد اختياره لها."""
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "UPDATE users SET region_name = ? WHERE phone_number = ?"
    cursor.execute(sql, (region_name, phone_number))
    connection.commit()
    connection.close()

def insert_user(phone_number):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = """
    INSERT INTO users (phone_number, last_interaction, language)
    VALUES (?, CURRENT_TIMESTAMP, 'ar')
    ON CONFLICT(phone_number) DO UPDATE SET last_interaction = CURRENT_TIMESTAMP
    """
    cursor.execute(sql, (phone_number,))
    connection.commit()
    connection.close()

def get_categories(user_language):
    """جلب التصنيفات باللغة المناسبة"""
    connection = get_db_connection()
    cursor = connection.cursor()

    # ✅ اختيار العمود المناسب حسب اللغة
    column_name = "category_name_en" if user_language == "english" else "category_name"

    sql = f"SELECT id, {column_name} AS category_name FROM categories"
    cursor.execute(sql)
    
    categories = cursor.fetchall()
    connection.close()

    return categories  # تحويل الصفوف إلى قواميس

def get_issues_by_category(category_id, user_language):
    """جلب المشاكل الخاصة بتصنيف معين باللغة المناسبة"""
    connection = get_db_connection()
    cursor = connection.cursor()

    # ✅ تحديد الأعمدة الصحيحة بناءً على لغة المستخدم
    issue_column = "issue_name_en" if user_language == "english" else "issue_name"
    desc_column = "description_en" if user_language == "english" else "description"

    sql = f"SELECT id, {issue_column} AS issue_name, {desc_column} AS description FROM issues WHERE category_id = ?"
    cursor.execute(sql, (category_id,))
    issues = cursor.fetchall()
    connection.close()

    # ✅ تحويل البيانات إلى قائمة قواميس، مع قص النصوص لتجنب أخطاء WhatsApp API
    formatted_issues = [
        {
            "id": str(issue["id"]),  # تحويل ID إلى نص
            "title": issue["issue_name"][:24] if issue["issue_name"] else "No Title",  # الحد الأقصى 24 حرفًا
            "description": issue["description"][:50] if issue["description"] else "No description available"  
        }
        for issue in [dict(row) for row in issues]  # ✅ تحويل الصفوف إلى قواميس
    ]

    return formatted_issues

def update_session_stage(phone_number, stage):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = "UPDATE users SET session_stage = ? WHERE phone_number = ?"
    cursor.execute(sql, (stage, phone_number))
    
    connection.commit()
    connection.close()

#=======================for dashbord===============================
def get_All_category():
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = "SELECT * FROM categories"
    cursor.execute(sql)

    categories = cursor.fetchall()
    connection.close()
    return categories

def get_issues_by_category_name(category_name):
    connection = get_db_connection()
    cursor = connection.cursor()

    # الاستعلام الصحيح مع JOIN
    sql = """
        SELECT issues.id, issues.issue_name, issues.issue_link
        FROM issues
        JOIN category ON issues.category_id = category.id
        WHERE category.category_name = ?
    """
    
    cursor.execute(sql, (category_name,))  # استخدم ? بدلاً من %s

    issues = cursor.fetchall()
    connection.close()
    
    # تحويل النتائج إلى قائمة قواميس لتسهيل قراءتها
    return issues

def get_All_issues():
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = "SELECT * FROM issues"
    cursor.execute(sql)

    issues = cursor.fetchall()
    connection.close()
    return issues

# إضافة تصنيف جديد
def add_category(name , experts_link , category_name_en):
    try:
     connection = get_db_connection()
     cursor = connection.cursor()
     sql = "INSERT INTO categories (category_name , experts_link , category_name_en) VALUES (?, ?, ?)"
     cursor.execute(sql, (name, experts_link,category_name_en,))
     connection.commit()
     connection.close()
     return True
    except :
        return False

# حذف تصنيف
def delete_category(category_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "DELETE FROM categories WHERE id = ?"
    cursor.execute(sql, (category_id,))
    connection.commit()
    connection.close()
# تحديث اسم التصنيف
def update_category(category_id, new_name):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "UPDATE categories SET category_name = ? WHERE id = ?"
    cursor.execute(sql, (new_name, category_id))
    connection.commit()
    connection.close()
# إضافة مشكلة جديدة
def add_issue(category_id, issue_name, issue_link,description , issue_name_en,description_en):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO issues (category_id, issue_name, issue_link, description, issue_name_en, description_en) VALUES (?, ?, ?, ?, ?, ?)"
    cursor.execute(sql, (category_id, issue_name, issue_link,description,issue_name_en,description_en))
    connection.commit()
    connection.close()

# حذف مشكلة
def delete_issue(issue_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "DELETE FROM issues WHERE id = ?"
    cursor.execute(sql, (issue_id,))
    connection.commit()
    connection.close()

# ✅ تحديث بيانات المشكلة بالكامل (العربية والإنجليزية)
def update_issue(issue_id, new_category_id, new_issue_name, new_issue_name_en, new_description, new_description_en, new_issue_link):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = """
        UPDATE issues 
        SET category_id = ?, issue_name = ?, issue_name_en = ?, description = ?, description_en = ?, issue_link = ? 
        WHERE id = ?
    """
    cursor.execute(sql, (new_category_id, new_issue_name, new_issue_name_en, new_description, new_description_en, new_issue_link, issue_id))
    connection.commit()
    connection.close()

#جلب جميع المستخدمين
def get_all_users():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = "SELECT * FROM users"
    cursor.execute(sql)
    
    users = cursor.fetchall()
    connection.close()
    
    return users

# تسجيل مستخدم جديد
def register_user(username, password):
    connection = get_db_connection()
    cursor = connection.cursor()

    # 🔐 Encrypt password & decode to UTF-8 before storing
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        sql = "INSERT INTO admin (username, password_hash) VALUES (?, ?)"
        cursor.execute(sql, (username, password_hash))
        connection.commit()
        connection.close()
        return True
    except sqlite3.IntegrityError:
        connection.close()
        return False  # Handle duplicate username case properly
    
    #تسجيل دخول المستخدم
def login_user(username, password):
    connection = get_db_connection()
    connection.row_factory = sqlite3.Row  # Enables dictionary-like access
    cursor = connection.cursor()
    
    sql = "SELECT * FROM admin WHERE username = ?"
    cursor.execute(sql, (username,))
    
    user = cursor.fetchone()
    connection.close()

    # ✅ Check if user exists before accessing its data
    if user is None:
        return False

    # ✅ Password hash should already be a string, so remove extra encoding
    stored_hashed_password = user["password_hash"]  

    if bcrypt.checkpw(password.encode("utf-8"), stored_hashed_password.encode("utf-8")):
        return True

    return False

# لتخزين تفاعل المستخدم
def log_interaction(user_id, category_id=None, issue_id=None, message=""):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = """
    INSERT INTO interactions (user_id, category_id, issue_id, message)
    VALUES (?, ?, ?, ?)
    """
    
    cursor.execute(sql, (user_id, category_id, issue_id, message))
    connection.commit()
    connection.close()
    
#✅ دالة جلب رابط المشكلة
def get_issue_link(issue_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = "SELECT issue_link FROM issues WHERE id = ?"
    cursor.execute(sql, (issue_id,))
    
    row = cursor.fetchone()
    connection.close()
    
    return row["issue_link"] if row else None

# ارجاع رابط المجموعة الخاصة بالخبراء 
def get_experts_link(category_id):
    """جلب رابط مجموعة الخبراء الخاصة بتصنيف معين"""
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = "SELECT experts_link FROM categories WHERE id = ?"
    cursor.execute(sql, (category_id,))
    row = cursor.fetchone()
    connection.close()

    return row["experts_link"] if row and row["experts_link"] else None

# دالة لتحديث لغة المستخدم
def update_user_language(phone_number, language):
    """تحديث لغة المستخدم في قاعدة البيانات"""
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = "UPDATE users SET language = ? WHERE phone_number = ?"
    cursor.execute(sql, (language, phone_number))
    connection.commit()
    connection.close()

# ارجاع لفة المستحدم 
def get_user_language(phone_number):
    """جلب لغة المستخدم من قاعدة البيانات"""
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = "SELECT language FROM users WHERE phone_number = ?"
    cursor.execute(sql, (phone_number,))
    row = cursor.fetchone()
    connection.close()

    return row["language"] if row and row["language"] else "arabic"  # ✅ اللغة الافتراضية

# تحديث آخر وقت تفاعل للمستخدم  
import datetime

def update_last_interaction(phone_number):
    """تحديث آخر وقت تفاعل للمستخدم يدوياً"""
    connection = get_db_connection()
    cursor = connection.cursor()

    # 🔹 استخدم datetime.now() لتحصل على الوقت الحالي
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sql = "UPDATE users SET last_interaction = ? WHERE phone_number = ?"
    cursor.execute(sql, (now, phone_number))

    connection.commit()
    connection.close()

    
#  جلب التصنيف المرتبط بالمشكلة  
def get_category_by_issue(issue):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "select category_id from issues where id=?"
    cursor.execute(sql, (issue,))
    category_id=cursor.fetchone()
    connection.commit()
    connection.close()
    return category_id["category_id"] if category_id and category_id["category_id"] else None

def get_error_codes():
    """إرجاع قائمة بجميع رموز الأخطاء والإجراءات."""
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "SELECT code, action_ar, action_en FROM error_codes"
    cursor.execute(sql)
    error_codes = cursor.fetchall()
    connection.close()
    
    return [
        {"code": row["code"], "action_ar": row["action_ar"], "action_en": row["action_en"]}
        for row in error_codes
    ]

def add_error_code(code, action_ar, action_en):
    """إضافة رمز خطأ جديد إلى قاعدة البيانات"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        sql = "INSERT INTO error_codes (code, action_ar, action_en) VALUES (?, ?, ?)"
        cursor.execute(sql, (code, action_ar, action_en))
        connection.commit()
        return True  # تم الإدخال بنجاح
    except sqlite3.IntegrityError:
        return False  # فشل الإدخال بسبب تكرار الكود الأساسي
    finally:
        connection.close()

def delete_error_code(code):
    """حذف رمز خطأ من قاعدة البيانات"""
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = "DELETE FROM error_codes WHERE code = ?"
    cursor.execute(sql, (code,))
    connection.commit()
    
    deleted = cursor.rowcount > 0  # التحقق مما إذا تم الحذف بالفعل
    connection.close()
    
    return deleted

def get_error_action(error_code):
    """إرجاع الإجراء المرتبط برمز الخطأ."""
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "SELECT action_ar, action_en FROM error_codes WHERE code = ?"
    cursor.execute(sql, (error_code,))
    row = cursor.fetchone()
    connection.close()

    return {"action_ar": row["action_ar"], "action_en": row["action_en"]} if row else None

def delete_region(region_id):
    """حذف منطقة من قاعدة البيانات"""
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = "DELETE FROM region WHERE id = ?"
    cursor.execute(sql, (region_id,))
    connection.commit()
    
    deleted = cursor.rowcount > 0  # التحقق مما إذا تم الحذف بالفعل
    connection.close()
    
    return deleted

def add_region(name):
    """إضافة منطقة جديدة إلى قاعدة البيانات"""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        sql = "INSERT INTO region (name) VALUES (?)"
        cursor.execute(sql, (name,))
        connection.commit()
        connection.close()
        return True
    except sqlite3.IntegrityError:
        connection.close()
        return False  # إذا كان الاسم مكررًا

def get_regions():
    """إرجاع قائمة المناطق المتاحة من قاعدة البيانات."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM region")
    regions = cursor.fetchall()
    connection.close()
    return [{"id": str(r["id"]), "title": r["name"][:24]} for r in regions]

SESSION_TIMEOUT = 1  # عدد الدقائق قبل انتهاء الجلسة
def has_session_expired(user_phone):
    """التحقق مما إذا كانت الجلسة قد انتهت بسبب عدم النشاط"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = "SELECT last_interaction FROM users WHERE phone_number = ?"
    cursor.execute(sql, (user_phone,))
    row = cursor.fetchone()
    
    if row and row["last_interaction"]:
        last_interaction_str = row["last_interaction"]
        
        try:
            last_interaction = datetime.datetime.strptime(last_interaction_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("⚠️ خطأ في تنسيق التاريخ المخزن!")
            return False  # تجنب إنهاء الجلسة بسبب خطأ في البيانات
        
        now = datetime.datetime.now()
        time_difference = (now - last_interaction).total_seconds() / 60  # فرق الوقت بالدقائق

        if time_difference > SESSION_TIMEOUT:
            
            return True  # ✅ الجلسة انتهت

    return False  # ✅ الجلسة لا تزال نشطة
