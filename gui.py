import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from converter import convert_pdf_to_md


# =========================
# THEME (wireframe purple)
# =========================
BG = "#FAF7FF"
PURPLE = "#8A2BE2"
PURPLE_DARK = "#6F1FD1"
PURPLE_SOFT = "#C9A7FF"
TEXT = "#3A2A54"
MUTED = "#7A6B94"
SUCCESS = "#22C55E"

FONT_TITLE = ("Consolas", 16, "bold")
FONT_H1 = ("Consolas", 18, "bold")
FONT_BODY = ("Consolas", 11)
FONT_SMALL = ("Consolas", 9)
FONT_BTN = ("Consolas", 11, "bold")


def human_size(num_bytes: int) -> str:
    step = 1024.0
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < step:
            return f"{size:.1f} {unit}"
        size /= step
    return f"{size:.1f} TB"


class UI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF2MD v1.0")
        self.root.geometry("820x520")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # State
        self.pdf_path: Path | None = None
        self.pdf_size: int = 0
        self.generated_md: Path | None = None

        # Progress simulation
        self._progress = 0
        self._progress_running = False

        # Main canvas (wireframe-like)
        self.c = tk.Canvas(self.root, width=820, height=520, bg=BG, highlightthickness=0)
        self.c.pack(fill="both", expand=True)

        self.center_x = 410
        self.top_y = 90

        self._draw_window_chrome()
        self._draw_static_title()

        # clickable zones ids
        self._dropzone_id = None
        self._dropzone_hit = None

        # buttons / widgets
        self.btn_main = None
        self.link_left = None
        self.link_right = None

        # status texts
        self.txt_substatus = None
        self.txt_success = None

        # progress bar items
        self.pb_line_bg = None
        self.pb_line_fg = None
        self.pb_label_left = None
        self.pb_label_right = None

        # initial screen
        self.screen_idle()

    # -----------------------
    # Drawing helpers
    # -----------------------
    def _draw_window_chrome(self):
        # top chrome line and small dots (mac style)
        self.c.create_rectangle(30, 20, 790, 70, outline=PURPLE_SOFT, width=2)
        self.c.create_oval(45, 38, 57, 50, fill="#FF5F57", outline="")
        self.c.create_oval(65, 38, 77, 50, fill="#FEBC2E", outline="")
        self.c.create_oval(85, 38, 97, 50, fill="#28C840", outline="")
        self.c.create_text(410, 44, text="PDF2MD v1.0", fill=MUTED, font=FONT_SMALL)

    def _draw_static_title(self):
        self.c.create_text(
            self.center_x, self.top_y,
            text="PDF Converter for Markdown",
            fill=PURPLE,
            font=FONT_H1
        )

    def _round_rect(self, x1, y1, x2, y2, r=16, **kwargs):
        # draw a rounded rectangle on canvas
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.c.create_polygon(points, smooth=True, **kwargs)

    def _clear_dynamic(self):
        # remove everything except chrome + title (we redraw dynamic via tags)
        self.c.delete("dyn")
        if self.btn_main:
            self.btn_main.destroy()
            self.btn_main = None
        if self.link_left:
            self.link_left.destroy()
            self.link_left = None
        if self.link_right:
            self.link_right.destroy()
            self.link_right = None

    def _draw_doc_icon(self, cx, cy, scale=1.0, color=PURPLE):
        # simple document icon
        w = int(34 * scale)
        h = int(44 * scale)
        x1 = cx - w // 2
        y1 = cy - h // 2
        x2 = cx + w // 2
        y2 = cy + h // 2

        self.c.create_rectangle(x1, y1, x2, y2, outline=color, width=2, tags="dyn")
        # folded corner
        self.c.create_line(x2 - 10, y1, x2, y1 + 10, fill=color, width=2, tags="dyn")
        self.c.create_line(x2 - 10, y1, x2 - 10, y1 + 10, fill=color, width=2, tags="dyn")
        self.c.create_line(x2 - 10, y1 + 10, x2, y1 + 10, fill=color, width=2, tags="dyn")

        # inner lines
        self.c.create_line(x1 + 6, y1 + 18, x2 - 6, y1 + 18, fill=color, width=2, tags="dyn")
        self.c.create_line(x1 + 6, y1 + 26, x2 - 6, y1 + 26, fill=color, width=2, tags="dyn")

    def _open_output_folder(self):
        out_dir = Path("output").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.system(f'explorer "{str(out_dir)}"')
        else:
            os.system(f'open "{str(out_dir)}"')

    # -----------------------
    # Screen states
    # -----------------------
    def screen_idle(self):
        self._progress_running = False
        self._clear_dynamic()

        # Dropzone
        x1, y1, x2, y2 = 170, 150, 650, 320
        self._round_rect(x1, y1, x2, y2, r=18, outline=PURPLE_SOFT, width=2, fill=BG, tags="dyn")

        # dashed outline inside
        self._round_rect(x1 + 12, y1 + 12, x2 - 12, y2 - 12, r=14,
                         outline=PURPLE_SOFT, width=2, fill="", tags="dyn")

        self.c.create_text(self.center_x, 185, text="Input Files PDF", fill=PURPLE, font=FONT_TITLE, tags="dyn")
        self.c.create_text(self.center_x, 212, text="Drag & drop or click to select", fill=MUTED, font=FONT_BODY, tags="dyn")
        self._draw_doc_icon(self.center_x, 260, scale=1.1, color=PURPLE)

        # clickable overlay
        if self._dropzone_hit:
            self.c.delete(self._dropzone_hit)
        self._dropzone_hit = self.c.create_rectangle(x1, y1, x2, y2, outline="", fill="", tags="dyn")
        self.c.tag_bind(self._dropzone_hit, "<Button-1>", lambda e: self._select_pdf())

        # footer tiny status like wireframe
        self.c.create_text(60, 485, text="Ready", fill=MUTED, font=FONT_SMALL, tags="dyn")
        self.c.create_text(770, 485, text="Online", fill=SUCCESS, font=FONT_SMALL, tags="dyn")

        # reset state
        self.pdf_path = None
        self.generated_md = None

    def screen_selected(self):
        self._progress_running = False
        self._clear_dynamic()

        if not self.pdf_path:
            self.screen_idle()
            return

        # File card
        x1, y1, x2, y2 = 210, 150, 610, 310
        self._round_rect(x1, y1, x2, y2, r=16, outline=PURPLE_SOFT, width=2, fill=BG, tags="dyn")

        self._draw_doc_icon(self.center_x, 205, scale=1.0, color=PURPLE)
        self.c.create_text(self.center_x, 245, text=self.pdf_path.name, fill=TEXT, font=FONT_BODY, tags="dyn")
        self.c.create_text(self.center_x, 270, text=human_size(self.pdf_size), fill=MUTED, font=FONT_SMALL, tags="dyn")

        # Main button: CONVERT
        self.btn_main = tk.Button(
            self.root,
            text="⚡ CONVERT",
            font=FONT_BTN,
            fg="white",
            bg=PURPLE,
            activebackground=PURPLE_DARK,
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._start_convert
        )
        self.btn_main.place(x=310, y=345, width=200, height=44)

        # Link: choose a different file
        self.link_left = tk.Label(self.root, text="Choose a different file", fg=PURPLE, bg=BG, font=FONT_SMALL, cursor="hand2")
        self.link_left.place(x=330, y=395)
        self.link_left.bind("<Button-1>", lambda e: self._select_pdf())

    def screen_converting(self):
        self._clear_dynamic()
        if not self.pdf_path:
            self.screen_idle()
            return

        # File card (same, with "CONVERTING...")
        x1, y1, x2, y2 = 210, 150, 610, 310
        self._round_rect(x1, y1, x2, y2, r=16, outline=PURPLE_SOFT, width=2, fill=BG, tags="dyn")

        self._draw_doc_icon(self.center_x, 205, scale=1.0, color=PURPLE_SOFT)
        self.c.create_text(self.center_x, 245, text=self.pdf_path.name, fill=PURPLE, font=FONT_BODY, tags="dyn")
        self.c.create_text(self.center_x, 275, text="CONVERTING...", fill=MUTED, font=FONT_SMALL, tags="dyn")

        # Progress bar row
        self.c.create_text(120, 370, text="PROCESSING", fill=PURPLE, font=FONT_SMALL, anchor="w", tags="dyn")
        self.pb_label_right = self.c.create_text(700, 370, text="0%", fill=PURPLE, font=FONT_SMALL, anchor="e", tags="dyn")

        # base line
        self.pb_line_bg = self.c.create_line(120, 392, 700, 392, fill=PURPLE_SOFT, width=4, tags="dyn")
        self.pb_line_fg = self.c.create_line(120, 392, 120, 392, fill=PURPLE, width=4, tags="dyn")

        # small dotted indicator (like wireframe)
        for i in range(10):
            self.c.create_line(360 + i * 10, 412, 365 + i * 10, 412, fill=PURPLE_SOFT, width=2, tags="dyn")

        # Start fake progress animation
        self._progress = 0
        self._progress_running = True
        self._tick_progress()

    def screen_success(self):
        self._progress_running = False
        self._clear_dynamic()

        if not self.generated_md:
            self.screen_idle()
            return

        # success label
        self.c.create_text(self.center_x, 135, text="● SUCCESS", fill=SUCCESS, font=FONT_BODY, tags="dyn")

        # file card (md)
        x1, y1, x2, y2 = 250, 165, 570, 320
        self._round_rect(x1, y1, x2, y2, r=16, outline=PURPLE_SOFT, width=2, fill=BG, tags="dyn")

        self._draw_doc_icon(self.center_x, 220, scale=1.0, color=PURPLE_SOFT)
        self.c.create_text(self.center_x, 262, text=self.generated_md.name, fill=TEXT, font=FONT_BODY, tags="dyn")

        try:
            size = self.generated_md.stat().st_size
            self.c.create_text(self.center_x, 287, text=human_size(size), fill=MUTED, font=FONT_SMALL, tags="dyn")
        except Exception:
            pass

        # Save File button (must allow user choose location)
        self.btn_main = tk.Button(
            self.root,
            text="⬇ Save File",
            font=FONT_BTN,
            fg="white",
            bg=PURPLE,
            activebackground=PURPLE_DARK,
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._save_as
        )
        self.btn_main.place(x=310, y=350, width=200, height=44)

        # bottom links: Convert another | Open folder
        self.link_left = tk.Label(self.root, text="Convert another", fg=PURPLE, bg=BG, font=FONT_SMALL, cursor="hand2")
        self.link_left.place(x=320, y=405)
        self.link_left.bind("<Button-1>", lambda e: self.screen_idle())

        self.link_right = tk.Label(self.root, text="Open folder", fg=PURPLE, bg=BG, font=FONT_SMALL, cursor="hand2")
        self.link_right.place(x=440, y=405)
        self.link_right.bind("<Button-1>", lambda e: self._open_output_folder())

    # -----------------------
    # Actions
    # -----------------------
    def _select_pdf(self):
        path = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self.pdf_path = Path(path)
        try:
            self.pdf_size = self.pdf_path.stat().st_size
        except Exception:
            self.pdf_size = 0

        # output default
        out_dir = Path("output")
        out_dir.mkdir(parents=True, exist_ok=True)
        self.generated_md = out_dir / f"{self.pdf_path.stem}.md"

        self.screen_selected()

    def _start_convert(self):
        if not self.pdf_path:
            messagebox.showerror("Error", "Select a PDF first.")
            return

        self.screen_converting()

        def worker():
            try:
                # convert (native pdf -> md)
                convert_pdf_to_md(self.pdf_path, self.generated_md)
                self.root.after(0, self._finish_success)
            except Exception as e:
                self.root.after(0, lambda: self._finish_error(e))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_success(self):
        self._progress_running = False
        self.screen_success()

    def _finish_error(self, e: Exception):
        self._progress_running = False
        messagebox.showerror("Conversion error", str(e))
        self.screen_selected()

    def _tick_progress(self):
        if not self._progress_running:
            return

        # simulate up to 92% then wait for completion
        if self._progress < 92:
            self._progress += 3

        # update bar
        x_start, x_end = 120, 700
        width = x_end - x_start
        x_fill = x_start + int(width * (self._progress / 100.0))

        # update canvas line positions
        self.c.coords(self.pb_line_fg, x_start, 392, x_fill, 392)
        self.c.itemconfig(self.pb_label_right, text=f"{self._progress}%")

        self.root.after(120, self._tick_progress)

    def _save_as(self):
        """Wireframe requirement: user chooses where to save the .md"""
        if not self.generated_md or not self.generated_md.exists():
            messagebox.showerror("Error", "Generated markdown file not found.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Markdown",
            defaultextension=".md",
            initialfile=self.generated_md.name,
            filetypes=[("Markdown", "*.md")]
        )
        if not save_path:
            return  # canceled

        try:
            target = Path(save_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            # Move file to chosen location
            self.generated_md.replace(target)
            self.generated_md = target

            messagebox.showinfo("Saved", "File saved successfully.")
        except Exception as e:
            messagebox.showerror("Save error", str(e))


def main():
    root = tk.Tk()
    UI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
