import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv

# Load environment variables from ronit.env file
load_dotenv("ronit.env")

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_ADMIN_ID = os.getenv("BOT_ADMIN_ID")

# Check if BOT_ADMIN_ID is set and convert it to integer if it exists
if BOT_ADMIN_ID:
    BOT_ADMIN_ID = int(BOT_ADMIN_ID)  # Ensure it's an integer

# Check if TELEGRAM_BOT_TOKEN is set, handle it gracefully if it's missing
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("The TELEGRAM_BOT_TOKEN environment variable is missing!")

# Initialize the bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Dictionary to store GitHub tokens per user
user_github_tokens = {}

def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command."""
    update.message.reply_text(f"Hello {update.message.chat.first_name}! Use /help to see available commands.")

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle the /help command."""
    help_message = """
    Available Commands:
    /start - Start the bot
    /help - Display this help message
    /add <token> - Add your GitHub token to control your Codespaces
    /list_codespaces - List your active GitHub Codespaces with clickable buttons to copy IDs
    /start_codespace <id> - Start a GitHub Codespace by its ID
    /stop_codespace <id> - Stop a GitHub Codespace by its ID
    /send <message> - Send a message to all users (admin only)
    
    Bot created by @RONIT_IN.
    """
    update.message.reply_text(help_message)

def add_github_token(update: Update, context: CallbackContext) -> None:
    """Handle the /add command to add a GitHub token for a user."""
    user_id = update.message.from_user.id

    if context.args:
        github_token = context.args[0]
        user_github_tokens[user_id] = github_token
        update.message.reply_text(f"GitHub token added for user {update.message.chat.first_name}.")
    else:
        update.message.reply_text("Please provide a GitHub token. Usage: /add <token>")

def list_codespaces(update: Update, context: CallbackContext) -> None:
    """List the user's GitHub Codespaces with clickable buttons to copy IDs."""
    user_id = update.message.from_user.id
    github_token = user_github_tokens.get(user_id)

    if not github_token:
        update.message.reply_text("Please add your GitHub token first using /add <token>.")
        return

    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.get("https://api.github.com/user/codespaces", headers=headers)

    if response.status_code == 200:
        codespaces = response.json()
        if codespaces['codespaces']:
            keyboard = []
            for cs in codespaces['codespaces']:
                # Create a button for each Codespace with its ID
                keyboard.append([InlineKeyboardButton(f"Copy ID: {cs['id']}", callback_data=f"copy:{cs['id']}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Your Codespaces:", reply_markup=reply_markup)
        else:
            update.message.reply_text("You have no active Codespaces.")
    else:
        update.message.reply_text("Failed to fetch Codespaces. Please check your GitHub token.")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle the inline button clicks."""
    query = update.callback_query
    query.answer()

    # Get the callback data (e.g., 'copy:<codespace_id>')
    data = query.data
    if data.startswith("copy:"):
        codespace_id = data.split(":")[1]
        # Reply with the Codespace ID, user can copy it manually
        query.edit_message_text(text=f"Copied Codespace ID: `{codespace_id}`", parse_mode='Markdown')

def start_codespace(update: Update, context: CallbackContext) -> None:
    """Start a GitHub Codespace by its ID."""
    user_id = update.message.from_user.id
    github_token = user_github_tokens.get(user_id)

    if not github_token:
        update.message.reply_text("Please add your GitHub token first using /add <token>.")
        return

    if not context.args:
        update.message.reply_text("Please provide the Codespace ID. Usage: /start_codespace <id>")
        return

    codespace_id = context.args[0]
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.post(f"https://api.github.com/user/codespaces/{codespace_id}/start", headers=headers)

    if response.status_code == 202:
        update.message.reply_text(f"Codespace with ID {codespace_id} is starting.")
    else:
        update.message.reply_text("Failed to start the Codespace. Please check the ID and your token.")

def stop_codespace(update: Update, context: CallbackContext) -> None:
    """Stop a GitHub Codespace by its ID."""
    user_id = update.message.from_user.id
    github_token = user_github_tokens.get(user_id)

    if not github_token:
        update.message.reply_text("Please add your GitHub token first using /add <token>.")
        return

    if not context.args:
        update.message.reply_text("Please provide the Codespace ID. Usage: /stop_codespace <id>")
        return

    codespace_id = context.args[0]
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.post(f"https://api.github.com/user/codespaces/{codespace_id}/stop", headers=headers)

    if response.status_code == 202:
        update.message.reply_text(f"Codespace with ID {codespace_id} is stopping.")
    else:
        update.message.reply_text("Failed to stop the Codespace. Please check the ID and your token.")

def send_message(update: Update, context: CallbackContext) -> None:
    """Handle the /send command (only admin can use this)."""
    user_id = update.message.from_user.id

    if BOT_ADMIN_ID and user_id == BOT_ADMIN_ID:
        if context.args:
            message_to_send = " ".join(context.args)
            update.message.reply_text(f"Message sent to all users: {message_to_send}")
            # In a real-world scenario, you would broadcast the message to all bot users.
        else:
            update.message.reply_text("Please provide a message to send. Usage: /send <message>")
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
    dp.add_handler(CommandHandler("add", add_github_token))  # Add GitHub token
    dp.add_handler(CommandHandler("list_codespaces", list_codespaces))  # List GitHub Codespaces
    dp.add_handler(CommandHandler("start_codespace", start_codespace))  # Start a Codespace
    dp.add_handler(CommandHandler("stop_codespace", stop_codespace))  # Stop a Codespace
    dp.add_handler(CommandHandler("send", send_message))  # Admin send message

    # Register button callback handler
    dp.add_handler(CallbackQueryHandler(button_handler))

    # Start the Bot
    updater.start_polling()

    # Run the bot until Ctrl+C is pressed
    updater.idle()

if __name__ == '__main__':
    main()
