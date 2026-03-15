import hashlib
import platform
import subprocess
import os
import sqlite3
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class LicenseManager:
    """PROSOFT GLOBAL ACTIVATION SYSTEM (Universal)"""
    
    def __init__(self, db_path="brain.db"):
        self.db_path = db_path
        self.license_file = "prosoft.lic"
        self.trial_days = 3
        # Secret key for local encryption
        self.key = b'p-XqZw7S_v2v7z1-vJ9t7A7UuE-Y9xYVvV8uE-Xy9x8=' 
        self.cipher = Fernet(self.key)
        self._init_security_table()

    def _init_security_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS security_vault (id INTEGER PRIMARY KEY, install_date TEXT)")
        conn.commit()
        conn.close()

    def get_hwid(self):
        """Generates a unique Hardware ID for the machine."""
        hwid_str = platform.node() + platform.processor() + platform.machine()
        try:
            # Try to get disk serial number for stronger lock
            if os.name == 'nt':
                serial = subprocess.check_output('wmic diskdrive get serialnumber', shell=True).decode().split('\n')[1].strip()
            else:
                # Fallback for Linux (e.g. Railway)
                serial = "PROSOFT-NET-NODE-X"
            hwid_str += serial
        except: pass
        return hashlib.sha256(hwid_str.encode()).hexdigest()[:16].upper()

    def check_license_status(self):
        """Returns (is_active, days_left, hwid)"""
        hwid = self.get_hwid()
        
        # 1. Check Separate License File (External Activation)
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    encrypted_token = f.read().strip()
                decrypted_token = self.cipher.decrypt(encrypted_token.encode()).decode()
                if decrypted_token.startswith(hwid):
                    return True, 999, hwid
            except: pass

        # 2. Check Trial Status in Database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT install_date FROM security_vault LIMIT 1")
        record = cursor.fetchone()
        
        if not record:
            install_date = datetime.now().strftime("%Y-%m-%d")
            encrypted_date = self.cipher.encrypt(install_date.encode()).decode()
            cursor.execute("INSERT INTO security_vault (install_date) VALUES (?)", (encrypted_date,))
            conn.commit()
            conn.close()
            return False, self.trial_days, hwid

        encrypted_date = record[0]
        conn.close()

        # Check trial period expiry
        try:
            decrypted_date_str = self.cipher.decrypt(encrypted_date.encode()).decode()
            install_date = datetime.strptime(decrypted_date_str, "%Y-%m-%d")
            expiry_date = install_date + timedelta(days=self.trial_days)
            days_left = (expiry_date - datetime.now()).days
            
            if days_left < 0:
                return False, 0, hwid
            return False, days_left, hwid
        except:
            return False, 0, hwid

    def activate(self, license_key):
        """Verifies license and saves to separate .lic file."""
        hwid = self.get_hwid()
        expected_key = hashlib.md5((hwid + "PROSOFT2026").encode()).hexdigest().upper()[:12]
        
        if license_key == expected_key:
            encrypted_token = self.cipher.encrypt(f"{hwid}-ACTIVE".encode()).decode()
            with open(self.license_file, 'w') as f:
                f.write(encrypted_token)
            return True, "Activation Successful"
        return False, "Invalid License Key"

    def generate_admin_key(self, client_hwid):
        """Helper for you (the seller) to generate keys for clients."""
        return hashlib.md5((client_hwid + "PROSOFT2026").encode()).hexdigest().upper()[:12]
