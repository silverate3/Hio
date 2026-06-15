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
                f"📞 ابحث عن اسم أي رقم هاتف حول العالم!\n\n"
                f"👇 اضغط على البحث للبدء"
            ),
            reply_markup=markup
        )
    except Exception:
        pass

def get_country_from_code(phone_number):
    codes = {
        '+966': '🇸🇦 السعودية', '+971': '🇦🇪 الإمارات', '+964': '🇮🇶 العراق',
        '+965': '🇰🇼 الكويت', '+974': '🇶🇦 قطر', '+973': '🇧🇭 البحرين',
        '+968': '🇴🇲 عُمان', '+967': '🇾🇪 اليمن', '+20': '🇪🇬 مصر',
        '+212': '🇲🇦 المغرب', '+213': '🇩🇿 الجزائر', '+216': '🇹🇳 تونس',
        '+218': '🇱🇾 ليبيا', '+249': '🇸🇩 السودان', '+963': '🇸🇾 سوريا',
        '+961': '🇱🇧 لبنان', '+962': '🇯🇴 الأردن', '+970': '🇵🇸 فلسطين',
        '+98': '🇮🇷 إيران', '+90': '🇹🇷 تركيا', '+1': '🇺🇸 أمريكا/كندا',
        '+44': '🇬🇧 المملكة المتحدة', '+49': '🇩🇪 ألمانيا', '+33': '🇫🇷 فرنسا',
        '+7': '🇷🇺 روسيا', '+91': '🇮🇳 الهند', '+86': '🇨🇳 الصين',
        '+81': '🇯🇵 اليابان', '+82': '🇰🇷 كوريا الجنوبية', '+55': '🇧🇷 البرازيل',
        '+52': '🇲🇽 المكسيك', '+27': '🇿🇦 جنوب أفريقيا', '+234': '🇳🇬 نيجيريا',
    }
    for code, country in sorted(codes.items(), key=lambda x: -len(x[0])):
        if phone_number.startswith(code):
            return country
    return '🌍 غير محدد'

# ==================== خدمات البحث الأربع ====================

def search_api_caller(phone_number):
    """خدمة 1: Caller API"""
    try:
        url = "https://caller-uegx.vercel.app/api/v1/search"
        payload = {"phone": phone_number}
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            'Content-Type': "application/json",
            'origin': "https://caller-uegx.vercel.app",
            'referer': "https://caller-uegx.vercel.app/",
        }
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        data = response.json()
        if data and 'results' in data and data['results']:
            name = data['results'][0].get('name', None)
            if name and name.lower() not in ['unavailable', 'unknown', '']:
                return name, 'Caller API'
    except Exception:
        pass
    return None, None

def search_api_sync_me(phone_number):
    """خدمة 2: Sync.me"""
    try:
        clean = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        url = f"https://sync.me/search/?number={clean}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ar-SA,ar;q=0.9',
        }
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            text = response.text
            if '"name"' in text:
                import re
                match = re.search(r'"name"\s*:\s*"([^"]+)"', text)
                if match:
                    name = match.group(1)
                    if name and len(name) > 1:
                        return name, 'Sync.me'
    except Exception:
        pass
    return None, None

def search_api_phone_lookup(phone_number):
    """خدمة 3: Phone Lookup - معلومات الشبكة والنوع"""
    try:
        clean = phone_number.replace('+', '').replace(' ', '')
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key=free&phone={clean}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            carrier = None
            if isinstance(data.get('carrier'), dict):
                carrier = data['carrier'].get('name')
            elif isinstance(data.get('carrier'), str):
                carrier = data['carrier']
            line_type = data.get('type', None)
            if carrier or line_type:
                return carrier, line_type, 'Phone Lookup'
    except Exception:
        pass
    return None, None, None

def search_api_hlrlookup(phone_number):
    """خدمة 4: HLR Lookup - فحص الشبكة الفعلية"""
    try:
        clean = phone_number.replace('+', '').replace(' ', '')
        url = f"https://api.hlrlookups.com/v1/phone?number={clean}"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
        }
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            carrier = data.get('operator', None) or data.get('network', None)
            status = data.get('status', None)
            if carrier:
                return carrier, status, 'HLR Lookup'
    except Exception:
        pass
    return None, None, None

def search_all_apis(phone_number):
    """البحث في جميع الخدمات الأربع بالتوازي"""
    results = {
        'name': None,
        'carrier': None,
        'line_type': None,
        'status': None,
        'sources': []
    }

    # تشغيل الخدمات بالتوازي
    name_result = [None, None]
    name2_result = [None, None]
    lookup_result = [None, None, None]
    hlr_result = [None, None, None]

    def run_api1():
        name_result[0], name_result[1] = search_api_caller(phone_number)

    def run_api2():
        name2_result[0], name2_result[1] = search_api_sync_me(phone_number)

    def run_api3():
        lookup_result[0], lookup_result[1], lookup_result[2] = search_api_phone_lookup(phone_number)

    def run_api4():
        hlr_result[0], hlr_result[1], hlr_result[2] = search_api_hlrlookup(phone_number)

    threads = [
        threading.Thread(target=run_api1),
        threading.Thread(target=run_api2),
        threading.Thread(target=run_api3),
        threading.Thread(target=run_api4),
    ]

    for t in threads:
        t.daemon = True
        t.start()

    for t in threads:
        t.join(timeout=12)

    # جمع النتائج
    if name_result[0]:
        results['name'] = name_result[0]
        results['sources'].append(name_result[1])

    if not results['name'] and name2_result[0]:
        results['name'] = name2_result[0]
        results['sources'].append(name2_result[1])

    if lookup_result[0]:
        results['carrier'] = lookup_result[0]
    if lookup_result[1]:
        results['line_type'] = lookup_result[1]
    if lookup_result[2]:
        results['sources'].append(lookup_result[2])

    if hlr_result[0] and not results['carrier']:
        results['carrier'] = hlr_result[0]
    if hlr_result[1]:
        results['status'] = hlr_result[1]
    if hlr_result[2] and hlr_result[0]:
        results['sources'].append(hlr_result[2])

    return results

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
        try:
            bot.send_message(
                OWNER_ID,
                f"📲 <b>مستخدم جديد!</b>\n\n"
                f"👤 الاسم: {message.from_user.full_name}\n"
                f"🔗 المعرف: @{message.from_user.username or 'لا يوجد'}\n"
                f"🆔 الآيدي: <code>{user_id}</code>\n"
                f"📅 التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"👥 إجمالي المستخدمين: {len(bot_users)}"
            )
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
            f"⚠️ يجب الاشتراك في القناة أولاً:\n\n"
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

# ==================== البحث - callback ====================

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

# ==================== معالجة الرقم - مُصلح ====================

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_phone_number')
def process_phone_number(message):
    user_id = message.from_user.id
    phone_number = message.text.strip()

    if user_id in banned_users:
        return

    # تغيير الحالة فوراً لمنع التكرار
    user_states[user_id] = 'searching'

    if not phone_number.startswith('+') or len(phone_number) < 7:
        bot.send_message(
            message.chat.id,
            "❌ <b>رقم غير صحيح!</b>\n\n"
            "أرسل الرقم مع رمز الدولة\n"
            "مثال: <code>+9647801234567</code>",
            reply_markup=get_inline_back_to_main_keyboard()
        )
        user_states[user_id] = 'awaiting_phone_number'
        return

    # إرسال رسالة الانتظار
    waiting_msg = bot.send_message(message.chat.id, "🔍 <b>جاري البحث .</b>")
    stop_animation = threading.Event()

    def animate():
        frames = [
            "🔍 <b>جاري البحث ..</b>",
            "🔍 <b>جاري البحث ...</b>",
            "🔎 <b>تحليل البيانات...</b>",
            "📡 <b>الاتصال بالخوادم...</b>",
            "🔍 <b>جاري البحث .</b>",
        ]
        i = 0
        while not stop_animation.is_set():
            time.sleep(0.8)
            if stop_animation.is_set():
                break
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=waiting_msg.message_id,
                    text=frames[i % len(frames)]
                )
                i += 1
            except Exception:
                break

    anim_thread = threading.Thread(target=animate)
    anim_thread.daemon = True
    anim_thread.start()

    try:
        results = search_all_apis(phone_number)
        country = get_country_from_code(phone_number)
        search_counts[user_id] = search_counts.get(user_id, 0) + 1

        name = results.get('name')
        carrier = results.get('carrier')
        line_type = results.get('line_type')
        status = results.get('status')
        sources = results.get('sources', [])

        # إيقاف الانيميشن قبل تحديث الرسالة
        stop_animation.set()
        time.sleep(0.5)

        if name:
            result_text = (
                f"✅ <b>تم العثور على النتيجة!</b>\n"
                f"{'─' * 22}\n"
                f"📞 <b>الرقم:</b> <code>{phone_number}</code>\n"
                f"👤 <b>الاسم:</b> <b>{name}</b>\n"
                f"🌍 <b>الدولة:</b> {country}\n"
            )
        else:
            result_text = (
                f"⚠️ <b>لم يتم العثور على اسم</b>\n"
                f"{'─' * 22}\n"
                f"📞 <b>الرقم:</b> <code>{phone_number}</code>\n"
                f"🌍 <b>الدولة:</b> {country}\n"
            )

        if carrier:
            result_text += f"📶 <b>الشبكة:</b> {carrier}\n"

        if line_type:
            line_map = {'mobile': '📱 موبايل', 'landline': '☎️ أرضي', 'voip': '🌐 VoIP', 'fixed_line': '☎️ أرضي'}
            result_text += f"📋 <b>نوع الخط:</b> {line_map.get(line_type, line_type)}\n"

        if status:
            result_text += f"📡 <b>الحالة:</b> {status}\n"

        result_text += f"{'─' * 22}\n"
        result_text += f"🔢 <i>عملية البحث رقم {search_counts[user_id]}</i>"

        if sources:
            result_text += f"\n📡 <i>المصادر: {', '.join(set(sources))}</i>"

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
            text=result_text,
            reply_markup=get_search_result_keyboard()
        )

    except Exception:
        stop_animation.set()
        time.sleep(0.3)
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=waiting_msg.message_id,
                text="❌ <b>حدث خطأ، حاول مرة أخرى.</b>",
                reply_markup=get_main_inline_keyboard()
            )
        except Exception:
            pass
    finally:
        stop_animation.set()
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
            "📡 <b>الخدمات المستخدمة:</b>\n"
            "• 1️⃣ Caller API\n"
            "• 2️⃣ Sync.me\n"
            "• 3️⃣ Phone Lookup\n"
            "• 4️⃣ HLR Lookup\n\n"
            "⚠️ إذا لم يظهر اسم فالرقم غير موجود في قواعد البيانات\n\n"
            "👨‍💻 للتواصل: @BBBBYB2"
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
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ <b>تم التحقق!</b>\n\nأهلاً {user_name} 🎉",
                reply_markup=get_main_inline_keyboard()
            )
        except Exception:
            pass
        if user_id in user_states:
            del user_states[user_id]
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

# ==================== الرجوع للقائمة الرئيسية ====================

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main_menu')
def callback_back_to_main(call):
    user_name = call.from_user.first_name or call.from_user.username or str(call.from_user.id)
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"👋 <b>مرحباً {user_name}!</b>\n\n👇 اختر من القائمة",
            reply_markup=get_main_inline_keyboard()
        )
    except Exception:
        pass
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
        text="📨 <b>أرسل الرسالة الجماعية:</b>",
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
        f"✅ <b>تم إرسال الرسالة الجماعية</b>\n\n✅ نجح: {success}\n❌ فشل: {failed}",
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
        bot.send_message(message.chat.id, f"✅ تم حظر <code>{target_id}</code>", reply_markup=get_admin_keyboard())
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
            bot.send_message(target_id, "✅ <b>تم رفع الحظر عنك!</b>")
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
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"👋 <b>مرحباً {user_name}!</b>\n\n👇 اختر من القائمة",
            reply_markup=get_main_inline_keyboard()
        )
    except Exception:
        pass
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
                    bot.send_message(user_id, '❌ لا يمكن الحصول على رابط.', reply_markup=get_admin_channel_management_keyboard())
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
        bot.send_message(user_id, f"✅ تمت إضافة '<b>{channel_title}</b>' بنجاح!", reply_markup=get_admin_channel_management_keyboard())
    else:
        bot.send_message(user_id, '❌ حدث خطأ.', reply_markup=get_admin_channel_management_keyboard())

    user_states[user_id] = 'admin_channel_management'

# ==================== تشغيل البوت ====================

print("✅ البوت يعمل الآن...")
bot.polling(none_stop=True, interval=0, timeout=20)
