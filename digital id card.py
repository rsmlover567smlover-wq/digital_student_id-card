import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
import os
import json
import hashlib
import datetime
import random
import string

# ─────────────────────────────────────────────
#  DATA STORE  (simple JSON file)
# ─────────────────────────────────────────────
DATA_FILE = "students.json"
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_uid():
    return "STU" + "".join(random.choices(string.digits, k=7))

# ─────────────────────────────────────────────
#  QR CODE GENERATION
# ─────────────────────────────────────────────
def make_qr(text, size=150):
    qr = qrcode.QRCode(version=1, box_size=4, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a2463", back_color="white").convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    return img

# ─────────────────────────────────────────────
#  ID CARD IMAGE GENERATOR
# ─────────────────────────────────────────────
def make_id_card_image(student: dict, width=520, height=300):
    card = Image.new("RGB", (width, height), "#0a2463")

    # gradient-like side stripe
    stripe = Image.new("RGB", (12, height), "#3e92cc")
    card.paste(stripe, (0, 0))

    draw = ImageDraw.Draw(card)

    # header bar
    draw.rectangle([12, 0, width, 52], fill="#1b4f8a")
    draw.text((24, 8),  "SMART COLLEGE",  fill="#f0c040", font=None)
    draw.text((24, 28), "Digital Student Identity Card", fill="#c9d6df", font=None)

    # UID barcode-like text
    draw.text((width - 160, 14), f"ID: {student['uid']}", fill="#f0c040", font=None)

    # divider
    draw.line([(12, 53), (width, 53)], fill="#3e92cc", width=1)

    # QR code
    qr_img = make_qr(json.dumps({
        "uid": student["uid"],
        "name": student["name"],
        "roll": student["roll"],
        "dept": student["dept"],
        "year": student["year"],
    }), size=130)
    card.paste(qr_img, (width - 148, 65))
    draw.text((width - 148, 200), "Scan to Verify", fill="#8eb8c9", font=None)

    # student info
    y = 68
    fields = [
        ("Name",       student["name"]),
        ("Roll No",    student["roll"]),
        ("Department", student["dept"]),
        ("Year",       student["year"]),
        ("Email",      student["email"]),
        ("Phone",      student["phone"]),
    ]
    for label, value in fields:
        draw.text((24, y),      f"{label}:", fill="#8eb8c9", font=None)
        draw.text((120, y),     value,       fill="#ffffff",  font=None)
        y += 22

    # validity
    draw.rectangle([12, height - 36, width, height], fill="#1b4f8a")
    today = datetime.date.today()
    expiry = today.replace(year=today.year + 1)
    draw.text((24, height - 25),
              f"Valid From: {today}   |   Valid Until: {expiry}   |   Issued by: Smart College",
              fill="#c9d6df", font=None)

    return card


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class StudentIDApp(tk.Tk):
    DARK   = "#0d1b2a"
    MID    = "#1b2d42"
    ACCENT = "#3e92cc"
    GOLD   = "#f0c040"
    TEXT   = "#e8e8e8"
    SUBTEXT= "#8eb8c9"

    def __init__(self):
        super().__init__()
        self.title("Digital Student ID Card System")
        self.geometry("960x640")
        self.configure(bg=self.DARK)
        self.resizable(False, False)

        self.students = load_data()
        self._qr_photo  = None   # keep reference
        self._card_photo = None

        self._build_ui()
        self._refresh_list()

    # ── UI SKELETON ──────────────────────────
    def _build_ui(self):
        # ── Left panel ──
        left = tk.Frame(self, bg=self.MID, width=320)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="🎓 Student ID System", bg=self.MID,
                 fg=self.GOLD, font=("Courier", 13, "bold")).pack(pady=(18, 4))
        tk.Label(left, text="Smart College", bg=self.MID,
                 fg=self.SUBTEXT, font=("Courier", 9)).pack()

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10, padx=12)

        # Search
        sf = tk.Frame(left, bg=self.MID)
        sf.pack(fill="x", padx=12)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._refresh_list())
        tk.Entry(sf, textvariable=self.search_var,
                 bg="#253545", fg=self.TEXT, insertbackground=self.TEXT,
                 relief="flat", font=("Courier", 10)).pack(fill="x", ipady=5)
        tk.Label(sf, text="🔍  Search by name / roll / dept",
                 bg=self.MID, fg=self.SUBTEXT, font=("Courier", 8)).pack(anchor="w")

        # List
        frame_list = tk.Frame(left, bg=self.MID)
        frame_list.pack(fill="both", expand=True, padx=12, pady=6)

        sb = tk.Scrollbar(frame_list, bg=self.MID)
        sb.pack(side="right", fill="y")

        self.listbox = tk.Listbox(frame_list, yscrollcommand=sb.set,
                                  bg="#111e2b", fg=self.TEXT,
                                  selectbackground=self.ACCENT,
                                  selectforeground="white",
                                  activestyle="none",
                                  relief="flat", font=("Courier", 10),
                                  borderwidth=0, highlightthickness=0)
        self.listbox.pack(fill="both", expand=True)
        sb.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Buttons
        btn_cfg = dict(bg=self.ACCENT, fg="white", relief="flat",
                       font=("Courier", 9, "bold"), cursor="hand2",
                       activebackground="#2a7ab5", activeforeground="white")
        brow = tk.Frame(left, bg=self.MID)
        brow.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(brow, text="＋ New",   command=self._open_form, **btn_cfg).pack(side="left",  expand=True, fill="x", padx=(0,3))
        tk.Button(brow, text="✎ Edit",   command=self._edit,      **btn_cfg).pack(side="left",  expand=True, fill="x", padx=3)
        tk.Button(brow, text="🗑 Delete", command=self._delete, **{**btn_cfg, "bg": "#c0392b", "activebackground": "#a93226"}).pack(side="left", expand=True, fill="x", padx=(3,0))

        # ── Right panel ──
        right = tk.Frame(self, bg=self.DARK)
        right.pack(side="right", fill="both", expand=True)

        # Card preview area
        self.card_label = tk.Label(right, bg=self.DARK, text="← Select a student to view their ID card",
                                   fg=self.SUBTEXT, font=("Courier", 11))
        self.card_label.pack(pady=(40, 8))

        # QR large view
        self.qr_label = tk.Label(right, bg=self.DARK)
        self.qr_label.pack(pady=4)

        self.info_label = tk.Label(right, bg=self.DARK, fg=self.SUBTEXT,
                                   font=("Courier", 9), justify="center")
        self.info_label.pack()

        # Export button
        self.export_btn = tk.Button(right, text="💾 Export ID Card as Image",
                                    command=self._export,
                                    bg=self.GOLD, fg=self.DARK,
                                    relief="flat", font=("Courier", 10, "bold"),
                                    cursor="hand2", activebackground="#d4a800",
                                    state="disabled")
        self.export_btn.pack(pady=16)

    # ── LIST HELPERS ─────────────────────────
    def _refresh_list(self):
        q = self.search_var.get().lower()
        self.listbox.delete(0, "end")
        self._filtered_uids = []
        for uid, s in self.students.items():
            if q in s["name"].lower() or q in s["roll"].lower() or q in s["dept"].lower():
                self.listbox.insert("end", f"  {s['name']}  [{s['roll']}]")
                self._filtered_uids.append(uid)

    def _selected_uid(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self._filtered_uids[sel[0]]

    # ── DISPLAY CARD ─────────────────────────
    def _on_select(self, _event=None):
        uid = self._selected_uid()
        if not uid:
            return
        s = self.students[uid]

        # Full ID card image
        card_img = make_id_card_image(s)
        self._card_photo = ImageTk.PhotoImage(card_img)
        self.card_label.config(image=self._card_photo, text="")

        # QR preview below
        qr_img = make_qr(json.dumps({"uid": s["uid"], "name": s["name"]}), size=110)
        self._qr_photo = ImageTk.PhotoImage(qr_img)
        self.qr_label.config(image=self._qr_photo)

        self.info_label.config(
            text=f"UID: {s['uid']}   |   Dept: {s['dept']}   |   Year: {s['year']}\n"
                 f"Email: {s['email']}   |   Phone: {s['phone']}"
        )
        self.export_btn.config(state="normal")
        self._current_card_img = card_img

    # ── EXPORT ───────────────────────────────
    def _export(self):
        uid = self._selected_uid()
        if not uid:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")],
            initialfile=f"ID_{self.students[uid]['roll']}.png"
        )
        if path:
            self._current_card_img.save(path)
            messagebox.showinfo("Exported", f"ID card saved to:\n{path}")

    # ── FORM (Add / Edit) ────────────────────
    def _open_form(self, uid=None):
        win = tk.Toplevel(self)
        win.title("Edit Student" if uid else "New Student")
        win.configure(bg=self.MID)
        win.geometry("400x420")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Student Details", bg=self.MID,
                 fg=self.GOLD, font=("Courier", 13, "bold")).pack(pady=(16, 4))

        fields = [
            ("Full Name",   "name"),
            ("Roll No",     "roll"),
            ("Department",  "dept"),
            ("Year",        "year"),
            ("Email",       "email"),
            ("Phone",       "phone"),
        ]

        vars_ = {}
        frm = tk.Frame(win, bg=self.MID)
        frm.pack(padx=24, pady=8, fill="x")
        existing = self.students.get(uid, {})

        for label, key in fields:
            tk.Label(frm, text=label, bg=self.MID, fg=self.SUBTEXT,
                     font=("Courier", 9), anchor="w").pack(fill="x")
            v = tk.StringVar(value=existing.get(key, ""))
            vars_[key] = v
            tk.Entry(frm, textvariable=v,
                     bg="#111e2b", fg=self.TEXT, insertbackground=self.TEXT,
                     relief="flat", font=("Courier", 10)).pack(fill="x", ipady=4, pady=(0, 6))

        def save():
            data = {k: v.get().strip() for k, v in vars_.items()}
            if not all(data.values()):
                messagebox.showwarning("Missing", "All fields are required.", parent=win)
                return
            if uid:
                data["uid"] = existing["uid"]
                self.students[uid] = data
            else:
                new_uid = generate_uid()
                data["uid"] = new_uid
                self.students[new_uid] = data
            save_data(self.students)
            self._refresh_list()
            win.destroy()

        tk.Button(win, text="💾 Save", command=save,
                  bg=self.ACCENT, fg="white", relief="flat",
                  font=("Courier", 10, "bold"), cursor="hand2").pack(pady=10, ipadx=20)

    def _edit(self):
        uid = self._selected_uid()
        if not uid:
            messagebox.showinfo("Select", "Please select a student first.")
            return
        self._open_form(uid=uid)

    def _delete(self):
        uid = self._selected_uid()
        if not uid:
            messagebox.showinfo("Select", "Please select a student first.")
            return
        name = self.students[uid]["name"]
        if messagebox.askyesno("Delete", f"Delete ID card for {name}?"):
            del self.students[uid]
            save_data(self.students)
            self._refresh_list()
            self.card_label.config(image="", text="← Select a student to view their ID card")
            self.qr_label.config(image="")
            self.info_label.config(text="")
            self.export_btn.config(state="disabled")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import qrcode
        from PIL import Image, ImageTk, ImageDraw
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "qrcode[pil]", "Pillow", "--quiet"])
        import qrcode
        from PIL import Image, ImageTk, ImageDraw

    app = StudentIDApp()
    app.mainloop()
