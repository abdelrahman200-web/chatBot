import sqlite3
import os
import phonenumbers
from phonenumbers import geocoder
# إنشاء اتصال بقاعدة البيانات
def get_db_connection():
    db_path = os.getenv("DB_PATH", "whatsapp_bot")  # تحديد اسم قاعدة البيانات أو مسارها
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # تمكين الوصول إلى الصفوف كقواميس
    return conn

#عدد المستخدمين الجدد يوميًا/شهريًا
def get_new_users_count(period="daily"):
    """حساب عدد المستخدمين الجدد خلال فترة محددة"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if period == "daily":
        sql = "SELECT COUNT(DISTINCT user_phone) FROM interactions WHERE DATE(timestamp) = DATE('now')"
    elif period == "weekly":
        sql = "SELECT COUNT(DISTINCT user_phone) FROM interactions WHERE DATE(timestamp) >= DATE('now', '-7 days')"
    elif period == "monthly":
        sql = "SELECT COUNT(DISTINCT user_phone) FROM interactions WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')"
    elif period == "yearly":
        sql = "SELECT COUNT(DISTINCT user_phone) FROM interactions WHERE strftime('%Y', timestamp) = strftime('%Y', 'now')"
    else:
        return 0  # إذا كانت الفترة غير صحيحة، نُعيد 0
        
    cursor.execute(sql)
    result = cursor.fetchone()[0]
    connection.close()
    
    return result

#عدد الطلبات لكل تصنيف
def get_category_request_count():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = """
        SELECT categories.category_name, COUNT(interactions.id) AS request_count
        FROM interactions
        JOIN categories ON interactions.category_id = categories.id
        GROUP BY interactions.category_id
        ORDER BY request_count DESC
    """
    
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()
    
    return result  # ✅ سترجع قائمة تحتوي على التصنيفات وعدد مرات طلبها

#عدد الطلبات لكل مشكلة
def get_issue_request_count():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = """
        SELECT issues.issue_name, COUNT(interactions.id) AS request_count
        FROM interactions
        JOIN issues ON interactions.issue_id = issues.id
        GROUP BY interactions.issue_id
        ORDER BY request_count DESC
    """
    
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()
    
    return result  # ✅ سترجع قائمة تحتوي على المشاكل وعدد مرات طلبها
# أكثر المدن تفاعلاً
def get_top_cities():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = """
        SELECT country, COUNT(id) AS request_count
        FROM interactions
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY request_count DESC
        LIMIT 5
    """
    
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()
    
    return result  # ✅ سترجع قائمة بأكثر 5 مدن تفاعلاً

#عدد الطلبات لكل مستخدم (لرؤية المستخدمين النشطين)
def get_top_users():
    """جلب أكثر 5 مستخدمين نشاطًا مع إظهار منطقتهم"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = """
        SELECT user_phone, 
               COALESCE(region, 'غير محدد') AS region,  -- ✅ تعيين "غير محدد" إذا كانت القيمة NULL
               COUNT(id) AS request_count
        FROM interactions
        GROUP BY user_phone
        ORDER BY request_count DESC
        LIMIT 5
    """
    
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()
    
    return result  # ✅ سترجع قائمة بأكثر 5 مستخدمين نشاطًا مع منطقتهم

# """تسجيل تفاعل المستخدم مع البوت"""
def insert_interaction(user_phone, message, category_id=None, issue_id=None, region=None, country=None, request_type=None):
    """تسجيل تفاعل المستخدم مع البوت"""
    connection = get_db_connection()
    cursor = connection.cursor()

    sql = """
    INSERT INTO interactions (user_phone, message, category_id, issue_id, region, country, request_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(sql, (user_phone, message, category_id, issue_id, region, country, request_type))
    connection.commit()
    connection.close()

def get_country_from_phone(phone_number):
    """استخراج اسم الدولة من رقم الهاتف باستخدام phonenumbers"""
    try:
        parsed_number = phonenumbers.parse(phone_number, None)  # ✅ تحليل الرقم
        country = geocoder.country_name_for_number(parsed_number, "en")  # ✅ جلب اسم الدولة
        return country
    except:
        return "Unknown"  # ❌ إذا لم يتم التعرف على الرقم

def get_most_requested_options():
    """إحصائيات أكثر الخيارات طلبًا (تعليمات السلامة - تعليمات العمل - رموز الأخطاء)"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = """
        SELECT request_type, COUNT(*) AS request_count
        FROM interactions
        WHERE request_type IN ('safety', 'work', 'error_codes')
        GROUP BY request_type
        ORDER BY request_count DESC
    """
    
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()
    
    return result  # ✅ سترجع قائمة بأكثر الخيارات طلبًا

def get_top_regions():
    """إرجاع أكثر المناطق تفاعلًا بناءً على عدد الطلبات"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    sql = """
        SELECT COALESCE(region, 'غير محدد') AS region, COUNT(*) AS request_count
        FROM interactions
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY request_count DESC
        LIMIT 5
    """
    
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()
    
    return result  # ✅ سترجع قائمة بأكثر 5 مناطق تفاعلًا
