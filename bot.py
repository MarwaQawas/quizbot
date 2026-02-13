    # from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

def parse_question_block(block: str):
    """
    Parses one question block and returns:
    (question, options, correct_index, explanation)
    Rules:
    - First line = question
    - Following lines = options
    - Option ending with '*' = correct answer
    - Line starting with '#' = explanation
    """
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        raise ValueError("السؤال فارغ")

    # --- Explanation ---
    explanation = None
    for i, line in enumerate(lines):
        if line.startswith("#"):
            explanation = line[1:].strip()
            lines.pop(i)
            break

    if len(lines) < 2:
        raise ValueError("عدد الخيارات غير كافٍ")

    # --- Question ---
    question = lines[0]

    # --- Options ---
    options = []
    correct_index = None

    for idx, opt in enumerate(lines[1:]):
        if opt.endswith("*"):
            opt = opt[:-1].strip()
            correct_index = idx
        options.append(opt)

    if correct_index is None:
        raise ValueError("لم يتم تحديد الجواب الصحيح (*)")

    return question, options, correct_index, explanation


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # --- Split into question blocks by empty line ---
    blocks = text.split("\n\n")

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
