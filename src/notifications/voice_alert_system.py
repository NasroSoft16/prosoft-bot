"""
PROSOFT QUANTUM - نظام التنبيهات الصوتية الذكية (Voice Alert System)
يُصدر صوتاً مخصصاً لكل حدث تداولي مهم.
يعمل على نظام Windows بدون أي مكتبات خارجية مدفوعة.
"""
import os
import threading
import subprocess
from src.utils.logger import app_logger


class VoiceAlertSystem:
    """
    Smart sound alerts using Windows built-in beep system.
    No external TTS library required — pure Python winsound.
    Falls back silently on non-Windows systems.
    """

    def __init__(self, enabled=True):
        self.enabled = enabled
        self._check_availability()

    def _check_availability(self):
        """Checks if the winsound module is available (Windows only)."""
        try:
            import winsound
            self._winsound = winsound
            app_logger.info("[Voice Alert] System initialized. Windows beep alerts ACTIVE.")
        except ImportError:
            self._winsound = None
            app_logger.warning("[Voice Alert] winsound not available (non-Windows). Alerts DISABLED.")

    def _beep_async(self, frequency, duration):
        """Plays a beep in a background thread to avoid blocking the main loop."""
        if self._winsound and self.enabled:
            def _play():
                try:
                    self._winsound.Beep(frequency, duration)
                except Exception:
                    pass
            threading.Thread(target=_play, daemon=True).start()

    def say(self, message):
        """Uses Windows PowerShell SAPI to speak the message aloud."""
        if not self.enabled: return
        
        def _speak():
            try:
                # Clean message for shell
                safe_msg = message.replace('"', "").replace("'", "")
                # Use PowerShell to speak safely with subprocess to handle quoting
                ps_script = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_msg}")'
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
            except Exception as e:
                app_logger.error(f"Voice say error: {e}")

        threading.Thread(target=_speak, daemon=True).start()

    # --- Alert Methods ---

    def alert_buy_signal(self):
        """🟢 BUY signal detected — ascending triple beep."""
        app_logger.info("[Voice Alert] 🔊 BUY Signal Alert!")
        self._beep_async(880, 150)
        threading.Timer(0.2, lambda: self._beep_async(1047, 150)).start()
        threading.Timer(0.4, lambda: self._beep_async(1319, 250)).start()

    def alert_take_profit(self):
        """💰 Take Profit hit — celebratory ascending tones."""
        app_logger.info("[Voice Alert] 🔊 Take Profit Hit!")
        for i, (freq, delay) in enumerate([(784, 0), (1047, 0.2), (1319, 0.4), (1568, 0.6)]):
            threading.Timer(delay, lambda f=freq: self._beep_async(f, 200)).start()

    def alert_stop_loss(self):
        """🔴 Stop Loss hit — descending warning beeps."""
        app_logger.info("[Voice Alert] 🔊 Stop Loss Triggered!")
        for i, (freq, delay) in enumerate([(523, 0), (392, 0.3), (261, 0.6)]):
            threading.Timer(delay, lambda f=freq: self._beep_async(f, 300)).start()

    def alert_partial_tp(self):
        """🟡 Partial Take Profit — double pleasant beep."""
        app_logger.info("[Voice Alert] 🔊 Partial TP Executed!")
        self._beep_async(1047, 200)
        threading.Timer(0.3, lambda: self._beep_async(1047, 200)).start()

    def alert_whale_warning(self):
        """🐋 Whale movement — urgent rapid beeps."""
        app_logger.info("[Voice Alert] 🔊 Whale Warning!")
        for i in range(4):
            threading.Timer(i * 0.15, lambda: self._beep_async(440, 100)).start()

    def alert_manipulation_detected(self):
        """🛡️ Manipulation shield triggered — low danger tone."""
        app_logger.info("[Voice Alert] 🔊 Manipulation Detected!")
        self._beep_async(330, 500)
        threading.Timer(0.6, lambda: self._beep_async(220, 400)).start()

    def alert_bot_started(self):
        """🚀 Bot startup complete — ascending success jingle."""
        app_logger.info("[Voice Alert] 🔊 Bot Started!")
        sequence = [(523, 0), (659, 0.15), (784, 0.3), (1047, 0.45)]
        for freq, delay in sequence:
            threading.Timer(delay, lambda f=freq: self._beep_async(f, 150)).start()

    def alert_protocol_omega(self):
        """🚨 Protocol Omega — urgent alarm sequence."""
        app_logger.info("[Voice Alert] 🔊 PROTOCOL OMEGA!")
        for i in range(6):
            freq = 880 if i % 2 == 0 else 440
            threading.Timer(i * 0.25, lambda f=freq: self._beep_async(f, 200)).start()

    def alert_sniper_hit(self, symbol):
        """🎯 Listing Sniper success - verbal notification."""
        self.alert_buy_signal() # Play tones first
        self.say(f"Listing Sniper Alert. Successfully sniped {symbol}. Check your dashboard.")

    def alert_revenue_received(self, source, amount):
        """Announce new revenue from a stream."""
        if not self.enabled: return
        self._beep_async(880, 200) # High double beep
        self._beep_async(1046, 300)
        self.say(f"Operational revenue received from {source}. Total amount, {amount} dollars.")
