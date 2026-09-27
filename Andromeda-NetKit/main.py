import json
import queue
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from network_tools.advanced_dns import run as advanced_dns
from network_tools.basic_dns import run as basic_dns
from network_tools.ping_test import run as ping_test
from network_tools.port_scanner import run as port_scan
from network_tools.subnet_scan import run as subnet_scan
from network_tools.traceroute import run as traceroute
from network_tools.web_security import run as web_security
from network_tools.wifi_analyzer import run as wifi_analyzer
from network_tools.speed_quality import run as speed_quality
from network_tools.system_info import run as system_info
from network_tools.whois_lookup import run as whois_lookup


TOOLS = {
    "Basic DNS Lookup": ("Hostname", "example.com", basic_dns),
    "Advanced DNS Records": ("Domain name", "example.com", advanced_dns),
    "Ping Test": ("Hostname or IP address", "1.1.1.1", ping_test),
    "Web Security Check": ("Website address", "https://example.com", web_security),
    "Traceroute": ("Hostname or IP address", "example.com", traceroute),
    "Local Subnet Scan": ("Subnet prefix (/24)", "192.168.1", subnet_scan),
    "Full-Port TCP/UDP Scanner": ("Hostname or IP address", "example.com", port_scan),
    "Wi-Fi Analyzer": ("Wi-Fi scan", "Scan nearby networks", wifi_analyzer),
    "Internet Speed & Quality": (
        "Speed test",
        "Use the best available test server",
        speed_quality,
    ),
    "WHOIS Lookup": ("Domain name", "example.com", whois_lookup),
}

TOOL_EMOJIS = {
    "Basic DNS Lookup": "🌐",
    "Advanced DNS Records": "📚",
    "Ping Test": "📡",
    "Web Security Check": "🔒",
    "Traceroute": "🗺️",
    "Local Subnet Scan": "🏠",
    "Full-Port TCP/UDP Scanner": "🔍",
    "Wi-Fi Analyzer": "📶",
    "Internet Speed & Quality": "🚀",
    "WHOIS Lookup": "📋",
}

APP_VERSION = "1.0"
DEVELOPER_NAME = "Konstantinos Aimoniotis"

ABOUT_TEXT = (
    f"⚡ Andromeda NetKit — Version {APP_VERSION}\n"
    f"Developed by {DEVELOPER_NAME}\n\n"
    "A desktop toolkit for investigating network connectivity and gathering "
    "local network details.\n\n"
    "Resolve DNS records, test reachability with ping, inspect a route with "
    "traceroute, check HTTP-to-HTTPS redirection, scan a local /24 subnet, "
    "and probe TCP/UDP ports. It can also list nearby Wi-Fi networks, measure "
    "internet speed and connection quality, and retrieve domain WHOIS data.\n\n"
    "My Host Information displays local addresses, gateways, DNS, proxy and "
    "available Wi-Fi details, with optional public IPv4/IPv6 lookups. Results "
    "depend on operating-system tools, network access and permissions. Port "
    "scans should only be run on systems you own or are authorized to test."
)
DONATION_URL = "https://ko-fi.com/aimoniotis"
GITHUB_URL = "https://github.com/aimoniotis/network-engineering-portfolio"
SUPPORT_URL = f"{GITHUB_URL}/issues"
PRIVACY_TEXT = (
    "Andromeda NetKit does not upload a diagnostic report or keep an "
    "account. Each tool contacts the target or service needed for its task. "
    "The app periodically checks internet availability by requesting Google's "
    "connectivity-check endpoint; no diagnostic data is sent in that request. "
    "When online, it also shares your public IP with ipwho.is to identify the "
    "internet provider; the provider name is shown in the app. "
    "The host-information view checks public IP addresses through api.ipify.org. "
    "The speed test sends test traffic to a selected third-party server. "
    "DNS, WHOIS, web checks, ping, traceroute, Wi-Fi scans, and port scans "
    "naturally contact the selected host, configured resolver, or local network. "
    "Results are displayed locally and are not saved by the app."
)
FEATURES = (
    ("Basic DNS Lookup", "Resolve a hostname to its IPv4 address."),
    ("Advanced DNS Records", "Query common DNS record types such as A, AAAA, MX, NS and TXT."),
    ("Ping Test", "Check host reachability and show the operating system's ping output."),
    ("Web Security Check", "Check whether a website redirects from HTTP to HTTPS."),
    ("Traceroute", "Display the network route to a destination where supported."),
    ("Local Subnet Scan", "Check hosts in a /24 subnet for ping responses."),
    ("Full-Port TCP/UDP Scanner", "Probe ports 1–65535 over TCP and UDP."),
    ("Wi-Fi Analyzer", "List nearby Wi-Fi networks using available OS tools."),
    ("Internet Speed & Quality", "Measure download/upload speed, latency, jitter and packet loss."),
    ("WHOIS Lookup", "Retrieve domain registration data from the IANA WHOIS service."),
    ("My Host Information", "View local addresses, subnet prefixes, gateways, DNS, proxy, Wi-Fi and public IP."),
)


class NetworkDiagnosticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Andromeda NetKit")
        self.root.geometry("900x620")
        self.root.minsize(760, 520)
        self.root.configure(bg="#172b43")
        self.theme = "dark"
        self._text_widgets = []
        icon_path = self._resource_path("assets/network_diagnostics.png")
        self._window_icon = tk.PhotoImage(file=str(icon_path))
        self.root.iconphoto(True, self._window_icon)

        self._background_source = Image.open(
            self._resource_path("assets/network_background.png")
        ).convert("RGB")
        self._background_image = None
        self._background_resize_job = None
        self.background_label = tk.Label(self.root, bd=0, highlightthickness=0)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.bind("<Configure>", self._schedule_window_resize)

        self.selected_tool = tk.StringVar(value=next(iter(TOOLS)))
        self.input_value = tk.StringVar()
        self.busy = False
        self._ui_events = queue.Queue()
        self._system_info_window = None
        self._internet_check_running = False
        self._provider_lookup_running = False
        self._provider_last_checked = 0.0

        self._configure_style()
        self._build_layout()
        self._apply_theme()
        self._update_tool()
        self.root.after_idle(self._maximize_window)
        self.root.after(100, self._resize_window_images)
        self.root.after(50, self._process_ui_events)
        self.root.after(0, self._schedule_internet_check)

    @staticmethod
    def _resource_path(relative_path):
        bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        return bundle_dir / relative_path

    def _maximize_window(self):
        try:
            self.root.state("zoomed")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)
            except tk.TclError:
                width = self.root.winfo_screenwidth()
                height = self.root.winfo_screenheight()
                self.root.geometry(f"{width}x{height}+0+0")

    def _schedule_window_resize(self, event):
        if event.widget is self.root:
            if self._background_resize_job is not None:
                self.root.after_cancel(self._background_resize_job)
            self._background_resize_job = self.root.after(
                100, self._resize_window_images
            )

    def _resize_window_images(self):
        self._background_resize_job = None
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        if width < 2 or height < 2:
            return
        resized = ImageOps.fit(
            self._background_source,
            (width, height),
            method=Image.Resampling.LANCZOS,
        )
        tint = Image.new(
            "RGB",
            resized.size,
            "#09111b" if self.theme == "dark" else "#eaf3fb",
        )
        resized = Image.blend(resized, tint, 0.16 if self.theme == "dark" else 0.22)
        self._background_image = ImageTk.PhotoImage(resized)
        self.background_label.configure(image=self._background_image)
        self._resize_banner()

    def _resize_banner(self):
        width = self.banner.winfo_width()
        height = self.banner.winfo_height()
        if width < 2 or height < 2:
            return

        image = ImageOps.fit(
            self._background_source,
            (width, height),
            method=Image.Resampling.LANCZOS,
        ).convert("RGBA")
        overlay_color = (9, 26, 48) if self.theme == "dark" else (224, 239, 251)
        overlay = Image.new("RGBA", image.size, (*overlay_color, 0))
        pixels = overlay.load()
        gradient_width = max(1, int(width * 0.72))
        for x in range(gradient_width):
            alpha = int((135 if self.theme == "dark" else 75) * (1 - x / gradient_width))
            for y in range(height):
                pixels[x, y] = (*overlay_color, alpha)
        image = Image.alpha_composite(image, overlay)
        self._banner_image = ImageTk.PhotoImage(image)
        self.banner.itemconfigure(self._banner_background, image=self._banner_image)
        self.banner.itemconfigure(
            self._banner_title,
            fill="#ffffff" if self.theme == "dark" else "#172b43",
        )
        self.banner.itemconfigure(
            self._banner_subtitle,
            fill="#f2f7fc" if self.theme == "dark" else "#263b52",
        )
        self.banner.itemconfigure(
            self._connection_provider_text,
            fill="#f2f7fc" if self.theme == "dark" else "#263b52",
        )
        self.banner.coords(self._banner_title, 28, 48)
        self.banner.coords(self._banner_subtitle, 30, 91)
        self.banner.coords(self._system_info_button, 30, 138)
        self._position_banner_actions(width)
        self._position_connection_status(width)

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Accent.TButton", font=("TkDefaultFont", 10, "bold"), padding=8)
        style.configure(
            "Donate.TButton",
            background="#000000",
            foreground="#ffffff",
            font=("TkDefaultFont", 10, "bold"),
            padding=(18, 9),
        )
        style.map(
            "Donate.TButton",
            background=[("active", "#252525")],
            foreground=[("active", "#ffffff")],
        )
        style.configure("TEntry", padding=7)

    def _apply_theme(self):
        palettes = {
            "light": {
                "window": "#e7edf4",
                "panel": "#ffffff",
                "foreground": "#192536",
                "muted": "#5a687a",
                "selected": "#dceaff",
                "hover": "#edf3fa",
                "entry": "#ffffff",
                "output": "#f7f9fc",
                "output_text": "#202c3a",
                "footer": "#52627a",
            },
            "dark": {
                "window": "#121a25",
                "panel": "#1d2938",
                "foreground": "#e8eef6",
                "muted": "#aab7c7",
                "selected": "#293e59",
                "hover": "#273647",
                "entry": "#243142",
                "output": "#101827",
                "output_text": "#e6edf7",
                "footer": "#c1ccda",
            },
        }
        self.palette = palettes[self.theme]
        colors = self.palette
        style = ttk.Style()
        self.root.configure(bg=colors["window"])
        style.configure("TFrame", background=colors["window"])
        style.configure("Card.TFrame", background=colors["panel"])
        style.configure(
            "Card.TLabel",
            background=colors["panel"],
            foreground=colors["foreground"],
        )
        style.configure(
            "Footer.TLabel",
            background=colors["window"],
            foreground=colors["footer"],
            font=("TkDefaultFont", 9),
        )
        style.configure(
            "Subtitle.TLabel",
            background=colors["window"],
            foreground=colors["muted"],
            font=("TkDefaultFont", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background=colors["panel"],
            foreground=colors["foreground"],
            font=("TkDefaultFont", 12, "bold"),
        )
        style.configure(
            "Tool.TRadiobutton",
            background=colors["panel"],
            foreground=colors["foreground"],
            padding=(10, 8),
            font=("TkDefaultFont", 10),
        )
        style.map(
            "Tool.TRadiobutton",
            background=[("selected", colors["selected"]), ("active", colors["hover"])],
            foreground=[("selected", colors["foreground"])],
        )
        style.configure(
            "TButton",
            background=colors["panel"],
            foreground=colors["foreground"],
            padding=7,
        )
        style.map(
            "TButton",
            background=[("active", colors["hover"])],
            foreground=[("disabled", colors["muted"])],
        )
        style.configure(
            "Accent.TButton",
            font=("TkDefaultFont", 10, "bold"),
            padding=8,
            background=colors["selected"],
            foreground=colors["foreground"],
        )
        style.configure(
            "TEntry",
            fieldbackground=colors["entry"],
            foreground=colors["foreground"],
            insertcolor=colors["foreground"],
        )
        for widget in self._text_widgets:
            if widget.winfo_exists():
                widget.configure(
                    bg=colors["output"],
                    fg=colors["output_text"],
                    insertbackground=colors["output_text"],
                )
        if hasattr(self, "theme_button"):
            self.theme_button.configure(
                text="☀️  Light mode" if self.theme == "dark" else "🌙  Dark mode"
            )
        if hasattr(self, "banner"):
            self._resize_window_images()

    def _toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._apply_theme()

    def _position_banner_actions(self, width):
        rows = (
            (self._about_button, self._privacy_button),
            (self._faq_button, self._features_button, self._github_button),
        )
        for row_index, buttons in enumerate(rows):
            x = width - 18
            y = 38 + row_index * 43
            for button in buttons:
                widget = self.banner.nametowidget(
                    self.banner.itemcget(button, "window")
                )
                button_width = widget.winfo_reqwidth()
                x -= button_width / 2
                self.banner.coords(button, x, y)
                x -= button_width / 2 + 6
            if row_index == 1:
                self.banner.itemconfigure(
                    self._banner_subtitle,
                    width=max(220, x - 42),
                )

    def _position_connection_status(self, width):
        label = self.banner.itemcget(self._connection_status_text, "text")
        font = tkfont.Font(root=self.root, font=("TkDefaultFont", 10, "bold"))
        text_width = font.measure(label)
        text_right = width - 22
        text_left = text_right - int(text_width)
        self.banner.coords(self._connection_status_text, text_right, 123)
        dot_x = text_left - 12
        self.banner.coords(
            self._connection_status_dot, dot_x - 5, 118, dot_x + 5, 128
        )
        self.banner.coords(self._connection_provider_text, text_right, 151)

    def _build_layout(self):
        container = ttk.Frame(self.root, padding=(24, 12, 24, 24))
        container.place(x=0, y=0, relwidth=1, relheight=1)

        self.banner = tk.Canvas(
            container,
            height=180,
            bd=0,
            highlightthickness=0,
            background="#244362",
        )
        self.banner.pack(fill="x", pady=(0, 18))
        self._banner_background = self.banner.create_image(0, 0, anchor="nw")
        self._banner_title = self.banner.create_text(
            28,
            48,
            anchor="w",
            text="⚡ Andromeda NetKit",
            fill="white",
            font=("TkDefaultFont", 24, "bold"),
        )
        self._banner_subtitle = self.banner.create_text(
            30,
            91,
            anchor="w",
            text="Select a diagnostic tool, enter a target, and review the results.",
            fill="#f2f7fc",
            font=("TkDefaultFont", 11),
        )
        self._about_button = self.banner.create_window(
            0,
            36,
            anchor="center",
            window=ttk.Button(
                self.banner, text="ℹ️  About", command=self._show_about
            ),
        )
        self._system_info_button = self.banner.create_window(
            30,
            138,
            anchor="w",
            window=ttk.Button(
                self.banner,
                text="🖥  My Host Information",
                command=self.show_system_info,
            ),
        )
        self._privacy_button = self.banner.create_window(
            0,
            36,
            anchor="center",
            window=ttk.Button(
                self.banner, text="🔐  Privacy", command=self._show_privacy
            ),
        )
        self._faq_button = self.banner.create_window(
            0,
            79,
            anchor="center",
            window=ttk.Button(
                self.banner, text="❓  FAQ & Support", command=self._show_faq
            ),
        )
        self._features_button = self.banner.create_window(
            0,
            79,
            anchor="center",
            window=ttk.Button(
                self.banner, text="✨  Features", command=self._show_features
            ),
        )
        self._github_button = self.banner.create_window(
            0,
            79,
            anchor="center",
            window=ttk.Button(
                self.banner, text="🐙  GitHub ↗", command=self._open_github
            ),
        )
        self._connection_status_dot = self.banner.create_oval(
            0, 0, 0, 0, outline="", fill="#f0c75e"
        )
        self._connection_status_text = self.banner.create_text(
            0,
            123,
            anchor="e",
            text="Checking internet connection…",
            fill="#f0c75e",
            font=("TkDefaultFont", 10, "bold"),
        )
        self._connection_provider_text = self.banner.create_text(
            0,
            151,
            anchor="e",
            text="Provider: checking…",
            fill="#f2f7fc",
            font=("TkDefaultFont", 9),
        )
        self.banner.bind("<Configure>", lambda _event: self._resize_banner())

        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        tools_card = ttk.Frame(body, style="Card.TFrame", padding=14)
        tools_card.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        ttk.Label(
            tools_card,
            text="DIAGNOSTIC TOOLS",
            style="CardTitle.TLabel",
            anchor="center",
            justify="center",
        ).pack(fill="x", pady=(2, 8))
        self.theme_button = ttk.Button(
            tools_card, text="", command=self._toggle_theme
        )
        self.theme_button.pack(fill="x", pady=(0, 8))
        for name in TOOLS:
            ttk.Radiobutton(
                tools_card,
                text=f"{TOOL_EMOJIS.get(name, '🔧')}  {name}",
                variable=self.selected_tool,
                value=name,
                style="Tool.TRadiobutton",
                command=self._update_tool,
            ).pack(fill="x", anchor="w")
        ttk.Button(
            tools_card,
            text="💖  Donate",
            style="Donate.TButton",
            command=self._open_donation,
        ).pack(side="bottom", anchor="center", pady=(16, 2))

        content = ttk.Frame(body, style="Card.TFrame", padding=20)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(4, weight=1)

        self.tool_title = ttk.Label(content, text="", style="CardTitle.TLabel")
        self.tool_title.grid(row=0, column=0, sticky="w")
        ttk.Label(
            content,
            text=(
                "Network scans can take time.\n"
                "Only scan systems and networks you are authorized to test."
            ),
            wraplength=520,
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="ew", pady=(6, 16))

        self.input_caption = ttk.Label(content, text="", style="Card.TLabel")
        self.input_caption.grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.target_entry = ttk.Entry(content, textvariable=self.input_value)
        self.target_entry.grid(row=3, column=0, sticky="ew")
        self.target_entry.bind("<Return>", lambda _event: self._start_tool())

        controls = ttk.Frame(content, style="Card.TFrame")
        controls.grid(row=4, column=0, sticky="nsew", pady=(16, 0))
        controls.columnconfigure(0, weight=1)
        controls.rowconfigure(1, weight=1)

        action_row = ttk.Frame(controls, style="Card.TFrame")
        action_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.run_button = ttk.Button(
            action_row,
            text="▶️  Run diagnostic",
            style="Accent.TButton",
            command=self._start_tool,
        )
        self.run_button.pack(side="left")
        ttk.Button(
            action_row,
            text="🧹  Clear results",
            command=self._clear_results,
        ).pack(side="left", padx=(8, 0))
        self.status_label = ttk.Label(
            action_row, text="Ready", style="Card.TLabel"
        )
        self.status_label.pack(side="right")
        self.progress_bar = ttk.Progressbar(
            action_row, mode="indeterminate", length=140
        )

        self.output = tk.Text(
            controls,
            height=12,
            wrap="word",
            bg="#101827",
            fg="#e6edf7",
            insertbackground="#ffffff",
            relief="flat",
            padx=12,
            pady=12,
            font=("TkFixedFont", 10),
            state="disabled",
        )
        self._text_widgets.append(self.output)
        self.output.grid(row=1, column=0, sticky="nsew")
        self.output.tag_configure("error", foreground="#ff9b9b")
        ttk.Label(
            container,
            text=f"© 2026 {DEVELOPER_NAME}  |  Version {APP_VERSION}",
            style="Footer.TLabel",
        ).pack(anchor="e", pady=(10, 0))

    def _update_tool(self):
        label, placeholder, _function = TOOLS[self.selected_tool.get()]
        self.tool_title.configure(text=self.selected_tool.get())
        self.input_caption.configure(text=label)
        self.input_value.set(placeholder)
        self.target_entry.focus_set()

    def _start_tool(self):
        if self.busy:
            return
        value = self.input_value.get().strip()
        if not value:
            self._show_result("Enter a value before starting the diagnostic.", error=True)
            return

        tool_name = self.selected_tool.get()
        function = TOOLS[tool_name][2]
        self.busy = True
        self.run_button.configure(state="disabled")
        self.status_label.configure(text="Running…")
        self.progress_bar.pack(side="right", padx=(0, 10))
        self.progress_bar.start(12)
        self._show_result(f"Running {tool_name} for {value}...\n")

        threading.Thread(
            target=self._run_in_background,
            args=(function, value),
            daemon=True,
        ).start()

    def _run_in_background(self, function, value):
        try:
            result = function(value)
            self._post_to_ui(self._finish, result, None)
        except Exception as error:
            self._post_to_ui(self._finish, None, str(error))

    def _post_to_ui(self, callback, *args):
        self._ui_events.put((callback, args))

    def _process_ui_events(self):
        while True:
            try:
                callback, args = self._ui_events.get_nowait()
            except queue.Empty:
                break
            callback(*args)
        self.root.after(50, self._process_ui_events)

    def _schedule_internet_check(self):
        if self._internet_check_running:
            return
        self._internet_check_running = True
        threading.Thread(target=self._check_internet_connection, daemon=True).start()

    def _check_internet_connection(self):
        connected = False
        request = urllib.request.Request(
            "https://connectivitycheck.gstatic.com/generate_204",
            headers={"User-Agent": "AndromedaNetKit/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                connected = 200 <= response.status < 400
        except (OSError, urllib.error.URLError, TimeoutError):
            connected = False
        self._post_to_ui(self._update_internet_status, connected)

    def _update_internet_status(self, connected):
        if connected:
            text, color = "Connected to internet", "#76e39a"
        else:
            text, color = "No connection to internet", "#ff7777"
        self.banner.itemconfigure(self._connection_status_text, text=text, fill=color)
        self.banner.itemconfigure(self._connection_status_dot, fill=color)
        self._position_connection_status(self.banner.winfo_width())
        if connected:
            self._schedule_provider_lookup()
        elif self._provider_last_checked == 0:
            self._update_provider_status("unavailable")
        self._internet_check_running = False
        self.root.after(30000, self._schedule_internet_check)

    def _schedule_provider_lookup(self):
        if (
            self._provider_lookup_running
            or time.monotonic() - self._provider_last_checked < 900
        ):
            return
        self._provider_lookup_running = True
        self._provider_last_checked = time.monotonic()
        threading.Thread(target=self._lookup_internet_provider, daemon=True).start()

    def _lookup_internet_provider(self):
        provider = "unavailable"
        request = urllib.request.Request(
            "https://ipwho.is/?fields=success,connection",
            headers={"User-Agent": "AndromedaNetKit/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read(65536))
            if isinstance(data, dict) and data.get("success"):
                connection = data.get("connection")
                if isinstance(connection, dict):
                    provider_name = connection.get("isp")
                    if isinstance(provider_name, str) and provider_name.strip():
                        provider = provider_name.strip()[:60]
        except (OSError, urllib.error.URLError, TimeoutError, ValueError):
            pass
        self._post_to_ui(self._update_provider_status, provider)

    def _update_provider_status(self, provider):
        self.banner.itemconfigure(
            self._connection_provider_text,
            text=f"Provider: {provider}",
        )
        self._position_connection_status(self.banner.winfo_width())
        self._provider_lookup_running = False

    def _finish(self, result, error):
        self.busy = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.run_button.configure(state="normal")
        if error:
            self.status_label.configure(text="Failed")
            self._show_result(f"Diagnostic failed: {error}", error=True)
        else:
            self.status_label.configure(text="Complete")
            self._show_result(result or "No results.")

    def _show_result(self, text, error=False):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text, "error" if error else ())
        self.output.configure(state="disabled")

    def _clear_results(self):
        self._show_result("")
        self.status_label.configure(text="Ready")

    def _show_about(self):
        messagebox.showinfo("About Andromeda NetKit", ABOUT_TEXT, parent=self.root)

    def _show_text_window(self, title, text, links=()):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("680x520")
        window.minsize(520, 360)
        window.transient(self.root)
        window.iconphoto(True, self._window_icon)

        container = ttk.Frame(window, padding=18)
        container.pack(fill="both", expand=True)
        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        output = tk.Text(
            text_frame,
            wrap="word",
            bg=self.palette["panel"],
            fg=self.palette["foreground"],
            relief="flat",
            padx=12,
            pady=12,
            font=("TkDefaultFont", 10),
            yscrollcommand=scrollbar.set,
        )
        self._text_widgets.append(output)
        scrollbar.configure(command=output.yview)
        output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        output.insert("1.0", text)
        output.configure(state="disabled")
        if links:
            actions = ttk.Frame(container)
            actions.pack(fill="x", pady=(10, 0))
            for label, url in links:
                ttk.Button(
                    actions,
                    text=label,
                    command=lambda link=url: self._open_url(link),
                ).pack(side="right", padx=(8, 0))
        return window

    def _show_privacy(self):
        return self._show_text_window("Privacy", PRIVACY_TEXT)

    def _show_features(self):
        feature_list = "\n".join(
            f"• {name}\n  {description}" for name, description in FEATURES
        )
        return self._show_text_window(
            "Application Features",
            f"⚡ Andromeda NetKit — Version {APP_VERSION}\n"
            f"Developed by {DEVELOPER_NAME}\n\n{feature_list}",
        )

    def _show_faq(self):
        return self._show_text_window(
            "FAQ & Support",
            "Frequently Asked Questions\n\n"
            "Why is Wi-Fi information unavailable?\n"
            "Wi-Fi details depend on the operating system, wireless adapter, "
            "installed network utilities and permissions.\n\n"
            "Why is public IPv6 unavailable?\n"
            "The current network may not provide IPv6 connectivity, or the "
            "public-IP lookup service may not respond.\n\n"
            "Why can a UDP port show open|filtered?\n"
            "UDP services may not reply to an empty probe, so the app cannot "
            "distinguish an open port from filtering.\n\n"
            "Where can I report a problem or request a feature?\n"
            "Open a support issue in the project repository.",
            (
                ("🛟  Open GitHub Support", SUPPORT_URL),
                ("🐙  Open Repository", GITHUB_URL),
            ),
        )

    def _open_github(self):
        self._open_url(GITHUB_URL)

    def _open_url(self, url):
        try:
            opened = webbrowser.open(url, new=2)
        except webbrowser.Error as error:
            messagebox.showerror(
                "Unable to open link",
                f"Open this link in your browser:\n{url}\n\n{error}",
                parent=self.root,
            )
            return
        if not opened:
            messagebox.showerror(
                "Unable to open link",
                f"Open this link in your browser:\n{url}",
                parent=self.root,
            )

    def show_system_info(self):
        if self._system_info_window is not None and self._system_info_window.winfo_exists():
            self._system_info_window.lift()
            return

        window = tk.Toplevel(self.root)
        self._system_info_window = window
        window.title("PC & Connection Information")
        window.geometry("800x620")
        window.minsize(620, 420)
        window.transient(self.root)
        window.iconphoto(True, self._window_icon)
        window.protocol("WM_DELETE_WINDOW", lambda: self._close_system_info(window))

        container = ttk.Frame(window, padding=16)
        container.pack(fill="both", expand=True)
        ttk.Label(
            container,
            text="PC & Connection Information",
            style="CardTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            container,
            text="Collected from this computer. Public IP checks contact api.ipify.org.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 12))

        output = tk.Text(
            container,
            wrap="word",
            bg=self.palette["output"],
            fg=self.palette["output_text"],
            insertbackground=self.palette["output_text"],
            relief="flat",
            padx=12,
            pady=12,
            font=("TkFixedFont", 10),
            state="disabled",
        )
        self._text_widgets.append(output)
        output.pack(fill="both", expand=True)
        status = ttk.Label(container, text="Collecting network details…")
        status.pack(anchor="w", pady=(8, 0))

        def finish(result, error):
            if not window.winfo_exists():
                return
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert(
                "1.0",
                result if error is None else f"Unable to collect connection information:\n{error}",
            )
            output.configure(state="disabled")
            status.configure(text="Information ready" if error is None else "Collection failed")

        def collect():
            try:
                result = system_info()
                self._post_to_ui(finish, result, None)
            except Exception as error:
                self._post_to_ui(finish, None, str(error))

        def refresh():
            status.configure(text="Refreshing network details…")
            threading.Thread(target=collect, daemon=True).start()

        ttk.Button(
            container,
            text="🔄  Refresh",
            command=refresh,
        ).pack(anchor="e", pady=(8, 0))
        threading.Thread(target=collect, daemon=True).start()

    def _close_system_info(self, window):
        if window.winfo_exists():
            window.destroy()
        if self._system_info_window is window:
            self._system_info_window = None

    def _open_donation(self):
        try:
            opened = webbrowser.open(DONATION_URL, new=2)
        except webbrowser.Error as error:
            messagebox.showerror(
                "Unable to open donation page",
                f"Open this link in your browser:\n{DONATION_URL}\n\n{error}",
                parent=self.root,
            )
            return

        if not opened:
            messagebox.showerror(
                "Unable to open donation page",
                f"Open this link in your browser:\n{DONATION_URL}",
                parent=self.root,
            )


def main():
    root = tk.Tk()
    NetworkDiagnosticsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
