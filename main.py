import requests
import json
import webbrowser
import telebot
from telebot import types
import time
import threading




BOT_TOKEN = '384366955:AAFJdzI2untoSFoVTd_YSt79Uc7DCkwMbR4'
OWNER_ID = 256156772


bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

user_states = {}
mandatory_channels = {}
bot_users = set()

def get_main_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    item_search = types.InlineKeyboardButton('بحث عن الاسم', callback_data='search_name')
    item_dev = types.InlineKeyboardButton('Dev', url='https://t.me/BBBBYB2')
    item_help = types.InlineKeyboardButton('المساعده', callback_data='show_help_menu')
    markup.row(item_search)
    markup.row(item_dev, item_help)
    return markup

def get_inline_back_to_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='back_to_main_menu'))
    return markup

def get_admin_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('قسم الاشتراك الاجباري', callback_data='admin_manage_channels'))
    markup.add(types.InlineKeyboardButton('الاحصائيات', callback_data='admin_show_stats'))
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='admin_back_to_user_menu'))
    return markup

def get_admin_channel_management_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('اضافه قناة', callback_data='admin_add_channel'))
    markup.add(types.InlineKeyboardButton('حذف قناة', callback_data='admin_remove_channel'))
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='admin_back_to_admin_panel'))
    return markup

def get_inline_back_to_channel_management_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='admin_back_to_admin_channel_management'))
    return markup

def check_user_subscription(user_id):
    if not mandatory_channels:
        return True, None
    for channel_id, channel_info in mandatory_channels.items():
        try:
            member = bot.get_chat_member(channel_id, user_id)
            if member.status not in ['member', 'creator', 'administrator']:
                return False, channel_info
                def animated_welcome(chat_id, user_name, markup):
    frames = [
        "🌑 جاري تحميل البوت...",
        "🌒 جاري تحميل البوت...",
        "🌓 جاري تحميل البوت...",
        "🌔 جاري تحميل البوت...",
        "🌕 اكتمل التحميل!",
    ]
    msg = bot.send_message(chat_id, frames[0])
    for frame in frames[1:]:
        time.sleep(0.6)
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=frame)
    time.sleep(0.5)
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg.message_id,
        text=(
            f"🎉 أهلاً وسهلاً {user_name}!\n\n"
            f"✨ يسعدنا انضمامك لبوت معرفة اسم الرقم\n\n"
            f"📞 ابحث عن اسم أي رقم حول العالم!\n\n"
            f"👇 اضغط على البحث للبدء"
        ),
        reply_markup=markup
    )

        except Exception:
            return False, channel_info
    return True, None

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name if message.from_user.first_name else (message.from_user.username if message.from_user.username else str(user_id))

    if user_id not in bot_users:
        bot_users.add(user_id)
        owner_message = (
            f"دخول جديد للبوت\n"
            f"name: {message.from_user.full_name}\n"
            f"user: @{message.from_user.username if message.from_user.username else user_id}"
        )
        bot.send_message(OWNER_ID, owner_message)

    subscribed, channel_to_join = check_user_subscription(user_id)
    if not subscribed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(channel_to_join['title'], url=channel_to_join['link']))
        markup.add(types.InlineKeyboardButton('اشترك', url=channel_to_join['link']), types.InlineKeyboardButton('تحقق', callback_data='check_sub_again'))
        bot.send_message(
            message.chat.id,
            f"عذرا عزيزي {user_name} عليك الاشتراك بل قناة",
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
            f"👋 مرحباً {user_name}!\n\n👇 اضغط على البحث للبدء",
            reply_markup=get_main_inline_keyboard()
        )
    if user_id in user_states:
        del user_states[user_id]

    if user_id in user_states:
        del user_states[user_id]

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    bot.send_message(message.chat.id, "لوحه ادمن", reply_markup=get_admin_keyboard())
    user_states[user_id] = 'admin_panel'

@bot.message_handler(func=lambda message: message.text == 'بحث عن الاسم')
def handle_search_name_text_button(message):
    user_id = message.from_user.id
    subscribed, _ = check_user_subscription(user_id)
    if not subscribed:
        handle_start(message)
        return
    bot.send_message(message.chat.id, 'الان ارسل الرقم مع رمز دوله مع + -', reply_markup=get_inline_back_to_main_keyboard())
    user_states[user_id] = 'awaiting_phone_number'

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_phone_number')
def process_phone_number(message):
    user_id = message.from_user.id
    phone_number = message.text.strip()
    
    if not (phone_number.replace('+', '').isdigit() or phone_number.startswith('+') and phone_number[1:].isdigit()):
        bot.send_message(message.chat.id, 'الرجاء ارسال رقم هاتف صحيح.', reply_markup=get_inline_back_to_main_keyboard())
        return

    url = "https://caller-uegx.vercel.app/api/v1/search"
    payload = {"phone": phone_number}
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Google Chrome\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://caller-uegx.vercel.app",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://caller-uegx.vercel.app/",
        'accept-language': "ar-IQ,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        'priority': "u=1, i",
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response_json = response.json()
        name = "unavailable"
        if response_json and 'results' in response_json and response_json['results']:
            name = response_json['results'][0].get('name', 'unavailable')

        bot.send_message(
            message.chat.id,
            f"Name: {name}\n"
            f"The phone : {phone_number}",
            reply_markup=get_main_inline_keyboard()
        )
    except requests.exceptions.RequestException:
        bot.send_message(message.chat.id, 'حدث خطأ أثناء الاتصال بالخادم.', reply_markup=get_main_inline_keyboard())
    except json.JSONDecodeError:
        bot.send_message(message.chat.id, 'خطأ في تحليل الاستجابة من الخادم.', reply_markup=get_main_inline_keyboard())
    finally:
        if user_id in user_states:
            del user_states[user_id]

@bot.message_handler(func=lambda message: message.text == 'المساعده')
def handle_help_text_button(message):
    user_id = message.from_user.id
    subscribed, _ = check_user_subscription(user_id)
    if not subscribed:
        handle_start(message)
        return
    bot.send_message(message.chat.id, 'اضغط اولا على الزر البحث عن الاسم ثانيأ ارسل الرقم مع رمز الدوله ثالثأ ان لم يضهر لك ف انه لا يوجد بل داتا ', reply_markup=get_inline_back_to_main_keyboard())
    user_states[user_id] = 'help_menu'

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main_menu')
def callback_back_to_main_menu(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name if call.from_user.first_name else (call.from_user.username if call.from_user.username else str(user_id))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"اهلا عزيزي {user_name} في بوت معرفه اسمه الرقم -",
        reply_markup=get_main_inline_keyboard()
    )
    if user_id in user_states:
        del user_states[user_id]
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('search_name'))
def callback_search_name(call):
    user_id = call.from_user.id
    subscribed, _ = check_user_subscription(user_id)
    if not subscribed:
        bot.answer_callback_query(call.id, "عذرا، عليك الاشتراك في القناة أولا.")
        handle_start(call.message)
        return
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='الان ارسل الرقم مع رمز دوله مع + -', reply_markup=get_inline_back_to_main_keyboard())
    user_states[user_id] = 'awaiting_phone_number'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_help_menu'))
def callback_show_help(call):
    user_id = call.from_user.id
    subscribed, _ = check_user_subscription(user_id)
    if not subscribed:
        bot.answer_callback_query(call.id, "عذرا، عليك الاشتراك في القناة أولا.")
        handle_start(call.message)
        return
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='اضغط اولا على الزر البحث عن الاسم ثانيأ ارسل الرقم مع رمز الدوله ثالثأ ان لم يضهر لك ف انه لا يوجد بل دات', reply_markup=get_inline_back_to_main_keyboard())
    user_states[user_id] = 'help_menu'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub_again')
def callback_check_subscription(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name if call.from_user.first_name else (call.from_user.username if call.from_user.username else str(user_id))
    
    subscribed, _ = check_user_subscription(user_id)
    if subscribed:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="يمكنك استخدام البوت الان"
        )
        bot.send_message(
            call.message.chat.id,
            f"اهلا عزيزي {user_name} في بوت معرفه اسمه الرقم -",
            reply_markup=get_main_inline_keyboard()
        )
        if user_id in user_states:
            del user_states[user_id]
    else:
        bot.answer_callback_query(call.id, "لم يتم الاشتراك بعد، الرجاء الاشتراك والمحاولة مرة أخرى.")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_manage_channels' and call.from_user.id == OWNER_ID)
def callback_admin_manage_channels(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='إدارة قنوات الاشتراك الاجباري',
        reply_markup=get_admin_channel_management_keyboard()
    )
    user_states[call.from_user.id] = 'admin_channel_management'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_show_stats' and call.from_user.id == OWNER_ID)
def callback_admin_show_stats(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"عدد المستخدمين: {len(bot_users)}",
        reply_markup=get_admin_keyboard()
    )
    user_states[call.from_user.id] = 'admin_panel'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_user_menu' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_user_menu(call):
    user_name = call.from_user.first_name if call.from_user.first_name else (call.from_user.username if call.from_user.username else str(call.from_user.id))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"اهلا عزيزي {user_name} في بوت معرفه اسمه الرقم -",
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
        text='الان ارسل رابط القناة واذا خاصه ارسل توجيه منها -',
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
            text='لا توجد قنوات لإزالتها.',
            reply_markup=get_admin_channel_management_keyboard()
        )
        user_states[call.from_user.id] = 'admin_channel_management'
        bot.answer_callback_query(call.id)
        return

    markup = types.InlineKeyboardMarkup()
    for ch_id, ch_info in mandatory_channels.items():
        markup.add(types.InlineKeyboardButton(ch_info['title'], callback_data=f'delete_channel_{ch_id}'))
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='admin_back_to_admin_channel_management'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='اختر القناة المراد حذفها:',
        reply_markup=markup
    )
    user_states[call.from_user.id] = 'awaiting_channel_to_remove'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_channel_') and call.from_user.id == OWNER_ID)
def callback_delete_channel(call):
    channel_id_to_delete = int(call.data.replace('delete_channel_', ''))
    if channel_id_to_delete in mandatory_channels:
        del mandatory_channels[channel_id_to_delete]
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='تم حذف القناة بنجاح.',
            reply_markup=get_admin_channel_management_keyboard()
        )
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='القناة غير موجودة.',
            reply_markup=get_admin_channel_management_keyboard()
        )
    user_states[call.from_user.id] = 'admin_channel_management'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_panel' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_admin_panel(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='لوحه ادمن',
        reply_markup=get_admin_keyboard()
    )
    user_states[call.from_user.id] = 'admin_panel'
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_back_to_admin_channel_management' and call.from_user.id == OWNER_ID)
def callback_admin_back_to_admin_channel_management(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='إدارة قنوات الاشتراك الاجباري',
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
                invite_link = chat.invite_link
                if invite_link:
                    channel_link = invite_link
                else:
                    bot.send_message(user_id, 'لا يمكن الحصول على رابط دعوة لهذه القناة الخاصة. يجب إضافة البوت كمسؤول.', reply_markup=get_admin_channel_management_keyboard())
                    user_states[user_id] = 'admin_channel_management'
                    return
            except Exception:
                bot.send_message(user_id, 'حدث خطأ. تأكد من أن البوت مسؤول في القناة الخاصة.', reply_markup=get_admin_channel_management_keyboard())
                user_states[user_id] = 'admin_channel_management'
                return

    elif message.text and (message.text.startswith('https://t.me/') or message.text.startswith('@')):
        channel_link = message.text
        try:
            if message.text.startswith('@'):
                chat_username = message.text[1:]
                chat_info = bot.get_chat(chat_username)
                channel_id = chat_info.id
                channel_title = chat_info.title
            else:
                parts = message.text.split('/')
                if len(parts) >= 4:
                    chat_username_or_id = parts[3]
                    if chat_username_or_id.isdigit() or chat_username_or_id.startswith('-100'):
                        channel_id = int(chat_username_or_id)
                        chat_info = bot.get_chat(channel_id)
                        channel_title = chat_info.title
                    else:
                        chat_info = bot.get_chat(f'@{chat_username_or_id}')
                        channel_id = chat_info.id
                        channel_title = chat_info.title
                else:
                    bot.send_message(user_id, 'الرجاء إرسال رابط قناة صحيح أو معرف مستخدم.', reply_markup=get_admin_channel_management_keyboard())
                    user_states[user_id] = 'admin_channel_management'
                    return
        except Exception:
            bot.send_message(user_id, 'لم يتم العثور على القناة أو أن الرابط غير صحيح. تأكد من أن البوت مسؤول في القناة العامة أو أن الرابط صحيح.', reply_markup=get_admin_channel_management_keyboard())
            user_states[user_id] = 'admin_channel_management'
            return
    else:
        bot.send_message(user_id, 'الرجاء إرسال رابط قناة صحيح أو توجيه رسالة من القناة.', reply_markup=get_admin_channel_management_keyboard())
        user_states[user_id] = 'admin_channel_management'
        return

    if channel_id and channel_link and channel_title:
        try:
            bot_member = bot.get_chat_member(channel_id, bot.get_me().id)
            if bot_member.status not in ['administrator', 'creator']:
                bot.send_message(user_id, 'البوت ليس مسؤولاً في هذه القناة. يجب إضافة البوت كمسؤول.', reply_markup=get_admin_channel_management_keyboard())
                user_states[user_id] = 'admin_channel_management'
                return
        except Exception:
            bot.send_message(user_id, 'حدث خطأ عند التحقق من حالة البوت في القناة. تأكد من أن البوت مسؤول فيها.', reply_markup=get_admin_channel_management_keyboard())
            user_states[user_id] = 'admin_channel_management'
            return

        mandatory_channels[channel_id] = {'title': channel_title, 'link': channel_link}
        bot.send_message(user_id, f"تمت إضافة القناة '{channel_title}' بنجاح للاشتراك الاجباري.", reply_markup=get_admin_channel_management_keyboard())
    else:
        bot.send_message(user_id, 'حدث خطأ. لم يتم إضافة القناة.', reply_markup=get_admin_channel_management_keyboard())
    
    user_states[user_id] = 'admin_channel_management'

bot.polling(none_stop=True)
