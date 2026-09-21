import os
import re
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# Check of config er is
try:
    import config
except ImportError:
    messagebox.showerror("Fout", "Hernoem 'config.example.py' naar 'config.py' en vul de paden in.")
    exit()

def clean_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def set_gui_state(state):
    # Schakel GUI elementen aan/uit tijdens het rippen
    start_btn.config(state=state)
    name_entry.config(state=state)
    year_dropdown.config(state="readonly" if state == "normal" else "disabled")
    browse_btn.config(state=state)

def run_rip_thread(cmd, movie_name, iso_path):
    try:
        subprocess.run(cmd, check=True)
        
        # Check of de ISO echt bestaat en gevuld is
        if os.path.isfile(iso_path) and os.path.getsize(iso_path) > 0:
            root.after(0, lambda: rip_finished(True, movie_name))
        else:
            root.after(0, lambda: rip_finished(False, "Geen geldig ISO-bestand aangemaakt."))
    except Exception as e:
        root.after(0, lambda: rip_finished(False, f"Fout tijdens het rippen:\n{e}"))

def rip_finished(success, info):
    set_gui_state("normal")
    if success:
        status_label.config(text="Status: Succes!", fg="green")
        messagebox.showinfo("Klaar", f"'{info}' succesvol opgeslagen.")
        name_entry.delete(0, tk.END)
        name_entry.focus()
    else:
        status_label.config(text="Status: Mislukt.", fg="red")
        messagebox.showerror("Fout", info)

def start_rip():
    movie_name = clean_filename(name_entry.get())
    movie_year = year_dropdown.get()
    output_base = dir_entry.get().strip()

    # Validatie
    if not movie_name or not movie_year or not output_base:
        messagebox.showerror("Fout", "Vul alle velden in.")
        return
        
    if not os.path.isfile(config.IMGBURN_PATH):
        messagebox.showerror("Fout", f"ImgBurn.exe niet gevonden op:\n{config.IMGBURN_PATH}")
        return

    # Map en ISO pad aanmaken
    folder_name = f"{movie_name} ({movie_year})"
    target_folder = os.path.join(output_base, folder_name)
    iso_path = os.path.join(target_folder, f"{folder_name}.iso")

    try:
        os.makedirs(target_folder, exist_ok=True)
    except OSError as e:
        messagebox.showerror("Fout", f"Kon map niet aanmaken:\n{e}")
        return

    if os.path.exists(iso_path):
        if not messagebox.askyesno("Bestaat al", "ISO overschrijven?"):
            return

    set_gui_state("disabled")
    status_label.config(text=f"Status: Rippen van '{movie_name}'...", fg="orange")
    
    # ImgBurn commandopdracht samenstellen
    cmd = [
        config.IMGBURN_PATH, "/MODE", "READ", "/SRC", config.DVD_DRIVE_LETTER, 
        "/DEST", iso_path, "/START", "/CLOSE", "/EJECT"
    ]
    
    # Start de achtergrondtaak
    t = threading.Thread(target=run_rip_thread, args=(cmd, movie_name, iso_path))
    t.daemon = True
    t.start()

def browse_directory():
    init_dir = dir_entry.get() if dir_entry.get() else config.OUTPUT_DIR
    selected_dir = filedialog.askdirectory(initialdir=init_dir)
    if selected_dir:
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, selected_dir)

# --- GUI Layout ---
root = tk.Tk()
root.title("DVD Ripper GUI")
root.geometry("500x320")

# Filmnaam
tk.Label(root, text="Filmnaam:", font=("Arial", 11, "bold")).pack(pady=(15, 2))
name_entry = tk.Entry(root, font=("Arial", 11), width=45)
name_entry.pack(pady=5)
name_entry.focus()

# Jaar
tk.Label(root, text="Jaar van uitgave:", font=("Arial", 11, "bold")).pack(pady=(10, 2))
current_year = datetime.now().year
years = [str(y) for y in range(current_year, 1950, -1)]
year_dropdown = ttk.Combobox(root, values=years, font=("Arial", 10), width=10, state="readonly")
year_dropdown.set(str(current_year))
year_dropdown.pack(pady=5)

# Uitvoermap
tk.Label(root, text="Hoofdmap voor films:", font=("Arial", 10)).pack(pady=(10, 2))
dir_frame = tk.Frame(root)
dir_frame.pack()
dir_entry = tk.Entry(dir_frame, font=("Arial", 9), width=45)
dir_entry.insert(0, config.OUTPUT_DIR)
dir_entry.pack(side=tk.LEFT, padx=5)

browse_btn = tk.Button(dir_frame, text="Bladeren...", command=browse_directory)
browse_btn.pack(side=tk.RIGHT)

# Status en Start
status_label = tk.Label(root, text="Status: Wacht op invoer...", font=("Arial", 10, "italic"), fg="gray")
status_label.pack(pady=(20, 5))

start_btn = tk.Button(root, text="Start Rip", font=("Arial", 12, "bold"), bg="#59CD5D", fg="white", padx=20, pady=5, command=start_rip)
start_btn.pack(pady=10)

root.mainloop()