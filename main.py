import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler,
                          ConversationHandler)
import requests
from datetime import date

TOKEN = '7376461438:AAFbawDNREONCnoCxxdQ6Wmkbqg6ewQmrgI'
id_adm = 1918076606
email = 'fnnce_support@gmail.com'
tgk = "@fnnce_advcs"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

f_currency, s_currency, dep, feedback, adv, debts = range(6)

list_of_currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "KZT", "TRY", "CHF", "AUD", "AZN", "AMD", "THB", "BYN",
                       "BGN", "BRL", "KRW", "HKD", "UAH", "DKK", "AED", "VND", "EGP", "PLN", "INR", "RUB"]

cb_link = 'https://www.cbr-xml-daily.ru/daily_json.js'


def calculate_deposit(initial_sum, interest_rate, years, days=365):
    day = years * days
    return round((float(initial_sum) * interest_rate * day) / (days * 100), 2)


def an_debt(summ_of_debt, percent, duration):
    months = duration * 12
    monthly_percent = percent / 12 / 100
    numerator = summ_of_debt * monthly_percent * pow(1 + monthly_percent, months)
    denominator = pow(1 + monthly_percent, months) - 1
    monthly_payment = numerator / denominator
    total_payment = monthly_payment * months
    return round(monthly_payment, 2), round(total_payment, 2)


def diff_total_payment(summ_of_debt, percent, duration):
    months = duration * 12
    monthly_percent = percent / 12 / 100
    total_payment = 0
    balance = summ_of_debt
    for i in range(int(months)):
        payment_body = balance / months
        payment_interest = balance * monthly_percent
        total_payment += payment_body + payment_interest
        balance -= payment_body
    return round(total_payment, 2)


async def start_command(update, context):
    keyboard = [
        [InlineKeyboardButton("Рассчитать итоговую сумму вклада", callback_data="deposit")],
        [InlineKeyboardButton("Отправить отзыв", callback_data="feedback")],
        [InlineKeyboardButton("Курс валют", callback_data="exchange_rate")],
        [InlineKeyboardButton("Отправить совет по финансововй грамотности", callback_data="advice")],
        [InlineKeyboardButton("Расчеты по кредиту", callback_data="loan_calculation")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Доброго времени суток, я — бот-помощник по финансовой грамотности.\nЧто вы хотите сделать?",
        reply_markup=reply_markup
    )


async def help(update, context):
    await update.message.reply_text(
        "В функции расчета кредита и вклада надо вводить именно числа через одиночный пробел. \n В курсе валют "
        "необходимо ввести код валюты(RUB, USD). /n Список всех доступных в этом боте валют: USD, EUR, GBP, JPY, CNY, "
        "KZT, TRY, CHF, AUD, AZN, AMD, THB, BYN, BGN, BRL, KRW, HKD, UAH, DKK, AED, VND, EGP, PLN, INR, RUB")


async def button_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "deposit":
        await query.edit_message_text(
            "Напишите начальную сумму вклада, процентную ставку и срок (в годах) через пробел.\n\n",
            parse_mode="Markdown"
        )
        return dep

    elif query.data == "feedback":
        await query.edit_message_text("Спасибо за ваш отзыв! Напишите его подробно.")
        return feedback

    elif query.data == "exchange_rate":
        await query.edit_message_text("Укажите валюту, из которой будете конвертировать (например, USD):")
        return f_currency

    elif query.data == "advice":
        await query.edit_message_text("Спасибо за то, что решили отправить совет. "
                                      "Он будет опубликован в нашем Telegram-канале. Напишите ваш совет подробно.")
        return adv

    elif query.data == "loan_calculation":
        await query.edit_message_text(
            "Введите исходную сумму кредита, процентную ставку и срок (в годах).",
            parse_mode="Markdown"
        )
        return debts


async def first_currency(update, context):
    first_currency = update.message.text.upper()
    if first_currency not in list_of_currencies:
        await update.message.reply_text("Указанная валюта не поддерживается. Используйте доступные коды валют.")
        return f_currency
    context.user_data['first_currency'] = first_currency
    await update.message.reply_text("Укажите валюту, в которую хотите конвертировать (например, EUR):")
    return s_currency


async def second_currency(update, context):
    second_currency = update.message.text.upper()
    if second_currency not in list_of_currencies:
        await update.message.reply_text("Указанная валюта не поддерживается. Используйте доступные коды валют.")
        return s_currency
    context.user_data['second_currency'] = second_currency

    first_currency = context.user_data['first_currency']
    second_currency = context.user_data['second_currency']

    response = requests.get(cb_link)
    data = response.json()

    today = date.today().strftime("%d-%m-%Y")

    first_valute = next((v for k, v in data["Valute"].items() if v["CharCode"] == first_currency), None)
    second_valute = next((v for k, v in data["Valute"].items() if v["CharCode"] == second_currency), None)

    if first_currency == "RUB":
        if second_valute is None:
            await update.message.reply_text("Вторая валюта не найдена.")
            return ConversationHandler.END
        exchange_rate = 1 / second_valute['Value']
    else:
        if first_valute is None or second_valute is None:
            await update.message.reply_text("Данные по указанным валютам временно недоступны.")
            return ConversationHandler.END
        exchange_rate = first_valute['Value'] / second_valute['Value']

    answer = f"Сегодня ({today}) курс {first_currency} к {second_currency}: {exchange_rate:.2f}"
    await update.message.reply_text(answer)
    return ConversationHandler.END


async def cancel(update, context):
    keyboard = [
        [InlineKeyboardButton("Рассчитать итоговую сумму вклада", callback_data="deposit")],
        [InlineKeyboardButton("Отправить отзыв", callback_data="feedback")],
        [InlineKeyboardButton("Курс валют", callback_data="exchange_rate")],
        [InlineKeyboardButton("Cоветы по финансовой грамотности", callback_data="advice")],
        [InlineKeyboardButton("Расчеты по кредиту", callback_data="loan_calculation")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Доброго времени суток, я — бот-помощник по финансовой грамотности.\nЧто вы хотите сделать?",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


async def process_deposit_input(update, context):
    message_text = update.message.text.strip()
    user_input = message_text.split()

    if len(user_input) != 3:
        await update.message.reply_text(
            "Неправильный формат данных. Отправьте три числа через пробел: начальная сумма, процентная ставка и "
            "срок в годах.")
        return dep
    try:
        initial_sum = float(user_input[0])
        interest_rate = float(user_input[1])
        years = float(user_input[2])

        final_amount = calculate_deposit(initial_sum, interest_rate, years)
        await update.message.reply_text(f"Ваш вклад вырастет до {final_amount} рублей.")
    except ValueError:
        await update.message.reply_text("Ошибка: убедитесь, что ввели числа корректно.")
    return ConversationHandler.END


async def process_feedback(update, context):
    feedback = update.message.text.strip()
    chat_id = update.effective_chat.id

    feedback_text = f"Отзыв от пользователя {chat_id}:\n\n{feedback}"
    await context.bot.send_message(chat_id=id_adm, text=feedback_text)
    await update.message.reply_text(
        f"Ваш отзыв отправлен модераторам. Спасибо за участие!\n"
        f"Если возникли сбои в работе бота, то наша поддержка обитает по адресу *{email}*",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def process_loan_details(update, context):
    message_text = update.message.text.strip()
    user_input = message_text.split()

    if len(user_input) != 3:
        await update.message.reply_text(
            "Неправильный формат данных. Отправьте три числа через пробел: сумма кредита, процентная ставка и "
            "срок в годах.")
        return debts
    try:
        loan_sum = float(user_input[0])
        rate = float(user_input[1])
        years = float(user_input[2])

        annuity_monthly, annuity_total = an_debt(loan_sum, rate, years)
        diff_total = diff_total_payment(loan_sum, rate, years)

        await update.message.reply_text(
            f"Аннуитетный платеж:\n"
            f"  Ежемесячный платеж: {annuity_monthly} ₽\n"
            f"  Итоговая сумма: {annuity_total} ₽\n\n"
            f"Дифференцированный платеж:\n"
            f"  Итоговая сумма: {diff_total} ₽"
        )
    except ValueError:
        await update.message.reply_text("Ошибка: убедитесь, что ввели числа корректно.")
    return ConversationHandler.END


async def process_advice(update, context):
    advice = update.message.text.strip()

    formatted_post = (
        f"<b>✨ Советы по финансовой грамотности ✨</b>\n\n"
        f"{advice}\n\n"
    )

    await context.bot.send_message(chat_id=tgk, text=formatted_post, parse_mode="HTML")
    await update.message.reply_text("Ваш совет опубликован в Telegram-канале! Спасибо за вашу помощь.")
    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()

    currency_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^exchange_rate$")],
        states={
            f_currency: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_currency)],
            s_currency: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_currency)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    deposit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^deposit$")],
        states={
            dep: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    feedback_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^feedback$")],
        states={
            feedback: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_feedback)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    advice_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^advice$")],
        states={
            adv: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_advice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    loan_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^loan_calculation$")],
        states={
            debts: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_loan_details)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(currency_handler)
    application.add_handler(deposit_handler)
    application.add_handler(feedback_handler)
    application.add_handler(advice_handler)
    application.add_handler(loan_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", help))

    logger.info('Bot started')
    application.run_polling()


if __name__ == '__main__':
    main()