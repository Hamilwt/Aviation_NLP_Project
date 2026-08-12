"""Generate 'Aviation_NLP_Pipeline_Report.docx' — project summary + full implementation code."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Aviation_NLP_Pipeline_Report.docx"

CODE_FILES = [
    "app.py",
    "pipeline/paths.py",
    "pipeline/preprocess.py",
    "pipeline/fetch_data.py",
    "pipeline/train_model.py",
    "pipeline/rag_explainer.py",
    "pipeline/analyst.py",
    "requirements.txt",
]

ACCENT = RGBColor(0x0F, 0x6B, 0x9E)
CODE_BG = "F2F4F6"
CODE_FONT = "Consolas"


def shade(paragraph, fill):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def add_code_block(doc, code: str):
    for line in code.splitlines() or [""]:
        p = doc.add_paragraph()
        run = p.add_run(line if line else " ")
        run.font.name = CODE_FONT
        run.font.size = Pt(7.5)
        run.font.color.rgb = RGBColor(0x1F, 0x29, 0x33)
        pf = p.paragraph_format
        pf.space_after = Pt(0)
        pf.space_before = Pt(0)
        pf.line_spacing = 1.0
        pf.left_indent = Inches(0.08)
        shade(p, CODE_BG)
    # spacing after the block
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def main():
    doc = Document()

    # Base style
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)

    # ---------- Title ----------
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("Aviation NLP Safety Pipeline")
    r.font.size = Pt(26)
    r.font.bold = True
    r.font.color.rgb = ACCENT

    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run("Terminal-based NLP demonstration — ASRS dataset · TF-IDF · Logistic Regression · RAG")
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    d = doc.add_paragraph()
    d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = d.add_run("Implementation Code & Project Summary (DOCX)")
    r.font.size = Pt(11)
    r.font.italic = True

    doc.add_paragraph()

    # ---------- 1. Project summary ----------
    doc.add_heading("1. Project Summary", level=1)
    doc.add_paragraph(
        "This project is a terminal TUI (Textual) application that visually demonstrates a complete "
        "NLP pipeline for aviation safety, working on real NASA ASRS (Aviation Safety Reporting System) "
        "incident reports. Everything runs inside the terminal — no browser required."
    )

    doc.add_heading("1.1 Key features", level=2)
    for item in [
        "Numbered option menu (1–7): Fetch / View Datasets / Train / RAG Explainer / NLP Data Assistant / Pipeline Log / Exit.",
        "Visual progress: every operation shows a live stage label + progress bar ([███░░░] DOWNLOADING ASRS REPORTS ...).",
        "Smart caching: if the dataset (data/*.csv) or model (data/*.pkl) already exists, its contents are displayed in the terminal instead of being re-generated.",
        "Dataset viewer: lists every CSV in data/ in a dropdown and shows a narrative preview table plus the anomaly-category distribution.",
        "NLP data assistant (keyless, no LLM/API key): reports data-quality issues (duplicates, short reports, class imbalance) and a safety-criticality breakdown (CFIT, NMAC, loss of control, ...). It can also scan any pasted report narrative for high-risk phrases (TCAS RA, terrain, fatigue, fire, wake vortex).",
        "RAG explainer: classifies a new incident and retrieves the top-3 most similar historical reports (cosine similarity) as evidence with similarity bars.",
        "Headless CLI fallback: python app.py --fetch / --train / --explain <text> for scripting/CI.",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("1.2 Pipeline architecture", level=2)
    arch = (
        "data/real_asrs_dataset.csv   (NASA ASRS, 2000 cleaned reports, 16 anomaly categories)\n"
        "        |\n"
        "  1. FETCH   (Hugging Face -> clean -> primary anomaly category, top-15 + 'Other')\n"
        "        |\n"
        "  2. PREPROCESS  (lowercase + remove non-alphanumerics)\n"
        "        |\n"
        "  3. TRAIN   (TF-IDF bigrams -> Logistic Regression, balanced weights)\n"
        "        |         accuracy 46.2%, 16 classes, saved as data/*.pkl\n"
        "  4. RAG EXPLAINER (vectorize new report -> predict category ->\n"
        "                     cosine similarity vs 2000 reports -> top-3 evidence)\n"
        "        |\n"
        "  5. NLP DATA ASSISTANT (pandas insights: quality audit + safety criticality)"
    )
    add_code_block(doc, arch)

    doc.add_heading("1.3 Results", level=2)
    for item in [
        "Dataset: 2,000 real ASRS reports downloaded from Hugging Face (elihoole/asrs-aviation-reports), reduced from 807 multi-label strings to 16 tractable primary anomaly classes.",
        "Model accuracy: 46.2% (weighted avg F1 0.47) with TF-IDF + Logistic Regression — a solid baseline given the very noisy, imbalanced aviation narratives (class imbalance e.g. ATC issues 446 vs altitude overshoot 15).",
        "RAG explainer: sample ILS/misheard-altitude report correctly predicted as 'Deviation - Altitude Excursion From Assigned Altitude' with 3 historical evidence spans.",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("1.4 How to run", level=2)
    add_code_block(
        doc,
        "pip install -r requirements.txt\n"
        "python app.py                          # interactive TUI (numbered menu)\n"
        "python app.py --fetch                  # headless: download/reuse dataset\n"
        "python app.py --train                  # headless: train model\n"
        'python app.py --explain "engine fire right after takeoff"   # headless explain',
    )

    # ---------- 2. Project structure ----------
    doc.add_heading("2. Project Structure", level=1)
    add_code_block(
        doc,
        "Aviation_NLP_Project/\n"
        "├── app.py                 TUI entry point (Textual) + headless CLI\n"
        "├── pipeline/\n"
        "│   ├── paths.py           data/ layout, artifact discovery, defaults\n"
        "│   ├── fetch_data.py      step 1: download/clean ASRS dataset\n"
        "│   ├── preprocess.py      shared domain preprocessing\n"
        "│   ├── train_model.py     step 2: TF-IDF + LogisticRegression training\n"
        "│   ├── rag_explainer.py   step 3: classify + semantic evidence retrieval\n"
        "│   └── analyst.py         NLP data assistant (quality & safety analysis)\n"
        "├── data/                  artifacts (datasets *.csv, models *.pkl)\n"
        "├── requirements.txt       textual, pandas, scikit-learn, datasets, joblib\n"
        "└── README.md",
    )
    doc.add_paragraph(
        "scikit-learn appears in requirements.txt because the training step uses its "
        "TfidfVectorizer, LogisticRegression, train_test_split and classification_report, "
        "and the RAG step uses its cosine_similarity."
    )

    # ---------- 3. Implementation code ----------
    doc.add_heading("3. Implementation Code", level=1)
    doc.add_paragraph(
        "Complete source of every file in the project. Each code block is rendered in "
        "monospace (Consolas) with a shaded background for readability."
    )
    for rel in CODE_FILES:
        path = ROOT / rel
        doc.add_heading(f"3.{CODE_FILES.index(rel) + 1}  {rel}", level=2)
        add_code_block(doc, path.read_text(encoding="utf-8"))

    # ---------- 4. Dependencies ----------
    doc.add_heading("4. Dependencies", level=1)
    add_code_block(
        doc,
        "textual>=8.2        Terminal UI framework (progress bars, tables, menus)\n"
        "pandas>=2.2         Dataframes for dataset processing & assistant analysis\n"
        "scikit-learn>=1.5   TF-IDF, LogisticRegression, cosine similarity, metrics\n"
        "datasets>=3.0       Hugging Face dataset downloader\n"
        "joblib>=1.4         Model & vectorizer pickling",
    )

    doc.add_paragraph()
    end = doc.add_paragraph()
    end.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = end.add_run("— End of report —")
    r.font.italic = True
    r.font.color.rgb = RGBColor(0x9A, 0xA0, 0xAA)

    doc.save(OUT)
    print(f"Created: {OUT}")


if __name__ == "__main__":
    main()