import os
import tkinter as tk
from tkinter import scrolledtext, font
from dotenv import load_dotenv
from groq import Groq
import threading
from datetime import datetime

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("API key not found. Make sure the .env file contains 'GROQ_API_KEY=<api_key>'")
client = Groq(api_key=api_key)


class ChatSession:
    def __init__(self, title="New Chat"):
        self.title = title
        self.messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
        self.timestamp = datetime.now()
        self.is_greeted = False


class ModernChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chat Assistant")
        self.root.geometry("1100x600")  # LINE 24: Manipulate window size here (width x height)
        self.sessions = [ChatSession()]
        self.current_session = 0
        self.colors = {
            "bg_dark": "#0D0D0D", "bg_sidebar": "#171717", "bg_chat": "#212121",
            "bg_input": "#2A2A2A", "user_bubble": "#2F2F2F", "ai_bubble": "#1A1A1A",
            "accent": "#10A37F", "accent_hover": "#0E8B6F", "text": "#ECECEC",
            "text_dim": "#8E8E8E", "border": "#3A3A3A"
        }
        self.setup_ui()
        
    def setup_ui(self):
        main_container = tk.Frame(self.root, bg=self.colors["bg_dark"])
        main_container.pack(fill=tk.BOTH, expand=True)
        self.create_sidebar(main_container)
        self.create_chat_area(main_container)
        tk.Frame(self.scrollable_frame, bg=self.colors["bg_chat"], height=30).pack(fill=tk.X)
        greeting = "How can I assist you today?"
        self.sessions[0].messages.append({"role": "assistant", "content": greeting})
        self.sessions[0].is_greeted = True
        self.display_ai_message(greeting)
        
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=self.colors["bg_sidebar"], width=260)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        header = tk.Frame(sidebar, bg=self.colors["bg_sidebar"])
        header.pack(fill=tk.X, padx=15, pady=20)
        tk.Label(header, text="AI Assistant", font=("Segoe UI", 16, "bold"),
                bg=self.colors["bg_sidebar"], fg=self.colors["text"]).pack(anchor="w")
        
        tk.Button(sidebar, text="+ New Chat", font=("Segoe UI", 11),
                 bg=self.colors["accent"], fg="white", activebackground=self.colors["accent_hover"],
                 bd=0, cursor="hand2", command=self.new_chat, padx=20, pady=12).pack(fill=tk.X, padx=15, pady=(0, 20))
        
        tk.Label(sidebar, text="Recent Chats", font=("Segoe UI", 10),
                bg=self.colors["bg_sidebar"], fg=self.colors["text_dim"]).pack(anchor="w", padx=15, pady=(0, 10))
        
        self.chat_list_frame = tk.Frame(sidebar, bg=self.colors["bg_sidebar"])
        self.chat_list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self.update_chat_list()
        
    def create_chat_area(self, parent):
        chat_container = tk.Frame(parent, bg=self.colors["bg_chat"])
        chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        chat_frame = tk.Frame(chat_container, bg=self.colors["bg_chat"])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        self.canvas = tk.Canvas(chat_frame, bg=self.colors["bg_chat"], highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_frame, orient="vertical", command=self.canvas.yview,
                                bg=self.colors["bg_chat"], troughcolor=self.colors["bg_chat"], width=10)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors["bg_chat"])
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        self.create_input_area(chat_container)
        
    def create_input_area(self, parent):
        input_container = tk.Frame(parent, bg=self.colors["bg_chat"])
        input_container.pack(fill=tk.X, padx=60, pady=(0, 30))
        
        input_frame = tk.Frame(input_container, bg=self.colors["border"],
                              highlightthickness=1, highlightbackground=self.colors["border"])
        input_frame.pack(fill=tk.X)
        
        inner_frame = tk.Frame(input_frame, bg=self.colors["bg_input"])
        inner_frame.pack(fill=tk.BOTH, padx=1, pady=1)
        
        self.input_field = tk.Text(inner_frame, height=3, font=("Segoe UI", 11),
                                  bg=self.colors["bg_input"], fg=self.colors["text"],
                                  insertbackground=self.colors["text"], bd=0, wrap=tk.WORD, padx=15, pady=12)
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_field.bind("<Return>", lambda e: self.send_message() or "break" if not e.state & 0x1 else None)
        self.input_field.bind("<Shift-Return>", lambda e: None)
        
        self.send_button = tk.Label(inner_frame, text="➤", font=("Segoe UI", 18),
                                   bg=self.colors["bg_input"], fg=self.colors["text_dim"], cursor="hand2", padx=15)
        self.send_button.pack(side=tk.RIGHT, padx=10)
        self.send_button.bind("<Button-1>", lambda e: self.send_message())
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(fg=self.colors["accent"]))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(fg=self.colors["text_dim"]))
        self.input_field.focus()
        
    def display_user_message(self, message):
        msg_frame = tk.Frame(self.scrollable_frame, bg=self.colors["bg_chat"])
        msg_frame.pack(fill=tk.X, pady=10, padx=40)
        bubble_frame = tk.Frame(msg_frame, bg=self.colors["bg_chat"])
        bubble_frame.pack(anchor="e")
        
        tk.Label(bubble_frame, text="You", font=("Segoe UI", 9, "bold"),
                bg=self.colors["bg_chat"], fg=self.colors["text_dim"]).pack(anchor="e", pady=(0, 5))
        
        bubble = tk.Frame(bubble_frame, bg=self.colors["user_bubble"],
                         highlightthickness=1, highlightbackground=self.colors["border"])
        bubble.pack(anchor="e")
        
        tk.Label(bubble, text=message, font=("Segoe UI", 11), bg=self.colors["user_bubble"],
                fg=self.colors["text"], wraplength=700, justify=tk.LEFT, padx=15, pady=12).pack()
        self.scroll_to_bottom()
        
    def display_ai_message(self, message):
        msg_frame = tk.Frame(self.scrollable_frame, bg=self.colors["bg_chat"])
        msg_frame.pack(fill=tk.X, pady=10, padx=40)
        bubble_frame = tk.Frame(msg_frame, bg=self.colors["bg_chat"])
        bubble_frame.pack(anchor="w", fill=tk.X)
        
        tk.Label(bubble_frame, text="🤖 AI Assistant", font=("Segoe UI", 9, "bold"),
                bg=self.colors["bg_chat"], fg=self.colors["accent"]).pack(anchor="w", pady=(0, 5))
        
        bubble = tk.Frame(bubble_frame, bg=self.colors["ai_bubble"],
                         highlightthickness=1, highlightbackground=self.colors["border"])
        bubble.pack(anchor="w", fill=tk.X)
        
        text_widget = tk.Text(bubble, font=("Segoe UI", 11), bg=self.colors["ai_bubble"],
                             fg=self.colors["text"], wrap=tk.WORD, padx=15, pady=12, bd=0,
                             highlightthickness=0, spacing1=3, spacing2=2, spacing3=3, width=80, height=1)
        text_widget.pack(fill=tk.X)
        
        for tag, config in [("bold", {"font": ("Segoe UI", 11, "bold")}),
                           ("code", {"font": ("Consolas", 10), "background": "#1a1a1a", "foreground": "#00ff00"}),
                           ("heading", {"font": ("Segoe UI", 13, "bold"), "foreground": self.colors["accent"], "spacing1": 10, "spacing3": 5}),
                           ("bullet", {"lmargin1": 20, "lmargin2": 35}),
                           ("number", {"lmargin1": 20, "lmargin2": 35}),
                           ("quote", {"lmargin1": 15, "lmargin2": 15, "foreground": self.colors["text_dim"], "font": ("Segoe UI", 10, "italic")})]:
            text_widget.tag_configure(tag, **config)
        
        self.format_message(text_widget, message)
        text_widget.config(state=tk.DISABLED)
        text_widget.update_idletasks()
        text_widget.config(height=int(text_widget.index('end-1c').split('.')[0]))
        self.scroll_to_bottom()
    
    def format_message(self, text_widget, message):
        lines, i, in_code_block = message.split('\n'), 0, False
        
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                i += 1
                continue
            if in_code_block:
                text_widget.insert(tk.END, line + '\n', 'code')
            elif line.startswith('### '):
                text_widget.insert(tk.END, line[4:] + '\n', 'heading')
            elif line.startswith('## '):
                text_widget.insert(tk.END, line[3:] + '\n', 'heading')
            elif line.startswith('# '):
                text_widget.insert(tk.END, line[2:] + '\n', 'heading')
            elif line.strip() and line.lstrip()[0].isdigit() and '. ' in line[:5]:
                text_widget.insert(tk.END, line + '\n', 'number')
            elif line.strip().startswith(('- ', '• ', '* ')):
                text_widget.insert(tk.END, '  • ' + line.strip()[2:] + '\n', 'bullet')
            elif line.strip().startswith('>'):
                text_widget.insert(tk.END, '  ' + line.strip()[1:].strip() + '\n', 'quote')
            else:
                self.insert_formatted_line(text_widget, line)
            i += 1
    
    def insert_formatted_line(self, text_widget, line):
        if not line.strip():
            text_widget.insert(tk.END, '\n')
            return
        
        i = 0
        while i < len(line):
            if line[i:i+2] == '**' and (end := line.find('**', i+2)) != -1:
                text_widget.insert(tk.END, line[i+2:end], 'bold')
                i = end + 2
            elif line[i] == '`' and (end := line.find('`', i+1)) != -1:
                text_widget.insert(tk.END, line[i+1:end], 'code')
                i = end + 1
            else:
                text_widget.insert(tk.END, line[i])
                i += 1
        text_widget.insert(tk.END, '\n')
        
    def scroll_to_bottom(self):
        self.root.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
    def send_message(self):
        if not (user_message := self.input_field.get("1.0", tk.END).strip()):
            return
        
        self.input_field.delete("1.0", tk.END)
        self.display_user_message(user_message)
        
        current = self.sessions[self.current_session]
        if len(current.messages) == 2:
            current.title = (user_message[:35] + "...") if len(user_message) > 35 else user_message
            current.title = ' '.join(current.title.split())
            self.update_chat_list()
        
        self.send_button.config(fg=self.colors["text_dim"])
        self.input_field.config(state=tk.DISABLED)
        threading.Thread(target=self.get_ai_response, args=(user_message,), daemon=True).start()
        
    def get_ai_response(self, user_message):
        try:
            current = self.sessions[self.current_session]
            current.messages.append({"role": "user", "content": user_message})
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile", messages=current.messages,
                temperature=1, max_tokens=1024, top_p=1, stream=True, stop=None)
            
            ai_response = "".join(chunk.choices[0].delta.content or "" for chunk in completion)
            current.messages.append({"role": "assistant", "content": ai_response})
            self.root.after(0, self.display_ai_message, ai_response)
        except Exception as e:
            self.root.after(0, self.display_ai_message, f"Error: {str(e)}")
        finally:
            self.root.after(0, lambda: self.input_field.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.input_field.focus())
            
    def new_chat(self):
        new_session = ChatSession()
        new_session.timestamp = datetime.now()
        self.sessions.append(new_session)
        self.current_session = len(self.sessions) - 1
        
        greeting = "How can I assist you today?"
        new_session.messages.append({"role": "assistant", "content": greeting})
        new_session.is_greeted = True
        
        self.clear_chat()
        tk.Frame(self.scrollable_frame, bg=self.colors["bg_chat"], height=30).pack(fill=tk.X)
        self.update_chat_list()
        self.display_ai_message(greeting)
        self.input_field.focus()
        
    def switch_chat(self, index):
        self.current_session = index
        self.clear_chat()
        tk.Frame(self.scrollable_frame, bg=self.colors["bg_chat"], height=30).pack(fill=tk.X)
        
        for msg in self.sessions[self.current_session].messages[1:]:
            (self.display_user_message if msg["role"] == "user" else self.display_ai_message)(msg["content"])
        
        self.update_chat_list()
        self.input_field.focus()
                
    def clear_chat(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
    def update_chat_list(self):
        for widget in self.chat_list_frame.winfo_children():
            widget.destroy()
        
        for i in range(len(self.sessions) - 1, -1, -1):
            session = self.sessions[i]
            bg_color = self.colors["bg_dark"] if i == self.current_session else self.colors["bg_sidebar"]
            
            chat_container = tk.Frame(self.chat_list_frame, bg=bg_color)
            chat_container.pack(fill=tk.X, pady=2)
            
            chat_btn = tk.Button(chat_container, text=session.title, font=("Segoe UI", 10),
                                bg=bg_color, fg=self.colors["text"], activebackground=self.colors["bg_dark"],
                                bd=0, cursor="hand2", anchor="w", padx=10, pady=8,
                                command=lambda idx=i: self.switch_chat(idx))
            chat_btn.pack(fill=tk.X)
            
            time_str = session.timestamp.strftime("%I:%M %p" if session.timestamp.date() == datetime.now().date() else "%b %d")
            time_label = tk.Label(chat_container, text=time_str, font=("Segoe UI", 8),
                                 bg=bg_color, fg=self.colors["text_dim"], anchor="w", padx=10)
            time_label.pack(fill=tk.X)
            
            def make_hover(cont, btn, lbl, idx):
                def on_enter(e):
                    cont.config(bg=self.colors["bg_dark"])
                    btn.config(bg=self.colors["bg_dark"])
                    lbl.config(bg=self.colors["bg_dark"])
                
                def on_leave(e):
                    color = self.colors["bg_dark"] if idx == self.current_session else self.colors["bg_sidebar"]
                    cont.config(bg=color)
                    btn.config(bg=color)
                    lbl.config(bg=color)
                
                for w in [cont, btn, lbl]:
                    w.bind("<Enter>", on_enter)
                    w.bind("<Leave>", on_leave)
            
            make_hover(chat_container, chat_btn, time_label, i)


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernChatGUI(root)
    root.mainloop()