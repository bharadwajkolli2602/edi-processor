# EDI File Processor 🔄

A Python-based EDI file processing tool that reads, parses, validates, and reports on EDI transactions — with professional logging and API notifications.

Built as a learning project by an Enterprise Integration Architect with 10 years of IBM Sterling B2B experience.

---

## 🚀 Features

- 📂 **File Detection** — Automatically scans input folder and identifies EDI, CSV, and unknown files
- 🔍 **EDI Parsing** — Parses key EDI segments (ISA, ST, BEG, PO1) and extracts structured data
- ✅ **Validation** — Validates required fields and catches malformed EDI files gracefully
- 📊 **Report Generation** — Creates timestamped reports in the `output/` folder
- 📋 **Professional Logging** — Logs all activity with timestamps and log levels to `logs/` folder
- 🔔 **API Notifications** — Sends processing summary to a webhook endpoint on completion
- 🛡️ **Error Handling** — Handles broken files, missing folders, and API failures without crashing

---

## 📁 Project Structure

```
edi-processor/
│
├── input/                  # Drop EDI files here for processing
│   └── orders.edi          # Sample EDI 850 Purchase Order
│
├── output/                 # Generated reports (timestamped)
│   └── report_YYYYMMDD_HHMMSS.txt
│
├── logs/                   # Processing logs (daily log files)
│   └── processor_YYYYMMDD.log
│
└── processor.py            # Main processor script
```

---

## ⚙️ How It Works

```
input/orders.edi
      ↓
  read_file()         → reads raw file content
      ↓
  parse_edi()         → extracts sender, receiver, PO number, line items
      ↓
  print_summary()     → logs structured summary to console & log file
      ↓
  write_report()      → saves report to output/ folder
      ↓
  send_notification() → sends JSON payload to webhook endpoint
```

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Requests](https://img.shields.io/badge/requests-2.34-FF6B35?style=flat-square)
![Logging](https://img.shields.io/badge/logging-built--in-4A90D9?style=flat-square)
![EDI](https://img.shields.io/badge/EDI-X12%20850-052FAD?style=flat-square)

---

## 📋 Supported EDI Segments

| Segment | Description | Extracted Fields |
|---------|-------------|-----------------|
| `ISA` | Interchange Header | Sender ID, Receiver ID |
| `ST` | Transaction Set | Transaction Type (850, 810, etc.) |
| `BEG` | Beginning of PO | PO Number |
| `PO1` | Line Item | Quantity, Unit, Price |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- `requests` library

### Installation

```bash
# Clone the repository
git clone https://github.com/bharadwajkolli2602/edi-processor.git
cd edi-processor

# Install dependencies
pip install requests

# Create required folders
mkdir input output logs
```

### Usage

```bash
# Drop your EDI files into the input/ folder
# Then run:
python processor.py
```

### Sample Output

```
2026-06-14 22:02:59 - INFO - Logging initialized
2026-06-14 22:02:59 - INFO - Scanning folder: input
2026-06-14 22:02:59 - INFO - Processing EDI file: orders.edi
2026-06-14 22:02:59 - INFO - ==================================================
2026-06-14 22:02:59 - INFO -   FILE     : orders.edi
2026-06-14 22:02:59 - INFO -   SENDER   : CATERPILLAR
2026-06-14 22:02:59 - INFO -   RECEIVER : TRUISTBANK
2026-06-14 22:02:59 - INFO -   TYPE     : 850
2026-06-14 22:02:59 - INFO -   PO NUM   : PO-12345
2026-06-14 22:02:59 - INFO -   ITEMS    : 1
2026-06-14 22:02:59 - INFO -   Qty: 100 EA @ $25.00
2026-06-14 22:02:59 - INFO - ==================================================
2026-06-14 22:02:59 - INFO -   PROCESSED : 1 files
2026-06-14 22:02:59 - INFO -   SKIPPED   : 0 files
2026-06-14 22:02:59 - INFO -   ERRORS    : 0 files
2026-06-14 22:02:59 - INFO - Notification sent successfully!
```

---

## 🔔 Webhook Notifications

On completion, the processor sends a JSON payload to a configured webhook:

```json
{
  "summary": "EDI Processing Complete",
  "timestamp": "2026-06-14 22:02:59",
  "results": {
    "processed": 1,
    "skipped": 0,
    "errors": 0,
    "report": "output/report_20260614_220259.txt"
  },
  "status": "SUCCESS"
}
```

To configure, update `WEBHOOK_URL` in `processor.py`:
```python
WEBHOOK_URL = "https://your-webhook-url-here"
```

---

## 🗺️ Roadmap

- [x] Phase 1 — Read & Parse EDI files
- [x] Phase 2 — Timestamped report generation
- [x] Phase 3 — Professional logging
- [x] Phase 4 — Error handling & processing stats
- [x] Phase 5 — API notifications via webhook
- [ ] Phase 6 — Support for 810 (Invoice) and 856 (ASN) transactions
- [ ] Phase 7 — Archive processed files automatically
- [ ] Phase 8 — REST API wrapper with Flask

---

## 👨‍💻 Author

**Bharadwaj Kolli** — Enterprise Integration Architect

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/bharadwaj-kolli-5b1a5576/)
[![GitHub](https://img.shields.io/badge/GitHub-Profile-100000?style=flat-square&logo=github)](https://github.com/bharadwajkolli2602)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-navy?style=flat-square)](https://bharadwajkolli2602.github.io)

---

> *"Built by someone who has spent 10 years working with EDI systems — now automating them with Python."*
