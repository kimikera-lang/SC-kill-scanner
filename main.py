import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import os
import time
import re
import json
import webbrowser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogMonitor(FileSystemEventHandler):
    def __init__(self, text_widget, kills_tree, log_path):
        self.text_widget = text_widget
        self.kills_tree = kills_tree
        self.last_position = 0
        self.log_path = log_path
        self.last_check = 0
        self.check_interval = 0.1  # Check every 100ms
        self.kill_count = 0

    def parse_kill(self, line):
        # Pattern to match kill entries with killer information and zone
        pattern = r'<Actor Death>.+?\'([^\']+)\'.+?zone \'([^\']+)\'.+?killed by \'([^\']+)\''
        match = re.search(pattern, line)
        if match:
            victim = match.group(1)
            zone = match.group(2)
            killer = match.group(3)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert with alternating row colors
            tags = ('kill_even',) if self.kill_count % 2 == 0 else ('kill_odd',)
            self.kills_tree.insert('', 0, values=(victim, killer, timestamp, zone), tags=tags)

    def check_file(self):
        try:
            current_time = time.time()
            if current_time - self.last_check < self.check_interval:
                return
            self.last_check = current_time

            if os.path.exists(self.log_path):
                with open(self.log_path, 'r', encoding='utf-8') as file:
                    file.seek(self.last_position)
                    new_text = file.read()
                    if new_text:
                        self.last_position = file.tell()
                        self.text_widget.insert(tk.END, new_text)
                        self.text_widget.see(tk.END)
                        
                        # Process each line for kills
                        for line in new_text.splitlines():
                            if '<Actor Death>' in line:
                                self.parse_kill(line)
        except Exception as e:
            print(f"Error reading log: {str(e)}")

    def on_modified(self, event):
        if event.src_path == self.log_path:
            self.check_file()

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Star Citizen Log Scanner")
        self.geometry("1000x600")
        self.minsize(800, 400)
        
        # Initialize variables before creating layout
        self.config_file = os.path.join(os.path.expanduser('~'), 'sc_scanner_config.json')
        self.log_path = None
        self.monitor = None
        self.observer = None
        
        # Modern theme configurations
        self.dark_theme = {
            'bg': '#1a1b1e',
            'fg': '#ffffff',
            'select_bg': '#663399',
            'select_fg': '#ffffff',
            'tree_bg': '#2a2b2e',
            'tree_fg': '#ffffff',
            'button_bg': '#663399',
            'button_fg': '#ffffff',
            'text_bg': '#1a1b1e',
            'text_fg': '#e2e8f0',
            'frame_bg': '#2a2b2e',
            'hover_bg': '#7a3db8',
            'border': '#3b3b3b',
            'alternate_row': '#222326'
        }
        
        self.light_theme = {
            'bg': '#ffffff',
            'fg': '#1a1b1e',
            'select_bg': '#3b82f6',
            'select_fg': '#ffffff',
            'tree_bg': '#f8fafc',
            'tree_fg': '#1a1b1e',
            'button_bg': '#3b82f6',
            'button_fg': '#ffffff',
            'text_bg': '#ffffff',
            'text_fg': '#1a1b1e',
            'frame_bg': '#f1f5f9',
            'hover_bg': '#7a3db8',
            'border': '#e2e8f0',
            'alternate_row': '#f8fafc'
        }
        
        self.current_theme = self.dark_theme
        self.setup_styles()
        self.create_layout()
        
        # Set up file monitoring
        self.config_file = os.path.join(os.path.expanduser('~'), 'sc_scanner_config.json')
        self.log_path = self.load_config()
        self.monitor = None
        self.observer = None
        
        # Add file selection button to controls
        self.select_file_button = self.create_custom_button(
            self.controls_frame,
            "Select Log File",
            self.select_log_file
        )
        self.select_file_button.pack(side='right', padx=5)
        
        self.setup_file_monitoring()

    def create_custom_button(self, parent, text, command):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.current_theme['button_bg'],
            fg=self.current_theme['button_fg'],
            relief='flat',
            padx=15,
            pady=5,
            font=('Segoe UI', 9),
            cursor='hand2'
        )
        btn.bind('<Enter>', lambda e: btn.configure(background=self.current_theme['hover_bg']))
        btn.bind('<Leave>', lambda e: btn.configure(background=self.current_theme['button_bg']))
        return btn

    def setup_styles(self):
        self.configure(bg=self.current_theme['bg'])
        style = ttk.Style()
        style.theme_use('default')

        # Configure Treeview
        style.configure('Treeview',
            background=self.current_theme['tree_bg'],
            foreground=self.current_theme['tree_fg'],
            fieldbackground=self.current_theme['tree_bg'],
            borderwidth=0)
        
        style.configure('Treeview.Heading',
            background=self.current_theme['frame_bg'],
            foreground=self.current_theme['fg'],
            relief='flat',
            font=('Segoe UI', 9, 'bold'))
        
        style.map('Treeview.Heading',
            background=[('active', self.current_theme['frame_bg'])])
            
        style.configure('TLabelframe',
            background=self.current_theme['frame_bg'],
            bordercolor=self.current_theme['border'])
        
        style.configure('TLabelframe.Label',
            background=self.current_theme['frame_bg'],
            foreground=self.current_theme['fg'],
            font=('Segoe UI', 9, 'bold'))
            
        # Configure alternating row colors
        style.map('Treeview',
            background=[('selected', self.current_theme['select_bg'])],
            foreground=[('selected', self.current_theme['select_fg'])])

    def create_tooltip(self, widget, text):
        if self.tooltip:
            self.tooltip.destroy()
        
        # Get mouse position relative to screen
        x = self.winfo_pointerx() + 15
        y = self.winfo_pointery() + 10
        
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip,
            text=text,
            justify='left',
            background=self.current_theme['frame_bg'],
            foreground=self.current_theme['fg'],
            relief='solid',
            borderwidth=1,
            padx=5,
            pady=2
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def on_tree_motion(self, event):
        item = self.kills_tree.identify_row(event.y)
        if not item:
            self.hide_tooltip()
            return
            
        column = self.kills_tree.identify_column(event.x)
        if column in ('#1', '#2'):  # Victim or Killer columns
            self.create_tooltip(event.widget, "Click to open RSI profile")
        else:
            self.hide_tooltip()

    def on_tree_motion(self, event):
        item = self.kills_tree.identify_row(event.y)
        column = self.kills_tree.identify_column(event.x)
        
        if item and column in ('#1', '#2'):  # Victim or Killer columns
            self.kills_tree.configure(cursor='hand2')
            self.create_tooltip(event.widget, "Click to open RSI profile")
        else:
            self.kills_tree.configure(cursor='')
            self.hide_tooltip()

    def on_tree_click(self, event):
        item = self.kills_tree.identify_row(event.y)
        if not item:
            return
            
        column = self.kills_tree.identify_column(event.x)
        if column not in ('#1', '#2'):  # Not Victim or Killer columns
            return
            
        # Get the player name from the clicked cell
        col_id = int(column[1]) - 1
        player_name = self.kills_tree.item(item)['values'][col_id]
        
        # Open RSI profile in default browser
        url = f"https://robertsspaceindustries.com/citizens/{player_name}"
        webbrowser.open(url)

    def toggle_theme(self):
        self.current_theme = self.light_theme if self.current_theme == self.dark_theme else self.dark_theme
        self.setup_styles()
        
        # Update text widget colors
        self.log_text.configure(
            bg=self.current_theme['text_bg'],
            fg=self.current_theme['text_fg'],
            insertbackground=self.current_theme['text_fg'],
            selectbackground=self.current_theme['select_bg'],
            selectforeground=self.current_theme['select_fg']
        )
        
        # Update control buttons
        for btn in [self.theme_button, self.clear_button, self.toggle_log_button]:
            btn.configure(bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'])
            
        # Update tooltip if it exists
        if self.tooltip:
            for child in self.tooltip.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(
                        background=self.current_theme['frame_bg'],
                        foreground=self.current_theme['fg']
                    )
            
        # Update tree colors
        self.kills_tree.tag_configure('kill_even', background=self.current_theme['alternate_row'])
        self.kills_tree.tag_configure('kill_odd', background=self.current_theme['tree_bg'])

    def toggle_log_visibility(self):
        if self.log_frame.winfo_viewable():
            current_height = self.winfo_height()
            log_height = self.log_frame.winfo_height()
            self.log_frame.pack_forget()
            self.toggle_log_button.configure(text="Show Log")
            # Adjust window size when hiding log
            self.geometry(f"{self.winfo_width()}x{current_height - log_height}")
        else:
            self.log_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))
            self.toggle_log_button.configure(text="Hide Log")

    def clear_kills_log(self):
        if messagebox.askyesno("Confirm Clear", 
            "Are you sure you want to clear the kills log?\nThis action cannot be undone.",
            icon='warning'):
            for item in self.kills_tree.get_children():
                self.kills_tree.delete(item)
            self.monitor.kill_count = 0

    def create_layout(self):
        # Create controls frame at the top
        self.controls_frame = tk.Frame(self, bg=self.current_theme['bg'])
        self.controls_frame.pack(fill='x', padx=10, pady=(5, 0))
        
        # Add control buttons with modern style
        self.theme_button = self.create_custom_button(
            self.controls_frame,
            "Toggle Theme",
            self.toggle_theme
        )
        self.theme_button.pack(side='left', padx=(0, 5))

        self.pause_button = self.create_custom_button(
            self.controls_frame,
            "Pause Log",
            self.toggle_pause
        )
        self.pause_button.pack(side='left', padx=5)
        self.log_paused = False
        
        self.clear_button = self.create_custom_button(
            self.controls_frame,
            "Clear Kills Log",
            self.clear_kills_log
        )
        self.clear_button.pack(side='left', padx=5)
        
        self.toggle_log_button = self.create_custom_button(
            self.controls_frame,
            "Hide Log",
            self.toggle_log_visibility
        )
        self.toggle_log_button.pack(side='left', padx=5)
        
        # Add file selection button
        self.select_file_button = self.create_custom_button(
            self.controls_frame,
            "Select Log File",
            self.select_log_file
        )
        self.select_file_button.pack(side='right', padx=5)

        # Create kills frame
        self.kills_frame = ttk.LabelFrame(self, text="Kills Log")
        self.kills_frame.pack(fill='both', padx=10, pady=(0, 10), ipady=5)

        # Create kills treeview with modern styling
        self.kills_tree = ttk.Treeview(
            self.kills_frame, 
            columns=('Victim', 'Killer', 'Time', 'Zone'), 
            show='headings',
            style='Treeview',
            height=4  # Show only 4 rows by default
        )
        
        # Configure modern headings
        headings = {
            'Victim': 'Victim',
            'Killer': 'Killed By',
            'Time': 'Time',
            'Zone': 'Zone / Vehicle'
        }
        
        for col in headings:
            self.kills_tree.heading(col, 
                text=headings[col],
                anchor='w' if col not in ('Time',) else 'center')
        
        # Configure columns with modern proportions
        self.kills_tree.column('Victim', width=300, minwidth=200)
        self.kills_tree.column('Killer', width=300, minwidth=200)
        self.kills_tree.column('Time', width=100, minwidth=100, anchor='center')
        self.kills_tree.column('Zone', width=250, minwidth=150)
        
        # Configure clickable names
        self.kills_tree.tag_configure('clickable', foreground=self.current_theme['select_bg'])
        self.kills_tree.bind('<Button-1>', self.on_tree_click)
        
        # Add tooltip
        self.tooltip = None
        self.kills_tree.bind('<Motion>', self.on_tree_motion)
        self.kills_tree.bind('<Leave>', self.hide_tooltip)
        
        # Configure row tags for alternating colors
        self.kills_tree.tag_configure('kill_even', background=self.current_theme['alternate_row'])
        self.kills_tree.tag_configure('kill_odd', background=self.current_theme['tree_bg'])
        
        self.kills_tree.pack(expand=True, fill='both', padx=5, pady=5)

        # Create log frame
        self.log_frame = ttk.LabelFrame(self, text="Full Log")
        self.log_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))

        # Create main text area with modern theme
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            bg=self.current_theme['text_bg'],
            fg=self.current_theme['text_fg'],
            insertbackground=self.current_theme['text_fg'],
            selectbackground=self.current_theme['select_bg'],
            selectforeground=self.current_theme['select_fg'],
            font=('Consolas', 10),
            relief='flat',
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.log_text.pack(expand=True, fill='both', padx=5, pady=5)

    def load_config(self):
        default_path = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\Game.log"
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('log_path', default_path)
        except Exception:
            pass
        return default_path

    def save_config(self):
        try:
            config = {'log_path': self.log_path}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {str(e)}")

    def select_log_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Star Citizen Game.log file",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.log_path)
        )
        if file_path:
            self.log_path = file_path
            self.save_config()
            self.restart_monitoring()

    def stop_monitoring(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.monitor = None

    def restart_monitoring(self):
        self.stop_monitoring()
        # Clear existing content
        self.log_text.delete('1.0', tk.END)
        for item in self.kills_tree.get_children():
            self.kills_tree.delete(item)
        self.setup_file_monitoring()

    def setup_file_monitoring(self):
        if not self.log_path or not os.path.exists(self.log_path):
            self.log_text.insert(tk.END, "Please select the Star Citizen Game.log file using the 'Select Log File' button.\n")
            return

        try:
            with open(self.log_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.log_text.insert(tk.END, content)
                self.log_text.see(tk.END)
                
                # Create monitor first so it's available for parsing kills
                self.monitor = LogMonitor(self.log_text, self.kills_tree, self.log_path)
                
                # Process existing kills
                for line in content.splitlines():
                    if '<Actor Death>' in line:
                        self.monitor.parse_kill(line)
        except Exception as e:
            self.log_text.insert(tk.END, f"Error reading log file: {str(e)}\n")
            return

        # Set up watchdog observer
        try:
            self.observer = Observer()
            self.observer.schedule(self.monitor, os.path.dirname(self.log_path), recursive=False)
            self.observer.start()
            self.check_updates()
        except Exception as e:
            self.log_text.insert(tk.END, f"Error setting up file monitoring: {str(e)}\n")

    def toggle_pause(self):
        self.log_paused = not self.log_paused
        if self.log_paused:
            self.pause_button.configure(text="Resume Log")
        else:
            self.pause_button.configure(text="Pause Log")
            # Ensure we're at the end of the log when resuming
            self.log_text.see(tk.END)

    def check_updates(self):
        if self.monitor and not self.log_paused:
            self.monitor.check_file()
        self.after(100, self.check_updates)  # Schedule next check in 100ms

if __name__ == "__main__":
    app = Application()
    app.mainloop()