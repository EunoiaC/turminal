import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
import subprocess
import threading
import os
from PIL import Image, ImageTk

class TerminalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("turminal")
        
        # Default colors with good contrast
        self.colors = {
            'input': '#00CED1',  # Dark turquoise
            'output': 'black',
            'error': '#B22222',  # Firebrick
            'bg': 'white',
            'fg': 'black'
        }
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')
        
        self.create_menu()
        self.folder_icon = self.load_folder_icon()
        self.tabs = {}
        self.history = {}
        self.create_new_tab()
        
        # Add button to create new tabs
        new_tab_button = tk.Button(root, text="New Tab", command=self.create_new_tab)
        new_tab_button.pack()
    
    def load_folder_icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'folder_icon.png')
        folder_icon = Image.open(icon_path).convert("RGBA")
        folder_icon = folder_icon.resize((20, 20), Image.LANCZOS)
        return ImageTk.PhotoImage(folder_icon)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        
        settings_menu.add_command(label="Change Input Color", command=lambda: self.change_color('input'))
        settings_menu.add_command(label="Change Output Color", command=lambda: self.change_color('output'))
        settings_menu.add_command(label="Change Error Color", command=lambda: self.change_color('error'))
        settings_menu.add_command(label="Change Background Color", command=lambda: self.change_color('bg'))
        settings_menu.add_command(label="Change Foreground Color", command=lambda: self.change_color('fg'))
    
    def change_color(self, color_type):
        current_color = self.colors[color_type]
        color = colorchooser.askcolor(title=f"Choose {color_type} color", initialcolor=current_color)[1]
        if color:
            self.colors[color_type] = color
            for tab_id, tab_data in self.tabs.items():
                text_area = tab_data['text_area']
                if color_type == 'bg':
                    text_area.config(bg=self.colors['bg'])
                elif color_type == 'fg':
                    text_area.config(fg=self.colors['fg'])
                else:
                    text_area.tag_configure(color_type, foreground=self.colors[color_type])
    
    def create_new_tab(self):
        frame = ttk.Frame(self.notebook)
        tab_id = self.notebook.index('end') + 1
        self.notebook.add(frame, text=f"Terminal {tab_id}")
        
        current_dir = tk.StringVar(value=os.getcwd())
        self.tabs[tab_id] = {'frame': frame, 'current_dir': current_dir, 'history_index': -1, 'history': []}
        self.history[tab_id] = []
        
        # Working directory and folder icon
        dir_frame = ttk.Frame(frame)
        dir_frame.pack(fill='x')
        
        working_dir_label = tk.Label(dir_frame, textvariable=current_dir, anchor="w")
        working_dir_label.pack(side='left', fill='x', expand=True)
        
        folder_button = tk.Button(dir_frame, image=self.folder_icon, command=lambda: self.change_working_directory(tab_id))
        folder_button.pack(side='right')
        
        text_area = tk.Text(frame, wrap='word', height=20, width=80, bg=self.colors['bg'], fg=self.colors['fg'])
        text_area.pack(expand=True, fill='both', padx=5, pady=5)
        
        text_area.tag_configure("input", foreground=self.colors['input'])
        text_area.tag_configure("output", foreground=self.colors['output'])
        text_area.tag_configure("error", foreground=self.colors['error'])
        
        text_area.bind("<Button-3>", lambda event, ta=text_area: self.show_context_menu(event, ta))
        text_area.bind("<Up>", lambda event, ta=text_area, tid=tab_id: self.navigate_history(ta, tid, direction='up'))
        text_area.bind("<Down>", lambda event, ta=text_area, tid=tab_id: self.navigate_history(ta, tid, direction='down'))
        
        self.tabs[tab_id]['text_area'] = text_area
        
        command_label = tk.Label(frame, text="Command: ")
        command_label.pack(side='left')
        
        entry = tk.Entry(frame)
        entry.pack(fill='x', side='left', expand=True)
        
        entry.bind("<Return>", lambda event, ta=text_area, en=entry, tid=tab_id: self.execute_command(ta, en, tid))
        entry.bind("<Up>", lambda event, ta=entry, tid=tab_id: self.navigate_history(entry, tid, direction='up'))
        entry.bind("<Down>", lambda event, ta=entry, tid=tab_id: self.navigate_history(entry, tid, direction='down'))
        entry.focus_set()
        
        # Automatically select the newly created tab
        self.notebook.select(frame)
    
    def show_context_menu(self, event, text_area):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Change Input Color", command=lambda: self.change_color('input'))
        menu.add_command(label="Change Output Color", command=lambda: self.change_color('output'))
        menu.add_command(label="Change Error Color", command=lambda: self.change_color('error'))
        menu.add_command(label="Change Background Color", command=lambda: self.change_color('bg'))
        menu.add_command(label="Change Foreground Color", command=lambda: self.change_color('fg'))
        
        menu.post(event.x_root, event.y_root)
    
    def navigate_history(self, widget, tab_id, direction):
        history = self.tabs[tab_id]['history']
        if direction == 'up':
            if self.tabs[tab_id]['history_index'] < len(history) - 1:
                self.tabs[tab_id]['history_index'] += 1
        elif direction == 'down':
            if self.tabs[tab_id]['history_index'] >= 0:
                self.tabs[tab_id]['history_index'] -= 1
        
        if self.tabs[tab_id]['history_index'] >= 0:
            # access history in reverse order
            widget.delete(0, tk.END)
            widget.insert(0, history[-(self.tabs[tab_id]['history_index'] + 1)])
        else:
            widget.delete(0, tk.END)
    
    def change_working_directory(self, tab_id):
        new_dir = filedialog.askdirectory()
        if new_dir:
            self.tabs[tab_id]['current_dir'].set(new_dir)
            os.chdir(new_dir)
    
    def execute_command(self, text_area, entry, tab_id):
        command = entry.get().strip()
        if not command:
            return
        
        entry.delete(0, tk.END)

        # Add command to history
        self.tabs[tab_id]['history'].append(command)
        self.tabs[tab_id]['history_index'] = -1
        
        if command == "clear":
            text_area.delete('1.0', tk.END)
            return
        
        def run_command():
            try:
                text_area.insert(tk.END, f"Input: {command}\n", "input")
                text_area.see(tk.END)
                
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.tabs[tab_id]['current_dir'].get(), text=True)
                stdout, stderr = process.communicate()
                
                if stdout:
                    self.append_text(text_area, f"Output: {stdout.rstrip()}\n", "output")
                if stderr:
                    self.append_text(text_area, f"Error: {stderr.rstrip()}\n", "error")
                
                # Update the working directory if the command changes it
                if command.startswith("cd "):
                    try:
                        new_dir = command[3:].strip()
                        os.chdir(new_dir)
                        self.tabs[tab_id]['current_dir'].set(os.getcwd())
                    except Exception as e:
                        self.append_text(text_area, f"cd: {e}\n", "error")
            except Exception as e:
                self.append_text(text_area, f"Error: {e}\n", "error")
        
        threading.Thread(target=run_command).start()
    
    def append_text(self, text_area, text, tag=None):
        text_area.insert(tk.END, text, tag)
        text_area.see(tk.END)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalApp(root)
    root.mainloop()
