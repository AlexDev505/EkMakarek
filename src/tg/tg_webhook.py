from flask import request, abort
from telebot.types import Update

from app import app
from .bot import bot, config, setup_webhook


@app.route(f"/{config.tg_bot.webhook.secret_key}", methods=["POST"])
def telegram_webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = Update.de_json(json_string)
        print(update)
        bot.process_new_updates([update])
        return ""
    else:
        abort(403)
