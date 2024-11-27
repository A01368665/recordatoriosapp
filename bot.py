import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, JobQueue

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token here
BOT_TOKEN = os.getenv("TOKEN")

# Dictionary to store user responses
user_responses = {}
tracking_users = {}


# Start tracking messages every 20 minutes
async def start_tracking(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_chat.id
    tracking_users[user_id] = True
    user_responses[user_id] = []

    await update.message.reply_text(
        "Tracking started! I'll ask you every 20 minutes to share your progress. Type /stop to end tracking."
    )

    # Schedule the reminder job
    job_queue = context.application.job_queue
    job_name = f"reminder_{user_id}"  # Unique name for the job
    job_queue.run_repeating(
        send_reminder, interval=10, first=0, data=user_id, name=job_name
    )


# Function to send reminders
async def send_reminder(context: CallbackContext) -> None:
    user_id = context.job.data
    await context.bot.send_message(chat_id=user_id, text="Reminder: How are you doing?")


# Stop tracking and send a summary of responses
async def stop_tracking(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_chat.id

    # Ensure tracking was active for the user
    if user_id in tracking_users and tracking_users[user_id]:
        # Fetch and send summary
        responses = "\n".join(user_responses.get(user_id, []))
        await update.message.reply_text(f"Here is your summary:\n{responses}")

        # Clear user data and stop tracking
        tracking_users[user_id] = False
        user_responses[user_id] = []

        # Stop the associated job
        job_name = f"reminder_{user_id}"
        current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()

        await update.message.reply_text("Tracking stopped. Goodbye!")
    else:
        await update.message.reply_text("You are not currently being tracked.")


# Save user responses when they reply
async def save_response(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_chat.id

    # Check if tracking is active
    if user_id in tracking_users and tracking_users[user_id]:
        response = update.message.text
        user_responses[user_id].append(response)
        await update.message.reply_text("Response saved! I'll remind you again soon.")
    else:
        await update.message.reply_text(
            "You are not being tracked. Start tracking with /start."
        )


# Main function to configure the bot
def main() -> None:
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_tracking))
    application.add_handler(CommandHandler("stop", stop_tracking))

    # Add message handler to capture responses
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, save_response)
    )

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
