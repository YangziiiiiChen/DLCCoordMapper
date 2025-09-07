import tkinter as tk
from tkinter import messagebox

class CoordinateInputDialog:
    def __init__(self, parent, frame_num, dlc_coord):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Enter World Coordinates for Frame {frame_num}")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        info_frame = tk.Frame(self.dialog)
        info_frame.pack(pady=10)

        tk.Label(info_frame, text=f"Calibration Point for Frame {frame_num}", font=("Arial", 12, "bold")).pack()
        tk.Label(info_frame, text=f"DeepLabCut Coordinate: ({dlc_coord[0]:.1f}, {dlc_coord[1]:.1f})",
                 font=("Arial", 10)).pack()
        if len(dlc_coord) > 2:
            tk.Label(info_frame, text=f"Likelihood: {dlc_coord[2]:.3f}",
                     font=("Arial", 10)).pack()
        tk.Label(info_frame, text="Please enter corresponding world coordinates (range: 0–75)",
                 font=("Arial", 10)).pack()

        coord_frame = tk.Frame(self.dialog)
        coord_frame.pack(pady=15)

        tk.Label(coord_frame, text="X coordinate:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.x_entry = tk.Entry(coord_frame, width=10, font=("Arial", 10))
        self.x_entry.grid(row=0, column=1, padx=5, pady=5)
        self.x_entry.focus()

        tk.Label(coord_frame, text="Y coordinate:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.y_entry = tk.Entry(coord_frame, width=10, font=("Arial", 10))
        self.y_entry.grid(row=1, column=1, padx=5, pady=5)

        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="Confirm", command=self.confirm,
                  width=8, font=("Arial", 10)).pack(side='left', padx=10)
        tk.Button(button_frame, text="Cancel", command=self.cancel,
                  width=8, font=("Arial", 10)).pack(side='left', padx=10)

        self.dialog.bind('<Return>', lambda e: self.confirm())
        self.dialog.bind('<Escape>', lambda e: self.cancel())

    def confirm(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            if not (0 <= x <= 75):
                messagebox.showerror("Error", "X coordinate must be in range 0–75", parent=self.dialog)
                return
            if not (0 <= y <= 75):
                messagebox.showerror("Error", "Y coordinate must be in range 0–75", parent=self.dialog)
                return
            self.result = (x, y)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers", parent=self.dialog)

    def cancel(self):
        self.result = None
        self.dialog.destroy()


class BodyPartSelectionDialog:
    def __init__(self, parent, bodyparts):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Body Part for Calibration")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        tk.Label(self.dialog, text="Please select a body part to use for calibration:",
                 font=("Arial", 12, "bold")).pack(pady=10)

        list_frame = tk.Frame(self.dialog)
        list_frame.pack(pady=10, padx=20, fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.listbox.yview)

        for bodypart in bodyparts:
            self.listbox.insert(tk.END, bodypart)
        if bodyparts:
            self.listbox.select_set(0)

        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="Confirm", command=self.confirm,
                 width=8, font=("Arial", 10)).pack(side='left', padx=10)
        tk.Button(button_frame, text="Cancel", command=self.cancel,
                 width=8, font=("Arial", 10)).pack(side='left', padx=10)

        self.listbox.bind('<Double-Button-1>', lambda e: self.confirm())
        self.dialog.bind('<Return>', lambda e: self.confirm())
        self.dialog.bind('<Escape>', lambda e: self.cancel())

    def confirm(self):
        selection = self.listbox.curselection()
        if selection:
            self.result = self.listbox.get(selection[0])
        self.dialog.destroy()

    def cancel(self):
        self.result = None
        self.dialog.destroy()
