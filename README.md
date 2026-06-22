# EDI Gate — Retail EDI Validation Portal

> A real-time EDI pre-validation gateway built in Python — 
> catches errors before files reach Sterling File Gateway.

---

## The Problem It Solves

Suppliers send EDI files to retailers like Walmart and wait **hours** to find out if their file was rejected. This portal gives them **instant validation** — before the file ever enters the EDI pipeline.

---

## What It Does

Upload an EDI file → get results in seconds.

| Step | What Happens |
|------|-------------|
| 🔍 **Detect** | Reads the ST segment, identifies transaction type automatically |
| ✅ **Validate** | Checks all mandatory segments against Walmart X12 004010 spec |
| 📄 **Transform** | Converts raw EDI → structured XML for downstream systems |
| 📨 **Acknowledge** | Generates a 997 FA — accepted or rejected with error details |
| 📬 **Submit** | Routes valid files to the trading partner's SFG mailbox |

---

## Supported Transactions

| Code | Transaction | Direction |
|------|-------------|-----------|
| 850 | Purchase Order | Walmart → Supplier |
| 810 | Invoice | Supplier → Walmart |
| 856 | Ship Notice / ASN | Supplier → Walmart |
| 830 | Planning Schedule | Walmart → Supplier |

---

## Demo

**Valid file** — instant summary, XML download, 997 FA, one-click SFG submission

**Invalid file** — exact errors listed by segment, rejected 997 FA generated
Missing mandatory segment: BEG (required by Walmart 850 spec)

Missing mandatory segment: DTM (required by Walmart 850 spec)

Missing mandatory segment: N1  (required by Walmart 850 spec)

Missing mandatory segment: CTT (required by Walmart 850 spec)

---

## Tech Stack
Python 3.13 · Flask · X12 EDI 004010 · XML · HTML/CSS

---

## Quick Start

```bash
git clone https://github.com/bharadwajkolli2602/edi-processor.git
cd edi-processor
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`

---

## Project Structure
edi/

├── detector.py       identify transaction type

├── validator.py      Walmart spec validation

├── parser.py         extract business data

├── xml_builder.py    EDI → XML

├── acknowledger.py   generate 997 FA

└── mailbox.py        SFG mailbox submission

---

**EDI Gate** — Built by Bharadwaj Kolli  
Enterprise Integration Architect | B2B EDI Specialist  
*Demonstrating hands-on EDI knowledge that most developers don't have.*