#!/usr/bin/env python3

print("Testing imports from telegram_bot.py...")

try:
    from telegram_bot import notify_match, notify_no_match
    print("✅ Successfully imported notify_match and notify_no_match from telegram_bot")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise

print("All imports successful!")