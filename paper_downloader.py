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

# Suppress SSL verification warnings for a cleaner user experience
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

SETTINGS_FILE = 'downloader_settings.json'

def sanitize_filename(filename):
    """
    Removes characters that are not allowed in filenames and limits length.
    """
    s = re.sub(r'[\\/*?:"<>|]', "", filename)
    return s[:200] # Limit filename length to avoid OS errors

# --- Thread-Safe Queues for Communication ---
download_queue = queue.Queue()
update_queue = queue.Queue()

def downloader_worker():
    """
    This function runs in a separate thread.
    It takes paper titles and a download path from the download_queue,
    searches Google Scholar, downloads PDFs, and sends status updates to the GUI.
    """
    while True:
        title_query, num_to_download, download_path = download_queue.get()
        
        try:
            update_queue.put(('update_status', title_query, 'Searching...'))
            
            search_query = f'{title_query}'
            search_url = f"https://scholar.google.com/scholar?hl=en&q={quote_plus(search_query)}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
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
                    
                    # FIX: Package filename and status into a single 'data' tuple
                    update_queue.put(('add_sub_task', sub_task_id, (filename, 'Downloading...')))
                    
                    try:
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
            # Add a message to insert a separator after the job is done
            update_queue.put(('add_separator', title_query, None))


        except Exception as e:
            print(f"Error processing '{title_query}': {e}")
            update_queue.put(('update_status', title_query, 'Error: Search Failed'))
        
        finally:
            download_queue.task_done()

def load_settings():
    """Loads paths and last selection from the JSON settings file."""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default settings if file doesn't exist or is corrupted
        default_path = os.getcwd()
        return {'paths': [default_path], 'last_selected': default_path}

def save_settings(settings):
    """Saves the current settings to the JSON file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def create_gui():
    """
    Creates and runs the main Tkinter GUI.
    """
    root = tk.Tk()
    root.title("Paper Downloader")
    root.geometry("1200x800")
    root.minsize(900, 600)
    
    # --- GLOBAL COLORS & FONTS ---
    BG_COLOR = '#f7f7f8'
    CONTENT_BG = '#ffffff'
    BORDER_COLOR = '#e5e5e5'
    ACCENT_COLOR = '#007aff'
    ACCENT_ACTIVE_COLOR = '#005ecb'
    FONT_FAMILY = 'Roboto' # A clean, modern font used by Google
    
    root.configure(bg=BG_COLOR)
    settings = load_settings()

    # --- Style Configuration ---
    style = ttk.Style(root)
    if 'aqua' in style.theme_names():
        style.theme_use('aqua')
    
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
    
    # Style for the separator
    style.configure("Separator.TFrame", background=BORDER_COLOR)


    # --- Main Layout ---
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # --- Left Sidebar ---
    left_frame = ttk.Frame(root, width=350, style='Content.TFrame')
    left_frame.grid(row=0, column=0, sticky='nsew', padx=(10,0), pady=10)
    left_frame.pack_propagate(False) # Prevent resizing

    sidebar_content = ttk.Frame(left_frame, padding=20, style='Content.TFrame')
    sidebar_content.pack(fill=tk.BOTH, expand=True)

    ttk.Label(sidebar_content, text="Enter Paper Titles", style='Bold.TLabel', background=CONTENT_BG).pack(anchor='w', pady=(0, 10))
    input_text = scrolledtext.ScrolledText(sidebar_content, wrap=tk.WORD, relief=tk.FLAT,
                                           borderwidth=1, highlightthickness=1, highlightbackground=BORDER_COLOR,
                                           font=(FONT_FAMILY, 13))
    input_text.pack(fill=tk.BOTH, expand=True)
    input_text.focus()

    # --- Path Management ---
    path_frame = ttk.Frame(sidebar_content, style='Content.TFrame')
    path_frame.pack(fill=tk.X, pady=(20, 5))
    ttk.Label(path_frame, text="Download to:", style='Content.TLabel').pack(side=tk.LEFT, padx=(0, 10))
    path_var = tk.StringVar(value=settings.get('last_selected', os.getcwd()))
    path_combobox = ttk.Combobox(path_frame, textvariable=path_var, values=settings['paths'])
    path_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

    path_buttons_frame = ttk.Frame(sidebar_content, style='Content.TFrame')
    path_buttons_frame.pack(fill=tk.X, pady=(5, 20))
    
    def open_selected_folder():
        path = path_var.get()
        if not os.path.isdir(path):
            messagebox.showwarning("Path Not Found", f"The folder does not exist:\n{path}")
            return
        if platform.system() == "Windows": os.startfile(path)
        elif platform.system() == "Darwin": subprocess.run(['open', path])
        else: subprocess.run(['xdg-open', path])

    def open_path_manager():
        manager_win = tk.Toplevel(root)
        manager_win.title("Manage Download Paths")
        manager_win.transient(root); manager_win.grab_set()

        listbox = tk.Listbox(manager_win, height=10, font=(FONT_FAMILY, 12))
        for p in settings['paths']: listbox.insert(tk.END, p)
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(manager_win)
        btn_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        def add_path():
            new_path = filedialog.askdirectory(title="Select a Folder")
            if new_path and new_path not in settings['paths']:
                settings['paths'].append(new_path); listbox.insert(tk.END, new_path)
                path_combobox['values'] = settings['paths']; save_settings(settings)

        def remove_path():
            selected_indices = listbox.curselection()
            if not selected_indices: return
            selected_path = listbox.get(selected_indices[0])
            if len(settings['paths']) > 1:
                settings['paths'].remove(selected_path); listbox.delete(selected_indices[0])
                path_combobox['values'] = settings['paths']
                if path_var.get() == selected_path: path_var.set(settings['paths'][0])
                save_settings(settings)
            else:
                messagebox.showwarning("Cannot Remove", "You must have at least one download path.")

        ttk.Button(btn_frame, text="Add...", command=add_path).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Remove", command=remove_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Done", command=manager_win.destroy).pack(side=tk.RIGHT)
    
    ttk.Button(path_buttons_frame, text="Manage", command=open_path_manager).pack(side=tk.LEFT, padx=5)
    ttk.Button(path_buttons_frame, text="Open", command=open_selected_folder).pack(side=tk.LEFT)
    

    # --- Add to Queue Controls ---
    controls_frame = ttk.Frame(sidebar_content, style='Content.TFrame')
    controls_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)

    max_downloads_frame = ttk.Frame(controls_frame, style='Content.TFrame')
    max_downloads_frame.pack(side=tk.LEFT)
    ttk.Label(max_downloads_frame, text="Max Downloads:", style='Content.TLabel').pack(side=tk.LEFT, padx=(0, 10))
    num_downloads_var = tk.IntVar(value=1)
    ttk.Spinbox(max_downloads_frame, from_=1, to=100, textvariable=num_downloads_var, width=5).pack(side=tk.LEFT)

    def add_papers_to_queue():
        titles = input_text.get("1.0", tk.END).strip().split('\n')
        num_to_download = num_downloads_var.get(); download_path = path_var.get()
        if not os.path.isdir(download_path):
            messagebox.showerror("Invalid Path", f"The selected download folder does not exist:\n{download_path}")
            return
        for title in titles:
            clean_title = title.strip()
            if clean_title and not queue_tree.exists(clean_title):
                queue_tree.insert('', 'end', iid=clean_title, values=(clean_title, '', 'Queued'), open=True)
                download_queue.put((clean_title, num_to_download, download_path))
        input_text.delete("1.0", tk.END)

    ttk.Button(controls_frame, text="Start", command=add_papers_to_queue).pack(side=tk.LEFT)
    # --- Right Main Content Area ---
    right_frame = ttk.Frame(root, padding=(10, 0, 0, 0))
    right_frame.grid(row=0, column=1, sticky='nsew', pady=10, padx=(10,10))
    right_frame.grid_rowconfigure(1, weight=1)
    right_frame.grid_columnconfigure(0, weight=1)

    # --- Header for the Queue ---
    header_frame = ttk.Frame(right_frame)
    header_frame.grid(row=0, column=0, sticky='ew', pady=(20, 10))
    ttk.Label(header_frame, text="Download Queue", style='Bold.TLabel').pack(side=tk.LEFT)

    # --- Treeview in its own frame for border ---
    tree_frame = ttk.Frame(right_frame, style='Content.TFrame', relief='solid', borderwidth=1)
    tree_frame.grid(row=1, column=0, sticky='nsew')
    
    columns = ('query', 'filename', 'status')
    queue_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', style='Treeview')
    queue_tree.heading('query', text='Your Query'); queue_tree.heading('filename', text='Downloaded File'); queue_tree.heading('status', text='Status')
    queue_tree.column('query', width=250, anchor='w'); queue_tree.column('filename', width=400, anchor='w'); queue_tree.column('status', width=120, anchor='center')
    queue_tree.pack(fill=tk.BOTH, expand=True)
    
    # Add a separator tag for styling
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
                    # FIX: Unpack the 'data' tuple correctly
                    filename, status = data
                    original_query = item_id.split('_')[0]
                    if not queue_tree.exists(original_query): continue
                    if item_id.endswith('_1'):
                        queue_tree.set(original_query, 'filename', filename); queue_tree.set(original_query, 'status', status)
                    else:
                        if not queue_tree.exists(item_id):
                            queue_tree.insert(original_query, 'end', iid=item_id, values=('', filename, status))
                
                elif msg_type == 'add_separator':
                    # Insert a non-selectable, styled item as a separator
                    separator_id = f"sep_{item_id}"
                    if not queue_tree.exists(separator_id):
                        queue_tree.insert('', 'end', iid=separator_id, tags=('separator',))


        finally:
            root.after(100, process_gui_updates)

    def on_closing():
        settings['last_selected'] = path_var.get()
        save_settings(settings)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    process_gui_updates()
    root.mainloop()

if __name__ == "__main__":
    downloader_thread = threading.Thread(target=downloader_worker, daemon=True)
    downloader_thread.start()
    create_gui()
