# EDI Gate

> A real-time EDI pre-validation portal that catches errors before files reach Sterling File Gateway.

---

## The Problem It Solves

Trading partners upload EDI files and wait **hours** to find out if their file was rejected.  
**EDI Gate** eliminates that wait — instant validation, instant feedback, instant routing.

---

## How It Works

Upload an EDI file → results in seconds.

| Step | What Happens |
|------|-------------|
| 🔍 **Detect**    | Reads the ST segment, identifies transaction type automatically |
| ✅ **Validate**  | Checks all mandatory segments against X12 EDI 004010 standards |
| 📄 **Transform** | Converts raw EDI → structured XML for downstream systems |
| 📨 **Acknowledge** | Generates a 997 FA — accepted or rejected with exact error details |
| 📬 **Route**     | Submits valid files to the trading partner's SFG mailbox |

---

## Supported Transactions

| Code | Transaction | Direction |
|------|-------------|-----------|
| 850  | Purchase Order    | Retailer → Supplier |
| 810  | Invoice           | Supplier → Retailer |
| 856  | Ship Notice / ASN | Supplier → Retailer |
| 830  | Planning Schedule | Retailer → Supplier |

---

## Demo

**Valid file** → summary, XML download, 997 FA, one-click SFG routing

**Invalid file** → exact errors listed by segment, rejected 997 FA generated
Missing mandatory segment: BEG (required by X12 850 spec)

Missing mandatory segment: DTM (required by X12 850 spec)

Missing mandatory segment: N1  (required by X12 850 spec)

Missing mandatory segment: CTT (required by X12 850 spec)

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

├── detector.py       identify transaction type from ST segment

├── validator.py      X12 mandatory segment and field validation

├── parser.py         extract business data per transaction type

├── xml_builder.py    EDI → XML transformation

├── acknowledger.py   generate 997 Functional Acknowledgment

└── mailbox.py        route files to SFG mailbox

---

**EDI Gate** — Built by Bharadwaj Kolli  
Enterprise Integration Architect | B2B EDI Specialist  
*Demonstrating hands-on EDI knowledge that most developers don't have.*