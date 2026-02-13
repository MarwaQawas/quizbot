import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

QUESTION_REGEX = re.compile(r"^\s*\d+\.\s*(.+)", re.MULTILINE)
OPTION_REGEX = re.compile(r"^[A-Z]\.\s*(.+)", re.MULTILINE)

def parse_question_block(block: str):
    """
    Parses one question block and returns:
    (question, options, correct_index, explanation)
    """

    # --- Explanation ---
    if "#" in block:
        main_text, explanation = block.split("#", 1)
        explanation = explanation.strip()
    else:
        main_text = block
        explanation = None

    # --- Question ---
    q_match = QUESTION_REGEX.search(main_text)
    if not q_match:
        raise ValueError("لم أستطع التعرف على السؤال")

    question = q_match.group(1).strip()

    # --- Options ---
    options = []
    correct_index = None

    for line in main_text.splitlines():
        line = line.strip()
        opt_match = re.match(r"^[A-Z]\.\s*(.+)", line)
        if opt_match:
            option_text = opt_match.group(1)

            if option_text.endswith("*"):
                option_text = option_text[:-1].strip()
                correct_index = len(options)

            options.append(option_text)

    if correct_index is None:
        raise ValueError("لم يتم تحديد الجواب الصحيح (*)")

    if len(options) < 2:
        raise ValueError("عدد الخيارات غير كافٍ")

    return question, options, correct_index, explanation


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # --- Split into question blocks by empty line ---
    blocks = re.split(r"\n\s*\n", text)

    sent_any = False

    for block in blocks:
        if not block.strip():
            continue

        try:
            question, options, correct_index, explanation = parse_question_block(block)

            await context.bot.send_poll(
                chat_id=update.effective_chat.id,
                question=question,
                options=options,
                type="quiz",
                correct_option_id=correct_index,
                explanation=explanation,
                is_anonymous=False,
            )

            sent_any = True

        except ValueError as e:
            await update.message.reply_text(f"❌ خطأ في سؤال:\n{e}")

    if not sent_any:
        await update.message.reply_text("❌ لم يتم العثور على أي أسئلة صالحة")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
