import requests
import os
import module as module
import Statistics_function as Statistics
WHATSAPP_TOKEN="EAAPZCAhZAKUeABOwXZBRZAFGlUB7Rg4ku5ZCewEsDsHRsayqAvDQQ6yWO3u5stDlDj2fTjc3tZCZBSUyo7ZCiBiZCBrZBhYs6BAoJ3gMZCHuZBe1ahNNKzqn8r2ZAoAFTRnFhCYatgwNGSZA70v3C5TZCjfyC1GWxOgGHR7yrMG8VUysy5DaMYDYEKZAUonzXbwUyCrBTzHjCMAGLGoUkgGZAIBDBH1PsmojRxZCbR"
PHONE_NUMBER_ID="556436610884697"
VERIFY_TOKEN="1966820c6ab65959244fdc849247dd74f40ba0f632d0b19987ae2bdf292e4810"

def handle_message(message):
    sender_id = message["from"]
    text = message.get("text", {}).get("body", "").strip().lower()
    # ✅ تحديث آخر تفاعل للمستخدم
    module.update_last_interaction(sender_id)
    # جلب مرحلة المستخدم
    connection = module.get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT session_stage FROM users WHERE phone_number = ?", (sender_id,))
    row = cursor.fetchone()
    if row:
     session_stage = row["session_stage"]
     if session_stage == 'start':
        session_stage="language_selection"
    else:
        module.insert_user(sender_id)
        session_stage="start"

    if session_stage == "start":
        module.update_session_stage(sender_id, "language_selection")
        send_ar_en_buttons(sender_id)

    elif session_stage == "language_selection":
        answer=None
        if message.get("interactive") and message["interactive"].get("button_reply"):
           answer = message["interactive"]["button_reply"]["id"]
        else:
           send_message(sender_id, "⚠️ خطأ في الادخال / Input error")
           send_ar_en_buttons(sender_id)
           return
        if answer:
            if answer =='ar':
             send_message(sender_id, "تم ضبط  على اللغة العربية.")
             module.update_user_language(sender_id, "arabic")             
            elif answer =='en':
             send_message(sender_id, "Language set to English.")
             module.update_user_language(sender_id, "english")
            else:
             send_message(sender_id, "الرجاء اختيار اللغه الصحيحه / Please select the correct language.⚠️")
             send_ar_en_buttons(sender_id)
             return
        module.update_session_stage(sender_id, "region_selection")
        send_region_list(sender_id)

    elif session_stage == "region_selection":
     if message.get("interactive") and message["interactive"].get("list_reply"):
        region_name = message["interactive"]["list_reply"]["title"]
        if region_name:
         lan = module.get_user_language(sender_id)
        # ✅ حفظ اختيار المستخدم للمنطقة
         module.update_user_region(sender_id, region_name)
         if lan =='arabic':
          send_message(sender_id, f"✅ تم اختيار المنطقة: {region_name}")
         else:
            send_message(sender_id, f"✅ The area has been selected.: {region_name}")
        # ✅ الانتقال إلى الخيارات الرئيسية بعد اختيار المنطقة
         module.update_session_stage(sender_id, "main_options")
         send_main_options(sender_id,lan)
         send_return_button(sender_id)
        else:
           send_message(sender_id, "⚠️ خيار غير معروف، يرجى اختيار المنطقة من القائمة. / Unknown option, please select region from list")
           send_region_list(sender_id)
     else:
       send_message(sender_id, "⚠️ خطأ في الادخال / Input error")
       send_region_list(sender_id)

    elif session_stage == "main_options":
        if message.get("interactive") and message["interactive"].get("button_reply"):
            choice = message["interactive"]["button_reply"]["id"]
            if choice == "safety_instructions":
                send_safety_instructions(sender_id)
                module.update_session_stage(sender_id, "start")
            elif choice == "work_instructions":
                send_category_list(sender_id)
                send_return_button(sender_id)
                module.update_session_stage(sender_id, "category_selection")
            elif choice == "error_codes":
                send_error_codes(sender_id)
                send_return_button(sender_id)
                module.update_session_stage(sender_id, "error_selection")
            elif choice == "return_to_start":
               send_message(sender_id, "🔙 Returning to the start. / 🔙 الرجوع إلى البداية")
               module.update_session_stage(sender_id, "start")
               send_ar_en_buttons(sender_id)
               return
            else:
                send_message(sender_id, "⚠️ خيار غير معروف. / Unknown option.")
                lan = module.get_user_language(sender_id)
                send_main_options(sender_id,lan)
        else:
           send_message(sender_id, "⚠️ خطأ في الادخال / Input error")
           lan = module.get_user_language(sender_id)
           send_main_options(sender_id,lan)
           send_return_button(sender_id)

    elif session_stage == "error_selection":
     if message.get("interactive") and message["interactive"].get("list_reply"):
        error_code = message["interactive"]["list_reply"].get("id")

        # ✅ جلب لغة المستخدم
        lan = module.get_user_language(sender_id)

        # ✅ جلب الإجراء المناسب من قاعدة البيانات
        error_action = module.get_error_action(error_code)

        if error_action:
            action_text = error_action["action_ar"] if lan == "arabic" else error_action["action_en"]
            send_message(sender_id, f"🔍 *الإجراء المتبع لحل المشكلة {error_code}:*\n\n{action_text}")
        else:
            send_message(sender_id, "⚠️ لم يتم العثور على إجراء لهذا الرمز.")

        send_message(sender_id, "🔙 Returning to the start.")
        module.update_session_stage(sender_id, "start")  # ✅ إعادة تعيين الجلسة بعد إرسال الحل
        send_ar_en_buttons(sender_id)

     elif message.get("interactive") and message["interactive"].get("button_reply"):
        if message["interactive"]["button_reply"].get("id") == "return_to_start":
            send_message(sender_id, "🔙 Returning to the start.")
            module.update_session_stage(sender_id, "start")
            send_ar_en_buttons(sender_id)  # إعادة اختيار اللغة
     else:
        send_message(sender_id, "⚠️ خطأ في الإدخال / Input error")
        send_error_codes(sender_id)
        send_return_button(sender_id)


    elif session_stage == "category_selection":
        if text.isdigit():  # إذا كان المستخدم أدخل رقم يدويًا (يجب الاختيار من القائمة فقط)
         send_message(sender_id, "⚠️ الرجاء الاختيار من القائمة")  # ✅ رسالة تنبيه
         send_category_list(sender_id)
         return
        elif message.get("interactive") and message["interactive"].get("list_reply"):
         category_id = message["interactive"]["list_reply"]["id"]  # ✅ جلب ID التصنيف
        else:
            send_message(sender_id, "⚠️ حدث خطأ، لم يتم استقبال التصنيف بشكل صحيح.")  # ❌ خطأ في تحديد التصنيف
            send_message(sender_id, "🔙 Returning to the start.")
            module.update_session_stage(sender_id, "start")
            send_ar_en_buttons(sender_id)
            return
        if category_id.isdigit():  # ✅ تأكد أن التصنيف هو رقم
            module.update_session_stage(sender_id, "final_step")
            send_issue_list(sender_id, category_id)  # ✅ إرسال قائمة المشاكل بناءً على التصنيف
            send_return_button(sender_id)
        else:
            send_message(sender_id, "⚠️ حدث خطأ، لم يتم استقبال التصنيف بشكل صحيح.")  # ❌ خطأ في تحديد التصنيف
            send_message(sender_id, "🔙 Returning to the start.")
            module.update_session_stage(sender_id, "start")

    elif session_stage == "final_step":
     issue_link = None  # ✅ تعريف المتغير قبل الاستخدام
     if text.isdigit():
        send_message(sender_id, "⚠️ خطأ في الادخال / Input error")
        send_message(sender_id, "🔙 Returning to the start.")
        module.update_session_stage(sender_id, "start")
        send_ar_en_buttons(sender_id)
        return
     elif message.get("interactive") and message["interactive"].get("list_reply"):
        issue_id = message["interactive"]["list_reply"]["id"]
        text = message["interactive"]["list_reply"]["title"]  # ✅ جلب اسم المشكلة

        # ✅ جلب التصنيف المرتبط بالمشكلة
        category_id = module.get_category_by_issue(issue_id)

        # ✅ تخزين التفاعل فقط عند اختيار المشكلة (وليس عند اختيار التصنيف)
        user_phone = sender_id  # ✅ رقم المستخدم
        if not user_phone.startswith("+"):
         user_phone = "+" + user_phone
        # يجب ارسال الرقم في صورة string
        country = Statistics.get_country_from_phone(user_phone)  # ✅ جلب الدولة من رقم الهاتف 
        Statistics.insert_interaction(user_phone, text, category_id=category_id, issue_id=issue_id, country=country)

        issue_link = module.get_issue_link(issue_id)
     elif message["interactive"]["button_reply"]["id"] == 'return_to_start':
        send_message(sender_id, "🔙 Returning to the start.")
        module.update_session_stage(sender_id, "start")
        send_ar_en_buttons(sender_id)  # Restart language selection
        return
     else:
        send_message(sender_id, "⚠️ خطأ في الادخال / Input error")
        send_message(sender_id, "🔙 Returning to the start.")
        module.update_session_stage(sender_id, "start")
        send_ar_en_buttons(sender_id)
        return

     if issue_link:
        user_language = module.get_user_language(sender_id)  # ✅ تصحيح جلب لغة المستخدم

        if user_language == 'arabic':
            send_message(sender_id, f"🔗 رابط الحل للمشكلة:\n{issue_link}")
            send_yes_no_buttons(sender_id)  # ✅ إرسال أزرار الاختيار بعد الحل
        else:
            send_message(sender_id, f"🔗 Link to the solution:\n{issue_link}")
            send_yes_no_buttons(sender_id)

        module.update_session_stage(sender_id, "ask_experts")  # ✅ تحديث الجلسة لمرحلة سؤال الخبراء

     else:
        send_message(sender_id, "لا يوجد رابط لحل هذه المشكلة / There is no link to solve this problem.")
        send_message(sender_id, "🔙 Returning to the start.")
        module.update_session_stage(sender_id, "start")
        send_ar_en_buttons(sender_id)
        return

    elif session_stage == "ask_experts":
     if message.get("interactive") and message["interactive"].get("button_reply"):
           answer = message["interactive"]["button_reply"]["id"]
           if answer == "yes_experts":
               send_category_list(sender_id)  # ✅ إرسال قائمة التصنيفات لاختيار الخبراء
               module.update_session_stage(sender_id, "choose_expert_category")
           elif answer == "no_experts":
             lan = module.get_user_language(sender_id)
             if lan == "arabic":
                send_message(sender_id, "😊 شكرًا لك على استخدام نظامنا!")
                send_message(sender_id, "🔙 Returning to the start.")
                module.update_session_stage(sender_id, "start")
                send_ar_en_buttons(sender_id)
             else:
                send_message(sender_id, "😊 Thank you for using our system!")
             module.update_session_stage(sender_id, "start")  # ✅ إعادة تعيين الجلسة
           else:
             send_message(sender_id, "⚠️ يرجى اختيار أحد الخيارات: ✅ نعم أو ❌ لا.")
     else:
            send_message(sender_id, "⚠️ خطأ في الادخال / Input error")
            send_message(sender_id, "🔙 Returning to the start.")
            module.update_session_stage(sender_id, "start")
            send_ar_en_buttons(sender_id)
       
    elif session_stage == "choose_expert_category":
      if text.isdigit():
        send_message(sender_id, "⚠️ يرجى اختيار التصنيف من القائمة.")
        send_category_list(sender_id)
      elif message.get("interactive") and message["interactive"].get("list_reply"):
        category_id = int(message["interactive"]["list_reply"]["id"])
      else:
        send_message(sender_id, "⚠️ يرجى اختيار التصنيف من القائمة.")
        return
      if category_id:
       send_experts_message(sender_id , category_id)
       send_message(sender_id, "🔙 Returning to the start.")
       module.update_session_stage(sender_id, "start") 

def send_message(to, text):
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, json=data, headers=headers)


#======================================new====================================================
def send_category_list(to):
    """إرسال قائمة التصنيفات بلغة المستخدم عبر WhatsApp API"""
    
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # ✅ جلب لغة المستخدم
    lan = module.get_user_language(to)
    # ✅ جلب التصنيفات من قاعدة البيانات
    categories = module.get_categories(lan)

    # ✅ التأكد من وجود تصنيفات
    if not categories:
        if lan == "arabic":
            send_message(to, "⚠️ لا توجد تصنيفات متاحة حاليًا.")
        else:
            send_message(to, "⚠️ No categories available at the moment.")
        return

    # ✅ ترجمة النصوص بناءً على اللغة المختارة
    if lan == "arabic":
        body_text = "📂 اختر تصنيف المشكلة من القائمة:"
        button_text = "اختر التصنيف"
        section_title = "التصنيفات المتاحة"
    else:
        body_text = "📂 Select a category from the list:"
        button_text = "Select Category"
        section_title = "Available Categories"

    # ✅ تجهيز قائمة التصنيفات
    category_buttons = [
        {
            "id": str(c["id"]),  # تأكد أن ID نصي
            "title": c["category_name"][:24]  # WhatsApp يحد العناوين بـ 24 حرفًا
        }
        for c in categories
    ]

    # ✅ إنشاء الرسالة التفاعلية
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": [
                    {
                        "title": section_title,
                        "rows": category_buttons
                    }
                ]
            }
        }
    }

    # ✅ إرسال القائمة إلى المستخدم
    response = requests.post(url, json=data, headers=headers)
    return response.json()  # لمعرفة استجابة API


def send_issue_list(to, category_id):
    """إرسال قائمة تفاعلية بالمشاكل الخاصة بالتصنيف عبر WhatsApp API"""

    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

   # ✅ جلب لغة المستخدم
    lan = module.get_user_language(to)
     # جلب المشاكل المرتبطة بالتصنيف
    issues = module.get_issues_by_category(category_id,lan)
    

    # التحقق مما إذا كانت هناك مشاكل لهذا التصنيف
    if not issues:
        if lan == "arabic":
            send_message(to, "⚠️ لا توجد مشاكل متاحة لهذا التصنيف.")
        elif lan == "english":
            send_message(to, "⚠️ There are no issues available for this category.")
        return  # ✅ إنهاء الدالة لتجنب إرسال قائمة فارغة

    # تجهيز النصوص بناءً على لغة المستخدم
    if lan == "arabic":
        body_text = "❗ اختر المشكلة التي تواجهها:"
        button_text = "اختر المشكلة"
        section_title = "المشاكل المتاحة"
    else:
        body_text = "❗ Select the issue you are facing:"
        button_text = "Select Issue"
        section_title = "Available Issues"

    # إنشاء القائمة التفاعلية
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": [
                    {
                        "title": section_title,
                        "rows": [
                            {
                                "id": str(issue["id"]),  # تأكد أن ID نصي
                                "title": issue["title"][:24],  # الحد الأقصى للطول 24 حرفًا
                                "description": issue["description"][:50] if issue["description"] else "لا يوجد وصف"
                            }
                            for issue in issues
                        ]
                    }
                ]
            }
        }
    }

    # إرسال القائمة إلى المستخدم
    response = requests.post(url, json=data, headers=headers)
    return response.json()  # ✅ لمعرفة استجابة API


def send_yes_no_buttons(to):
    """إرسال أزرار نعم/لا لسؤال المستخدم عن التواصل مع الخبراء"""
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # ✅ جلب لغة المستخدم
    lan = module.get_user_language(to)

    # ✅ تحديد النصوص بناءً على اللغة المختارة
    if lan == "arabic":
        message_text = "هل لديك أي استفسار آخر؟\n*يرجى التواصل مع خبراء النظام.*"
        yes_text = "✅ نعم"
        no_text = "❌ لا"
       
    else:
        message_text = "Do you have any further questions?\n*Please contact our system experts.*"
        yes_text = "✅ Yes"
        no_text = "❌ No"
       

    # ✅ إنشاء بيانات الأزرار
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": message_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "yes_experts", "title": yes_text}},
                    {"type": "reply", "reply": {"id": "no_experts", "title": no_text}}
                ]
            }
        }
    }

    # ✅ إرسال البيانات إلى WhatsApp API والتحقق من الاستجابة
    try:
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        print(f"📌 استجابة WhatsApp API: {response_data}")  # ✅ طباعة الاستجابة لمراقبة الأخطاء
        return response_data
    except Exception as e:
        print(f"❌ خطأ أثناء إرسال الأزرار: {e}")
        return None


def send_ar_en_buttons(to):
    """إرسال أزرار نعم/لا لسؤال المستخدم عن التواصل مع الخبراء"""
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "🎓 *يجري اختيار اللغة المناسبة / Choose your language*"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "ar", "title": " العربية"}},
                    {"type": "reply", "reply": {"id": "en", "title": " English"}}
                ]
            }
        }
    }

    response = requests.post(url, json=data, headers=headers)
    return response.json()

def send_experts_message(to, category_id):
    """إرسال رسالة تحتوي على رابط مجموعة خبراء التصنيف المحدد باللغة المناسبة"""

    # ✅ جلب رابط الخبراء من قاعدة البيانات
    experts_link = module.get_experts_link(category_id)

    # ✅ جلب لغة المستخدم
    user_language = module.get_user_language(to)

    # ✅ إذا لم يكن هناك رابط متاح، أرسل رسالة تفيد بذلك
    if not experts_link:
        if user_language == "arabic":
            send_message(to, "⚠️ لا توجد مجموعة خبراء متاحة لهذا التصنيف في الوقت الحالي.")
        else:
            send_message(to, "⚠️ No expert group is available for this category at the moment.")
        return

    # ✅ نص الرسالة بناءً على اللغة المختارة
    if user_language == "arabic":
        message_text = f"""📢 *للتواصل مع خبراء النظام يرجى الدخول على المجموعة أدناه:*
🔗 *واتساب:* {experts_link}

______
🤝 *TAHAKOM MNT* شكرًا لاستخدامك  
نحن هنا لخدمتك في أي وقت  
إذا كان لديك أي استفسارات أو تحتاج إلى مساعدة إضافية، فلا تتردد في التواصل معنا  
نتمنى لك يومًا سعيدًا! 😊

📌 *مع تحيات الإدارة الهندسية بقسم الصيانة*"""
    
    else:  # English
        message_text = f"""📢 *To contact the experts, please join the group below:*
🔗 *WhatsApp:* {experts_link}

______
🤝 *Thank you for using TAHAKOM MNT bot.*  
We are here to assist you at any time.  
If you have any inquiries or need additional help, feel free to contact us.  
Have a great day! 😊

📌 *Thank you for contacting the engineering maintenance department*"""

    # ✅ إرسال الرسالة إلى المستخدم
    send_message(to, message_text)

#==========================================================================================
def send_main_options(to, lan):
    """إرسال الخيارات الرئيسية بعد اختيار اللغة"""
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # ✅ اختيار النصوص بناءً على اللغة
    if lan == "arabic":
        body_text = "📋 يرجى اختيار الخدمة المطلوبة:"
        safety_title = "🔹 تعليمات السلامة"[:20]  # ✅ تقصير العنوان
        work_title = "📂 تعليمات العمل"[:20]  # ✅ تقصير العنوان
        error_title = "⚠️ أخطاء فيترونيك"[:20]  # ✅ تقصير العنوان
    else:
        body_text = "📋 Please select the required service:"
        safety_title = "🔹 Safety Guide"[:20]  # ✅ تقصير العنوان
        work_title = "📂 Work Guide"[:20]  # ✅ تقصير العنوان
        error_title = "⚠️ Vitronic Errors"[:20]  # ✅ تقصير العنوان


    # ✅ إعداد الرسالة التفاعلية
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "safety_instructions", "title": safety_title}},
                    {"type": "reply", "reply": {"id": "work_instructions", "title": work_title}},
                    {"type": "reply", "reply": {"id": "error_codes", "title": error_title}}
                ]
            }
        }
    }

    # ✅ طباعة البيانات للتحقق قبل الإرسال
    print("📌 البيانات المرسلة إلى API:")

    # ✅ إرسال البيانات إلى API والتحقق من الاستجابة
    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    print(f"📌 استجابة WhatsApp API: {response_data}")  # ✅ طباعة الاستجابة للتحقق من الأخطاء

    return response_data


def send_safety_instructions(to):
    file_url = "https://yourserver.com/safety_instructions.pdf"
    send_message(to, f"📄 *تعليمات السلامة*: يمكنك تنزيل الملف من هنا:")


def send_error_codes(to):
    """إرسال قائمة رموز الأخطاء عبر واتساب."""
    
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # ✅ جلب لغة المستخدم
    lan = module.get_user_language(to)
    
    # ✅ جلب رموز الأخطاء من قاعدة البيانات
    error_codes = module.get_error_codes()
    
    # ✅ التحقق مما إذا كانت هناك رموز متاحة
    if not error_codes:
        send_message(to, "⚠️ لا توجد رموز أخطاء متاحة في الوقت الحالي." if lan == "arabic" else "⚠️ No error codes available at the moment.")
        return
    
    # ✅ تجهيز النصوص بناءً على لغة المستخدم
    if lan == "arabic":
        body_text = "⚠️ اختر رمز الخطأ لمعرفة الإجراء المناسب:"
        button_text = "اختر الرمز"
        section_title = "رموز الأخطاء المتاحة"
    else:
        body_text = "⚠️ Select the error code to see the corrective action:"
        button_text = "Select Code"
        section_title = "Available Error Codes"

    # ✅ تجهيز قائمة الرموز
    error_buttons = [
        {
            "id": error["code"],  # رمز الخطأ كـ ID
            "title": error["code"],  # يظهر الرمز فقط
        }
        for error in error_codes
    ]

    # ✅ إنشاء الرسالة التفاعلية
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": [
                    {
                        "title": section_title,
                        "rows": error_buttons
                    }
                ]
            }
        }
    }

    # ✅ إرسال القائمة إلى المستخدم
    response = requests.post(url, json=data, headers=headers)
    return response.json()  # ✅ لمعرفة استجابة API

def send_region_list(to):
    """إرسال قائمة المناطق إلى المستخدم بعد اختيار اللغة."""
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    regions = module.get_regions()  # جلب قائمة المناطق
    if not regions:
        send_message(to, "⚠️ لا توجد مناطق متاحة حاليًا.")
        return

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": "📍 *يرجى اختيار المنطقة:*"},
            "action": {
                "button": "اختر المنطقة",
                "sections": [{"title": "المناطق المتاحة", "rows": regions}]
            }
        }
    }

    requests.post(url, json=data, headers=headers)


def send_return_button(to):
    """Send a return button to go back to the start stage."""
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "🔙 الرجوع إلى البداية / Return to Start"},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "return_to_start",
                            "title": "🔙 Return"
                        }
                    }
                ]
            }
        }
    }
    requests.post(url, json=data, headers=headers)
