import requests
import json
import telebot
from telebot import types
import time
import threading
import datetime
import re

# ==================== الإعدادات ====================
BOT_TOKEN = '384366955:AAFJdzI2untoSFoVTd_YSt79Uc7DCkwMbR4'
OWNER_ID = 256156772

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ==================== البيانات ====================
user_states = {}
mandatory_channels = {}
bot_users = set()
banned_users = set()
start_time = datetime.datetime.now()

# ==================== لوحات المفاتيح ====================

def get_main_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('📞 بحث برقم الهاتف', callback_data='search_phone'))
    markup.row(
        types.InlineKeyboardButton('📸 انستقرام', callback_data='search_instagram'),
        types.InlineKeyboardButton('🎵 تيك توك', callback_data='search_tiktok')
    )
    markup.row(
        types.InlineKeyboardButton('📧 بحث ايميل', callback_data='search_email'),
        types.InlineKeyboardButton('🌐 معلومات موقع', callback_data='search_domain')
    )
    markup.row(
        types.InlineKeyboardButton('👨‍💻 المطور', url='https://t.me/BBBBYB2'),
        types.InlineKeyboardButton('❓ المساعدة', callback_data='show_help_menu')
    )
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_main_menu'))
    return markup

def get_result_keyboard(url=None):
    markup = types.InlineKeyboardMarkup()
    if url:
        markup.add(types.InlineKeyboardButton('🔗 فتح', url=url))
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

def get_back_to_channel_management_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='admin_back_to_admin_channel_management'))
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

def normalize_iraq_phone(phone):
    """تحويل أرقام العراق لتنسيق دولي"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    # إذا بدأ بـ 07 أو 7 (عراقي)
    if phone.startswith('07') and len(phone) == 11:
        return '+964' + phone[1:]
    if phone.startswith('7') and len(phone) == 10:
        return '+964' + phone
    if phone.startswith('009647'):
        return '+' + phone[2:]
    if phone.startswith('9647') and len(phone) >= 12:
        return '+' + phone
    # إذا كان مكتمل بالرمز الدولي
    if phone.startswith('+'):
        return phone
    return None

def get_country_from_code(phone):
    codes = {
        '+966': '🇸🇦 السعودية', '+971': '🇦🇪 الإمارات', '+964': '🇮🇶 العراق',
        '+965': '🇰🇼 الكويت', '+974': '🇶🇦 قطر', '+973': '🇧🇭 البحرين',
        '+968': '🇴🇲 عُمان', '+967': '🇾🇪 اليمن', '+20': '🇪🇬 مصر',
        '+212': '🇲🇦 المغرب', '+213': '🇩🇿 الجزائر', '+216': '🇹🇳 تونس',
        '+218': '🇱🇾 ليبيا', '+963': '🇸🇾 سوريا', '+961': '🇱🇧 لبنان',
        '+98': '🇮🇷 إيران', '+90': '🇹🇷 تركيا', '+1': '🇺🇸 أمريكا',
        '+44': '🇬🇧 بريطانيا', '+7': '🇷🇺 روسيا',
    }
    for code, country in sorted(codes.items(), key=lambda x: -len(x[0])):
        if phone.startswith(code):
            return country
    return '🌍 غير محدد'

# ==================== دالة البحث مع الانيميشن ====================

def run_search(chat_id, user_id, search_func, format_func, wait_text):
    waiting_msg = bot.send_message(chat_id, wait_text)
    stop_anim = threading.Event()

    def animate():
        frames = [
            "🔍 <b>جاري البحث .</b>",
            "🔍 <b>جاري البحث ..</b>",
            "🔍 <b>جاري البحث ...</b>",
            "📡 <b>جاري الاتصال...</b>",
            "🔎 <b>تحليل البيانات...</b>",
        ]
        i = 0
        while not stop_anim.is_set():
            time.sleep(0.9)
            if stop_anim.is_set():
                break
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text=frames[i % len(frames)])
                i += 1
            except Exception:
                break

    t = threading.Thread(target=animate)
    t.daemon = True
    t.start()

    try:
        result = search_func()
        stop_anim.set()
        time.sleep(0.5)
        text, markup = format_func(result)
        bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text=text, reply_markup=markup)
    except Exception:
        stop_anim.set()
        time.sleep(0.3)
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id,
                text="❌ <b>حدث خطأ، حاول مرة أخرى.</b>", reply_markup=get_back_keyboard())
        except Exception:
            pass
    finally:
        stop_anim.set()
        user_states.pop(user_id, None)

# ==================== خدمة 1: بحث رقم الهاتف ====================

def search_phone_number(phone):
    name = None
    carrier = None
    line_type = None

    try:
        r = requests.post(
            "https://caller-uegx.vercel.app/api/v1/search",
            data=json.dumps({"phone": phone}),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
            timeout=10
        )
        d = r.json()
        if d.get('results'):
            n = d['results'][0].get('name', '')
            if n and n.lower() not in ['unavailable', 'unknown', '']:
                name = n
    except Exception:
        pass

    return {'name': name, 'carrier': carrier, 'line_type': line_type}

# ==================== خدمة 2: انستقرام ====================

def search_instagram(username):
    if "@" in username:
        username = username.split("@")[0]
    username = username.strip()

    headers = {
        "accept": "*/*",
        "accept-language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": "\"Chromium\";v=\"139\", \"Not;A=Brand\";v=\"99\"",
        "sec-ch-ua-full-version-list": "\"Chromium\";v=\"139.0.7339.0\", \"Not;A=Brand\";v=\"99.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"Linux\"",
        "sec-ch-ua-platform-version": "\"\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-asbd-id": "359341",
        "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "0",
        "x-requested-with": "XMLHttpRequest",
    }

    try:
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        r = requests.get(url, headers=headers, timeout=12)
        data = r.json()

        if data.get("status") != "ok" or "data" not in data or "user" not in data["data"]:
            return None

        u = data["data"]["user"]
        return {
            'full_name': u.get('full_name') or username,
            'username': u.get('username', username),
            'id': u.get('id', ''),
            'bio': (u.get('biography') or 'لا يوجد')[:200],
            'followers': f"{u.get('edge_followed_by', {}).get('count', 0):,}",
            'following': f"{u.get('edge_follow', {}).get('count', 0):,}",
            'posts': f"{u.get('edge_owner_to_timeline_media', {}).get('count', 0):,}",
            'highlights': u.get('highlight_reel_count', 0),
            'has_clips': u.get('has_clips', False),
            'is_private': '🔒 خاص' if u.get('is_private') else '🌐 عام',
            'is_verified': '✅ موثق' if u.get('is_verified') else '❌ غير موثق',
            'category': u.get('category_name') or '',
            'external_url': u.get('external_url') or '',
        }
    except Exception:
        pass

    return None

# ==================== خدمة 3: تيك توك ====================

def search_tiktok(username):
    username = username.strip().lstrip('@')

    try:
        r = requests.get(
            f"https://www.tiktok.com/oembed?url=https://www.tiktok.com/@{username}",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=10
        )
        if r.status_code == 200:
            d = r.json()
            author = d.get('author_name', username)
            followers = likes = videos = 'غير محدد'
            verified = '❓ غير محدد'
            try:
                r2 = requests.get(
                    f"https://www.tiktok.com/@{username}",
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept-Language': 'en-US,en;q=0.9',
                    },
                    timeout=12
                )
                if r2.status_code == 200:
                    t = r2.text
                    f_m = re.search(r'"followerCount":(\d+)', t)
                    l_m = re.search(r'"heartCount":(\d+)', t)
                    v_m = re.search(r'"videoCount":(\d+)', t)
                    n_m = re.search(r'"nickname":"([^"]+)"', t)
                    ver_m = re.search(r'"verified":(true|false)', t)
                    if f_m: followers = f"{int(f_m.group(1)):,}"
                    if l_m: likes = f"{int(l_m.group(1)):,}"
                    if v_m: videos = f"{int(v_m.group(1)):,}"
                    if n_m: author = n_m.group(1)
                    if ver_m: verified = '✅ موثق' if ver_m.group(1) == 'true' else '❌ غير موثق'
            except Exception:
                pass
            return {
                'nickname': author,
                'username': username,
                'followers': followers,
                'likes': likes,
                'videos': videos,
                'is_verified': verified,
            }
    except Exception:
        pass

    try:
        r = requests.get(
            f"https://www.tiktok.com/@{username}",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            timeout=12
        )
        if r.status_code == 200:
            t = r.text
            n_m = re.search(r'"nickname":"([^"]+)"', t)
            f_m = re.search(r'"followerCount":(\d+)', t)
            l_m = re.search(r'"heartCount":(\d+)', t)
            v_m = re.search(r'"videoCount":(\d+)', t)
            ver_m = re.search(r'"verified":(true|false)', t)
            if n_m or f_m:
                return {
                    'nickname': n_m.group(1) if n_m else username,
                    'username': username,
                    'followers': f"{int(f_m.group(1)):,}" if f_m else 'غير محدد',
                    'likes': f"{int(l_m.group(1)):,}" if l_m else 'غير محدد',
                    'videos': f"{int(v_m.group(1)):,}" if v_m else 'غير محدد',
                    'is_verified': '✅ موثق' if ver_m and ver_m.group(1) == 'true' else '❌ غير موثق',
                }
    except Exception:
        pass

    return None

# ==================== خدمة 4: بحث الايميل ====================

def search_email(email):
    email = email.strip().lower()
    results = {'email': email, 'valid': False, 'domain': '', 'mx': False,
               'disposable': False, 'free': False, 'accounts': []}

    # التحقق من صيغة الايميل
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return None

    domain = email.split('@')[1]
    results['domain'] = domain
    results['valid'] = True

    # التحقق من الدومين
    free_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                      'icloud.com', 'protonmail.com', 'mail.com', 'aol.com',
                      'yandex.com', 'gmx.com']
    disposable = ['tempmail.com', 'guerrillamail.com', 'mailinator.com',
                  'throwam.com', '10minutemail.com', 'yopmail.com']

    results['free'] = domain in free_providers
    results['disposable'] = domain in disposable

    # API مجاني للتحقق من الايميل
    try:
        r = requests.get(
            f"https://api.hunter.io/v2/email-verifier?email={email}&api_key=free",
            timeout=8
        )
        if r.status_code == 200:
            d = r.json().get('data', {})
            if d.get('status') == 'valid':
                results['mx'] = True
    except Exception:
        pass

    # البحث عن حسابات مرتبطة
    try:
        r2 = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers={
                'User-Agent': 'Mozilla/5.0',
                'hibp-api-key': 'free'
            },
            timeout=8
        )
        if r2.status_code == 200:
            breaches = r2.json()
            results['breaches'] = [b.get('Name') for b in breaches[:5]]
        else:
            results['breaches'] = []
    except Exception:
        results['breaches'] = []

    # فحص وجود الايميل في بعض المنصات
    platforms_found = []
    checks = {
        'Gravatar': f"https://www.gravatar.com/{__import__('hashlib').md5(email.encode()).hexdigest()}.json",
    }
    for platform, url in checks.items():
        try:
            r3 = requests.get(url, timeout=5)
            if r3.status_code == 200:
                platforms_found.append(platform)
        except Exception:
            pass

    results['platforms'] = platforms_found
    return results

# ==================== خدمة 5: معلومات الدومين/الموقع ====================

def search_domain(domain):
    domain = domain.strip().lower()
    domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

    result = {'domain': domain, 'ip': None, 'country': None, 'org': None,
              'registrar': None, 'created': None, 'expires': None,
              'status': None, 'nameservers': []}

    # معلومات IP
    try:
        r = requests.get(f"https://ipapi.co/{domain}/json/", timeout=8)
        if r.status_code == 200:
            d = r.json()
            result['ip'] = d.get('ip')
            result['country'] = d.get('country_name')
            result['org'] = d.get('org')
            result['city'] = d.get('city')
    except Exception:
        pass

    # معلومات WHOIS
    try:
        r2 = requests.get(
            f"https://api.whoapi.com/?domain={domain}&r=whois&apikey=free",
            timeout=8
        )
        if r2.status_code == 200:
            d2 = r2.json()
            result['registrar'] = d2.get('registrar')
            result['created'] = d2.get('date_created')
            result['expires'] = d2.get('date_expires')
    except Exception:
        pass

    # معلومات DNS
    try:
        r3 = requests.get(
            f"https://dns.google/resolve?name={domain}&type=A",
            timeout=8
        )
        if r3.status_code == 200:
            d3 = r3.json()
            answers = d3.get('Answer', [])
            if answers and not result['ip']:
                result['ip'] = answers[0].get('data')
    except Exception:
        pass

    # فحص SSL
    try:
        r4 = requests.get(f"https://{domain}", timeout=6, verify=True)
        result['ssl'] = '✅ يوجد SSL'
        result['status_code'] = r4.status_code
    except requests.exceptions.SSLError:
        result['ssl'] = '❌ SSL غير صالح'
        result['status_code'] = None
    except Exception:
        result['ssl'] = '❓ غير محدد'
        result['status_code'] = None

    return result if result['ip'] or result['registrar'] else None

# ==================== /start ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if user_id in banned_users:
        bot.send_message(message.chat.id, "🚫 <b>تم حظرك.</b>")
        return

    user_name = message.from_user.first_name or message.from_user.username or str(user_id)
    is_new = user_id not in bot_users

    if is_new:
        bot_users.add(user_id)
        try:
            bot.send_message(OWNER_ID,
                f"📲 <b>مستخدم جديد!</b>\n"
                f"👤 {message.from_user.full_name}\n"
                f"🔗 @{message.from_user.username or 'لا يوجد'}\n"
                f"🆔 <code>{user_id}</code>\n"
                f"👥 الإجمالي: {len(bot_users)}")
        except Exception:
            pass

    subscribed, ch = check_user_subscription(user_id)
    if not subscribed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"📢 {ch['title']}", url=ch['link']))
        markup.row(types.InlineKeyboardButton('✅ اشتركت', callback_data='check_sub_again'),
                   types.InlineKeyboardButton('🔄 تحقق', callback_data='check_sub_again'))
        bot.send_message(message.chat.id,
            f"👋 <b>{user_name}</b>\n\n⚠️ يجب الاشتراك أولاً ثم اضغط <b>تحقق</b>",
            reply_markup=markup)
        user_states[user_id] = 'awaiting_subscription_check'
        return

    bot.send_message(message.chat.id,
        f"👋 <b>مرحباً {user_name}!</b>\n\n👇 اختر نوع البحث",
        reply_markup=get_main_inline_keyboard())
    user_states.pop(user_id, None)

# ==================== /admin ====================

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if message.from_user.id != OWNER_ID:
        return
    uptime = datetime.datetime.now() - start_time
    h = int(uptime.total_seconds() // 3600)
    m = int((uptime.total_seconds() % 3600) // 60)
    bot.send_message(message.chat.id,
        f"⚙️ <b>لوحة التحكم</b>\n\n"
        f"👥 المستخدمين: <b>{len(bot_users)}</b>\n"
        f"🚫 المحظورين: <b>{len(banned_users)}</b>\n"
        f"⏱ التشغيل: <b>{h}س {m}د</b>",
        reply_markup=get_admin_keyboard())
    user_states[message.from_user.id] = 'admin_panel'

# ==================== Callbacks البحث ====================

def set_search_state(call, state, text):
    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "🚫 أنت محظور!", show_alert=True)
        return
    subscribed, _ = check_user_subscription(user_id)
    if not subscribed:
        bot.answer_callback_query(call.id, "⚠️ يجب الاشتراك أولاً!", show_alert=True)
        return
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=text, reply_markup=get_back_keyboard())
    user_states[user_id] = state
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'search_phone')
def cb_phone(call):
    set_search_state(call, 'awaiting_phone',
        "📞 <b>أرسل رقم الهاتف</b>\n\n"
        "✅ يمكن إرسال الرقم العراقي مباشرة:\n"
        "<code>07701234567</code> أو <code>7701234567</code>\n\n"
        "أو مع رمز الدولة:\n"
        "<code>+9647701234567</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_instagram')
def cb_instagram(call):
    set_search_state(call, 'awaiting_instagram',
        "📸 <b>أرسل اسم مستخدم انستقرام</b>\n\nمثال: <code>cristiano</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_tiktok')
def cb_tiktok(call):
    set_search_state(call, 'awaiting_tiktok',
        "🎵 <b>أرسل اسم مستخدم تيك توك</b>\n\nمثال: <code>khaby.lame</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_email')
def cb_email(call):
    set_search_state(call, 'awaiting_email',
        "📧 <b>أرسل الايميل للبحث عنه</b>\n\nمثال: <code>example@gmail.com</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_domain')
def cb_domain(call):
    set_search_state(call, 'awaiting_domain',
        "🌐 <b>أرسل اسم الموقع أو الدومين</b>\n\nمثال: <code>google.com</code>")

# ==================== معالجة الرسائل ====================

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in [
    'awaiting_phone', 'awaiting_instagram', 'awaiting_tiktok',
    'awaiting_email', 'awaiting_domain'
])
def handle_search_input(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    query = message.text.strip()
    user_states[user_id] = 'searching'

    # ==================== الرقم ====================
    if state == 'awaiting_phone':
        phone = normalize_iraq_phone(query)
        if not phone:
            bot.send_message(message.chat.id,
                "❌ <b>رقم غير صحيح!</b>\n\n"
                "أرسل رقم عراقي مثل: <code>07701234567</code>\n"
                "أو مع رمز الدولة: <code>+9647701234567</code>",
                reply_markup=get_back_keyboard())
            user_states[user_id] = 'awaiting_phone'
            return

        def search(): return search_phone_number(phone)
        def fmt(r):
            country = get_country_from_code(phone)
            name = r.get('name')
            if name:
                text = (f"✅ <b>تم العثور على النتيجة!</b>\n{'─'*22}\n"
                        f"📞 <b>الرقم:</b> <code>{phone}</code>\n"
                        f"👤 <b>الاسم:</b> <b>{name}</b>\n"
                        f"🌍 <b>الدولة:</b> {country}\n")
            else:
                text = (f"⚠️ <b>لم يتم العثور على اسم</b>\n{'─'*22}\n"
                        f"📞 <b>الرقم:</b> <code>{phone}</code>\n"
                        f"🌍 <b>الدولة:</b> {country}\n")
            return text, get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "📞 <b>جاري البحث...</b>")).start()

    # ==================== انستقرام ====================
    elif state == 'awaiting_instagram':
        username = query.lstrip('@')
        def search(): return search_instagram(username)
        def fmt(r):
            if r:
                text = (f"📸 <b>نتيجة انستقرام</b>\n{'─'*22}\n"
                        f"👤 <b>الاسم:</b> {r['full_name']}\n"
                        f"🔗 <b>المعرف:</b> @{r['username']}\n"
                        f"🆔 <b>الآيدي:</b> <code>{r.get('id','')}</code>\n")
                if r.get('category'):
                    text += f"🏷 <b>الفئة:</b> {r['category']}\n"
                text += (f"📝 <b>البايو:</b> {r['bio'] or 'لا يوجد'}\n"
                         f"👥 <b>المتابعون:</b> {r['followers']}\n"
                         f"➡️ <b>يتابع:</b> {r['following']}\n"
                         f"🖼 <b>المنشورات:</b> {r['posts']}\n"
                         f"🔦 <b>الهايلايت:</b> {r.get('highlights', 0)}\n"
                         f"🎬 <b>ريلز:</b> {'✅' if r.get('has_clips') else '❌'}\n"
                         f"🔐 <b>الحساب:</b> {r['is_private']}\n"
                         f"✅ <b>التوثيق:</b> {r['is_verified']}\n")
                if r.get('external_url'):
                    text += f"🌐 <b>الموقع:</b> {r['external_url']}\n"
                return text, get_result_keyboard(f"https://instagram.com/{r['username']}")
            return (f"❌ <b>لم يتم العثور على الحساب</b>\n\n"
                    f"تأكد من اسم المستخدم: <code>@{username}</code>"), get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "📸 <b>جاري البحث في انستقرام...</b>")).start()

    # ==================== تيك توك ====================
    elif state == 'awaiting_tiktok':
        username = query.lstrip('@')
        def search(): return search_tiktok(username)
        def fmt(r):
            if r:
                text = (f"🎵 <b>نتيجة تيك توك</b>\n{'─'*22}\n"
                        f"👤 <b>الاسم:</b> {r['nickname']}\n"
                        f"🔗 <b>المعرف:</b> @{r['username']}\n"
                        f"👥 <b>المتابعون:</b> {r['followers']}\n"
                        f"❤️ <b>الإعجابات:</b> {r['likes']}\n"
                        f"🎬 <b>الفيديوهات:</b> {r['videos']}\n"
                        f"✅ <b>التوثيق:</b> {r['is_verified']}\n")
                return text, get_result_keyboard(f"https://tiktok.com/@{r['username']}")
            return f"❌ <b>لم يتم العثور على</b> @{username}", get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "🎵 <b>جاري البحث في تيك توك...</b>")).start()

    # ==================== ايميل ====================
    elif state == 'awaiting_email':
        email = query.lower()
        def search(): return search_email(email)
        def fmt(r):
            if not r:
                return "❌ <b>صيغة الايميل غير صحيحة</b>", get_back_keyboard()
            text = (f"📧 <b>نتيجة فحص الايميل</b>\n{'─'*22}\n"
                    f"📨 <b>الايميل:</b> <code>{r['email']}</code>\n"
                    f"🌐 <b>الدومين:</b> {r['domain']}\n"
                    f"✅ <b>الصيغة:</b> {'صحيحة ✅' if r['valid'] else 'خاطئة ❌'}\n"
                    f"📮 <b>النوع:</b> {'مجاني' if r['free'] else 'خاص'}\n"
                    f"🗑 <b>مؤقت:</b> {'نعم ⚠️' if r['disposable'] else 'لا ✅'}\n")
            if r.get('breaches'):
                text += f"⚠️ <b>تسريبات:</b> {', '.join(r['breaches'])}\n"
            elif 'breaches' in r:
                text += f"🛡 <b>تسريبات:</b> لا يوجد ✅\n"
            if r.get('platforms'):
                text += f"🔗 <b>منصات:</b> {', '.join(r['platforms'])}\n"
            return text, get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "📧 <b>جاري فحص الايميل...</b>")).start()

    # ==================== دومين ====================
    elif state == 'awaiting_domain':
        domain = query
        def search(): return search_domain(domain)
        def fmt(r):
            if not r:
                return f"❌ <b>لم يتم العثور على معلومات</b>\n<code>{domain}</code>", get_back_keyboard()
            text = (f"🌐 <b>معلومات الموقع</b>\n{'─'*22}\n"
                    f"🔗 <b>الدومين:</b> <code>{r['domain']}</code>\n")
            if r.get('ip'):
                text += f"🖥 <b>الـ IP:</b> <code>{r['ip']}</code>\n"
            if r.get('country'):
                text += f"🌍 <b>الدولة:</b> {r['country']}\n"
            if r.get('city'):
                text += f"📍 <b>المدينة:</b> {r['city']}\n"
            if r.get('org'):
                text += f"🏢 <b>المزود:</b> {r['org']}\n"
            if r.get('ssl'):
                text += f"🔒 <b>SSL:</b> {r['ssl']}\n"
            if r.get('registrar'):
                text += f"📋 <b>المسجّل:</b> {r['registrar']}\n"
            if r.get('created'):
                text += f"📅 <b>تاريخ الإنشاء:</b> {r['created']}\n"
            if r.get('expires'):
                text += f"⏳ <b>تاريخ الانتهاء:</b> {r['expires']}\n"
            return text, get_result_keyboard(f"https://{r['domain']}")
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "🌐 <b>جاري جلب معلومات الموقع...</b>")).start()

# ==================== Callbacks عامة ====================

@bot.callback_query_handler(func=lambda call: call.data == 'show_help_menu')
def cb_help(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=("❓ <b>كيفية الاستخدام</b>\n\n"
              "📞 <b>رقم الهاتف:</b>\n"
              "   <code>07701234567</code> عراقي مباشر\n"
              "   <code>+9647701234567</code> مع رمز الدولة\n\n"
              "📸 <b>انستقرام / 🎵 تيك توك:</b>\n"
              "   أرسل اسم المستخدم: <code>cristiano</code>\n\n"
              "📧 <b>ايميل:</b>\n"
              "   <code>example@gmail.com</code>\n\n"
              "🌐 <b>موقع:</b>\n"
              "   <code>google.com</code>\n\n"
              "👨‍💻 للتواصل: @BBBBYB2"),
        reply_markup=get_back_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub_again')
def cb_check_sub(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name or str(user_id)
    subscribed, _ = check_user_subscription(user_id)
    if subscribed:
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=f"✅ <b>تم التحقق!</b>\n\nأهلاً {user_name} 🎉",
                reply_markup=get_main_inline_keyboard())
        except Exception:
            pass
        user_states.pop(user_id, None)
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main_menu')
def cb_back(call):
    user_name = call.from_user.first_name or str(call.from_user.id)
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=f"👋 <b>مرحباً {user_name}!</b>\n\n👇 اختر نوع البحث",
            reply_markup=get_main_inline_keyboard())
    except Exception:
        pass
    user_states.pop(call.from_user.id, None)
    bot.answer_callback_query(call.id)

# ==================== لوحة الأدمن ====================

@bot.callback_query_handler(func=lambda call: call.data == 'admin_show_stats' and call.from_user.id == OWNER_ID)
def cb_admin_stats(call):
    uptime = datetime.datetime.now() - start_time
    h = int(uptime.total_seconds() // 3600)
    m = int((uptime.total_seconds() % 3600) // 60)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=(f"📊 <b>إحصائيات البوت</b>\n\n"
              f"👥 المستخدمين: <b>{len(bot_users)}</b>\n"
              f"🚫 المحظورين: <b>{len(banned_users)}</b>\n"
              f"📢 القنوات: <b>{len(mandatory_channels)}</b>\n"
              f"⏱ التشغيل: <b>{h}س {m}د</b>"),
        reply_markup=get_admin_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_broadcast' and call.from_user.id == OWNER_ID)
def cb_broadcast(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text="📨 <b>أرسل الرسالة الجماعية:</b>", reply_markup=get_admin_keyboard())
    user_states[call.from_user.id] = 'awaiting_broadcast'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'awaiting_broadcast' and m.from_user.id == OWNER_ID)
def process_broadcast(message):
    ok, fail = 0, 0
    for uid in bot_users:
        try:
            bot.send_message(uid, f"📢 <b>رسالة من الإدارة:</b>\n\n{message.text}")
            ok += 1
            time.sleep(0.05)
        except Exception:
            fail += 1
    bot.send_message(message.chat.id, f"✅ نجح: {ok}\n❌ فشل: {fail}", reply_markup=get_admin_keyboard())
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ban_user' and call.from_user.id == OWNER_ID)
def cb_ban(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text="🚫 <b>أرسل آيدي المستخدم لحظره:</b>", reply_markup=get_admin_keyboard())
    user_states[call.from_user.id] = 'awaiting_ban'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'awaiting_ban' and m.from_user.id == OWNER_ID)
def process_ban(message):
    try:
        tid = int(message.text.strip())
        banned_users.add(tid)
        bot.send_message(message.chat.id, f"✅ تم حظر <code>{tid}</code>", reply_markup=get_admin_keyboard())
        try: bot.send_message(tid, "🚫 <b>تم حظرك.</b>")
        except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ آيدي غير صحيح.", reply_markup=get_admin_keyboard())
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_unban_user' and call.from_user.id == OWNER_ID)
def cb_unban(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text="✅ <b>أرسل آيدي المستخدم لرفع الحظر:</b>", reply_markup=get_admin_keyboard())
    user_states[call.from_user.id] = 'awaiting_unban'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'awaiting_unban' and m.from_user.id == OWNER_ID)
def process_unban(message):
    try:
        tid = int(message.text.strip())
        banned_users.discard(tid)
        bot.send_message(message.chat.id, f"✅ تم رفع الحظر عن <code>{tid}</code>", reply_markup=get_admin_keyboard())
        try: bot.send_message(tid, "✅ <b>تم رفع الحظر!</b>")
        except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ آيدي غير صحيح.", reply_markup=get_admin_keyboard())
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_manage_channels' and call.from_user.id == OWNER_ID)
def cb_manage_channels(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text="📢 <b>إدارة القنوات</b>", reply_markup=get_admin_channel_management_keyboard())
    user_states[call.from_user.id] = 'admin_channels'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_user_menu' and call.from_user.id == OWNER_ID)
def cb_admin_back_user(call):
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            text="👋 <b>مرحباً!</b>\n\n👇 اختر نوع البحث", reply_markup=get_main_inline_keyboard())
    except: pass
    user_states.pop(call.from_user.id, None)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_channel' and call.from_user.id == OWNER_ID)
def cb_add_channel(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text='📢 <b>أرسل رابط القناة أو وجّه رسالة منها:</b>',
        reply_markup=get_back_to_channel_management_keyboard())
    user_states[call.from_user.id] = 'awaiting_channel'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_remove_channel' and call.from_user.id == OWNER_ID)
def cb_remove_channel(call):
    if not mandatory_channels:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            text='⚠️ لا توجد قنوات.', reply_markup=get_admin_channel_management_keyboard())
        bot.answer_callback_query(call.id)
        return
    markup = types.InlineKeyboardMarkup()
    for ch_id, ch_info in mandatory_channels.items():
        markup.add(types.InlineKeyboardButton(f"❌ {ch_info['title']}", callback_data=f'del_ch_{ch_id}'))
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='admin_back_to_admin_channel_management'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text='اختر القناة:', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_ch_') and call.from_user.id == OWNER_ID)
def cb_del_channel(call):
    cid = int(call.data.replace('del_ch_', ''))
    text = '✅ تم الحذف.' if cid in mandatory_channels else '❌ غير موجودة.'
    mandatory_channels.pop(cid, None)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=text, reply_markup=get_admin_channel_management_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_panel' and call.from_user.id == OWNER_ID)
def cb_back_admin(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text='⚙️ <b>لوحة التحكم</b>', reply_markup=get_admin_keyboard())
    user_states[call.from_user.id] = 'admin_panel'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_channel_management' and call.from_user.id == OWNER_ID)
def cb_back_channels(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text='📢 <b>إدارة القنوات</b>', reply_markup=get_admin_channel_management_keyboard())
    user_states[call.from_user.id] = 'admin_channels'
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text', 'forward_from_chat'],
    func=lambda m: user_states.get(m.from_user.id) == 'awaiting_channel' and m.from_user.id == OWNER_ID)
def process_channel_add(message):
    user_id = message.from_user.id
    channel_id = channel_link = channel_title = None

    if message.forward_from_chat and message.forward_from_chat.type in ['channel', 'supergroup']:
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title
        if message.forward_from_chat.username:
            channel_link = f"https://t.me/{message.forward_from_chat.username}"
        else:
            try:
                chat = bot.get_chat(channel_id)
                channel_link = chat.invite_link
            except Exception:
                pass
            if not channel_link:
                bot.send_message(user_id, '❌ لا يمكن الحصول على رابط.', reply_markup=get_admin_channel_management_keyboard())
                user_states[user_id] = 'admin_channels'
                return
    elif message.text and (message.text.startswith('https://t.me/') or message.text.startswith('@')):
        channel_link = message.text
        try:
            uname = message.text[1:] if message.text.startswith('@') else message.text.split('/')[3]
            info = bot.get_chat(uname)
            channel_id = info.id
            channel_title = info.title
        except Exception:
            bot.send_message(user_id, '❌ رابط غير صحيح.', reply_markup=get_admin_channel_management_keyboard())
            user_states[user_id] = 'admin_channels'
            return
    else:
        bot.send_message(user_id, '❌ أرسل رابطاً صحيحاً.', reply_markup=get_admin_channel_management_keyboard())
        user_states[user_id] = 'admin_channels'
        return

    if channel_id and channel_link and channel_title:
        mandatory_channels[channel_id] = {'title': channel_title, 'link': channel_link}
        bot.send_message(user_id, f"✅ تمت إضافة <b>{channel_title}</b>!", reply_markup=get_admin_channel_management_keyboard())
    else:
        bot.send_message(user_id, '❌ حدث خطأ.', reply_markup=get_admin_channel_management_keyboard())
    user_states[user_id] = 'admin_channels'

# ==================== تشغيل البوت ====================
print("✅ البوت يعمل...")
bot.polling(none_stop=True, interval=0, timeout=20)
