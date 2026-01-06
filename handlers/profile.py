from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler

GENDER, LOOKING, AGE, CITY = range(4)

def ask_gender(update, context):
    kb = [["M", "F"]]
    update.message.reply_text(
        "Select your gender:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return GENDER

def save_gender(update, context):
    context.user_data["gender"] = update.message.text.strip()
    kb = [["M", "F"]]
    update.message.reply_text(
        "Looking for:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return LOOKING

def save_looking(update, context):
    context.user_data["looking"] = update.message.text.strip()
    update.message.reply_text("Enter your age (number):")
    return AGE

def save_age(update, context):
    context.user_data["age"] = update.message.text.strip()
    update.message.reply_text("Which city in Cambodia? (PP/SR/BT/SHV/O):")
    return CITY

def save_city(update, context):
    context.user_data["city"] = update.message.text.strip()
    update.message.reply_text("✅ Profile saved!\nNow type /mat (coming next).")
    return ConversationHandler.END
