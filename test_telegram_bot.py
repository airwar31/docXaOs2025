import unittest
import asyncio
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class TestTelegramBot(unittest.TestCase):
    
    @patch('telegram_bot.bot')
    @patch('telegram_bot.dp')
    def test_start_bot(self, mock_dp, mock_bot):
        from telegram_bot import start_bot
        
        async def mock_start_polling(*args, **kwargs):
            return True
        
        mock_dp.start_polling = MagicMock(side_effect=mock_start_polling)
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(start_bot())
        
        mock_dp.start_polling.assert_called_once_with(mock_bot, skip_updates=True)
        self.assertTrue(result)
    
    @patch('telegram_bot.bot')
    def test_stop_bot(self, mock_bot):
        from telegram_bot import stop_bot
        
        async def mock_close(*args, **kwargs):
            return True
        mock_bot.session.close = MagicMock(side_effect=mock_close)
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(stop_bot())
        
        mock_bot.session.close.assert_called_once()
        self.assertTrue(result)
    
    @patch('telegram_bot.bot')
    async def test_send_notification(self, mock_bot):
        from telegram_bot import send_notification
        
        async def mock_send_message(*args, **kwargs):
            return True
        
        mock_bot.send_message = MagicMock(side_effect=mock_send_message)
        
        chat_id = "123456"
        message = "Test message"
        result = await send_notification(chat_id, message)
        
        mock_bot.send_message.assert_called_once_with(chat_id, message)
        self.assertTrue(result)
        
        mock_bot.send_message = MagicMock(side_effect=Exception("Test error"))
        result = await send_notification(chat_id, message)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
