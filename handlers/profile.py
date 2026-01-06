from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, filters

GENDER, LOOKING, AGE, CITY = range(4)

def ask_gender(update, context):
    kb = [["M", "F"]]
    update.message.reply_text(
        "Select your gender:",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True)
    )
    return GENDER

def save_gender(update, context):
    context.user_data["gender"] = update.message.text
    kb = [["M", "F"]]
    update.message.reply_text(
        "Looking for:",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True)
    )
    return LOOKING

def save_looking(update, context):
    context.user_data["looking"] = update.message.text
    update.message.reply_text("Enter your age:")
    return AGE

def save_age(update, context):
    context.user_data["age"] = update.message.text
    update.message.reply_text("Which city in Cambodia?")
    return CITY

def save_city(update, context):
    context.user_data["city"] = update.message.text
    update.message.reply_text(
        "✅ Profile saved!\nType /mat to start matching"
    )
    return ConversationHandler.END
