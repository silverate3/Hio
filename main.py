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
        types.InlineKeyboardButton('👻 سناب شات', callback_data='search_snapchat'),
        types.InlineKeyboardButton('🐦 تويتر/X', callback_data='search_twitter')
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
        markup.add(types.InlineKeyboardButton('🔗 فتح الحساب', url=url))
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

def get_country_from_code(phone_number):
    codes = {
        '+966': '🇸🇦 السعودية', '+971': '🇦🇪 الإمارات', '+964': '🇮🇶 العراق',
        '+965': '🇰🇼 الكويت', '+974': '🇶🇦 قطر', '+973': '🇧🇭 البحرين',
        '+968': '🇴🇲 عُمان', '+967': '🇾🇪 اليمن', '+20': '🇪🇬 مصر',
        '+212': '🇲🇦 المغرب', '+213': '🇩🇿 الجزائر', '+216': '🇹🇳 تونس',
        '+218': '🇱🇾 ليبيا', '+249': '🇸🇩 السودان', '+963': '🇸🇾 سوريا',
        '+961': '🇱🇧 لبنان', '+962': '🇯🇴 الأردن', '+98': '🇮🇷 إيران',
        '+90': '🇹🇷 تركيا', '+1': '🇺🇸 أمريكا', '+44': '🇬🇧 بريطانيا',
        '+7': '🇷🇺 روسيا', '+91': '🇮🇳 الهند', '+86': '🇨🇳 الصين',
    }
    for code, country in sorted(codes.items(), key=lambda x: -len(x[0])):
        if phone_number.startswith(code):
            return country
    return '🌍 غير محدد'

def animated_welcome(chat_id, user_name, markup):
    frames = ["🌑 جاري تحميل البوت...", "🌒 جاري تحميل البوت...",
              "🌓 جاري تحميل البوت...", "🌔 جاري تحميل البوت...", "🌕 اكتمل! ✨"]
    try:
        msg = bot.send_message(chat_id, frames[0])
        for frame in frames[1:]:
            time.sleep(0.6)
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=frame)
        time.sleep(0.5)
        bot.edit_message_text(
            chat_id=chat_id, message_id=msg.message_id,
            text=(f"🎉 <b>أهلاً {user_name}!</b>\n\n"
                  f"🔍 اختر نوع البحث من القائمة أدناه 👇"),
            reply_markup=markup
        )
    except Exception:
        pass

# ==================== دالة البحث مع الانيميشن ====================

def run_search(chat_id, user_id, search_func, format_func, wait_text):
    waiting_msg = bot.send_message(chat_id, wait_text)
    stop_anim = threading.Event()

    def animate():
        frames = ["🔍 <b>جاري البحث .</b>", "🔍 <b>جاري البحث ..</b>",
                  "🔍 <b>جاري البحث ...</b>", "📡 <b>جاري الاتصال...</b>",
                  "🔎 <b>تحليل البيانات...</b>"]
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

    # Caller API
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

    # NumLookup API (مجاني بدون مفتاح)
    try:
        clean = phone.replace('+', '').replace(' ', '')
        r2 = requests.get(
            f"https://www.numlookup.com/api/lookup?apikey=free&number={clean}",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=8
        )
        if r2.status_code == 200:
            d2 = r2.json()
            if not name:
                name = d2.get('name') or d2.get('caller_name')
            carrier = d2.get('carrier') or d2.get('operator')
            line_type = d2.get('line_type') or d2.get('type')
    except Exception:
        pass

    return {'name': name, 'carrier': carrier, 'line_type': line_type}

# ==================== خدمة 2: انستقرام (RapidAPI مجاني) ====================

def search_instagram(username):
    username = username.strip().lstrip('@')

    # محاولة 1: Instagram oEmbed API (رسمي ومجاني)
    try:
        r = requests.get(
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
            headers={
                'User-Agent': 'Instagram 155.0.0.37.107',
                'Accept': '*/*',
                'Accept-Language': 'en-US',
                'x-ig-app-id': '936619743392459',
                'x-asbd-id': '198387',
                'x-ig-www-claim': '0',
                'origin': 'https://www.instagram.com',
                'referer': f'https://www.instagram.com/{username}/',
            },
            timeout=10
        )
        if r.status_code == 200:
            d = r.json()
            u = d.get('data', {}).get('user', {})
            if u:
                return {
                    'full_name': u.get('full_name') or 'غير محدد',
                    'username': u.get('username', username),
                    'bio': (u.get('biography') or 'لا يوجد')[:150],
                    'followers': f"{u.get('edge_followed_by', {}).get('count', 0):,}",
                    'following': f"{u.get('edge_follow', {}).get('count', 0):,}",
                    'posts': f"{u.get('edge_owner_to_timeline_media', {}).get('count', 0):,}",
                    'is_private': '🔒 خاص' if u.get('is_private') else '🌐 عام',
                    'is_verified': '✅ موثق' if u.get('is_verified') else '❌ غير موثق',
                }
    except Exception:
        pass

    # محاولة 2: Picuki (موقع بديل يعرض معلومات انستقرام)
    try:
        r2 = requests.get(
            f"https://www.picuki.com/profile/{username}",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            timeout=10
        )
        if r2.status_code == 200:
            text = r2.text
            name_m = re.search(r'<h1[^>]*class="[^"]*profile-name[^"]*"[^>]*>([^<]+)<', text)
            followers_m = re.search(r'(\d[\d,.]+)\s*[Ff]ollowers', text)
            following_m = re.search(r'(\d[\d,.]+)\s*[Ff]ollowing', text)
            posts_m = re.search(r'(\d[\d,.]+)\s*[Pp]osts', text)
            if name_m or followers_m:
                return {
                    'full_name': name_m.group(1).strip() if name_m else username,
                    'username': username,
                    'bio': 'غير متاح',
                    'followers': followers_m.group(1) if followers_m else 'غير محدد',
                    'following': following_m.group(1) if following_m else 'غير محدد',
                    'posts': posts_m.group(1) if posts_m else 'غير محدد',
                    'is_private': '❓ غير محدد',
                    'is_verified': '❓ غير محدد',
                }
    except Exception:
        pass

    # محاولة 3: Imginn
    try:
        r3 = requests.get(
            f"https://imginn.com/{username}/",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=10
        )
        if r3.status_code == 200:
            text = r3.text
            name_m = re.search(r'<div class="name">([^<]+)<', text)
            followers_m = re.search(r'<span>([\d,.KkMm]+)</span>\s*[Ff]ollowers', text)
            following_m = re.search(r'<span>([\d,.KkMm]+)</span>\s*[Ff]ollowing', text)
            posts_m = re.search(r'<span>([\d,.KkMm]+)</span>\s*[Pp]osts', text)
            if name_m or followers_m:
                return {
                    'full_name': name_m.group(1).strip() if name_m else username,
                    'username': username,
                    'bio': 'غير متاح',
                    'followers': followers_m.group(1) if followers_m else 'غير محدد',
                    'following': following_m.group(1) if following_m else 'غير محدد',
                    'posts': posts_m.group(1) if posts_m else 'غير محدد',
                    'is_private': '❓ غير محدد',
                    'is_verified': '❓ غير محدد',
                }
    except Exception:
        pass

    return None

# ==================== خدمة 3: تيك توك ====================

def search_tiktok(username):
    username = username.strip().lstrip('@')

    # محاولة 1: TikTok oEmbed
    try:
        r = requests.get(
            f"https://www.tiktok.com/oembed?url=https://www.tiktok.com/@{username}",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=10
        )
        if r.status_code == 200:
            d = r.json()
            author = d.get('author_name') or d.get('author_url', '').split('@')[-1]
            if author:
                # نجلب المزيد من المعلومات
                followers = 'غير محدد'
                likes = 'غير محدد'
                videos = 'غير محدد'
                try:
                    r2 = requests.get(
                        f"https://www.tiktok.com/@{username}",
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept-Language': 'en-US,en;q=0.9',
                        },
                        timeout=10
                    )
                    if r2.status_code == 200:
                        text = r2.text
                        f_m = re.search(r'"followerCount":(\d+)', text)
                        l_m = re.search(r'"heartCount":(\d+)', text)
                        v_m = re.search(r'"videoCount":(\d+)', text)
                        nick_m = re.search(r'"nickname":"([^"]+)"', text)
                        if f_m: followers = f"{int(f_m.group(1)):,}"
                        if l_m: likes = f"{int(l_m.group(1)):,}"
                        if v_m: videos = f"{int(v_m.group(1)):,}"
                        if nick_m: author = nick_m.group(1)
                except Exception:
                    pass
                return {
                    'nickname': author,
                    'username': username,
                    'followers': followers,
                    'likes': likes,
                    'videos': videos,
                    'is_verified': '❓ غير محدد',
                }
    except Exception:
        pass

    # محاولة 2: صفحة TikTok مباشرة
    try:
        r = requests.get(
            f"https://www.tiktok.com/@{username}",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml',
            },
            timeout=12
        )
        if r.status_code == 200:
            text = r.text
            nick_m = re.search(r'"nickname":"([^"]+)"', text)
            f_m = re.search(r'"followerCount":(\d+)', text)
            l_m = re.search(r'"heartCount":(\d+)', text)
            v_m = re.search(r'"videoCount":(\d+)', text)
            ver_m = re.search(r'"verified":(true|false)', text)
            if nick_m or f_m:
                return {
                    'nickname': nick_m.group(1) if nick_m else username,
                    'username': username,
                    'followers': f"{int(f_m.group(1)):,}" if f_m else 'غير محدد',
                    'likes': f"{int(l_m.group(1)):,}" if l_m else 'غير محدد',
                    'videos': f"{int(v_m.group(1)):,}" if v_m else 'غير محدد',
                    'is_verified': '✅ موثق' if ver_m and ver_m.group(1) == 'true' else '❌ غير موثق',
                }
    except Exception:
        pass

    return None

# ==================== خدمة 4: سناب شات ====================

def search_snapchat(username):
    username = username.strip().lstrip('@')

    # محاولة 1: Snapchat Public Profiles API
    try:
        r = requests.get(
            f"https://storysharing.snapchat.com/v1/user/{username}",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            },
            timeout=10
        )
        if r.status_code == 200:
            d = r.json()
            story = d.get('story', {})
            metadata = story.get('metadata', {})
            if metadata or story:
                return {
                    'display_name': metadata.get('title') or username,
                    'username': username,
                    'bio': metadata.get('description') or 'لا يوجد',
                    'subscribers': 'غير محدد',
                    'is_verified': '✅ موثق' if metadata.get('is_verified') else '❓ غير محدد',
                }
    except Exception:
        pass

    # محاولة 2: صفحة الإضافة
    try:
        r2 = requests.get(
            f"https://www.snapchat.com/add/{username}",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            timeout=10
        )
        if r2.status_code == 200:
            text = r2.text
            name_m = re.search(r'"displayName"\s*:\s*"([^"]+)"', text)
            bio_m = re.search(r'"bio"\s*:\s*"([^"]*)"', text)
            subs_m = re.search(r'"subscriberCount"\s*:\s*(\d+)', text)
            ver_m = re.search(r'"isVerified"\s*:\s*(true|false)', text)

            if name_m or (r2.status_code == 200 and username.lower() in text.lower()):
                return {
                    'display_name': name_m.group(1) if name_m else username,
                    'username': username,
                    'bio': bio_m.group(1) if bio_m else 'لا يوجد',
                    'subscribers': f"{int(subs_m.group(1)):,}" if subs_m else 'غير محدد',
                    'is_verified': '✅ موثق' if ver_m and ver_m.group(1) == 'true' else '❌ غير موثق',
                }
    except Exception:
        pass

    # محاولة 3: Snapchat Public Profile
    try:
        r3 = requests.post(
            "https://www.snapchat.com/web/public_profile_info",
            json={"username": username},
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/json',
                'origin': 'https://www.snapchat.com',
            },
            timeout=10
        )
        if r3.status_code == 200:
            d3 = r3.json()
            if d3.get('publicProfileInfo'):
                info = d3['publicProfileInfo']
                return {
                    'display_name': info.get('title') or username,
                    'username': username,
                    'bio': info.get('description') or 'لا يوجد',
                    'subscribers': f"{info.get('subscriberCount', 0):,}",
                    'is_verified': '✅ موثق' if info.get('isVerified') else '❌ غير موثق',
                }
    except Exception:
        pass

    return None

# ==================== خدمة 5: تويتر/X ====================

def search_twitter(username):
    username = username.strip().lstrip('@')

    # محاولة 1: Nitter (مرآة تويتر مفتوحة المصدر)
    nitter_instances = [
        f"https://nitter.privacydev.net/{username}",
        f"https://nitter.poast.org/{username}",
        f"https://nitter.1d4.us/{username}",
    ]
    for url in nitter_instances:
        try:
            r = requests.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                timeout=8
            )
            if r.status_code == 200 and 'profile' in r.text.lower():
                text = r.text
                name_m = re.search(r'<a class="profile-card-fullname"[^>]*>\s*([^<]+)\s*<', text)
                username_m = re.search(r'<a class="profile-card-username"[^>]*>\s*(@[^<]+)\s*<', text)
                bio_m = re.search(r'<p class="profile-bio"[^>]*>(.*?)</p>', text, re.DOTALL)
                tweets_m = re.search(r'<li[^>]*>\s*<span class="profile-stat-header">Tweets</span>\s*<span[^>]*>([^<]+)<', text)
                following_m = re.search(r'<li[^>]*>\s*<span class="profile-stat-header">Following</span>\s*<span[^>]*>([^<]+)<', text)
                followers_m = re.search(r'<li[^>]*>\s*<span class="profile-stat-header">Followers</span>\s*<span[^>]*>([^<]+)<', text)
                if name_m:
                    bio_text = re.sub(r'<[^>]+>', '', bio_m.group(1)).strip() if bio_m else 'لا يوجد'
                    return {
                        'name': name_m.group(1).strip(),
                        'username': (username_m.group(1).strip() if username_m else f"@{username}"),
                        'bio': bio_text[:150],
                        'tweets': tweets_m.group(1).strip() if tweets_m else 'غير محدد',
                        'following': following_m.group(1).strip() if following_m else 'غير محدد',
                        'followers': followers_m.group(1).strip() if followers_m else 'غير محدد',
                        'is_verified': '❓ غير محدد',
                    }
        except Exception:
            continue

    # محاولة 2: Twitter oEmbed
    try:
        r2 = requests.get(
            f"https://publish.twitter.com/oembed?url=https://twitter.com/{username}&omit_script=true",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=8
        )
        if r2.status_code == 200:
            d2 = r2.json()
            author = d2.get('author_name', username)
            return {
                'name': author,
                'username': f"@{username}",
                'bio': 'غير متاح',
                'tweets': 'غير محدد',
                'following': 'غير محدد',
                'followers': 'غير محدد',
                'is_verified': '❓ غير محدد',
            }
    except Exception:
        pass

    return None

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

    if is_new:
        threading.Thread(target=animated_welcome, args=(message.chat.id, user_name, get_main_inline_keyboard())).start()
    else:
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

def check_and_set_search_state(call, state, prompt_text):
    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "🚫 أنت محظور!", show_alert=True)
        return False
    subscribed, _ = check_user_subscription(user_id)
    if not subscribed:
        bot.answer_callback_query(call.id, "⚠️ يجب الاشتراك أولاً!", show_alert=True)
        return False
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=prompt_text, reply_markup=get_back_keyboard())
    user_states[user_id] = state
    bot.answer_callback_query(call.id)
    return True

@bot.callback_query_handler(func=lambda call: call.data == 'search_phone')
def cb_search_phone(call):
    check_and_set_search_state(call, 'awaiting_phone',
        "📞 <b>أرسل رقم الهاتف مع رمز الدولة</b>\n\nمثال: <code>+9647801234567</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_instagram')
def cb_search_instagram(call):
    check_and_set_search_state(call, 'awaiting_instagram',
        "📸 <b>أرسل اسم مستخدم انستقرام</b>\n\nمثال: <code>cristiano</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_tiktok')
def cb_search_tiktok(call):
    check_and_set_search_state(call, 'awaiting_tiktok',
        "🎵 <b>أرسل اسم مستخدم تيك توك</b>\n\nمثال: <code>khaby.lame</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_snapchat')
def cb_search_snapchat(call):
    check_and_set_search_state(call, 'awaiting_snapchat',
        "👻 <b>أرسل اسم مستخدم سناب شات</b>\n\nمثال: <code>snapchat</code>")

@bot.callback_query_handler(func=lambda call: call.data == 'search_twitter')
def cb_search_twitter(call):
    check_and_set_search_state(call, 'awaiting_twitter',
        "🐦 <b>أرسل اسم مستخدم تويتر/X</b>\n\nمثال: <code>elonmusk</code>")

# ==================== معالجة الرسائل ====================

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in [
    'awaiting_phone', 'awaiting_instagram', 'awaiting_tiktok',
    'awaiting_snapchat', 'awaiting_twitter'
])
def handle_search_input(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    query = message.text.strip()
    user_states[user_id] = 'searching'

    if state == 'awaiting_phone':
        if not query.startswith('+') or len(query) < 7:
            bot.send_message(message.chat.id, "❌ أرسل الرقم مع رمز الدولة\nمثال: <code>+9647801234567</code>", reply_markup=get_back_keyboard())
            user_states[user_id] = 'awaiting_phone'
            return

        def search(): return search_phone_number(query)
        def fmt(r):
            country = get_country_from_code(query)
            name = r.get('name')
            carrier = r.get('carrier')
            line_type = r.get('line_type')
            if name:
                text = (f"✅ <b>تم العثور على النتيجة!</b>\n{'─'*22}\n"
                        f"📞 <b>الرقم:</b> <code>{query}</code>\n"
                        f"👤 <b>الاسم:</b> <b>{name}</b>\n"
                        f"🌍 <b>الدولة:</b> {country}\n")
            else:
                text = (f"⚠️ <b>لم يتم العثور على اسم</b>\n{'─'*22}\n"
                        f"📞 <b>الرقم:</b> <code>{query}</code>\n"
                        f"🌍 <b>الدولة:</b> {country}\n")
            if carrier: text += f"📶 <b>الشبكة:</b> {carrier}\n"
            if line_type:
                lm = {'mobile': '📱 موبايل', 'landline': '☎️ أرضي', 'voip': '🌐 VoIP'}
                text += f"📋 <b>نوع الخط:</b> {lm.get(line_type, line_type)}\n"
            return text, get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "📞 <b>جاري البحث عن الرقم...</b>")).start()

    elif state == 'awaiting_instagram':
        username = query.lstrip('@')
        def search(): return search_instagram(username)
        def fmt(r):
            if r:
                text = (f"📸 <b>نتيجة انستقرام</b>\n{'─'*22}\n"
                        f"👤 <b>الاسم:</b> {r['full_name']}\n"
                        f"🔗 <b>المعرف:</b> @{r['username']}\n"
                        f"📝 <b>البايو:</b> {r['bio']}\n"
                        f"👥 <b>المتابعون:</b> {r['followers']}\n"
                        f"➡️ <b>يتابع:</b> {r['following']}\n"
                        f"🖼 <b>المنشورات:</b> {r['posts']}\n"
                        f"🔐 <b>الحساب:</b> {r['is_private']}\n"
                        f"✅ <b>التوثيق:</b> {r['is_verified']}\n")
                return text, get_result_keyboard(f"https://instagram.com/{r['username']}")
            return f"❌ <b>لم يتم العثور على</b> @{username}\n\nتأكد من اسم المستخدم.", get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "📸 <b>جاري البحث في انستقرام...</b>")).start()

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

    elif state == 'awaiting_snapchat':
        username = query.lstrip('@')
        def search(): return search_snapchat(username)
        def fmt(r):
            if r:
                text = (f"👻 <b>نتيجة سناب شات</b>\n{'─'*22}\n"
                        f"👤 <b>الاسم:</b> {r['display_name']}\n"
                        f"🔗 <b>المعرف:</b> {r['username']}\n"
                        f"📝 <b>البايو:</b> {r['bio']}\n"
                        f"👥 <b>المشتركون:</b> {r['subscribers']}\n"
                        f"✅ <b>التوثيق:</b> {r['is_verified']}\n")
                return text, get_result_keyboard(f"https://snapchat.com/add/{r['username']}")
            return f"❌ <b>لم يتم العثور على</b> {username}", get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "👻 <b>جاري البحث في سناب شات...</b>")).start()

    elif state == 'awaiting_twitter':
        username = query.lstrip('@')
        def search(): return search_twitter(username)
        def fmt(r):
            if r:
                text = (f"🐦 <b>نتيجة تويتر/X</b>\n{'─'*22}\n"
                        f"👤 <b>الاسم:</b> {r['name']}\n"
                        f"🔗 <b>المعرف:</b> {r['username']}\n"
                        f"📝 <b>البايو:</b> {r['bio']}\n"
                        f"👥 <b>المتابعون:</b> {r['followers']}\n"
                        f"➡️ <b>يتابع:</b> {r['following']}\n"
                        f"🐦 <b>التغريدات:</b> {r['tweets']}\n"
                        f"✅ <b>التوثيق:</b> {r['is_verified']}\n")
                return text, get_result_keyboard(f"https://twitter.com/{username}")
            return f"❌ <b>لم يتم العثور على</b> @{username}", get_back_keyboard()
        threading.Thread(target=run_search, args=(message.chat.id, user_id, search, fmt, "🐦 <b>جاري البحث في تويتر...</b>")).start()

# ==================== Callbacks عامة ====================

@bot.callback_query_handler(func=lambda call: call.data == 'show_help_menu')
def cb_help(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=("❓ <b>كيفية الاستخدام</b>\n\n"
              "📞 <b>رقم الهاتف:</b> أرسل مع رمز الدولة\n"
              "   مثال: <code>+9647801234567</code>\n\n"
              "📸 <b>انستقرام / 🎵 تيك توك\n"
              "👻 سناب شات / 🐦 تويتر:</b>\n"
              "   أرسل اسم المستخدم فقط\n"
              "   مثال: <code>cristiano</code>\n\n"
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
    if cid in mandatory_channels:
        del mandatory_channels[cid]
        text = '✅ تم الحذف.'
    else:
        text = '❌ غير موجودة.'
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
