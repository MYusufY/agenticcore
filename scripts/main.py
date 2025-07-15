import os
import subprocess
import threading
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import time
import signal
import atexit
import queue

class ModelSelector:
    def __init__(self, root):
        self.root = root
        self.selected_model = None
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("AgenticCore")
        self.root.geometry("800x500")
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(False, False)
        
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        left_frame = tk.Frame(main_frame, bg='#ffffff', bd=2, relief='groove')
        left_frame.pack(side='left', fill='both', expand=False, padx=10, pady=10)
        
        right_frame = tk.Frame(main_frame, bg='#ffffff', bd=2, relief='groove')
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        title_label = tk.Label(right_frame, text="AgenticCore", font=('Arial', 24, 'bold'), bg='#ffffff')
        title_label.pack(pady=10)
        
        info_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=20, font=('Arial', 11), bg='#ffffff')
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        info_text.insert('1.0', "Welcome to AgenticCore!\n\nPlease select a GGUF model file to get started with AI inference.\n\nThe model will be automatically loaded and configured.\n\nSupported format: .gguf files optimized for llama.cpp.\n\nPlease report bugs or issues to us using our website. AgenticCore is distrubuted with NO warranty!\n\nModel selection is up to you. Smaller models can give unsupported formats and the program may not detect code scripts sometimes. You can tell them to give the script in the correct format if that happens.\n\nCurrently tested with Qwen2.5 0.5B, Qwen2.5 0.5B Coder and Deepseek 1.5B. For slower systems, Qwen2.5 0.5B Coder recommended but you can use whatever model you want (as GGUF).\n\nBigger models should of course work better, you can choose one that your system can handle and download from 'huggingface.co'.\n\nThis is an Alpha version of AgenticCore. With your support, lots of more features and fixes will be released.")
        info_text.config(state='disabled')
        
        select_button = tk.Button(left_frame, text="Browse Model File", command=self.select_model, 
                                font=('Arial', 12), bg='#4CAF50', fg='white', relief='flat', padx=20, pady=10)
        select_button.pack(fill='x', pady=10, padx=20)
        
        self.ok_button = tk.Button(left_frame, text="OK", command=self.continue_setup, 
                                 font=('Arial', 12), bg='#2196F3', fg='white', relief='flat', padx=20, pady=10, state='disabled')
        self.ok_button.pack(fill='x', pady=10, padx=20)
        
        self.status_label = tk.Label(left_frame, text="No model selected", font=('Arial', 11), bg='#ffffff', fg='#666666')
        self.status_label.pack(fill='x', pady=10, padx=20)
        
    def select_model(self):
        file_path = filedialog.askopenfilename(
            title="Select GGUF Model File",
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        
        if file_path:
            if file_path.endswith('.gguf'):
                self.selected_model = file_path
                filename = os.path.basename(file_path)
                self.status_label.config(text=f"Selected: {filename}", fg='#4CAF50')
                self.ok_button.config(state='normal')
            else:
                self.status_label.config(text="Error: Unsupported file format", fg='#f44336')
                self.ok_button.config(state='disabled')
                
    def continue_setup(self):
        if self.selected_model:
            config_dir = "/ace/LocalAgent/gui"
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "modelpath.conf")
            
            try:
                with open(config_path, 'w') as f:
                    f.write(self.selected_model)
                self.root.destroy()
            except Exception as e:
                self.status_label.config(text=f"Error saving config: {str(e)}", fg='#f44336')

class AgenticCore:
    def __init__(self):
        self.server_url = "http://127.0.0.1:8080"
        self.conversation = []
        self.current_script = None
        self.first_message_sent = False
        self.server_process = None
        
    def start_llama_server(self, model_path, status_callback=None):
        try:
            server_dir = "/ace/LocalAgent/tc-llamacpp/"
            
            cmd = ["./llama-server", "-m", model_path]
            self.server_process = subprocess.Popen(
                cmd,
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                preexec_fn=os.setsid
            )

            server_started = False
            while True:
                output = self.server_process.stdout.readline()
                if output == '' and self.server_process.poll() is not None:
                    break
                if output:
                    if status_callback:
                        status_callback(f"Server: {output.strip()}")
                    
                    if "127.0.0.1:8080" in output or "listening on" in output.lower() or "server started" in output.lower():
                        server_started = True
                        if status_callback:
                            status_callback("Server is ready!")
                        break
                    
                    if "error" in output.lower() or "failed" in output.lower():
                        if status_callback:
                            status_callback(f"Server error: {output.strip()}")
                        return False
            
            if server_started:
                for i in range(10):
                    try:
                        response = requests.get(f"{self.server_url}/health", timeout=2)
                        if response.status_code == 200:
                            return True
                    except:
                        time.sleep(1)
            
            return server_started
            
        except Exception as e:
            if status_callback:
                status_callback(f"Error starting llama-server: {e}")
            return False

    def stop_llama_server(self):
        if self.server_process:
            try:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                self.server_process.wait(timeout=5)
            except:
                try:
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                except:
                    pass
            self.server_process = None

    def process_user_request_stream(self, request_text, callback):
        system_prompt = """You are AgenticCore, an AI assistant that helps with computer tasks on Tiny Core Linux. Always provide bash scripts when asked to do tasks.

CRITICAL: When providing scripts, use EXACTLY this format:
[AGENTIC_SCRIPT]
#!/bin/sh
your commands here
[/AGENTIC_SCRIPT]

IMPORTANT RULES:
- Use 'tce-load -wi package-name' to install packages
- Use 'tce-search term' to find package names
- Home directory: /home/tc
- Username: tc
- Always wrap scripts in [AGENTIC_SCRIPT] tags
- Never use ```bash``` or other code blocks
- Give working bash commands only
- If uncertain about package names, use tce-search first

Example response:
I'll help you install Firefox. Here's the script:

[AGENTIC_SCRIPT]
#!/bin/sh
tce-load -wi firefox
[/AGENTIC_SCRIPT]

This will install Firefox browser for you."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request_text}
        ]
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                json={
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "stream": True
                },
                headers={"Content-Type": "application/json"},
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            data_text = line_text[6:]
                            if data_text.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_text)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        callback(delta['content'])
                            except json.JSONDecodeError:
                                continue
                callback(None)
            else:
                callback(f"Error: Server returned status {response.status_code}")
                
        except Exception as e:
            callback(f"Error communicating with local AI: {str(e)}")
        
    def fix_script(self, original_script, error_output):
        system_prompt = """You are AgenticCore. Fix the bash script that failed. Analyze the error and provide a corrected version.

CRITICAL: Use EXACTLY this format:
[AGENTIC_SCRIPT]
#!/bin/sh
corrected commands here
[/AGENTIC_SCRIPT]

RULES:
- Fix the specific error shown
- Use tce-load -wi for packages
- Use tce-search if package name is wrong
- Never use ```bash``` or other code blocks
- Always wrap in [AGENTIC_SCRIPT] tags"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Original script:\n{original_script}\n\nError output:\n{error_output}"}
        ]
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                json={
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "stream": False
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: Server returned status {response.status_code}"
                
        except Exception as e:
            return f"Error communicating with local AI: {str(e)}"

    def run_script(self, script_content):
        try:
            script_path = os.path.join(os.getcwd(), "agenticcore_script.sh")
            with open(script_path, "w") as f:
                f.write(script_content)
            
            os.chmod(script_path, 0o755)
            
            process = subprocess.Popen(
                ["sh", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                output_lines.append(line.strip())
                
            process.stdout.close()
            return_code = process.wait()
            
            return {
                'success': return_code == 0,
                'output': output_lines,
                'return_code': return_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': [f"Error running script: {str(e)}"],
                'return_code': -1
            }

class ScriptWidget:
    def __init__(self, parent, script_content, run_callback):
        self.parent = parent
        self.script_content = script_content
        self.run_callback = run_callback
        self.is_expanded = False
        
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        
    def create_widgets(self):
        self.collapsed_frame = ttk.Frame(self.frame, style='Script.TFrame')
        self.collapsed_frame.pack(fill='x', pady=2)
        
        self.reveal_button = ttk.Button(
            self.collapsed_frame, 
            text="📜 Script Generated - Click to Reveal",
            command=self.toggle_script,
            style='Script.TButton'
        )
        self.reveal_button.pack(side='left', fill='x', expand=True, padx=5)
        
        self.quick_run_button = ttk.Button(
            self.collapsed_frame, 
            text="▶ Run",
            command=self.run_script,
            style='Run.TButton'
        )
        self.quick_run_button.pack(side='right', padx=5)
        
        self.expanded_frame = ttk.LabelFrame(self.frame, text="Generated Script", padding=10)
        
        self.script_text = scrolledtext.ScrolledText(
            self.expanded_frame,
            wrap=tk.WORD,
            width=80,
            height=8,
            font=('Courier New', 11),
            bg='#263238',
            fg='#eceff1'
        )
        self.script_text.pack(fill='both', expand=True, pady=(0, 10))
        self.script_text.insert('1.0', self.script_content)
        self.script_text.config(state='disabled')
        
        buttons_frame = ttk.Frame(self.expanded_frame)
        buttons_frame.pack(fill='x')
        
        self.run_button = ttk.Button(buttons_frame, text="Run Script", command=self.run_script)
        self.run_button.pack(side='left', padx=(0, 5))
        
        self.hide_button = ttk.Button(buttons_frame, text="Hide", command=self.toggle_script)
        self.hide_button.pack(side='left')
        
    def toggle_script(self):
        if self.is_expanded:
            self.expanded_frame.pack_forget()
            self.collapsed_frame.pack(fill='x', pady=2)
            self.is_expanded = False
        else:
            self.collapsed_frame.pack_forget()
            self.expanded_frame.pack(fill='both', expand=True, pady=2)
            self.is_expanded = True
            
    def run_script(self):
        self.run_callback(self.script_content)
        
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

class AgenticCoreGUI:
    def __init__(self, root):
        self.root = root
        self.agenticcore = AgenticCore()
        self.is_typing = False
        self.is_server_starting = False
        self.current_response = ""
        self.response_start_index = None
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("AgenticCore")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f8f9fa')
        
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Model Path", command=self.change_model_path)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit_application)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 28, 'bold'), background='#667eea', foreground='white')
        style.configure('Subtitle.TLabel', font=('Arial', 14), background='#667eea', foreground='white')
        style.configure('Custom.TFrame', background='#667eea')
        style.configure('Script.TFrame', background='#e9ecef')
        style.configure('Script.TButton', font=('Arial', 11))
        style.configure('Run.TButton', font=('Arial', 11, 'bold'))
        
        header_frame = ttk.Frame(self.root, style='Custom.TFrame', padding=25)
        header_frame.pack(fill='x')
        
        title_label = ttk.Label(header_frame, text="AgenticCore", style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Linux/Bash Agent", style='Subtitle.TLabel')
        subtitle_label.pack()
        
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill='both', expand=True)
        
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame, 
            wrap=tk.WORD, 
            width=85, 
            height=28,
            font=('Arial', 12),
            bg='white',
            fg='#333',
            state='disabled'
        )
        self.chat_text.pack(fill='both', expand=True, pady=(0, 15))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill='x')
        
        self.input_entry = ttk.Entry(input_frame, font=('Arial', 13))
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.input_entry.bind('<Return>', self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side='right')
        
        self.chat_text.tag_configure("user", foreground="#667eea", font=('Arial', 12, 'bold'))
        self.chat_text.tag_configure("bot", foreground="#333", font=('Arial', 12))
        self.chat_text.tag_configure("output", foreground="#28a745", font=('Courier New', 11))
        self.chat_text.tag_configure("error", foreground="#dc3545", font=('Arial', 12, 'bold'))
        self.chat_text.tag_configure("success", foreground="#28a745", font=('Arial', 12, 'bold'))
        self.chat_text.tag_configure("system", foreground="#6c757d", font=('Arial', 11, 'italic'))
        self.chat_text.tag_configure("loading", foreground="#ff6b35", font=('Arial', 12, 'bold'))
        
        self.set_input_enabled(False)
        
        self.add_message("AgenticCore is starting up...", "system")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def change_model_path(self):
        config_path = "/ace/LocalAgent/gui/modelpath.conf"
        try:
            if os.path.exists(config_path):
                os.remove(config_path)
            self.agenticcore.stop_llama_server()
            self.root.destroy()
            main()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change model path: {str(e)}")
    
    def quit_application(self):
        self.on_closing()
    
    def on_closing(self):
        self.agenticcore.stop_llama_server()
        self.root.destroy()
        
    def set_input_enabled(self, enabled):
        state = 'normal' if enabled else 'disabled'
        self.input_entry.config(state=state)
        self.send_button.config(state=state)
        
        if enabled:
            self.input_entry.focus()
        
    def add_message(self, message, tag):
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, message + "\n\n", tag)
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
        
    def add_script_widget(self, script_content):
        self.chat_text.config(state='normal')
        
        script_widget = ScriptWidget(self.chat_text, script_content, self.run_script_callback)
        
        self.chat_text.window_create(tk.END, window=script_widget.frame)
        self.chat_text.insert(tk.END, "\n\n")
        
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
        
        return script_widget
        
    def send_message(self, event=None):
        if self.is_typing or self.is_server_starting:
            return
            
        message = self.input_entry.get().strip()
        if not message:
            return
            
        self.add_message(f"You: {message}", "user")
        self.input_entry.delete(0, tk.END)
        
        self.current_response = ""
        
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, "AgenticCore: ")
        self.response_start_index = self.chat_text.index(tk.INSERT)
        self.chat_text.config(state='disabled')
        
        threading.Thread(target=self.process_message_stream, args=(message,), daemon=True).start()
        
    def process_message_stream(self, message):
        def stream_callback(chunk):
            if chunk is None:
                self.root.after(0, self.stream_complete)
            else:
                self.root.after(0, self.handle_stream_chunk, chunk)
        
        self.agenticcore.process_user_request_stream(message, stream_callback)
        
    def handle_stream_chunk(self, chunk):
        self.current_response += chunk
        
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, chunk, "bot")
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
            
    def stream_complete(self):
        if "[AGENTIC_SCRIPT]" in self.current_response and "[/AGENTIC_SCRIPT]" in self.current_response:
            try:
                script_start = self.current_response.find("[AGENTIC_SCRIPT]")
                script_end = self.current_response.find("[/AGENTIC_SCRIPT]")
                
                if script_start != -1 and script_end != -1 and script_end > script_start:
                    pre_script = self.current_response[:script_start].strip()
                    script_content = self.current_response[script_start + len("[AGENTIC_SCRIPT]"):script_end].strip()
                    post_script = self.current_response[script_end + len("[/AGENTIC_SCRIPT]"):].strip()
                    
                    self.chat_text.config(state='normal')
                    
                    current_content = self.chat_text.get(self.response_start_index, tk.END)
                    self.chat_text.delete(self.response_start_index, tk.END)
                    
                    if pre_script:
                        self.chat_text.insert(tk.END, pre_script + "\n\n", "bot")
                    
                    if script_content:
                        self.agenticcore.current_script = script_content
                        self.chat_text.config(state='disabled')
                        self.add_script_widget(script_content)
                        self.chat_text.config(state='normal')
                    
                    if post_script:
                        self.chat_text.insert(tk.END, post_script + "\n\n", "bot")
                    
                    self.chat_text.config(state='disabled')
                    self.chat_text.see(tk.END)
                    return
                    
            except Exception as e:
                print(f"Error processing script: {e}")
        
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, "\n\n")
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
            
    def run_script_callback(self, script_content):
        self.agenticcore.current_script = script_content
        self.add_message("Executing script...", "bot")
        
        threading.Thread(target=self.execute_script, daemon=True).start()
        
    def execute_script(self):
        result = self.agenticcore.run_script(self.agenticcore.current_script)
        
        self.root.after(0, self.handle_script_result, result)
        
    def handle_script_result(self, result):
        if result['output']:
            output_text = "\n".join(result['output'])
            self.add_message(f"Output:\n{output_text}", "output")
            
        if result['success']:
            self.add_message("Script completed successfully ✓", "success")
        else:
            self.add_message(f"Script failed with code {result['return_code']} ✗", "error")
            
            if messagebox.askyesno("Script Failed", "Would you like me to fix the script?"):
                self.fix_script(result['output'])
                
    def fix_script(self, error_output):
        self.add_message("Fixing script...", "bot")
        
        error_text = "\n".join(error_output)
        threading.Thread(target=self.process_fix, args=(error_text,), daemon=True).start()
        
    def process_fix(self, error_output):
        response = self.agenticcore.fix_script(self.agenticcore.current_script, error_output)
        
        self.root.after(0, self.handle_fix_response, response)
        
    def handle_fix_response(self, response):
        if "[AGENTIC_SCRIPT]" in response:
            parts = response.split("[AGENTIC_SCRIPT]")
            message_part = parts[0].strip()
            script_part = parts[1].split("[/AGENTIC_SCRIPT]")[0].strip()
            
            self.agenticcore.current_script = script_part
            self.add_message(f"AgenticCore: {message_part}", "bot")
            self.add_script_widget(script_part)
        else:
            self.add_message(f"AgenticCore: {response}", "bot")
        
    def server_status_callback(self, status_message):
        self.root.after(0, lambda: self.add_message(status_message, "system"))

def cleanup_server():
    if hasattr(cleanup_server, 'agenticcore') and cleanup_server.agenticcore:
        cleanup_server.agenticcore.stop_llama_server()

def main():
    config_path = "/ace/LocalAgent/gui/modelpath.conf"
    
    if not os.path.exists(config_path):
        root = tk.Tk()
        selector = ModelSelector(root)
        root.mainloop()
        
        if not os.path.exists(config_path):
            print("No model selected. Exiting.")
            return
    
    with open(config_path, 'r') as f:
        model_path = f.read().strip()
    
    root = tk.Tk()
    app = AgenticCoreGUI(root)
    
    cleanup_server.agenticcore = app.agenticcore
    
    atexit.register(cleanup_server)
    
    def start_server():
        app.is_server_starting = True
        app.add_message("Starting llama-server...", "system")
        
        success = app.agenticcore.start_llama_server(model_path, app.server_status_callback)
        
        app.root.after(0, lambda: server_startup_complete(success))
    
    def server_startup_complete(success):
        app.is_server_starting = False
        
        if success:
            app.add_message("AgenticCore is ready! Ask me to help with any task.", "system")
            app.set_input_enabled(True)
        else:
            app.add_message("Failed to start llama-server. Please check your model path and try again.", "error")
            app.set_input_enabled(True)
    
    threading.Thread(target=start_server, daemon=True).start()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_server()

if __name__ == '__main__':
    main()