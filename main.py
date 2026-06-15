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
search_counts = {}
banned_users = set()
start_time = datetime.datetime.now()

# ==================== لوحات المفاتيح ====================

def get_main_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('📞 بحث برقم الهاتف', callback_data='search_name'))
    markup.row(
        types.InlineKeyboardButton('📸 بحث انستقرام', callback_data='search_instagram'),
        types.InlineKeyboardButton('🎵 بحث تيك توك', callback_data='search_tiktok')
    )
    markup.row(
        types.InlineKeyboardButton('👻 بحث سناب شات', callback_data='search_snapchat'),
        types.InlineKeyboardButton('🐦 بحث تويتر', callback_data='search_twitter')
    )
    markup.row(
        types.InlineKeyboardButton('👨‍💻 المطور', url='https://t.me/BBBBYB2'),
        types.InlineKeyboardButton('❓ المساعدة', callback_data='show_help_menu')
    )
    return markup

def get_inline_back_to_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_main_menu'))
    return markup

def get_search_result_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔍 بحث آخر', callback_data='back_to_main_menu'))
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
                f"✨ يسعدنا انضمامك!\n\n"
                f"🔍 يمكنك البحث عن معلومات:\n"
                f"📞 أرقام الهواتف\n"
                f"📸 حسابات انستقرام\n"
                f"🎵 حسابات تيك توك\n"
                f"👻 حسابات سناب شات\n"
                f"🐦 حسابات تويتر\n\n"
                f"👇 اختر نوع البحث"
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
    }
    for code, country in sorted(codes.items(), key=lambda x: -len(x[0])):
        if phone_number.startswith(code):
            return country
    return '🌍 غير محدد'

# ==================== خدمات البحث عن الرقم ====================

def search_api_caller(phone_number):
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
                return name
    except Exception:
        pass
    return None

def search_api_sync_me(phone_number):
    try:
        clean = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        url = f"https://sync.me/search/?number={clean}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'ar-SA,ar;q=0.9',
        }
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            match = re.search(r'"name"\s*:\s*"([^"]+)"', response.text)
            if match:
                name = match.group(1)
                if name and len(name) > 1:
                    return name
    except Exception:
        pass
    return None

def search_phone_carrier(phone_number):
    try:
        clean = phone_number.replace('+', '').replace(' ', '')
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key=free&phone={clean}"
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            carrier = None
            if isinstance(data.get('carrier'), dict):
                carrier = data['carrier'].get('name')
            elif isinstance(data.get('carrier'), str):
                carrier = data['carrier']
            line_type = data.get('type', None)
            return carrier, line_type
    except Exception:
        pass
    return None, None

def search_all_phone_apis(phone_number):
    results = {'name': None, 'carrier': None, 'line_type': None}
    name_r = [None]
    name2_r = [None]
    carrier_r = [None, None]

    def r1(): name_r[0] = search_api_caller(phone_number)
    def r2(): name2_r[0] = search_api_sync_me(phone_number)
    def r3(): carrier_r[0], carrier_r[1] = search_phone_carrier(phone_number)

    threads = [threading.Thread(target=f) for f in [r1, r2, r3]]
    for t in threads:
        t.daemon = True
        t.start()
    for t in threads:
        t.join(timeout=12)

    results['name'] = name_r[0] or name2_r[0]
    results['carrier'] = carrier_r[0]
    results['line_type'] = carrier_r[1]
    return results

# ==================== خدمات البحث عن حسابات السوشيال ميديا ====================

def search_instagram(username):
    try:
        username = username.lstrip('@').strip()
        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
            'Accept-Language': 'ar-SA,ar;q=0.9',
            'x-ig-app-id': '936619743392459',
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user = data.get('graphql', {}).get('user') or data.get('data', {}).get('user')
            if user:
                return {
                    'full_name': user.get('full_name', 'غير محدد'),
                    'username': user.get('username', username),
                    'bio': user.get('biography', 'لا يوجد'),
                    'followers': f"{user.get('edge_followed_by', {}).get('count', 0):,}",
                    'following': f"{user.get('edge_follow', {}).get('count', 0):,}",
                    'posts': f"{user.get('edge_owner_to_timeline_media', {}).get('count', 0):,}",
                    'is_private': '🔒 خاص' if user.get('is_private') else '🌐 عام',
                    'is_verified': '✅ موثق' if user.get('is_verified') else '❌ غير موثق',
                    'profile_url': f"https://instagram.com/{username}"
                }
    except Exception:
        pass

    # محاولة ثانية بدون __a=1
    try:
        url2 = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers2 = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
            'x-ig-app-id': '936619743392459',
            'Accept': 'application/json',
        }
        r2 = requests.get(url2, headers=headers2, timeout=10)
        if r2.status_code == 200:
            d2 = r2.json()
            user = d2.get('data', {}).get('user', {})
            if user:
                return {
                    'full_name': user.get('full_name', 'غير محدد'),
                    'username': user.get('username', username),
                    'bio': user.get('biography', 'لا يوجد'),
                    'followers': f"{user.get('edge_followed_by', {}).get('count', 0):,}",
                    'following': f"{user.get('edge_follow', {}).get('count', 0):,}",
                    'posts': f"{user.get('edge_owner_to_timeline_media', {}).get('count', 0):,}",
                    'is_private': '🔒 خاص' if user.get('is_private') else '🌐 عام',
                    'is_verified': '✅ موثق' if user.get('is_verified') else '❌ غير موثق',
                    'profile_url': f"https://instagram.com/{username}"
                }
    except Exception:
        pass
    return None

def search_tiktok(username):
    try:
        username = username.lstrip('@').strip()
        url = f"https://www.tiktok.com/@{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept-Language': 'ar-SA,ar;q=0.9',
            'Accept': 'text/html,application/xhtml+xml',
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            text = response.text
            # استخراج البيانات من JSON المضمن
            match = re.search(r'"userInfo":\{"user":\{([^}]+)\}', text)
            
            followers_match = re.search(r'"followerCount":(\d+)', text)
            following_match = re.search(r'"followingCount":(\d+)', text)
            likes_match = re.search(r'"heartCount":(\d+)', text)
            videos_match = re.search(r'"videoCount":(\d+)', text)
            nickname_match = re.search(r'"nickname":"([^"]+)"', text)
            bio_match = re.search(r'"signature":"([^"]*)"', text)
            verified_match = re.search(r'"verified":(true|false)', text)

            if followers_match or nickname_match:
                return {
                    'nickname': nickname_match.group(1) if nickname_match else username,
                    'username': f"@{username}",
                    'bio': bio_match.group(1) if bio_match else 'لا يوجد',
                    'followers': f"{int(followers_match.group(1)):,}" if followers_match else 'غير محدد',
                    'following': f"{int(following_match.group(1)):,}" if following_match else 'غير محدد',
                    'likes': f"{int(likes_match.group(1)):,}" if likes_match else 'غير محدد',
                    'videos': f"{int(videos_match.group(1)):,}" if videos_match else 'غير محدد',
                    'is_verified': '✅ موثق' if verified_match and verified_match.group(1) == 'true' else '❌ غير موثق',
                    'profile_url': f"https://tiktok.com/@{username}"
                }
    except Exception:
        pass
    return None

def search_snapchat(username):
    try:
        username = username.lstrip('@').strip()
        url = f"https://www.snapchat.com/add/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept-Language': 'ar-SA,ar;q=0.9',
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            text = response.text
            name_match = re.search(r'"displayName":"([^"]+)"', text)
            bio_match = re.search(r'"bio":"([^"]*)"', text)
            subscribers_match = re.search(r'"subscriberCount":(\d+)', text)
            verified_match = re.search(r'"isVerified":(true|false)', text)

            if name_match or username in text:
                return {
                    'display_name': name_match.group(1) if name_match else username,
                    'username': username,
                    'bio': bio_match.group(1) if bio_match else 'لا يوجد',
                    'subscribers': f"{int(subscribers_match.group(1)):,}" if subscribers_match else 'غير محدد',
                    'is_verified': '✅ موثق' if verified_match and verified_match.group(1) == 'true' else '❌ غير موثق',
                    'profile_url': f"https://www.snapchat.com/add/{username}"
                }
    except Exception:
        pass
    return None

def search_twitter(username):
    try:
        username = username.lstrip('@').strip()
        url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user = None
            if 'timeline' in data:
                instructions = data['timeline'].get('instructions', [])
                for inst in instructions:
                    entries = inst.get('addEntries', {}).get('entries', [])
                    for entry in entries:
                        content = entry.get('content', {}).get('item', {}).get('content', {})
                        if 'user' in content:
                            user = content['user'].get('legacy', {})
                            break
            if user:
                return {
                    'name': user.get('name', username),
                    'username': f"@{user.get('screen_name', username)}",
                    'bio': user.get('description', 'لا يوجد'),
                    'followers': f"{user.get('followers_count', 0):,}",
                    'following': f"{user.get('friends_count', 0):,}",
                    'tweets': f"{user.get('statuses_count', 0):,}",
                    'is_verified': '✅ موثق' if user.get('verified') else '❌ غير موثق',
                    'location': user.get('location', 'غير محدد'),
                    'profile_url': f"https://twitter.com/{username}"
                }
    except Exception:
        pass

    # محاولة ثانية
    try:
        url2 = f"https://nitter.net/{username}"
        headers2 = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar'}
        r2 = requests.get(url2, headers=headers2, timeout=8)
        if r2.status_code == 200:
            text = r2.text
            name_match = re.search(r'<a class="profile-card-fullname"[^>]*>([^<]+)<', text)
            followers_match = re.search(r'Followers.*?<span[^>]*>([^<]+)<', text, re.DOTALL)
            bio_match = re.search(r'<p class="profile-bio"[^>]*>(.*?)</p>', text, re.DOTALL)
            if name_match:
                bio_text = re.sub(r'<[^>]+>', '', bio_match.group(1)).strip() if bio_match else 'لا يوجد'
                return {
                    'name': name_match.group(1).strip(),
                    'username': f"@{username}",
                    'bio': bio_text,
                    'followers': followers_match.group(1).strip() if followers_match else 'غير محدد',
                    'following': 'غير محدد',
                    'tweets': 'غير محدد',
                    'is_verified': '❌ غير موثق',
                    'location': 'غير محدد',
                    'profile_url': f"https://twitter.com/{username}"
                }
    except Exception:
        pass
    return None

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
            f"👇 اختر نوع البحث",
            reply_markup=get_main_inline_keyboard()
        )

    if user_id in user_states:
        del user_states[user_id]

# ==================== أمر /admin ====================

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    if message.from_user.id != OWNER_ID:
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

# ==================== دالة الانتظار المتحركة ====================

def send_waiting_and_search(chat_id, user_id, search_func, result_formatter, waiting_text="🔍 <b>جاري البحث...</b>"):
    waiting_msg = bot.send_message(chat_id, waiting_text)
    stop_animation = threading.Event()

    def animate():
        frames = [
            "🔍 <b>جاري البحث .</b>",
            "🔍 <b>جاري البحث ..</b>",
            "🔍 <b>جاري البحث ...</b>",
            "📡 <b>الاتصال بالخوادم...</b>",
            "🔎 <b>تحليل البيانات...</b>",
        ]
        i = 0
        while not stop_animation.is_set():
            time.sleep(0.8)
            if stop_animation.is_set():
                break
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text=frames[i % len(frames)])
                i += 1
            except Exception:
                break

    anim = threading.Thread(target=animate)
    anim.daemon = True
    anim.start()

    try:
        result = search_func()
        stop_animation.set()
        time.sleep(0.4)
        result_text, markup = result_formatter(result)
        bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text=result_text, reply_markup=markup)
    except Exception:
        stop_animation.set()
        time.sleep(0.3)
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text="❌ <b>حدث خطأ، حاول مرة أخرى.</b>", reply_markup=get_main_inline_keyboard())
        except Exception:
            pass
    finally:
        stop_animation.set()
        if user_id in user_states:
            del user_states[user_id]

# ==================== بحث رقم الهاتف ====================

@bot.callback_query_handler(func=lambda call: call.data == 'search_name')
def callback_search_phone(call):
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
             "مثال: <code>+9647801234567</code>",
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
    user_states[user_id] = 'searching'

    if not phone_number.startswith('+') or len(phone_number) < 7:
        bot.send_message(message.chat.id, "❌ <b>رقم غير صحيح!</b>\n\nمثال: <code>+9647801234567</code>", reply_markup=get_inline_back_to_main_keyboard())
        user_states[user_id] = 'awaiting_phone_number'
        return

    def do_search():
        return search_all_phone_apis(phone_number)

    def format_result(results):
        country = get_country_from_code(phone_number)
        name = results.get('name')
        carrier = results.get('carrier')
        line_type = results.get('line_type')

        if name:
            text = (
                f"✅ <b>تم العثور على النتيجة!</b>\n"
                f"{'─' * 22}\n"
                f"📞 <b>الرقم:</b> <code>{phone_number}</code>\n"
                f"👤 <b>الاسم:</b> <b>{name}</b>\n"
                f"🌍 <b>الدولة:</b> {country}\n"
            )
        else:
            text = (
                f"⚠️ <b>لم يتم العثور على اسم</b>\n"
                f"{'─' * 22}\n"
                f"📞 <b>الرقم:</b> <code>{phone_number}</code>\n"
                f"🌍 <b>الدولة:</b> {country}\n"
            )
        if carrier:
            text += f"📶 <b>الشبكة:</b> {carrier}\n"
        if line_type:
            line_map = {'mobile': '📱 موبايل', 'landline': '☎️ أرضي', 'voip': '🌐 VoIP'}
            text += f"📋 <b>نوع الخط:</b> {line_map.get(line_type, line_type)}\n"
        return text, get_search_result_keyboard()

    threading.Thread(target=send_waiting_and_search, args=(message.chat.id, user_id, do_search, format_result)).start()

# ==================== بحث انستقرام ====================

@bot.callback_query_handler(func=lambda call: call.data == 'search_instagram')
def callback_search_instagram(call):
    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "🚫 أنت محظور!", show_alert=True)
        return
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📸 <b>أرسل اسم مستخدم انستقرام</b>\n\n"
             "مثال: <code>cristiano</code> أو <code>@cristiano</code>",
        reply_markup=get_inline_back_to_main_keyboard()
    )
    user_states[user_id] = 'awaiting_instagram_username'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_instagram_username')
def process_instagram(message):
    user_id = message.from_user.id
    username = message.text.strip().lstrip('@')
    user_states[user_id] = 'searching'

    def do_search():
        return search_instagram(username)

    def format_result(data):
        if data:
            text = (
                f"📸 <b>نتيجة انستقرام</b>\n"
                f"{'─' * 22}\n"
                f"👤 <b>الاسم:</b> {data['full_name']}\n"
                f"🔗 <b>المعرف:</b> @{data['username']}\n"
                f"📝 <b>البايو:</b> {data['bio'][:100] if data['bio'] else 'لا يوجد'}\n"
                f"👥 <b>المتابعون:</b> {data['followers']}\n"
                f"➡️ <b>يتابع:</b> {data['following']}\n"
                f"🖼 <b>المنشورات:</b> {data['posts']}\n"
                f"🔐 <b>الحساب:</b> {data['is_private']}\n"
                f"✅ <b>التوثيق:</b> {data['is_verified']}\n"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('🔗 فتح الحساب', url=data['profile_url']))
            markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_main_menu'))
        else:
            text = f"❌ <b>لم يتم العثور على الحساب</b>\n\n<code>@{username}</code> غير موجود أو الحساب خاص."
            markup = get_search_result_keyboard()
        return text, markup

    threading.Thread(target=send_waiting_and_search, args=(message.chat.id, user_id, do_search, format_result, "📸 <b>جاري البحث في انستقرام...</b>")).start()

# ==================== بحث تيك توك ====================

@bot.callback_query_handler(func=lambda call: call.data == 'search_tiktok')
def callback_search_tiktok(call):
    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "🚫 أنت محظور!", show_alert=True)
        return
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🎵 <b>أرسل اسم مستخدم تيك توك</b>\n\n"
             "مثال: <code>khaby.lame</code> أو <code>@khaby.lame</code>",
        reply_markup=get_inline_back_to_main_keyboard()
    )
    user_states[user_id] = 'awaiting_tiktok_username'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_tiktok_username')
def process_tiktok(message):
    user_id = message.from_user.id
    username = message.text.strip().lstrip('@')
    user_states[user_id] = 'searching'

    def do_search():
        return search_tiktok(username)

    def format_result(data):
        if data:
            text = (
                f"🎵 <b>نتيجة تيك توك</b>\n"
                f"{'─' * 22}\n"
                f"👤 <b>الاسم:</b> {data['nickname']}\n"
                f"🔗 <b>المعرف:</b> {data['username']}\n"
                f"📝 <b>البايو:</b> {data['bio'][:100] if data['bio'] else 'لا يوجد'}\n"
                f"👥 <b>المتابعون:</b> {data['followers']}\n"
                f"➡️ <b>يتابع:</b> {data['following']}\n"
                f"❤️ <b>الإعجابات:</b> {data['likes']}\n"
                f"🎬 <b>الفيديوهات:</b> {data['videos']}\n"
                f"✅ <b>التوثيق:</b> {data['is_verified']}\n"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('🔗 فتح الحساب', url=data['profile_url']))
            markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_main_menu'))
        else:
            text = f"❌ <b>لم يتم العثور على الحساب</b>\n\n<code>@{username}</code> غير موجود."
            markup = get_search_result_keyboard()
        return text, markup

    threading.Thread(target=send_waiting_and_search, args=(message.chat.id, user_id, do_search, format_result, "🎵 <b>جاري البحث في تيك توك...</b>")).start()

# ==================== بحث سناب شات ====================

@bot.callback_query_handler(func=lambda call: call.data == 'search_snapchat')
def callback_search_snapchat(call):
    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "🚫 أنت محظور!", show_alert=True)
        return
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="👻 <b>أرسل اسم مستخدم سناب شات</b>\n\n"
             "مثال: <code>snapchat</code>",
        reply_markup=get_inline_back_to_main_keyboard()
    )
    user_states[user_id] = 'awaiting_snapchat_username'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_snapchat_username')
def process_snapchat(message):
    user_id = message.from_user.id
    username = message.text.strip().lstrip('@')
    user_states[user_id] = 'searching'

    def do_search():
        return search_snapchat(username)

    def format_result(data):
        if data:
            text = (
                f"👻 <b>نتيجة سناب شات</b>\n"
                f"{'─' * 22}\n"
                f"👤 <b>الاسم:</b> {data['display_name']}\n"
                f"🔗 <b>المعرف:</b> {data['username']}\n"
                f"📝 <b>البايو:</b> {data['bio'][:100] if data['bio'] else 'لا يوجد'}\n"
                f"👥 <b>المشتركون:</b> {data['subscribers']}\n"
                f"✅ <b>التوثيق:</b> {data['is_verified']}\n"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('🔗 فتح الحساب', url=data['profile_url']))
            markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_main_menu'))
        else:
            text = f"❌ <b>لم يتم العثور على الحساب</b>\n\n<code>{username}</code> غير موجود."
            markup = get_search_result_keyboard()
        return text, markup

    threading.Thread(target=send_waiting_and_search, args=(message.chat.id, user_id, do_search, format_result, "👻 <b>جاري البحث في سناب شات...</b>")).start()

# ==================== بحث تويتر/X ====================

@bot.callback_query_handler(func=lambda call: call.data == 'search_twitter')
def callback_search_twitter(call):
    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "🚫 أنت محظور!", show_alert=True)
        return
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🐦 <b>أرسل اسم مستخدم تويتر/X</b>\n\n"
             "مثال: <code>elonmusk</code> أو <code>@elonmusk</code>",
        reply_markup=get_inline_back_to_main_keyboard()
    )
    user_states[user_id] = 'awaiting_twitter_username'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_twitter_username')
def process_twitter(message):
    user_id = message.from_user.id
    username = message.text.strip().lstrip('@')
    user_states[user_id] = 'searching'

    def do_search():
        return search_twitter(username)

    def format_result(data):
        if data:
            text = (
                f"🐦 <b>نتيجة تويتر/X</b>\n"
                f"{'─' * 22}\n"
                f"👤 <b>الاسم:</b> {data['name']}\n"
                f"🔗 <b>المعرف:</b> {data['username']}\n"
                f"📝 <b>البايو:</b> {data['bio'][:100] if data['bio'] else 'لا يوجد'}\n"
                f"👥 <b>المتابعون:</b> {data['followers']}\n"
                f"➡️ <b>يتابع:</b> {data['following']}\n"
                f"🐦 <b>التغريدات:</b> {data['tweets']}\n"
                f"📍 <b>الموقع:</b> {data['location']}\n"
                f"✅ <b>التوثيق:</b> {data['is_verified']}\n"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('🔗 فتح الحساب', url=data['profile_url']))
            markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='back_to_main_menu'))
        else:
            text = f"❌ <b>لم يتم العثور على الحساب</b>\n\n<code>@{username}</code> غير موجود."
            markup = get_search_result_keyboard()
        return text, markup

    threading.Thread(target=send_waiting_and_search, args=(message.chat.id, user_id, do_search, format_result, "🐦 <b>جاري البحث في تويتر...</b>")).start()

# ==================== المساعدة ====================

@bot.callback_query_handler(func=lambda call: call.data == 'show_help_menu')
def callback_show_help(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            "❓ <b>كيفية الاستخدام</b>\n\n"
            "📞 <b>بحث رقم الهاتف:</b>\n"
            "أرسل الرقم مع رمز الدولة\n"
            "مثال: <code>+9647801234567</code>\n\n"
            "📸 <b>انستقرام / 🎵 تيك توك\n"
            "👻 سناب شات / 🐦 تويتر:</b>\n"
            "أرسل اسم المستخدم فقط\n"
            "مثال: <code>cristiano</code>\n\n"
            "👨‍💻 للتواصل: @BBBBYB2"
        ),
        reply_markup=get_inline_back_to_main_keyboard()
    )
    bot.answer_callback_query(call.id)

# ==================== التحقق من الاشتراك ====================

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub_again')
def callback_check_sub(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name or str(user_id)
    subscribed, _ = check_user_subscription(user_id)
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
    user_name = call.from_user.first_name or str(call.from_user.id)
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"👋 <b>مرحباً {user_name}!</b>\n\n👇 اختر نوع البحث",
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
    bot.send_message(message.chat.id, f"✅ نجح: {success}\n❌ فشل: {failed}", reply_markup=get_admin_keyboard())
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ban_user' and call.from_user.id == OWNER_ID)
def callback_admin_ban(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🚫 <b>أرسل آيدي المستخدم لحظره:</b>", reply_markup=get_admin_keyboard())
    user_states[call.from_user.id] = 'awaiting_ban_user_id'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_ban_user_id' and message.from_user.id == OWNER_ID)
def process_ban_user(message):
    try:
        target_id = int(message.text.strip())
        banned_users.add(target_id)
        bot.send_message(message.chat.id, f"✅ تم حظر <code>{target_id}</code>", reply_markup=get_admin_keyboard())
        try: bot.send_message(target_id, "🚫 <b>تم حظرك من استخدام البوت.</b>")
        except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ آيدي غير صحيح.", reply_markup=get_admin_keyboard())
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == 'admin_unban_user' and call.from_user.id == OWNER_ID)
def callback_admin_unban(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✅ <b>أرسل آيدي المستخدم لرفع الحظر:</b>", reply_markup=get_admin_keyboard())
    user_states[call.from_user.id] = 'awaiting_unban_user_id'
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_unban_user_id' and message.from_user.id == OWNER_ID)
def process_unban_user(message):
    try:
        target_id = int(message.text.strip())
        banned_users.discard(target_id)
        bot.send_message(message.chat.id, f"✅ تم رفع الحظر عن <code>{target_id}</code>", reply_markup=get_admin_keyboard())
        try: bot.send_message(target_id, "✅ <b>تم رفع الحظر عنك!</b>")
        except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ آيدي غير صحيح.", reply_markup=get_admin_keyboard())
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == 'admin_manage_channels' and call.from_user.id == OWNER_ID)
def callback_admin_manage_channels(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="📢 <b>إدارة قنوات الاشتراك الإجباري</b>", reply_markup=get_admin_channel_management_keyboard())
    user_states[call.from_user.id] = 'admin_channel_management'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_user_menu' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_user_menu(call):
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"👋 <b>مرحباً!</b>\n\n👇 اختر نوع البحث", reply_markup=get_main_inline_keyboard())
    except: pass
    if call.from_user.id in user_states:
        del user_states[call.from_user.id]
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_channel' and call.from_user.id == OWNER_ID)
def callback_admin_add_channel(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='📢 <b>أرسل رابط القناة أو وجّه رسالة منها:</b>', reply_markup=get_inline_back_to_channel_management_keyboard())
    user_states[call.from_user.id] = 'awaiting_channel_link_or_forward'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_remove_channel' and call.from_user.id == OWNER_ID)
def callback_admin_remove_channel(call):
    if not mandatory_channels:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='⚠️ لا توجد قنوات.', reply_markup=get_admin_channel_management_keyboard())
        bot.answer_callback_query(call.id)
        return
    markup = types.InlineKeyboardMarkup()
    for ch_id, ch_info in mandatory_channels.items():
        markup.add(types.InlineKeyboardButton(f"❌ {ch_info['title']}", callback_data=f'delete_channel_{ch_id}'))
    markup.add(types.InlineKeyboardButton('🔙 رجوع', callback_data='admin_back_to_admin_channel_management'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='اختر القناة:', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_channel_') and call.from_user.id == OWNER_ID)
def callback_delete_channel(call):
    channel_id_to_delete = int(call.data.replace('delete_channel_', ''))
    if channel_id_to_delete in mandatory_channels:
        del mandatory_channels[channel_id_to_delete]
        text = '✅ تم حذف القناة.'
    else:
        text = '❌ القناة غير موجودة.'
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=get_admin_channel_management_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_panel' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_admin_panel(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='⚙️ <b>لوحة التحكم</b>', reply_markup=get_admin_keyboard())
    user_states[call.from_user.id] = 'admin_panel'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_channel_management' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_channel_management(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='📢 <b>إدارة القنوات</b>', reply_markup=get_admin_channel_management_keyboard())
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
            uname = message.text[1:] if message.text.startswith('@') else message.text.split('/')[3]
            chat_info = bot.get_chat(uname)
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
        bot.send_message(user_id, f"✅ تمت إضافة '<b>{channel_title}</b>'!", reply_markup=get_admin_channel_management_keyboard())
    else:
        bot.send_message(user_id, '❌ حدث خطأ.', reply_markup=get_admin_channel_management_keyboard())

    user_states[user_id] = 'admin_channel_management'

# ==================== تشغيل البوت ====================
print("✅ البوت يعمل الآن...")
bot.polling(none_stop=True, interval=0, timeout=20)
