import logging
import asyncio
import re
import requests
import sys
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# === CONFIGURATION ===
BOT_TOKEN = '7571127846:AAENqigIYHONuMlDCw4W0d_q10wcG76O7LA'
ADMIN_ID = 7442841802

# Conversation States
ADD_USER, ADD_PASS, ADD_CHAT = range(3)
EDIT_L1_NAME, EDIT_L1_URL, EDIT_L2_NAME, EDIT_L2_URL = range(4, 8)

# Global Storage
ACCOUNTS = {} 
ALREADY_SENT = set()

# Dynamic Links (Can be edited from Admin Panel)
DYNAMIC_LINKS = {
    "link1_name": "📢 Main Channel",
    "link1_url": "https://t.me/example",
    "link2_name": "👥 Number Group",
    "link2_url": "https://t.me/example"
}

# === PANEL CONFIGURATION ===
PANEL_ORDER = [
    "SquadSms", "Proton=Ro=1", "SmsHadi", "Proton=Ra=2", "Proton=Ru=3",
    "LamixSms", "Mait=Ro=1", "Mait=A=2", "Mait=S=3", "Proton",
    "MSI", "NMPSMS", "D-Groupe", "SharkSms", "SNIPER", "KMSMS", "WolfSms"
]

PANEL_CONFIG = {
    "SquadSms": "http://51.77.221.209",
    "Proton=Ro=1": "http://109.236.84.81",
    "SmsHadi": "http://185.2.83.39",
    "Proton=Ra=2": "http://109.236.84.81",
    "Proton=Ru=3": "http://109.236.84.81",
    "LamixSms": "http://139.99.208.63",
    "Mait=Ro=1": "http://217.182.195.194",
    "Mait=A=2": "http://217.182.195.194",
    "Mait=S=3": "http://217.182.195.194",
    "Proton": "http://109.236.84.81",
    "MSI": "http://185.2.83.39",
    "NMPSMS": "http://185.2.83.39",
    "D-Groupe": "http://185.2.83.39",
    "SharkSms": "http://185.2.83.39",
    "SNIPER": "http://185.2.83.39",
    "KMSMS": "http://185.2.83.39",
    "WolfSms": "http://213.32.24.208"
}

# === FULL WORLD COUNTRY MAP (ALL COUNTRIES ADDED) ===
COUNTRY_MAP = {
    '1': '🇺🇸 USA/Canada', '7': '🇷🇺 Russia/Kazakhstan', '20': '🇪🇬 Egypt', '27': '🇿🇦 South Africa',
    '30': '🇬🇷 Greece', '31': '🇳🇱 Netherlands', '32': '🇧🇪 Belgium', '33': '🇫🇷 France', '34': '🇪🇸 Spain',
    '36': '🇭🇺 Hungary', '39': '🇮🇹 Italy', '40': '🇷🇴 Romania', '41': '🇨🇭 Switzerland', '43': '🇦🇹 Austria',
    '44': '🇬🇧 UK', '45': '🇩🇰 Denmark', '46': '🇸🇪 Sweden', '47': '🇳🇴 Norway', '48': '🇵🇱 Poland',
    '49': '🇩🇪 Germany', '51': '🇵🇪 Peru', '52': '🇲🇽 Mexico', '53': '🇨🇺 Cuba', '54': '🇦🇷 Argentina',
    '55': '🇧🇷 Brazil', '56': '🇨🇱 Chile', '57': '🇨🇴 Colombia', '58': '🇻🇪 Venezuela', '60': '🇲🇾 Malaysia',
    '61': '🇦🇺 Australia', '62': '🇮🇩 Indonesia', '63': '🇵🇭 Philippines', '64': '🇳🇿 New Zealand',
    '65': '🇸🇬 Singapore', '66': '🇹🇭 Thailand', '81': '🇯🇵 Japan', '82': '🇰🇷 South Korea', '84': '🇻🇳 Vietnam',
    '86': '🇨🇳 China', '90': '🇹🇷 Turkey', '91': '🇮🇳 India', '92': '🇵🇰 Pakistan', '93': '🇦🇫 Afghanistan',
    '94': '🇱🇰 Sri Lanka', '95': '🇲🇲 Myanmar', '98': '🇮🇷 Iran', '211': '🇸🇸 South Sudan', '212': '🇲🇦 Morocco', 
    '213': '🇩🇿 Algeria', '216': '🇹🇳 Tunisia', '218': '🇱🇾 Libya', '220': '🇬🇲 Gambia', '221': '🇸🇳 Senegal', 
    '222': '🇲🇷 Mauritania', '223': '🇲🇱 Mali', '224': '🇬🇳 Guinea', '225': '🇨🇮 Ivory Coast', '226': '🇧🇫 Burkina Faso', 
    '227': '🇳🇪 Niger', '228': '🇹🇬 Togo', '229': '🇧🇯 Benin', '230': '🇲🇺 Mauritius', '231': '🇱🇷 Liberia', 
    '232': '🇸🇱 Sierra Leone', '233': '🇬🇭 Ghana', '234': '🇳🇬 Nigeria', '235': '🇹🇩 Chad', '236': '🇨🇫 Central African Rep.', 
    '237': '🇨🇲 Cameroon', '238': '🇨🇻 Cape Verde', '239': '🇸🇹 Sao Tome and Principe', '240': '🇬🇶 Equatorial Guinea', 
    '241': '🇬🇦 Gabon', '242': '🇨🇬 Congo', '243': '🇨🇩 DR Congo', '244': '🇦🇴 Angola', '245': '🇬🇼 Guinea-Bissau', 
    '246': '🇮🇴 British Indian Ocean Territory', '248': '🇸🇨 Seychelles', '249': '🇸🇩 Sudan', '250': '🇷🇼 Rwanda', 
    '251': '🇪🇹 Ethiopia', '252': '🇸🇴 Somalia', '253': '🇩🇯 Djibouti', '254': '🇰🇪 Kenya', '255': '🇹🇿 Tanzania', 
    '256': '🇺🇬 Uganda', '257': '🇧🇮 Burundi', '258': '🇲🇿 Mozambique', '260': '🇿🇲 Zambia', '261': '🇲🇬 Madagascar', 
    '262': '🇷🇪 Reunion', '263': '🇿🇼 Zimbabwe', '264': '🇳🇦 Namibia', '265': '🇲🇼 Malawi', '266': '🇱🇸 Lesotho', 
    '267': '🇧🇼 Botswana', '268': '🇸🇿 Swaziland', '269': '🇰🇲 Comoros', '290': '🇸🇭 Saint Helena', '291': '🇪🇷 Eritrea', 
    '297': '🇦🇼 Aruba', '298': '🇫🇴 Faroe Islands', '299': '🇬🇱 Greenland', '350': '🇬🇮 Gibraltar', '351': '🇵🇹 Portugal', 
    '352': '🇱🇺 Luxembourg', '353': '🇮🇪 Ireland', '354': '🇮🇸 Iceland', '355': '🇦🇱 Albania', '356': '🇲🇹 Malta', 
    '357': '🇨🇾 Cyprus', '358': '🇫🇮 Finland', '359': '🇧🇬 Bulgaria', '370': '🇱🇹 Lithuania', '371': '🇱🇻 Latvia', 
    '372': '🇪🇪 Estonia', '373': '🇲🇩 Moldova', '374': '🇦🇲 Armenia', '375': '🇧🇾 Belarus', '376': '🇦🇩 Andorra', 
    '377': '🇲🇨 Monaco', '378': '🇸🇲 San Marino', '380': '🇺🇦 Ukraine', '381': '🇷🇸 Serbia', '382': '🇲🇪 Montenegro', 
    '383': '🇽🇰 Kosovo', '385': '🇭🇷 Croatia', '386': '🇸🇮 Slovenia', '387': '🇧🇦 Bosnia', '389': '🇲🇰 Macedonia', 
    '420': '🇨🇿 Czech Republic', '421': '🇸🇰 Slovakia', '423': '🇱🇮 Liechtenstein', '500': '🇫🇰 Falkland Islands', 
    '501': '🇧🇿 Belize', '502': '🇬🇹 Guatemala', '503': '🇸🇻 El Salvador', '504': '🇭🇳 Honduras', '505': '🇳🇮 Nicaragua', 
    '506': '🇨🇷 Costa Rica', '507': '🇵🇦 Panama', '508': '🇵🇲 Saint Pierre and Miquelon', '509': '🇭🇹 Haiti', 
    '590': '🇬🇵 Guadeloupe', '591': '🇧🇴 Bolivia', '592': '🇬🇾 Guyana', '593': '🇪🇨 Ecuador', '594': '🇬🇫 French Guiana', 
    '595': '🇵🇾 Paraguay', '596': '🇲🇶 Martinique', '597': '🇸🇷 Suriname', '598': '🇺🇾 Uruguay', '599': '🇨🇼 Curacao', 
    '670': '🇹🇱 Timor-Leste', '672': '🇦🇶 Antarctica', '673': '🇧🇳 Brunei', '674': '🇳🇷 Nauru', '675': '🇵🇬 Papua New Guinea', 
    '676': '🇹🇴 Tonga', '677': '🇸🇧 Solomon Islands', '678': '🇻🇺 Vanuatu', '679': '🇫🇯 Fiji', '680': '🇵🇼 Palau', 
    '681': '🇼🇫 Wallis and Futuna', '682': '🇨🇰 Cook Islands', '683': '🇳🇺 Niue', '685': '🇼🇸 Samoa', '686': '🇰🇮 Kiribati', 
    '687': '🇳🇨 New Caledonia', '688': '🇹🇻 Tuvalu', '689': '🇵🇫 French Polynesia', '690': '🇹🇰 Tokelau', 
    '691': '🇫🇲 Micronesia', '692': '🇲🇭 Marshall Islands', '850': '🇰🇵 North Korea', '852': '🇭🇰 Hong Kong', 
    '853': '🇲🇴 Macau', '855': '🇰🇭 Cambodia', '856': '🇱🇦 Laos', '880': '🇧🇩 Bangladesh', '886': '🇹🇼 Taiwan', 
    '960': '🇲🇻 Maldives', '961': '🇱🇧 Lebanon', '962': '🇯🇴 Jordan', '963': '🇸🇾 Syria', '964': '🇮🇶 Iraq', 
    '965': '🇰🇼 Kuwait', '966': '🇸🇦 Saudi Arabia', '967': '🇾🇪 Yemen', '968': '🇴🇲 Oman', '970': '🇵🇸 Palestine', 
    '971': '🇦🇪 UAE', '972': '🇮🇱 Israel', '973': '🇧🇭 Bahrain', '974': '🇶🇦 Qatar', '975': '🇧🇹 Bhutan', 
    '976': '🇲🇳 Mongolia', '977': '🇳🇵 Nepal', '992': '🇹🇯 Tajikistan', '993': '🇹🇲 Turkmenistan', 
    '994': '🇦🇿 Azerbaijan', '995': '🇬🇪 Georgia', '996': '🇰🇬 Kyrgyzstan', '998': '🇺🇿 Uzbekistan'
}

# === UTILITIES ===
def get_country(num):
    for code in sorted(COUNTRY_MAP.keys(), key=lambda x: -len(x)):
        if num.startswith(code): return COUNTRY_MAP[code]
    return '🌍 Unknown'

def hide_number_format(num):
    """Hide number with ⓇⓞⒷ in the middle"""
    if len(num) < 10: return num
    return f"{num[:-6]}ⓇⓞⒷ{num[-3:]}"

async def delete_messages(context, chat_id, message_ids):
    for mid in message_ids:
        try: await context.bot.delete_message(chat_id, mid)
        except: pass

async def login_logic(url, u, p):
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        url = url.rstrip('/')
        r = sess.get(f"{url}/ints/login", timeout=10)
        match = re.search(r'What is (\d+) \+ (\d+)', r.text)
        if not match: return None
        ans = int(match.group(1)) + int(match.group(2))
        payload = {"username": u, "password": p, "capt": ans}
        res = sess.post(f"{url}/ints/signin", data=payload, headers={"Referer": f"{url}/ints/login"})
        if "dashboard" in res.text.lower() or "logout" in res.text.lower():
            return sess
    except: pass
    return None

# === FORWARDER LOOP ===
async def main_forwarder_loop(bot_app):
    while True:
        for p_name, data in list(ACCOUNTS.items()):
            if data.get("active", True):
                try:
                    p_index = PANEL_ORDER.index(p_name) + 1
                    today = datetime.now().strftime("%Y-%m-%d")
                    target_url = f"{data['url']}/ints/agent/res/data_smscdr.php?fdate1={today}%2000:00:00&fdate2={today}%2023:59:59&sesskey=Q05RRkJOUEdCTg==&iDisplayLength=25"
                    resp = data['session'].get(target_url, headers={"X-Requested-With": "XMLHttpRequest"})
                    
                    if resp.status_code == 200:
                        rows = resp.json().get('aaData', [])
                        for row in rows:
                            date, ph, srv, msg = row[0], row[2], row[3], row[5]
                            otp_match = re.search(r'\d{3}-\d{3}|\d{4,6}', msg)
                            otp = otp_match.group() if otp_match else None
                            
                            if otp:
                                key = f"{ph}|{otp}"
                                if key not in ALREADY_SENT:
                                    ALREADY_SENT.add(key)
                                    text = (
                                        f"✨ <b>OTP Received</b> ✨\n\n"
                                        f"⏰ <b>Time:</b> {date}\n"
                                        f"📞 <b>Number:</b> <code>{hide_number_format(ph)}</code>\n"
                                        f"🌍 <b>Country:</b> {get_country(ph)}\n"
                                        f"🔧 <b>Service:</b> {srv}\n"
                                        f"🔐 <b>OTP Code:</b> <code>{otp}</code>\n\n"
                                        f"📂 <b>Panel {p_index}</b>\n\n"
                                        f"<b>POWERED BY MD ROBIUL ISLAM</b>"
                                    )
                                    kb = InlineKeyboardMarkup([
                                        [InlineKeyboardButton(DYNAMIC_LINKS["link1_name"], url=DYNAMIC_LINKS["link1_url"])],
                                        [InlineKeyboardButton(DYNAMIC_LINKS["link2_name"], url=DYNAMIC_LINKS["link2_url"])]
                                    ])
                                    await bot_app.bot.send_message(chat_id=data['chat_id'], text=text, parse_mode="HTML", reply_markup=kb)
                except: pass
        await asyncio.sleep(5)

# === ADMIN PANEL UI ===
async def show_main_panel(update_obj, context):
    rows = []
    for i in range(0, len(PANEL_ORDER), 2):
        pair = PANEL_ORDER[i:i+2]
        btn_row = [InlineKeyboardButton(f"{PANEL_ORDER.index(name)+1}. {name} {'🟢' if name in ACCOUNTS else '🔴'}", callback_data=f"p_{name}") for name in pair]
        rows.append(btn_row)
    
    rows.append([InlineKeyboardButton("⚙️ Edit Button Names & Links", callback_data="sys_edit_links")])
    rows.append([InlineKeyboardButton("🔄 Restart System", callback_data="sys_restart")])
    
    msg_text = "📁 <b>Admin Control Panel</b>\nManage your panels and system settings:"
    if isinstance(update_obj, Update) and update_obj.message:
        await update_obj.message.reply_text(msg_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
    else:
        await update_obj.edit_text(msg_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await show_main_panel(update, context)

async def handle_panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    panel = query.data.split("_")[1]
    context.user_data['selected_panel'] = panel
    context.user_data['msg_to_del'] = [query.message.message_id]
    
    if panel in ACCOUNTS:
        kb = [[InlineKeyboardButton("▶️ Start", callback_data=f"ctl_start_{panel}"), InlineKeyboardButton("⏸ Stop", callback_data=f"ctl_stop_{panel}")],
              [InlineKeyboardButton("🗑 Logout", callback_data=f"ctl_logout_{panel}")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        await query.edit_message_text(f"⚙️ <b>Panel: {panel}</b>\nStatus: Connected", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
    else:
        m = await query.edit_message_text(f"📝 <b>Setup {panel}</b>\nEnter <b>Username</b>:")
        context.user_data['msg_to_del'].append(m.message_id)
        return ADD_USER

async def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u'] = update.message.text
    context.user_data['msg_to_del'].append(update.message.message_id)
    m = await update.message.reply_text("🔑 Enter <b>Password</b>:")
    context.user_data['msg_to_del'].append(m.message_id)
    return ADD_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p'] = update.message.text
    context.user_data['msg_to_del'].append(update.message.message_id)
    m = await update.message.reply_text("🆔 Enter <b>Target Chat ID</b>:")
    context.user_data['msg_to_del'].append(m.message_id)
    return ADD_CHAT

async def finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['msg_to_del'].append(update.message.message_id)
    cid = update.message.text
    u, p = context.user_data['u'], context.user_data['p']
    panel = context.user_data['selected_panel']
    url = PANEL_CONFIG[panel]
    
    msg_wait = await update.message.reply_text("⏳ Authenticating...")
    sess = await login_logic(url, u, p)
    
    await delete_messages(context, update.effective_chat.id, context.user_data['msg_to_del'])
    
    if sess:
        ACCOUNTS[panel] = {"session": sess, "username": u, "chat_id": cid, "url": url, "active": True}
        await msg_wait.edit_text(f"✅ {panel} Setup Complete!")
    else:
        await msg_wait.edit_text("❌ Login Failed.")
    
    await show_main_panel(update, context)
    return ConversationHandler.END

# === BUTTON & LINK EDITOR ===
async def link_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "sys_edit_links":
        kb = [[InlineKeyboardButton("Main Channel Name", callback_data="ed_l1n"), InlineKeyboardButton("Edit URL", callback_data="ed_l1u")],
              [InlineKeyboardButton("Number Group Name", callback_data="ed_l2n"), InlineKeyboardButton("Edit URL", callback_data="ed_l2u")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        await query.edit_message_text("🔗 <b>Dynamic Button Settings</b>\nChange display names or URLs:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
    elif data == "ed_l1n": await query.edit_message_text("Send new Name for Main Channel Button:"); return EDIT_L1_NAME
    elif data == "ed_l1u": await query.edit_message_text("Send new URL for Main Channel:"); return EDIT_L1_URL
    elif data == "ed_l2n": await query.edit_message_text("Send new Name for Number Group Button:"); return EDIT_L2_NAME
    elif data == "ed_l2u": await query.edit_message_text("Send new URL for Number Group:"); return EDIT_L2_URL

async def save_link_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    step = context.user_data.get('link_step')
    if step == EDIT_L1_NAME: DYNAMIC_LINKS["link1_name"] = val
    elif step == EDIT_L1_URL: DYNAMIC_LINKS["link1_url"] = val
    elif step == EDIT_L2_NAME: DYNAMIC_LINKS["link2_name"] = val
    elif step == EDIT_L2_URL: DYNAMIC_LINKS["link2_url"] = val
    await update.message.reply_text("✅ Successfully Saved!")
    await show_main_panel(update, context)
    return ConversationHandler.END

async def system_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data.startswith("ctl_"):
        _, action, p = data.split("_")
        if action == "start": ACCOUNTS[p]["active"] = True
        elif action == "stop": ACCOUNTS[p]["active"] = False
        elif action == "logout": ACCOUNTS.pop(p, None)
        await show_main_panel(query.message, context)
    elif data == "back_to_main": await show_main_panel(query.message, context)
    elif data == "sys_restart": os.execl(sys.executable, sys.executable, *sys.argv)

# === MAIN RUNNER ===
async def post_init(app):
    asyncio.create_task(main_forwarder_loop(app))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    panel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_panel_click, pattern="^p_")],
        states={
            ADD_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user)],
            ADD_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            ADD_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_setup)],
        }, fallbacks=[]
    )

    link_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(link_callback_handler, pattern="^(sys_edit|ed_l)")],
        states={
            EDIT_L1_NAME: [MessageHandler(filters.TEXT, lambda u,c: (c.user_data.update({'link_step':EDIT_L1_NAME}), save_link_data(u,c))[1])],
            EDIT_L1_URL: [MessageHandler(filters.TEXT, lambda u,c: (c.user_data.update({'link_step':EDIT_L1_URL}), save_link_data(u,c))[1])],
            EDIT_L2_NAME: [MessageHandler(filters.TEXT, lambda u,c: (c.user_data.update({'link_step':EDIT_L2_NAME}), save_link_data(u,c))[1])],
            EDIT_L2_URL: [MessageHandler(filters.TEXT, lambda u,c: (c.user_data.update({'link_step':EDIT_L2_URL}), save_link_data(u,c))[1])],
        }, fallbacks=[]
    )

    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(system_callbacks, pattern="^(ctl|sys_restart|back)"))
    app.add_handler(panel_conv)
    app.add_handler(link_conv)
    app.run_polling()

if __name__ == "__main__":
    main()