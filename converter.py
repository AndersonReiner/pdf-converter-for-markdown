from pathlib import Path
import argparse

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions


def convert_pdf_to_md(input_pdf: Path, output_md: Path):
    if not input_pdf.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_pdf}")

    output_md.parent.mkdir(parents=True, exist_ok=True)

    # Pipeline para PDF NATIVO (sem OCR)
    options = PdfPipelineOptions()
    options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options)
        }
    )

    print(f"🔄 Convertendo PDF nativo: {input_pdf.name}")

    result = converter.convert(input_pdf)
    markdown = result.document.export_to_markdown()

    output_md.write_text(markdown, encoding="utf-8")

    print(f"✅ Markdown gerado: {output_md}")


def main():
    parser = argparse.ArgumentParser(
        description="Conversor PDF → Markdown (PDFs nativos | PT/EN)"
    )
    parser.add_argument("input_pdf", help="PDF de entrada (nativo)")
    parser.add_argument(
        "-o", "--output",
        help="Arquivo Markdown de saída (opcional)"
    )

    args = parser.parse_args()

    input_path = Path(args.input_pdf)
    output_path = (
        Path(args.output)
        if args.output
        else Path("output") / f"{input_path.stem}.md"
    )

    convert_pdf_to_md(input_path, output_path)


if __name__ == "__main__":
    main()
