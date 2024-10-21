import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables (replace these with actual values or keep them in a .env file)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_ADMIN_ID = int(os.getenv("BOT_ADMIN_ID"))  # The ID of the bot's admin (your Telegram user ID)

# Initialize the bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Store a single GitHub token (can be updated by public command)
github_token = None

def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command."""
    update.message.reply_text(f"Hello {update.message.chat.first_name}! Use /help to see available commands.")

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle the /help command."""
    help_message = """
    Available Commands:
    /start - Start the bot
    /help - Display this help message
    /add <token> - Add a new GitHub token
    /send <message> - Send a message to all users (admin only)
    
    Bot created by @RONIT_IN.
    """
    update.message.reply_text(help_message)

def add_github_token(update: Update, context: CallbackContext) -> None:
    """Handle the /add command to add a GitHub token."""
    global github_token
    
    if context.args:
        github_token = context.args[0]
        update.message.reply_text(f"GitHub token added: {github_token}")
    else:
        update.message.reply_text("Please provide a GitHub token. Usage: /add <token>")

def send_message(update: Update, context: CallbackContext) -> None:
    """Handle the /send_message command (only admin can use this)."""
    user_id = update.message.from_user.id
    
    if user_id == BOT_ADMIN_ID:
        if context.args:
            message_to_send = " ".join(context.args)
            update.message.reply_text(f"Message sent to all users: {message_to_send}")
            # In a real-world scenario, you would broadcast the message to all bot users.
        else:
            update.message.reply_text("Please provide a message to send. Usage: /send_message <message>")
    else:
        update.message.reply_text("You are not authorized to use this command.")

def main():
    """Start the bot."""
    # Create the Updater and pass it the bot token
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("add", add_github_token))  # Updated command to /add
    dp.add_handler(CommandHandler("send", send_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until Ctrl+C is pressed
    updater.idle()

if __name__ == '__main__':
    main()
