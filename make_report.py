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
    r = t.add_run("Aviation & Power-Grid Safety NLP Pipeline")
    r.font.size = Pt(26)
    r.font.bold = True
    r.font.color.rgb = ACCENT

    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run("Terminal-based NLP demonstration — NASA ASRS · NERC power grid · TF-IDF · SGD · RAG")
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
        "NLP pipeline for infrastructure safety, working on REAL incident data from two public domains: "
        "NASA ASRS aviation incident reports and NERC power-grid event analysis reports. Everything runs "
        "inside the terminal — no browser required."
    )

    doc.add_heading("1.1 Key features", level=2)
    for item in [
        "Numbered option menu (1–7): Fetch / View Datasets / Train / RAG Explainer / NLP Data Assistant / Pipeline Log / Exit.",
        "Visual progress: every operation shows a live stage label + progress bar driven by REAL work — rows streamed, documents NLTK-preprocessed, minibatches fitted ([███░░░] PREPROCESSING 412/2035 (NLTK)).",
        "Live data collection: option 1 LIVE-downloads real safety data every run — NASA ASRS reports (Hugging Face datasets-server) + 12 NERC event-analysis PDFs (parsed with pypdf, split with NLTK sentence tokenization), merged into one Domain-tagged dataset.",
        "Dataset viewer: lists every CSV in data/ in a dropdown and shows a narrative preview table (with domain) plus the anomaly-category distribution.",
        "NLP data assistant (keyless, no LLM/API key): reports data-quality issues (duplicates, short reports, class imbalance), a domain split (Aviation vs Power Grid) and a safety-criticality breakdown. It can also scan any pasted report narrative for high-risk phrases.",
        "RAG explainer: classifies a new incident (aviation or power-grid) and retrieves the top-3 most similar historical reports (cosine similarity) as evidence with similarity bars.",
        "Headless CLI fallback: python app.py --fetch / --train / --explain <text> for scripting/CI.",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("1.2 Pipeline architecture", level=2)
    arch = (
        "data/real_safety_dataset.csv   (NASA ASRS + NERC, ~3,700 domain-tagged reports)\n"
        "        |\n"
        "  1. FETCH   (live: ASRS datasets-server + NERC PDFs -> clean -> merge by Domain)\n"
        "        |\n"
        "  2. PREPROCESS  (NLTK tokenize -> stopword removal -> lemmatize, per-document)\n"
        "        |\n"
        "  3. TRAIN   (TF-IDF bigrams -> SGD/log-loss, balanced class weights,\n"
        "         |         minibatch partial_fit over 3 epochs, saved as data/*.pkl)\n"
        "  4. RAG EXPLAINER (vectorize new report -> predict category ->\n"
        "                     batch cosine similarity vs all reports -> top-3 evidence)\n"
        "        |\n"
        "  5. NLP DATA ASSISTANT (pandas insights: quality audit + domain + criticality)"
    )
    add_code_block(doc, arch)

    doc.add_heading("1.3 Results", level=2)
    for item in [
        "Dataset: ~3,700 cleaned reports — 2,000 NASA ASRS aviation narratives (expert anomaly labels from Events_Anomaly) + ~1,700 power-grid narratives extracted from 12 public NERC event-analysis PDFs.",
        "Model accuracy: ~68% weighted accuracy over 28 classes with TF-IDF + SGD/log-loss (aviation classes are noisy and imbalanced; power-grid classes like 'Northeast Blackout 2003' are cleanly separated).",
        "RAG explainer: aviation queries predict ATC/conflict categories with aviation evidence; power-grid queries predict NERC event categories (e.g. 'Power Grid - Northeast Snowstorm 2011') with grid-incident evidence — both with real similarity bars.",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("1.4 How to run", level=2)
    add_code_block(
        doc,
        "pip install -r requirements.txt\n"
        "python app.py                          # interactive TUI (numbered menu)\n"
        "python app.py --fetch                  # headless: live-download both domains\n"
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
        "│   ├── paths.py           data/ layout, live data-source URLs, defaults\n"
        "│   ├── fetch_data.py      step 1: live-download ASRS + NERC, merge by domain\n"
        "│   ├── preprocess.py      shared NLTK domain preprocessing\n"
        "│   ├── train_model.py     step 2: TF-IDF + SGD/log-loss minibatch training\n"
        "│   ├── rag_explainer.py   step 3: classify + batch semantic evidence retrieval\n"
        "│   └── analyst.py         NLP data assistant (quality & safety analysis)\n"
        "├── data/                  artifacts (datasets *.csv, models *.pkl)\n"
        "├── requirements.txt       textual, pandas, scikit-learn, datasets, joblib, nltk, pypdf\n"
        "└── README.md",
    )
    doc.add_paragraph(
        "scikit-learn appears in requirements.txt because the training step uses its "
        "TfidfVectorizer, SGDClassifier (log-loss, minibatch training), "
        "train_test_split and classification_report, and the RAG step uses its "
        "cosine_similarity."
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
        "scikit-learn>=1.5   TF-IDF, SGDClassifier, cosine similarity, metrics\n"
        "datasets>=3.0       Hugging Face datasets-server client (aviation source)\n"
        "joblib>=1.4         Model & vectorizer pickling\n"
        "nltk>=3.8           Tokenization, stopwords, lemmatization, sentence split\n"
        "pypdf>=4.0          NERC PDF text extraction (power-grid source)",
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