from fpdf import FPDF
import datetime
import os

class ReportGenerator:
    """PROSOFT AI: Institutional-Grade PDF Report Generator."""
    
    def __init__(self, output_dir=None):
        if output_dir is None:
            # Check for PROSOFT CLOUD PERSISTENCE (/data volume)
            root_data = '/data'
            if os.path.isdir(root_data):
                output_dir = os.path.join(root_data, "reports")
            else:
                # Local fallback
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
        
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

    def _clean_text(self, text):
        """Removes emojis and non-Latin-1 characters to prevent FPDF errors."""
        try:
            if not text: return ""
            # FPDF (default fonts) only supports Latin-1 (ISO-8859-1)
            # We encode to latin-1 and ignore errors, then decode back
            return text.encode('latin-1', 'ignore').decode('latin-1')
        except:
            return str(text)

    def generate_daily_report(self, stats, logs):
        """Creates an enhanced PROSOFT-branded institutional intelligence report."""
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        filename = f"PROSOFT_INTEL_{date_str}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        pdf = FPDF()
        pdf.add_page()
        
        # === HEADER BANNER (Professional Apex Theme) ===
        pdf.set_fill_color(10, 13, 20)
        pdf.rect(0, 0, 210, 50, 'F')
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(190, 22, "PROSOFT QUANTUM PRIME", ln=True, align='C')
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(150, 150, 170)
        pdf.cell(190, 6, self._clean_text("SOVEREIGN INSTITUTIONAL INTELLIGENCE CORE"), ln=True, align='C')
        pdf.set_font("Arial", '', 8)
        pdf.cell(190, 6, self._clean_text(f"Generation Cycle: {date_str} @ {time_str} | Internal ID: {hex(int(datetime.datetime.now().timestamp()))}"), ln=True, align='C')
        pdf.ln(15)
        
        # === SECTION 1: SYSTEM CORE ANALYTICS ===
        pdf.set_text_color(37, 99, 235)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(190, 10, "1. SYSTEM CORE & EQUITY ANALYTICS", ln=True)
        pdf.set_draw_color(37, 99, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        
        summary_data = [
            ("Global Valuation:", f"${stats.get('total_equity', 0):,.2f}"),
            ("Available Liquid USDT:", f"${stats.get('balance', 0):,.2f}"),
            ("AI Decision Confidence:", f"{stats.get('ai_conf', 0)*100:.1f}%"),
            ("Network Health Index:", f"{stats.get('market_health', 0):.0f}%"),
            ("Current Asset Focus:", stats.get('symbol', 'BTCUSDT')),
            ("Tactical Pulse:", stats.get('sentiment', 'N/A').upper()),
            ("Operational Mode:", stats.get('execution_mode', 'manual').upper()),
            ("Elite Cycle Rank:", "APEX ENFORCER"),
        ]
        
        # Two-column layout for summary
        pdf.set_font("Arial", '', 10)
        for i in range(0, len(summary_data), 2):
            label1, val1 = summary_data[i]
            pdf.set_text_color(100, 100, 100)
            pdf.cell(45, 8, label1, border=0)
            pdf.set_text_color(10, 13, 20)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(50, 8, self._clean_text(str(val1)), border=0)
            
            if i + 1 < len(summary_data):
                label2, val2 = summary_data[i+1]
                pdf.set_font("Arial", '', 10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(45, 8, label2, border=0)
                pdf.set_text_color(10, 13, 20)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(50, 8, self._clean_text(str(val2)), border=0)
            pdf.ln(8)
            
        pdf.ln(8)
        
        # === SECTION 2: AI NEURAL EVOLUTION (NEW) ===
        pdf.set_text_color(37, 99, 235)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(190, 10, "2. AI NEURAL EVOLUTION & LEARNING MATRIX", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        
        # Efficiency and Accuracy
        history = stats.get('ai_accuracy_history', [])
        current_acc = f"{history[-1]['accuracy']}%" if history else "N/A"
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(30,30,30)
        pdf.cell(60, 8, "Current Prediction Accuracy:", border=0)
        pdf.set_text_color(34, 197, 94) # Green
        pdf.cell(40, 8, current_acc, ln=True, border=0)
        
        if history:
            pdf.set_font("Arial", 'I', 8)
            pdf.set_text_color(100, 100, 100)
            acc_str = "Recent Acc. Sequence: " + " -> ".join([str(h['accuracy'])+"%" for h in history[-5:]])
            pdf.cell(190, 6, self._clean_text(acc_str), ln=True)
        
        # Revenue Streams
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(190, 8, "Institutional Revenue Streams:", ln=True)
        
        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(60, 6, f"- Passive Yield Farming: ${stats.get('yield_amount', 0):.4f}", ln=True)
        pdf.cell(60, 6, f"- Listing Sniper Hits: {stats.get('sniper_hits', 0)} Execute(s)", ln=True)
        pdf.cell(60, 6, f"- Funding Arbitrage: ${stats.get('funding_amount', 0):.4f}", ln=True)
        
        pdf.ln(8)
        
        # === SECTION 3: X-INTELLIGENCE & MARKET PULSE (NEW) ===
        pdf.set_text_color(37, 99, 235)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(190, 10, "3. X-INTELLIGENCE & GLOBAL PULSE", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        
        pulse = stats.get('market_pulse', {})
        feed = pulse.get('feed', [])
        
        if stats.get('news_highlight'):
            pdf.set_fill_color(230, 242, 255)
            pdf.set_font("Arial", 'B', 9)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(190, 8, self._clean_text(f"AI RADAR PRIORITY: {stats.get('news_highlight')}"), border=1, fill=True)
            pdf.ln(2)

        if feed:
            for f in feed[:5]:
                pdf.set_font("Arial", '', 8)
                pdf.set_text_color(50, 50, 50)
                source = f.get('source', 'WEB')
                title = f.get('title', 'N/A')
                type_tag = f.get('type', 'MARKET')
                pdf.set_font("Arial", 'B', 8)
                pdf.cell(25, 6, f"[{type_tag}]", border=0)
                pdf.set_font("Arial", '', 8)
                pdf.multi_cell(165, 6, self._clean_text(f"{source}: {title}"), border=0)
        else:
            pdf.set_font("Arial", 'I', 9)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(190, 7, "Awaiting global signals...", ln=True)

        # === FOOTER ===
        pdf.set_y(-25)
        pdf.set_draw_color(37, 99, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Arial", 'I', 7)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 5, f"PROSOFT AI ENTITY | ENCRYPTED REPORT | Page {pdf.page_no()} | CONFIDENTIAL", align='C')
        
        pdf.output(filepath)
        return filepath
