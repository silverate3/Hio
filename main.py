import requests
import json
import telebot
from telebot import types
import time
import threading
import datetime

# ==================== الإعدادات ====================
BOT_TOKEN = '384366955:AAFJdzI2untoSFoVTd_YSt79Uc7DCkwMbR4'
OWNER_ID = 256156772

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ==================== البيانات ====================
user_states = {}
mandatory_channels = {}
bot_users = set()
search_counts = {}
banned_users = set()
start_time = datetime.datetime.now()

# ==================== لوحات المفاتيح ====================

def get_main_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🔍 بحث عن الاسم', callback_data='search_name'))
    markup.row(
        types.InlineKeyboardButton('👨‍💻 المطور', url='https://t.me/BBBBYB2'),
        types.InlineKeyboardButton('❓ المساعدة', callback_data='show_help_menu')
    )
    markup.row(types.InlineKeyboardButton('📊 إحصائياتي', callback_data='my_stats'))
    return markup

def get_inline_back_to_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_main_menu'))
    return markup

def get_admin_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📢 الاشتراك الإجباري', callback_data='admin_manage_channels'))
    markup.add(types.InlineKeyboardButton('📊 الإحصائيات', callback_data='admin_show_stats'))
    markup.add(types.InlineKeyboardButton('📨 رسالة جماعية', callback_data='admin_broadcast'))
    markup.add(types.InlineKeyboardButton('🚫 حظر مستخدم', callback_data='admin_ban_user'))
    markup.add(types.InlineKeyboardButton('✅ رفع الحظر', callback_data='admin_unban_user'))
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='admin_back_to_user_menu'))
    return markup

def get_admin_channel_management_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ إضافة قناة', callback_data='admin_add_channel'))
    markup.add(types.InlineKeyboardButton('➖ حذف قناة', callback_data='admin_remove_channel'))
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='admin_back_to_admin_panel'))
    return markup

def get_inline_back_to_channel_management_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='admin_back_to_admin_channel_management'))
    return markup

def get_search_result_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔍 بحث آخر', callback_data='search_name'))
    markup.add(types.InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='back_to_main_menu'))
    return markup

# ==================== دوال مساعدة ====================

def check_user_subscription(user_id):
    if not mandatory_channels:
        return True, None
    for channel_id, channel_info in mandatory_channels.items():
        try:
            member = bot.get_chat_member(channel_id, user_id)
            if member.status not in ['member', 'creator', 'administrator']:
                return False, channel_info
        except Exception:
            return False, channel_info
    return True, None

def animated_welcome(chat_id, user_name, markup):
    frames = [
        "🌑 جاري تحميل البوت...",
        "🌒 جاري تحميل البوت...",
        "🌓 جاري تحميل البوت...",
        "🌔 جاري تحميل البوت...",
        "🌕 اكتمل التحميل! ✨",
    ]
    try:
        msg = bot.send_message(chat_id, frames[0])
        for frame in frames[1:]:
            time.sleep(0.6)
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=frame)
        time.sleep(0.5)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=(
                f"🎉 <b>أهلاً وسهلاً {user_name}!</b>\n\n"
                f"✨ يسعدنا انضمامك لبوت معرفة اسم الرقم\n\n"
                f"📞 ابحث عن اسم أي رقم هاتف حول العالم بسهولة وسرعة!\n\n"
                f"👇 اضغط على البحث للبدء"
            ),
            reply_markup=markup
        )
    except Exception:
        pass

def search_phone_api1(phone_number):
    """API الأول - caller"""
    url = "https://caller-uegx.vercel.app/api/v1/search"
    payload = {"phone": phone_number}
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'origin': "https://caller-uegx.vercel.app",
        'referer': "https://caller-uegx.vercel.app/",
        'accept-language': "ar-IQ,ar;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
    response_json = response.json()
    if response_json and 'results' in response_json and response_json['results']:
        return response_json['results'][0].get('name', None)
    return None

def search_phone_api2(phone_number):
    """API الثاني - numverify"""
    try:
        clean_number = phone_number.replace('+', '').replace(' ', '')
        url = f"http://apilayer.net/api/validate?access_key=free&number={clean_number}&country_code=&format=1"
        response = requests.get(url, timeout=8)
        data = response.json()
        if data.get('valid'):
            country = data.get('country_name', '')
            location = data.get('location', '')
            carrier = data.get('carrier', '')
            line_type = data.get('line_type', '')
            return None, country, location, carrier, line_type
    except Exception:
        pass
    return None, None, None, None, None

def get_phone_info(phone_number):
    """جلب معلومات الرقم من APIs متعددة"""
    name = None
    country = None
    location = None
    carrier = None

    # API الأول
    try:
        name = search_phone_api1(phone_number)
    except Exception:
        pass

    # API الثاني للمعلومات الإضافية
    try:
        clean = phone_number.replace('+', '').replace(' ', '')
        # تحديد الدولة من كود الدولة
        if phone_number.startswith('+966') or phone_number.startswith('966'):
            country = '🇸🇦 السعودية'
        elif phone_number.startswith('+971') or phone_number.startswith('971'):
            country = '🇦🇪 الإمارات'
        elif phone_number.startswith('+964') or phone_number.startswith('964'):
            country = '🇮🇶 العراق'
        elif phone_number.startswith('+965') or phone_number.startswith('965'):
            country = '🇰🇼 الكويت'
        elif phone_number.startswith('+974') or phone_number.startswith('974'):
            country = '🇶🇦 قطر'
        elif phone_number.startswith('+973') or phone_number.startswith('973'):
            country = '🇧🇭 البحرين'
        elif phone_number.startswith('+968') or phone_number.startswith('968'):
            country = '🇴🇲 عُمان'
        elif phone_number.startswith('+967') or phone_number.startswith('967'):
            country = '🇾🇪 اليمن'
        elif phone_number.startswith('+20') or phone_number.startswith('20'):
            country = '🇪🇬 مصر'
        elif phone_number.startswith('+212') or phone_number.startswith('212'):
            country = '🇲🇦 المغرب'
        elif phone_number.startswith('+213') or phone_number.startswith('213'):
            country = '🇩🇿 الجزائر'
        elif phone_number.startswith('+216') or phone_number.startswith('216'):
            country = '🇹🇳 تونس'
        elif phone_number.startswith('+1'):
            country = '🇺🇸 الولايات المتحدة/كندا'
        elif phone_number.startswith('+44'):
            country = '🇬🇧 المملكة المتحدة'
        elif phone_number.startswith('+90'):
            country = '🇹🇷 تركيا'
        elif phone_number.startswith('+98'):
            country = '🇮🇷 إيران'
        else:
            country = '🌍 غير محدد'
    except Exception:
        pass

    return name, country

# ==================== أمر /start ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id

    if user_id in banned_users:
        bot.send_message(message.chat.id, "🚫 <b>تم حظرك من استخدام البوت.</b>")
        return

    user_name = message.from_user.first_name or message.from_user.username or str(user_id)
    is_new_user = user_id not in bot_users

    if is_new_user:
        bot_users.add(user_id)
        search_counts[user_id] = 0
        owner_message = (
            f"📲 <b>مستخدم جديد!</b>\n\n"
            f"👤 الاسم: {message.from_user.full_name}\n"
            f"🔗 المعرف: @{message.from_user.username or 'لا يوجد'}\n"
            f"🆔 الآيدي: <code>{user_id}</code>\n"
            f"📅 التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"👥 إجمالي المستخدمين: {len(bot_users)}"
        )
        try:
            bot.send_message(OWNER_ID, owner_message)
        except Exception:
            pass

    subscribed, channel_to_join = check_user_subscription(user_id)
    if not subscribed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"📢 {channel_to_join['title']}", url=channel_to_join['link']))
        markup.row(
            types.InlineKeyboardButton('✅ اشتركت', callback_data='check_sub_again'),
            types.InlineKeyboardButton('🔄 تحقق', callback_data='check_sub_again')
        )
        bot.send_message(
            message.chat.id,
            f"👋 عزيزي <b>{user_name}</b>\n\n"
            f"⚠️ يجب الاشتراك في القناة أولاً للمتابعة:\n\n"
            f"بعد الاشتراك اضغط <b>تحقق</b> ✅",
            reply_markup=markup
        )
        user_states[user_id] = 'awaiting_subscription_check'
        return

    if is_new_user:
        t = threading.Thread(target=animated_welcome, args=(message.chat.id, user_name, get_main_inline_keyboard()))
        t.start()
    else:
        bot.send_message(
            message.chat.id,
            f"👋 <b>مرحباً {user_name}!</b>\n\n"
            f"🔍 ابحث عن اسم أي رقم الآن\n"
            f"👇 اضغط للبدء",
            reply_markup=get_main_inline_keyboard()
        )

    if user_id in user_states:
        del user_states[user_id]

# ==================== أمر /admin ====================

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحية.")
        return
    uptime = datetime.datetime.now() - start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    bot.send_message(
        message.chat.id,
        f"⚙️ <b>لوحة التحكم</b>\n\n"
        f"👥 المستخدمين: <b>{len(bot_users)}</b>\n"
        f"🚫 المحظورين: <b>{len(banned_users)}</b>\n"
        f"⏱ وقت التشغيل: <b>{hours}س {minutes}د</b>",
        reply_markup=get_admin_keyboard()
    )
    user_states[message.from_user.id] = 'admin_panel'

# ==================== البحث عن الرقم ====================

@bot.callback_query_handler(func=lambda call: call.data == 'search_name')
def callback_search_name(call):
    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "🚫 أنت محظور!", show_alert=True)
        return
    subscribed, _ = check_user_subscription(user_id)
    if not subscribed:
        bot.answer_callback_query(call.id, "⚠️ يجب الاشتراك أولاً!", show_alert=True)
        return
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📞 <b>أرسل رقم الهاتف مع رمز الدولة</b>\n\n"
             "مثال: <code>+9647801234567</code>\n"
             "أو: <code>+966501234567</code>",
        reply_markup=get_inline_back_to_main_keyboard()
    )
    user_states[user_id] = 'awaiting_phone_number'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_phone_number')
def process_phone_number(message):
    user_id = message.from_user.id
    phone_number = message.text.strip()

    if user_id in banned_users:
        return

    if not phone_number.startswith('+') or not phone_number[1:].replace(' ', '').isdigit() or len(phone_number) < 7:
        bot.send_message(
            message.chat.id,
            "❌ <b>رقم غير صحيح!</b>\n\n"
            "أرسل الرقم مع رمز الدولة\n"
            "مثال: <code>+9647801234567</code>",
            reply_markup=get_inline_back_to_main_keyboard()
        )
        return

    # رسالة الانتظار المتحركة
    frames = ["🔍 جاري البحث .", "🔍 جاري البحث ..", "🔍 جاري البحث ...", "🔎 تحليل البيانات..."]
    waiting_msg = bot.send_message(message.chat.id, frames[0])

    def animate_search():
        for i in range(1, 8):
            time.sleep(0.5)
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=waiting_msg.message_id,
                    text=frames[i % len(frames)]
                )
            except Exception:
                break

    anim_thread = threading.Thread(target=animate_search)
    anim_thread.daemon = True
    anim_thread.start()

    try:
        name, country = get_phone_info(phone_number)

        # إحصاء عمليات البحث
        search_counts[user_id] = search_counts.get(user_id, 0) + 1

        if name and name != 'unavailable':
            result_text = (
                f"✅ <b>تم العثور على النتيجة!</b>\n\n"
                f"📞 <b>الرقم:</b> <code>{phone_number}</code>\n"
                f"👤 <b>الاسم:</b> {name}\n"
                f"🌍 <b>الدولة:</b> {country or 'غير محدد'}\n\n"
                f"🔢 <i>بحثك رقم {search_counts[user_id]}</i>"
            )
        else:
            result_text = (
                f"⚠️ <b>لم يتم العثور على اسم</b>\n\n"
                f"📞 <b>الرقم:</b> <code>{phone_number}</code>\n"
                f"🌍 <b>الدولة:</b> {country or 'غير محدد'}\n\n"
                f"<i>الرقم غير موجود في قاعدة البيانات</i>"
            )

        time.sleep(2)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
            text=result_text,
            reply_markup=get_search_result_keyboard()
        )

    except requests.exceptions.RequestException:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
            text="❌ <b>خطأ في الاتصال بالخادم</b>\n\nحاول مرة أخرى لاحقاً.",
            reply_markup=get_main_inline_keyboard()
        )
    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
            text="❌ <b>حدث خطأ غير متوقع</b>\n\nحاول مرة أخرى.",
            reply_markup=get_main_inline_keyboard()
        )
    finally:
        if user_id in user_states:
            del user_states[user_id]

# ==================== إحصائيات المستخدم ====================

@bot.callback_query_handler(func=lambda call: call.data == 'my_stats')
def callback_my_stats(call):
    user_id = call.from_user.id
    count = search_counts.get(user_id, 0)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            f"📊 <b>إحصائياتك</b>\n\n"
            f"🔍 عدد عمليات البحث: <b>{count}</b>\n"
            f"👤 اسمك: {call.from_user.first_name or 'غير محدد'}\n"
            f"🆔 آيديك: <code>{user_id}</code>"
        ),
        reply_markup=get_inline_back_to_main_keyboard()
    )
    bot.answer_callback_query(call.id)

# ==================== المساعدة ====================

@bot.callback_query_handler(func=lambda call: call.data == 'show_help_menu')
def callback_show_help(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            "❓ <b>كيفية الاستخدام</b>\n\n"
            "1️⃣ اضغط على <b>بحث عن الاسم</b>\n"
            "2️⃣ أرسل رقم الهاتف مع رمز الدولة\n"
            "   مثال: <code>+9647801234567</code>\n"
            "3️⃣ انتظر النتيجة 🎯\n\n"
            "⚠️ <b>ملاحظة:</b> إذا لم يظهر اسم فالرقم غير موجود في قاعدة البيانات\n\n"
            "👨‍💻 للتواصل مع المطور: @BBBBYB2"
        ),
        reply_markup=get_inline_back_to_main_keyboard()
    )
    bot.answer_callback_query(call.id)

# ==================== التحقق من الاشتراك ====================

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub_again')
def callback_check_sub(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name or call.from_user.username or str(user_id)
    subscribed, channel_to_join = check_user_subscription(user_id)
    if subscribed:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ <b>تم التحقق!</b>\n\nأهلاً {user_name} 🎉",
            reply_markup=get_main_inline_keyboard()
        )
        if user_id in user_states:
            del user_states[user_id]
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)
    bot.answer_callback_query(call.id)

# ==================== الرجوع للقائمة الرئيسية ====================

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main_menu')
def callback_back_to_main(call):
    user_name = call.from_user.first_name or call.from_user.username or str(call.from_user.id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"👋 <b>مرحباً {user_name}!</b>\n\n👇 اختر من القائمة",
        reply_markup=get_main_inline_keyboard()
    )
    if call.from_user.id in user_states:
        del user_states[call.from_user.id]
    bot.answer_callback_query(call.id)

# ==================== لوحة الأدمن ====================

@bot.callback_query_handler(func=lambda call: call.data == 'admin_show_stats' and call.from_user.id == OWNER_ID)
def callback_admin_stats(call):
    uptime = datetime.datetime.now() - start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    total_searches = sum(search_counts.values())
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            f"📊 <b>إحصائيات البوت</b>\n\n"
            f"👥 إجمالي المستخدمين: <b>{len(bot_users)}</b>\n"
            f"🔍 إجمالي عمليات البحث: <b>{total_searches}</b>\n"
            f"🚫 المحظورين: <b>{len(banned_users)}</b>\n"
            f"📢 القنوات الإجبارية: <b>{len(mandatory_channels)}</b>\n"
            f"⏱ وقت التشغيل: <b>{hours}س {minutes}د</b>"
        ),
        reply_markup=get_admin_keyboard()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_broadcast' and call.from_user.id == OWNER_ID)
def callback_admin_broadcast(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📨 <b>أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:</b>",
        reply_markup=get_admin_keyboard()
    )
    user_states[call.from_user.id] = 'awaiting_broadcast_message'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_broadcast_message' and message.from_user.id == OWNER_ID)
def process_broadcast(message):
    success = 0
    failed = 0
    for uid in bot_users:
        try:
            bot.send_message(uid, f"📢 <b>رسالة من الإدارة:</b>\n\n{message.text}")
            success += 1
            time.sleep(0.05)
        except Exception:
            failed += 1
    bot.send_message(
        message.chat.id,
        f"✅ <b>تم إرسال الرسالة الجماعية</b>\n\n"
        f"✅ نجح: {success}\n❌ فشل: {failed}",
        reply_markup=get_admin_keyboard()
    )
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ban_user' and call.from_user.id == OWNER_ID)
def callback_admin_ban(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🚫 <b>أرسل آيدي المستخدم لحظره:</b>",
        reply_markup=get_admin_keyboard()
    )
    user_states[call.from_user.id] = 'awaiting_ban_user_id'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_ban_user_id' and message.from_user.id == OWNER_ID)
def process_ban_user(message):
    try:
        target_id = int(message.text.strip())
        banned_users.add(target_id)
        bot.send_message(message.chat.id, f"✅ تم حظر المستخدم <code>{target_id}</code>", reply_markup=get_admin_keyboard())
        try:
            bot.send_message(target_id, "🚫 <b>تم حظرك من استخدام البوت.</b>")
        except Exception:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ آيدي غير صحيح.", reply_markup=get_admin_keyboard())
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == 'admin_unban_user' and call.from_user.id == OWNER_ID)
def callback_admin_unban(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="✅ <b>أرسل آيدي المستخدم لرفع الحظر:</b>",
        reply_markup=get_admin_keyboard()
    )
    user_states[call.from_user.id] = 'awaiting_unban_user_id'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_unban_user_id' and message.from_user.id == OWNER_ID)
def process_unban_user(message):
    try:
        target_id = int(message.text.strip())
        banned_users.discard(target_id)
        bot.send_message(message.chat.id, f"✅ تم رفع الحظر عن <code>{target_id}</code>", reply_markup=get_admin_keyboard())
        try:
            bot.send_message(target_id, "✅ <b>تم رفع الحظر عنك، يمكنك استخدام البوت الآن.</b>")
        except Exception:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ آيدي غير صحيح.", reply_markup=get_admin_keyboard())
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == 'admin_manage_channels' and call.from_user.id == OWNER_ID)
def callback_admin_manage_channels(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📢 <b>إدارة قنوات الاشتراك الإجباري</b>",
        reply_markup=get_admin_channel_management_keyboard()
    )
    user_states[call.from_user.id] = 'admin_channel_management'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_user_menu' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_user_menu(call):
    user_name = call.from_user.first_name or str(call.from_user.id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"👋 <b>مرحباً {user_name}!</b>\n\n👇 اختر من القائمة",
        reply_markup=get_main_inline_keyboard()
    )
    if call.from_user.id in user_states:
        del user_states[call.from_user.id]
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_channel' and call.from_user.id == OWNER_ID)
def callback_admin_add_channel(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='📢 <b>أرسل رابط القناة أو وجّه رسالة منها:</b>',
        reply_markup=get_inline_back_to_channel_management_keyboard()
    )
    user_states[call.from_user.id] = 'awaiting_channel_link_or_forward'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_remove_channel' and call.from_user.id == OWNER_ID)
def callback_admin_remove_channel(call):
    if not mandatory_channels:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='⚠️ لا توجد قنوات لإزالتها.',
            reply_markup=get_admin_channel_management_keyboard()
        )
        bot.answer_callback_query(call.id)
        return
    markup = types.InlineKeyboardMarkup()
    for ch_id, ch_info in mandatory_channels.items():
        markup.add(types.InlineKeyboardButton(f"❌ {ch_info['title']}", callback_data=f'delete_channel_{ch_id}'))
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='admin_back_to_admin_channel_management'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='اختر القناة المراد حذفها:',
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_channel_') and call.from_user.id == OWNER_ID)
def callback_delete_channel(call):
    channel_id_to_delete = int(call.data.replace('delete_channel_', ''))
    if channel_id_to_delete in mandatory_channels:
        del mandatory_channels[channel_id_to_delete]
        text = '✅ تم حذف القناة بنجاح.'
    else:
        text = '❌ القناة غير موجودة.'
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=get_admin_channel_management_keyboard()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_panel' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_admin_panel(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='⚙️ <b>لوحة التحكم</b>',
        reply_markup=get_admin_keyboard()
    )
    user_states[call.from_user.id] = 'admin_panel'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_channel_management' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_channel_management(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='📢 <b>إدارة قنوات الاشتراك الإجباري</b>',
        reply_markup=get_admin_channel_management_keyboard()
    )
    user_states[call.from_user.id] = 'admin_channel_management'
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text', 'forward_from_chat'], func=lambda message: user_states.get(message.from_user.id) == 'awaiting_channel_link_or_forward' and message.from_user.id == OWNER_ID)
def process_channel_for_add(message):
    user_id = message.from_user.id
    channel_id = None
    channel_link = None
    channel_title = None

    if message.forward_from_chat and message.forward_from_chat.type in ['channel', 'supergroup']:
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title
        if message.forward_from_chat.username:
            channel_link = f"https://t.me/{message.forward_from_chat.username}"
        else:
            try:
                chat = bot.get_chat(channel_id)
                channel_link = chat.invite_link
                if not channel_link:
                    bot.send_message(user_id, '❌ لا يمكن الحصول على رابط دعوة.', reply_markup=get_admin_channel_management_keyboard())
                    user_states[user_id] = 'admin_channel_management'
                    return
            except Exception:
                bot.send_message(user_id, '❌ حدث خطأ.', reply_markup=get_admin_channel_management_keyboard())
                user_states[user_id] = 'admin_channel_management'
                return

    elif message.text and (message.text.startswith('https://t.me/') or message.text.startswith('@')):
        channel_link = message.text
        try:
            if message.text.startswith('@'):
                chat_info = bot.get_chat(message.text[1:])
            else:
                parts = message.text.split('/')
                chat_info = bot.get_chat(f'@{parts[3]}') if len(parts) >= 4 else None
            if chat_info:
                channel_id = chat_info.id
                channel_title = chat_info.title
        except Exception:
            bot.send_message(user_id, '❌ الرابط غير صحيح.', reply_markup=get_admin_channel_management_keyboard())
            user_states[user_id] = 'admin_channel_management'
            return
    else:
        bot.send_message(user_id, '❌ أرسل رابطاً صحيحاً.', reply_markup=get_admin_channel_management_keyboard())
        user_states[user_id] = 'admin_channel_management'
        return

    if channel_id and channel_link and channel_title:
        try:
            bot_member = bot.get_chat_member(channel_id, bot.get_me().id)
            if bot_member.status not in ['administrator', 'creator']:
                bot.send_message(user_id, '❌ البوت ليس مسؤولاً في القناة.', reply_markup=get_admin_channel_management_keyboard())
                user_states[user_id] = 'admin_channel_management'
                return
        except Exception:
            pass
        mandatory_channels[channel_id] = {'title': channel_title, 'link': channel_link}
        bot.send_message(user_id, f"✅ تمت إضافة القناة '<b>{channel_title}</b>' بنجاح!", reply_markup=get_admin_channel_management_keyboard())
    else:
        bot.send_message(user_id, '❌ حدث خطأ.', reply_markup=get_admin_channel_management_keyboard())

    user_states[user_id] = 'admin_channel_management'

# ==================== تشغيل البوت ====================

print("✅ البوت يعمل...")
bot.polling(none_stop=True, interval=0, timeout=20)
