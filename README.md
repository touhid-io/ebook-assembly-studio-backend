# 📚 Ebook Assembly Studio (Backend)

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production-success?style=for-the-badge)

**Ebook Assembly Studio** is a robust backend engine designed to automate the creation of high-fidelity, print-ready PDF ebooks. Built with **Flask** and **WeasyPrint**, it seamlessly merges raw PDF chapters with dynamically generated HTML front matter, supporting complex typography (including Bengali script), QR code generation and metadata injection.

---

## 🚀 Key Features

* **Dynamic Cover Generation:** Programmatically creates front/back covers and copyright pages using Jinja2 templates and CSS.
* **Bangla Typography Support:** Full support for complex scripts using `Noto Serif Bengali` and font subsets.
* **Smart PDF Merging:** Merges uploaded chapter PDFs while maintaining visual fidelity.
* **Interactive Navigation:** Automatically generates a clickable Table of Contents (TOC) and PDF bookmarks.
* **Metadata Injection:** Injects author, title, and publisher data directly into the PDF properties.
* **QR Code Integration:** Auto-generates QR codes for community groups or promotional links.

---

## 🛠 Tech Stack

* **Core Framework:** Python (Flask)
* **PDF Engine:** WeasyPrint (HTML to PDF), PyPDF (Merging & Metadata)
* **Templating:** Jinja2
* **Containerization:** Docker (Optimized for Render/Linux environments)

---

## 📂 Project Structure

```bash
ebook-assembly-studio-backend/
├── backend.py            # Main application entry point
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container configuration for Render
└── README.md             # Documentation
