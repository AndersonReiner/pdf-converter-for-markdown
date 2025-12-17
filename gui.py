import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from converter import convert_pdf_to_md


class PdfToMarkdownGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF → Markdown Converter")
        self.root.geometry("600x250")
        self.root.resizable(False, False)

        self.pdf_path = tk.StringVar()
        self.md_path = tk.StringVar()
        self.status = tk.StringVar(value="Aguardando ação...")

        self.build_layout()

    def build_layout(self):
        padding = {"padx": 10, "pady": 8}

        # PDF input
        tk.Label(self.root, text="Arquivo PDF:").grid(row=0, column=0, sticky="w", **padding)
        tk.Entry(self.root, textvariable=self.pdf_path, width=55).grid(row=0, column=1, **padding)
        tk.Button(self.root, text="Selecionar", command=self.select_pdf).grid(row=0, column=2, **padding)

        # Markdown output
        tk.Label(self.root, text="Saída Markdown:").grid(row=1, column=0, sticky="w", **padding)
        tk.Entry(self.root, textvariable=self.md_path, width=55).grid(row=1, column=1, **padding)
        tk.Button(self.root, text="Salvar como", command=self.select_output).grid(row=1, column=2, **padding)

        # Convert button
        tk.Button(
            self.root,
            text="Converter",
            width=20,
            command=self.convert
        ).grid(row=2, column=1, pady=15)

        # Status
        tk.Label(self.root, textvariable=self.status, fg="blue").grid(
            row=3, column=0, columnspan=3, pady=10
        )

    def select_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            self.pdf_path.set(file_path)
            default_output = Path("output") / (Path(file_path).stem + ".md")
            self.md_path.set(str(default_output))

    def select_output(self):
        file_path = filedialog.asksaveasfilename(
            title="Salvar Markdown",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md")]
        )
        if file_path:
            self.md_path.set(file_path)

    def convert(self):
        pdf = self.pdf_path.get()
        md = self.md_path.get()

        if not pdf or not md:
            messagebox.showerror("Erro", "Selecione o PDF e o arquivo de saída.")
            return

        try:
            self.status.set("Convertendo...")
            self.root.update_idletasks()

            convert_pdf_to_md(Path(pdf), Path(md))

            self.status.set("Conversão concluída com sucesso!")
            messagebox.showinfo("Sucesso", "PDF convertido para Markdown.")
        except Exception as e:
            self.status.set("Erro durante a conversão.")
            messagebox.showerror("Erro", str(e))


def main():
    root = tk.Tk()
    app = PdfToMarkdownGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
