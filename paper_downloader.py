import os
import re
import json
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import threading
import queue
from urllib.parse import quote_plus
import subprocess
import platform
import sys
import certifi
import signal
import atexit
import arxiv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Set the SSL_CERT_FILE environment variable to the path provided by certifi.
os.environ['SSL_CERT_FILE'] = certifi.where()

# Suppress SSL verification warnings for a cleaner user experience
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

SETTINGS_FILE = 'downloader_settings.json'
PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".paper_downloader_profile")


def sanitize_filename(filename):
    """
    Removes characters that are not allowed in filenames and limits length.
    """
    s = re.sub(r'[\\/*?:"<>|]', "", filename)
    return s[:200] # Limit filename length to avoid OS errors

def shorten_path(path, max_len=40):
    """Shortens a file path to a more displayable length."""
    if len(path) <= max_len:
        return path
    parts = path.split(os.path.sep)
    if len(parts) <= 2:
        return "..." + path[-max_len:]
    return os.path.join(parts[0], '...', *parts[-2:])

# --- Thread-Safe Queues for Communication ---
download_queue = queue.Queue()
update_queue = queue.Queue()

def downloader_worker():
    """
    This function runs in a separate thread.
    It uses Selenium with a persistent profile to reduce CAPTCHAs.
    """
    driver = None
    while True:
        item = download_queue.get()
        if item is None:
            break

        title_query, num_to_download, download_path = item
        
        try:
            update_queue.put(('update_status', title_query, 'Opening browser...'))
            
            options = webdriver.ChromeOptions()
            options.add_argument(f"user-data-dir={PROFILE_PATH}")
            
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            
            search_query = f'{title_query} + paper'
            search_url = f"https://scholar.google.com/scholar?hl=en&q={quote_plus(search_query)}"
            driver.get(search_url)

            WebDriverWait(driver, 300).until(
                EC.presence_of_element_located((By.ID, "gs_res_ccl_mid"))
            )
            
            update_queue.put(('update_status', title_query, 'Searching...'))
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            results = soup.find_all('div', class_='gs_scl')
            
            if not results:
                update_queue.put(('update_status', title_query, 'Error: Not Found'))
                continue

            update_queue.put(('update_status', title_query, f'Found {len(results)} results'))
            
            downloaded_count = 0
            for i, result in enumerate(results):
                if downloaded_count >= num_to_download:
                    break

                pdf_section = result.find('div', class_='gs_ggsd')
                if pdf_section and pdf_section.find('a'):
                    pdf_link = pdf_section.find('a')['href']
                    paper_title_tag = result.find('h3', class_='gs_rt')
                    paper_title = paper_title_tag.text if paper_title_tag else title_query
                    
                    sub_task_id = f"{title_query}_{i+1}"
                    filename = f"{sanitize_filename(paper_title)}.pdf"
                    filepath = os.path.join(download_path, filename)
                    
                    update_queue.put(('add_sub_task', sub_task_id, (filename, 'Downloading...')))
                    
                    try:
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                        pdf_response = requests.get(pdf_link, headers=headers, timeout=30, verify=False)
                        pdf_response.raise_for_status()
                        with open(filepath, 'wb') as f:
                            f.write(pdf_response.content)
                        update_queue.put(('update_status', sub_task_id, 'Complete'))
                        downloaded_count += 1
                    except requests.RequestException as e:
                        print(f"Failed to download {pdf_link}: {e}")
                        update_queue.put(('update_status', sub_task_id, 'Error: Failed'))

            final_status = f'Complete ({downloaded_count}/{num_to_download})'
            update_queue.put(('update_status', title_query, final_status))
            update_queue.put(('add_separator', title_query, None))

        except Exception as e:
            print(f"Error processing '{title_query}': {e}")
            update_queue.put(('update_status', title_query, 'Error: Search Failed'))
        
        finally:
            if driver:
                driver.quit()
            download_queue.task_done()

def get_application_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default_path = get_application_path()
        return {'paths': [default_path], 'last_selected': default_path}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def create_gui(downloader_thread):
    root = tk.Tk()
    root.title("Paper Downloader")
    root.geometry("1600x800")
    root.minsize(900, 600)
    
    BG_COLOR, CONTENT_BG, BORDER_COLOR = '#f7f7f8', '#ffffff', '#e5e5e5'
    ACCENT_COLOR, ACCENT_ACTIVE_COLOR = '#007aff', '#005ecb'
    FONT_FAMILY = 'Roboto'
    
    root.configure(bg=BG_COLOR)
    settings = load_settings()

    style = ttk.Style(root)
    if 'aqua' in style.theme_names(): style.theme_use('aqua')
    
    style.configure('TFrame', background=BG_COLOR)
    style.configure('Content.TFrame', background=CONTENT_BG)
    style.configure('TLabel', background=BG_COLOR, font=(FONT_FAMILY, 13))
    style.configure('Content.TLabel', background=CONTENT_BG, font=(FONT_FAMILY, 13))
    style.configure('Bold.TLabel', font=(FONT_FAMILY, 14, 'bold'))
    style.configure('TButton', font=(FONT_FAMILY, 13))
    style.configure('Add.TButton', font=(FONT_FAMILY, 13, 'bold'), foreground='white', background=ACCENT_COLOR)
    style.map('Add.TButton', background=[('active', ACCENT_ACTIVE_COLOR)])
    style.configure('Treeview', rowheight=28, font=(FONT_FAMILY, 12), background=CONTENT_BG, fieldbackground=CONTENT_BG, borderwidth=0)
    style.configure('Treeview.Heading', font=(FONT_FAMILY, 12, 'bold'), background='#f7f7f8', relief='flat')
    style.map('Treeview.Heading', background=[('active', '#f0f0f0')])
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
    style.configure("Separator.TFrame", background=BORDER_COLOR)

    root.grid_columnconfigure(1, weight=1); root.grid_rowconfigure(0, weight=1)

    left_frame = ttk.Frame(root, width=500, style='Content.TFrame')
    left_frame.grid(row=0, column=0, sticky='nsew', padx=(10,0), pady=10)
    left_frame.pack_propagate(False)

    sidebar_content = ttk.Frame(left_frame, padding=20, style='Content.TFrame')
    sidebar_content.pack(fill=tk.BOTH, expand=True)

    ttk.Label(sidebar_content, text="Enter Paper Titles", style='Bold.TLabel', background=CONTENT_BG).pack(anchor='w', pady=(0, 10))
    input_text = scrolledtext.ScrolledText(sidebar_content, wrap=tk.WORD, relief=tk.FLAT,
                                           borderwidth=1, highlightthickness=1, highlightbackground=BORDER_COLOR,
                                           font=(FONT_FAMILY, 13))
    input_text.pack(fill=tk.BOTH, expand=True); input_text.focus()

    path_frame = ttk.Frame(sidebar_content, style='Content.TFrame')
    path_frame.pack(fill=tk.X, pady=(20, 5))
    ttk.Label(path_frame, text="Download to:", style='Content.TLabel').pack(side=tk.LEFT, padx=(0, 10))
    
    display_paths = [shorten_path(p) for p in settings['paths']]
    path_var = tk.StringVar()
    path_combobox = ttk.Combobox(path_frame, textvariable=path_var, values=display_paths, state='readonly')
    
    last_selected_full = settings.get('last_selected', settings['paths'][0])
    if last_selected_full in settings['paths']:
        idx = settings['paths'].index(last_selected_full)
        path_combobox.current(idx)

    path_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

    path_buttons_frame = ttk.Frame(sidebar_content, style='Content.TFrame')
    path_buttons_frame.pack(fill=tk.X, pady=(5, 20))
    
    def get_current_full_path():
        if path_combobox.current() != -1:
            return settings['paths'][path_combobox.current()]
        return None

    def open_selected_folder():
        path = get_current_full_path()
        if path and os.path.isdir(path):
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.run(['open', path])
            else: subprocess.run(['xdg-open', path])
        else:
            messagebox.showwarning("Path Not Found", f"The folder does not exist:\n{path}")

    def open_path_manager():
        manager_win = tk.Toplevel(root)
        manager_win.title("Manage Download Paths"); manager_win.transient(root); manager_win.grab_set()
        manager_win.geometry("1000x400")
        listbox = tk.Listbox(manager_win, height=10, font=(FONT_FAMILY, 12))
        for p in settings['paths']: listbox.insert(tk.END, p)
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        btn_frame = ttk.Frame(manager_win)
        btn_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        def add_path():
            new_path = filedialog.askdirectory(title="Select a Folder")
            if new_path and new_path not in settings['paths']:
                settings['paths'].append(new_path); listbox.insert(tk.END, new_path)
                path_combobox['values'] = [shorten_path(p) for p in settings['paths']]; save_settings(settings)
        def remove_path():
            selected_indices = listbox.curselection()
            if not selected_indices: return
            selected_path = listbox.get(selected_indices[0])
            if len(settings['paths']) > 1:
                current_full_path = get_current_full_path()
                settings['paths'].remove(selected_path); listbox.delete(selected_indices[0])
                path_combobox['values'] = [shorten_path(p) for p in settings['paths']]
                if current_full_path == selected_path: path_combobox.current(0)
                else: path_combobox.current(settings['paths'].index(current_full_path))
                save_settings(settings)
            else:
                messagebox.showwarning("Cannot Remove", "You must have at least one download path.")
        ttk.Button(btn_frame, text="Add", command=add_path).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Remove", command=remove_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Done", command=manager_win.destroy).pack(side=tk.LEFT)
    
    ttk.Button(path_buttons_frame, text="Manage", command=open_path_manager).pack(side=tk.LEFT, padx=5)
    ttk.Button(path_buttons_frame, text="Open", command=open_selected_folder).pack(side=tk.LEFT)
    
    controls_frame = ttk.Frame(sidebar_content, style='Content.TFrame')
    controls_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
    max_downloads_frame = ttk.Frame(controls_frame, style='Content.TFrame')
    max_downloads_frame.pack(side=tk.LEFT)
    ttk.Label(max_downloads_frame, text="Max Downloads:", style='Content.TLabel').pack(side=tk.LEFT, padx=(0, 10))
    num_downloads_var = tk.IntVar(value=1)
    ttk.Spinbox(max_downloads_frame, from_=1, to=100, textvariable=num_downloads_var, width=5).pack(side=tk.LEFT)
    def add_papers_to_queue():
        titles = input_text.get("1.0", tk.END).strip().split('\n')
        num_to_download = num_downloads_var.get(); download_path = get_current_full_path()
        if not download_path or not os.path.isdir(download_path):
            messagebox.showerror("Invalid Path", f"The selected download folder does not exist:\n{download_path}")
            return
        for title in titles:
            clean_title = title.strip()
            if clean_title and not queue_tree.exists(clean_title):
                queue_tree.insert('', 'end', iid=clean_title, values=(clean_title, '', 'Queued'), open=True)
                download_queue.put((clean_title, num_to_download, download_path))
        input_text.delete("1.0", tk.END)
    ttk.Button(controls_frame, text="Start", command=add_papers_to_queue).pack(side=tk.LEFT)

    right_frame = ttk.Frame(root, padding=(10, 0, 0, 0))
    right_frame.grid(row=0, column=1, sticky='nsew', pady=10, padx=(10,10))
    right_frame.grid_rowconfigure(1, weight=1); right_frame.grid_columnconfigure(0, weight=1)

    header_frame = ttk.Frame(right_frame); header_frame.grid(row=0, column=0, sticky='ew', pady=(20, 10))
    ttk.Label(header_frame, text="Download Queue", style='Bold.TLabel').pack(side=tk.LEFT)

    tree_frame = ttk.Frame(right_frame, style='Content.TFrame', relief='solid', borderwidth=1)
    tree_frame.grid(row=1, column=0, sticky='nsew')
    
    columns = ('query', 'filename', 'status')
    queue_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', style='Treeview')
    queue_tree.heading('query', text='Your Query'); queue_tree.heading('filename', text='Downloaded File'); queue_tree.heading('status', text='Status')
    queue_tree.column('query', width=250, anchor='w'); queue_tree.column('filename', width=400, anchor='w'); queue_tree.column('status', width=120, anchor='center')
    queue_tree.pack(fill=tk.BOTH, expand=True)
    queue_tree.tag_configure('separator', background=BORDER_COLOR)

    def process_gui_updates():
        try:
            while not update_queue.empty():
                message = update_queue.get_nowait()
                msg_type, item_id, data = message
                if msg_type == 'update_status':
                    status = data
                    if '_' not in item_id:
                        if queue_tree.exists(item_id): queue_tree.set(item_id, 'status', status)
                    else:
                        original_query = item_id.split('_')[0]
                        if item_id.endswith('_1') and queue_tree.exists(original_query):
                            queue_tree.set(original_query, 'status', status)
                        elif queue_tree.exists(item_id):
                            queue_tree.set(item_id, 'status', status)
                elif msg_type == 'add_sub_task':
                    filename, status = data
                    original_query = item_id.split('_')[0]
                    if not queue_tree.exists(original_query): continue
                    if item_id.endswith('_1'):
                        queue_tree.set(original_query, 'filename', filename); queue_tree.set(original_query, 'status', status)
                    else:
                        if not queue_tree.exists(item_id):
                            queue_tree.insert(original_query, 'end', iid=item_id, values=('', filename, status))
                elif msg_type == 'add_separator':
                    separator_id = f"sep_{item_id}"
                    if not queue_tree.exists(separator_id):
                        queue_tree.insert('', 'end', iid=separator_id, tags=('separator',))
        except tk.TclError:
            # Window has been destroyed, stop processing updates
            return
        finally:
            # Only schedule next update if window still exists
            try:
                root.after(100, process_gui_updates)
            except tk.TclError:
                # Window destroyed, stop scheduling updates
                pass

    def on_closing():
        """Handles the window close event with proper Selenium cleanup."""
        try:
            # Save settings first (quick operation)
            current_path = get_current_full_path()
            if current_path:
                settings['last_selected'] = current_path
            save_settings(settings)
        except:
            pass  # Don't let settings save failure prevent shutdown
        
        try:
            # Signal the downloader thread to stop (but don't wait)
            download_queue.put(None)
        except:
            pass
        
        try:
            # Destroy the window
            root.destroy()
        except:
            pass
        
        # FORCE EXIT - Multiple methods to ensure termination
        if getattr(sys, 'frozen', False):
            # PyInstaller build - use most aggressive shutdown methods
            pid = os.getpid()
            
            # Method 1: Kill process by PID (most reliable)
            try:
                if platform.system() == "Windows":
                    # Windows: Use taskkill with force flag
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                 timeout=1, capture_output=True)
                elif platform.system() == "Darwin":  # macOS
                    # macOS: Use kill -9
                    subprocess.run(['kill', '-9', str(pid)], 
                                 timeout=1, capture_output=True)
                else:  # Linux
                    subprocess.run(['kill', '-9', str(pid)], 
                                 timeout=1, capture_output=True)
            except:
                pass
            
            # Method 2: Python's immediate exit
            try:
                os._exit(0)
            except:
                pass
            
            # Method 3: Alternative exit codes
            try:
                os._exit(1)
            except:
                pass
                
            # Method 4: Last resort - raise SystemExit
            try:
                raise SystemExit(0)
            except:
                pass
        else:
            # Development mode - graceful shutdown
            try:
                sys.exit(0)
            except:
                os._exit(0)


    root.protocol("WM_DELETE_WINDOW", on_closing)
    process_gui_updates()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()
    except Exception as e:
        print(f"GUI error: {e}")
        on_closing()

if __name__ == "__main__":
    # Global cleanup function
    def cleanup_on_exit():
        """Cleanup function to ensure proper shutdown."""
        try:
            download_queue.put(None)  # Signal worker to stop
        except:
            pass
        if getattr(sys, 'frozen', False):
            os._exit(0)  # Force exit for PyInstaller
    
    # Register cleanup for various exit scenarios
    atexit.register(cleanup_on_exit)
    
    # Handle Ctrl+C and other signals
    def signal_handler(signum, frame):
        cleanup_on_exit()
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        downloader_thread = threading.Thread(target=downloader_worker)
        downloader_thread.daemon = True # Ensure the thread is a daemon
        downloader_thread.start()
        create_gui(downloader_thread)
    except KeyboardInterrupt:
        cleanup_on_exit()
    except Exception as e:
        print(f"Error starting application: {e}")
        cleanup_on_exit()
