import os
import asyncio
import logging
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from dotenv import load_dotenv
from src.utils.logger import app_logger

load_dotenv()

class TelegramBot:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.bot = Bot(token=self.token) if self.token else None
        
    async def verify_connection(self):
        """Standard connectivity check (Used during startup/diagnostics)."""
        if not self.bot:
            return False
        try:
            await self.bot.get_me()
            return True
        except Exception as e:
            app_logger.error(f"🌐 [TELEGRAM LINK] Probe failed: {e}")
            return False

    async def send_signal(self, symbol, entry, sl, tp, confidence, side='BUY', timeframe='1h'):
        """Sends a formatted signal message to Telegram with high priority."""
        if not self.bot or not self.chat_id:
            return False
            
        emoji = "🚀" if side == 'BUY' else "📉"
        conf_pct = int(confidence * 100)
        
        message = (
            f"🚀 *NEW TRADING SIGNAL / إشارة تداول جديدة* 🚀\n\n"
            f"🔹 *Symbol / العملة:* `{symbol}`\n"
            f"🔹 *Side / العملية:* `{side}`\n"
            f"🔹 *Entry / الدخول:* `${entry:.6f}`\n"
            f"🔹 *Stop Loss / إيقاف خسارة:* `${sl:.6f}`\n"
            f"🔹 *Take Profit / جني أرباح:* `${tp:.6f}`\n\n"
            f"🤖 *AI Confidence / ثقة الذكاء الاصطناعي:* `{conf_pct}%`\n"
            f"⏰ *Timeframe / الإطار الزمني:* `{timeframe}`\n"
            f"✅ *Status / الحالة:* Active / نشط"
        )
        
        try:
            keyboard = [
                [InlineKeyboardButton("🚀 EXECUTE TRADE NOW", callback_data=f"exec_{symbol}_{side}")],
                [InlineKeyboardButton("📊 View Neural Report", url="https://prosoft-trading.com/dashboard")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=message, 
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            app_logger.info(f"Telegram Signal sent for {symbol} | {side}")
            return True
        except Exception as e:
            app_logger.error(f"Error sending Telegram signal: {e}")
            # Fallback to simple text if Markdown/Keyboard fails
            try:
                simple_msg = f"SIGNAL: {side} {symbol} @ {entry} | SL: {sl} | TP: {tp}"
                await self.bot.send_message(chat_id=self.chat_id, text=simple_msg)
                return True
            except:
                return False

    async def send_message(self, text, parse_mode=ParseMode.MARKDOWN):
        """Standard text message delivery with automatic Markdown fallback."""
        if not self.bot or not self.chat_id:
            return False
            
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=text, 
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            if parse_mode:
                # Retry without formatting if Markdown fails
                try:
                    await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode=None)
                    return True
                except: pass
            app_logger.error(f"Telegram Delivery Failed: {e}")
            return False

    async def send_notification(self, text):
        return await self.send_message(text, parse_mode=None)

    async def send_document(self, file_path, caption=None):
        """Sends a file (like a PDF report) to Telegram."""
        if not self.bot or not self.chat_id:
            return False
            
        try:
            with open(file_path, 'rb') as doc:
                await self.bot.send_document(
                    chat_id=self.chat_id, 
                    document=doc, 
                    caption=caption
                )
            return True
        except Exception as e:
            app_logger.error(f"Error sending Telegram document: {e}")
            return False
