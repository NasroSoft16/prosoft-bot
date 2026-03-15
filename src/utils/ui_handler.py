from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich import box
from datetime import datetime

class UIHandler:
    """PROSOFT UI: High-performance Terminal Dashboard."""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.setup_layout()

    def setup_layout(self):
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["body"].split_row(
            Layout(name="intel", ratio=1),
            Layout(name="pnl", ratio=1),
            Layout(name="log", ratio=2)
        )
        # Initialization
        self.layout["header"].update(Panel("BOOTING PROSOFT QUANTUM CORE...", style="bold white on blue"))
        self.layout["intel"].update(Panel("Neural link pending...", title="🧠 Market Intel"))
        self.layout["pnl"].update(Panel("Syncing Ledger...", title="💰 Portfolio Status"))
        self.layout["log"].update(Panel("Initializing Gateways...", title="📡 Action Stream"))
        self.layout["footer"].update(Panel("Ready.", style="dim"))

    def generate_header(self, symbol, timeframe):
        return Panel(
            f"💠 [bold white]PROSOFT QUANTUM[/bold white] [bold cyan]PRIME v11.2[/bold cyan] | [yellow]Asset: {symbol}[/yellow] | [green]TF: {timeframe}[/green] | [bold red]NODE: ACTIVE[/bold red]",
            style="#1a1c2c on #0a0d14",
            box=box.DOUBLE,
            padding=(0, 2)
        )

    def generate_intel_panel(self, bot_stats):
        health = bot_stats.get('market_health', 0)
        h_color = "green" if health > 70 else "yellow" if health > 40 else "red"
        
        sentiment = bot_stats.get('sentiment', 'NEUTRAL').upper()
        s_color = "green" if "BULL" in sentiment else "red" if "BEAR" in sentiment else "blue"
        
        conf = bot_stats.get('ai_conf', 0)
        c_color = "green" if conf >= 0.7 else "yellow" if conf >= 0.5 else "red"

        table = Table(box=box.SIMPLE, expand=True, show_header=False)
        table.add_row("Neural Health", f"[{h_color}]{health:.0f}%[/]")
        table.add_row("Sentiment", f"[{s_color}]{sentiment}[/]")
        table.add_row("AI Confidence", f"[bold {c_color}]{conf*100:.1f}%[/]")
        table.add_row("EMA Trend", "[green]BULLISH[/]" if bot_stats.get('ema50', 0) > bot_stats.get('ema200', 0) else "[red]BEARISH[/]")
        table.add_row("RSI (14)", f"{bot_stats.get('rsi', 0):.2f}")
        
        return Panel(table, title="🧠 Neural Intelligence", border_style="cyan")

    def generate_pnl_panel(self, bot_stats):
        price = bot_stats.get('price', 0.0)
        pnl = bot_stats.get('daily_pnl', 0.0)
        p_color = "green" if pnl >= 0 else "red"
        
        table = Table(box=box.SIMPLE, expand=True, show_header=False)
        table.add_row("USDT Balance", f"[bold white]${bot_stats.get('balance', 0.0):,.2f}[/]")
        table.add_row("Total Equity", f"${bot_stats.get('total_equity', 0.0):,.2f}")
        table.add_row("Market Price", f"${price:,.2f}")
        table.add_row("Daily Alpha", f"[{p_color}]{pnl:+.2f}%[/]")
        table.add_row("Trades Active", f"{bot_stats.get('active_count', 0)}")
        
        return Panel(table, title="💰 Sovereign Ledger", border_style="green")

    def generate_log_panel(self, logs):
        # Keep only the last 15 logs to prevent overcrowding
        log_text = "\n".join(logs[-15:])
        return Panel(log_text, title="📡 System Action Stream", border_style="#333333")

    def generate_footer(self):
        now = datetime.now().strftime("%H:%M:%S")
        return Panel(f"🛡️ [cyan]Sovereign Shell Active[/cyan] | [dim]Uptime Trace: {now}[/dim] | [bold green]WEB DASHBOARD: http://127.0.0.1:5000[/bold green]", style="dim", box=box.SIMPLE)

    def update_ui(self, symbol, timeframe, bot_stats, logs):
        self.layout["header"].update(self.generate_header(symbol, timeframe))
        self.layout["intel"].update(self.generate_intel_panel(bot_stats))
        self.layout["pnl"].update(self.generate_pnl_panel(bot_stats))
        self.layout["log"].update(self.generate_log_panel(logs))
        self.layout["footer"].update(self.generate_footer())
        return self.layout
