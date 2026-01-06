from telegram import ReplyKeyboardMarkup

def lang_keyboard():
    return ReplyKeyboardMarkup([["K", "E"]], resize_keyboard=True)

def yes_no():
    return ReplyKeyboardMarkup([["Y", "N"]], resize_keyboard=True)
