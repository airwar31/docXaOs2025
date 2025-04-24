#!/usr/bin/env python3

print("Testing Bot initialization from telegram_bot.py...")

try:
    from telegram_bot import bot
    print("✅ Successfully imported bot from telegram_bot")
    print(f"Bot info: {bot}")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise
except Exception as e:
    print(f"❌ Error: {e}")
    raise

print("Bot initialization successful!")