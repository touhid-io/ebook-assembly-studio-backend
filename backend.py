import os
import io
import base64
import qrcode
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from jinja2 import Template
from weasyprint import HTML
from pypdf import PdfWriter, PdfReader

# --- Configuration Section ---
app = Flask(__name__)
# CORS is enabled to allow the frontend to communicate with this backend.
CORS(app)

# --- HTML Template (CSS & Structure) ---
# NOTE: Google Fonts link removed. Using system fonts installed via Dockerfile.
html_template_str = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <title>Ebook Template</title>
    <style>
        :root {
            --primary-color: #1a1a2e; --accent-color: #e94560; --premium-gold: #d4af37; --secondary-dark: #16213e;
            --paper-white: #fffef9; --cream: #faf8f3; --text-primary: #1a1a1a; --text-secondary: #4a4a4a; --text-muted: #707070; --text-light: #ffffff;
            
            /* UPDATED FONT STACKS FOR LINUX SERVER */
            --font-display: 'Liberation Serif', serif; 
            --font-serif: 'Liberation Serif', serif;
            --font-bengali: 'Noto Sans Bengali', 'Noto Sans Bengali UI', sans-serif;
            --font-sans: 'Liberation Sans', sans-serif;

            --title-xl: 72px; --title-lg: 48px; --title-md: 36px; --title-sm: 24px; --body-lg: 16px; --body-md: 14px; --body-sm: 12px; --caption: 11px; --micro: 9px;
            --space-1: 6px; --space-2: 12px; --space-3: 18px; --space-4: 24px; --space-5: 36px; --space-6: 48px;
            --safe-margin: 15mm; --shadow-soft: 0 2px 12px rgba(0,0,0,0.08); --shadow-medium: 0 4px 20px rgba(0,0,0,0.15);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        body { font-family: var(--font-bengali); margin: 0; padding: 0; background: #2d3142; }
        
        /* Force page breaks */
        .page { width: 210mm; height: 297mm; background: var(--paper-white); position: relative; overflow: hidden; page-break-after: always; }
        
        /* ----- FRONT COVER STYLES ----- */
        .front-cover { background: linear-gradient(165deg, var(--paper-white) 0%, var(--cream) 100%); display: flex; flex-direction: column; justify-content: space-between; border: 3mm solid var(--primary-color); outline: 2px solid var(--premium-gold); outline-offset: -10px; }
        .cover-header { padding: var(--space-5) var(--space-4) 0; text-align: center; }
        .publisher-badge { display: inline-block; background: var(--primary-color); color: var(--text-light); padding: 6px var(--space-3); font-family: var(--font-sans); font-size: var(--micro); font-weight: 700; letter-spacing: 3px; text-transform: uppercase; border-radius: 2px; }
        .genre-tag { display: block; margin-top: var(--space-2); font-family: var(--font-sans); font-size: var(--caption); color: var(--accent-color); font-weight: 600; letter-spacing: 2px; text-transform: uppercase; }
        .cover-main { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
        .decorative-icon { width: 60px; height: auto; margin-bottom: var(--space-3); opacity: 0.7; }
        .book-title-en { font-family: var(--font-display); font-size: var(--title-xl); font-weight: 700; line-height: 0.85; color: var(--primary-color); letter-spacing: -1px; text-transform: uppercase; margin: 0; }
        .book-title-bn { font-family: var(--font-bengali); font-size: var(--title-md); font-weight: 700; color: var(--accent-color); margin-top: var(--space-3); display: inline-block; padding: 0 var(--space-4); position: relative; }
        .book-title-bn::before, .book-title-bn::after { content: ''; position: absolute; top: 50%; width: 35px; height: 2px; background: var(--accent-color); }
        .book-title-bn::before { right: 100%; margin-right: 12px; } .book-title-bn::after { left: 100%; margin-left: 12px; }
        .subtitle { font-family: var(--font-serif); font-size: var(--body-md); color: var(--text-secondary); font-style: italic; margin-top: var(--space-2); max-width: 380px; }
        .author-block { margin-top: var(--space-5); }
        .author-label { font-family: var(--font-sans); font-size: var(--caption); color: var(--text-muted); text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; display: block; margin-bottom: 6px; }
        .author-name { font-family: var(--font-display); font-size: var(--title-sm); font-weight: 600; color: var(--text-primary); }
        .cover-footer { padding: 0 var(--space-4) var(--space-5); text-align: center; }
        .translator-info { padding-top: var(--space-3); border-top: 2px solid rgba(212, 175, 55, 0.2); }
        .translator-label { font-family: var(--font-sans); font-size: var(--micro); color: var(--accent-color); text-transform: uppercase; letter-spacing: 2.5px; font-weight: 700; display: block; margin-bottom: 6px; }
        .translator-name { font-family: var(--font-bengali); font-size: var(--body-lg); font-weight: 700; color: var(--primary-color); }

        /* ----- COPYRIGHT PAGE STYLES ----- */
        .copyright-page { padding: var(--safe-margin); display: flex; flex-direction: column; font-family: var(--font-sans); font-size: var(--body-sm); line-height: 1.6; color: var(--text-secondary); }
        .copyright-header { text-align: center; padding-bottom: var(--space-3); border-bottom: 1px solid rgba(0,0,0,0.1); margin-bottom: var(--space-3); }
        .copyright-title { font-family: var(--font-display); font-size: var(--title-sm); color: var(--primary-color); font-weight: 600; }
        .copyright-main { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
        .copyright-section h3 { font-family: var(--font-sans); font-size: var(--caption); font-weight: 700; color: var(--primary-color); text-transform: uppercase; margin-bottom: 6px; }
        .isbn-block { background: var(--cream); padding: var(--space-2); border-left: 3px solid var(--accent-color); margin-top: 5px; }
        .full-width { grid-column: 1 / -1; }
        .copyright-footer { text-align: center; padding-top: var(--space-3); border-top: 1px solid rgba(0,0,0,0.1); margin-top: var(--space-3); font-size: var(--caption); }

        /* ----- INDEX PAGE STYLES ----- */
        .index-page { padding: var(--safe-margin); display: flex; flex-direction: column; }
        .index-header { text-align: center; margin-bottom: var(--space-5); position: relative; }
        .index-title { font-family: var(--font-display); font-size: var(--title-lg); font-weight: 700; color: var(--primary-color); text-transform: uppercase; letter-spacing: 3px; }
        .index-subtitle { font-family: var(--font-sans); font-size: var(--body-sm); color: var(--accent-color); text-transform: uppercase; letter-spacing: 2px; font-weight: 600; }
        .toc-table { width: 100%; border-collapse: separate; border-spacing: 0 var(--space-2); }
        .toc-chapter { font-family: var(--font-bengali); font-size: var(--body-md); font-weight: 600; color: var(--text-primary); padding: var(--space-2) 0; position: relative; }
        .toc-chapter::after { content: ''; position: absolute; bottom: 8px; left: 0; right: 20px; height: 1px; background: repeating-linear-gradient(to right, var(--text-muted) 0, var(--text-muted) 3px, transparent 3px, transparent 7px); opacity: 0.3; }
        .toc-page { font-family: var(--font-display); font-size: var(--title-sm); font-weight: 700; color: var(--accent-color); text-align: right; white-space: nowrap; width: 70px; }

        /* ----- BACK COVER STYLES ----- */
        .back-cover { display: flex; flex-direction: column; background: linear-gradient(165deg, var(--cream) 0%, var(--paper-white) 100%); }
        .bio-section { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: var(--space-6) var(--space-5); text-align: center; }
        .author-photo { width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 4px solid var(--premium-gold); box-shadow: var(--shadow-medium); margin-bottom: var(--space-4); }
        .bio-name { font-family: var(--font-display); font-size: var(--title-sm); font-weight: 700; color: var(--primary-color); margin-bottom: 6px; text-transform: uppercase; }
        .bio-title-tag { font-family: var(--font-sans); font-size: var(--caption); color: var(--accent-color); text-transform: uppercase; letter-spacing: 2.5px; font-weight: 700; margin-bottom: var(--space-3); display: block; }
        .bio-description { font-family: var(--font-bengali); font-size: var(--body-md); line-height: 1.7; color: var(--text-secondary); max-width: 420px; margin: 0 auto; }
        .cta-section { background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-dark) 100%); padding: var(--space-5); display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); position: relative; }
        .cta-section::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, var(--accent-color) 0%, var(--premium-gold) 50%, var(--accent-color) 100%); }
        .cta-content { flex: 1; max-width: 65%; }
        .cta-headline { font-family: var(--font-display); font-size: var(--title-sm); font-weight: 700; color: var(--text-light); margin-bottom: var(--space-2); }
        .cta-text { font-family: var(--font-bengali); font-size: var(--body-md); color: rgba(255,255,255,0.85); line-height: 1.6; }
        .qr-container { background: white; padding: 10px; border-radius: 8px; width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; border: 2px solid var(--premium-gold); }
        .qr-container img { width: 100%; height: 100%; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="page front-cover">
        <div class="cover-header">
            <div class="publisher-badge">{{ publisher_badge }}</div>
            <span class="genre-tag">{{ genre_tag }}</span>
        </div>
        <div class="cover-main">
            <svg class="decorative-icon" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><path d="M50 10 L60 40 L90 40 L65 60 L75 90 L50 70 L25 90 L35 60 L10 40 L40 40 Z" fill="none" stroke="#d4af37" stroke-width="2"/></svg>
            <h1 class="book-title-en">{{ book_title_en }}</h1>
            <div class="book-title-bn">{{ book_title_bn }}</div>
            <p class="subtitle">{{ subtitle }}</p>
            <div class="author-block">
                <span class="author-label">{{ author_label }}</span>
                <div class="author-name">{{ author_name }}</div>
            </div>
        </div>
        <div class="cover-footer">
            <div class="translator-info">
                <span class="translator-label">{{ translator_label }}</span>
                <div class="translator-name">{{ translator_name }}</div>
            </div>
        </div>
    </div>

    <div class="page copyright-page">
        <div class="copyright-header">
            <h2 class="copyright-title">{{ cp_title }}</h2>
            <div class="copyright-subtitle">{{ cp_subtitle }}</div>
        </div>
        <div class="copyright-main">
            <div class="copyright-section">
                <h3>Original Work</h3>
                <p><strong>Author:</strong> {{ cp_original_author }}</p>
                <p><strong>Published:</strong> {{ cp_pub_year }}</p>
                <p><strong>Language:</strong> {{ cp_lang }}</p>
            </div>
            <div class="copyright-section">
                <h3>This Edition</h3>
                <p><strong>Translator:</strong> {{ cp_translator }}</p>
                <p><strong>Publisher:</strong> {{ cp_publisher }}</p>
                <p><strong>Edition:</strong> {{ cp_edition }}</p>
            </div>
            <div class="copyright-section full-width">
                <h3>ISBN Information</h3>
                <div class="isbn-block">
                    <p class="isbn-label">{{ cp_isbn_13 }}</p>
                    <p class="isbn-label">{{ cp_isbn_10 }}</p>
                </div>
            </div>
            <div class="copyright-section full-width">
                <h3>Copyright Notice</h3>
                <p>{{ cp_copyright_text }}</p>
            </div>
            <div class="copyright-section">
                <h3>Contact</h3>
                <p><strong>Web:</strong> {{ cp_contact_web }}</p>
                <p><strong>Email:</strong> {{ cp_contact_email }}</p>
            </div>
        </div>
        <div class="copyright-footer">
            <p>Designed & Published in Bangladesh</p>
        </div>
    </div>

    <div class="page index-page">
        <div class="index-header">
            <h2 class="index-title">{{ index_title }}</h2>
            <span class="index-subtitle">{{ index_subtitle }}</span>
        </div>
        <table class="toc-table">
            {% for item in toc_list %}
            <tr class="toc-row">
                <td class="toc-chapter">{{ item.title }}</td>
                <td class="toc-page">{{ item.page }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="page back-cover">
        <div class="bio-section">
            <img src="{{ bio_img_url }}" alt="Translator" class="author-photo">
            <h3 class="bio-name">{{ bio_name }}</h3>
            <span class="bio-title-tag">{{ bio_title_tag }}</span>
            <p class="bio-description">{{ bio_description }}</p>
        </div>
        <div class="cta-section">
            <div class="cta-content">
                <h3 class="cta-headline">{{ cta_headline }}</h3>
                <p class="cta-text">{{ cta_text }}</p>
            </div>
            <div class="qr-container">
                <img src="{{ qr_code }}" alt="QR">
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- Helper Functions ---

def generate_qr_base64(data):
    """Generates a QR code and returns it as a Base64 string."""
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

def to_bangla_num(n):
    """Converts English digits to Bangla digits for display."""
    return str(n).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))

# --- Main Logic as an API Endpoint ---

@app.route('/api/generate', methods=['POST'])
def generate_book():
    """Endpoint to handle ebook generation request from frontend."""
    try:
        # 1. Get Form Data
        form_data = request.form
        
        # Build Config from Request (Defaults provided for robustness)
        book_config = {
            "publisher_badge": form_data.get("publisher_badge", "THE HIDDEN SHELF CLASSICS"),
            "genre_tag": form_data.get("genre_tag", "Political Philosophy"),
            "book_title_en": form_data.get("book_title_en", "THE PRINCE"),
            "book_title_bn": form_data.get("book_title_bn", "দ্য প্রিন্স"),
            "subtitle": form_data.get("subtitle", "A Timeless Manual on Power, Politics, and Leadership"),
            "author_label": form_data.get("author_label", "Original Masterpiece By"),
            "author_name": form_data.get("author_name", "Niccolò Machiavelli"),
            "translator_label": form_data.get("translator_label", "Bengali Translation & Analysis By"),
            "translator_name": form_data.get("translator_name", "Touhidul Islam"),
            
            "cp_title": form_data.get("cp_title", "THE PRINCE"),
            "cp_subtitle": form_data.get("cp_subtitle", "দ্য প্রিন্স"),
            "cp_original_author": form_data.get("cp_original_author", "Niccolò Machiavelli"),
            "cp_pub_year": form_data.get("cp_pub_year", "1532"),
            "cp_lang": form_data.get("cp_lang", "Italian"),
            "cp_translator": form_data.get("cp_translator", "Touhidul Islam"),
            "cp_publisher": form_data.get("cp_publisher", "The Hidden Shelf"),
            "cp_edition": form_data.get("cp_edition", "February 2026"),
            "cp_isbn_13": form_data.get("cp_isbn_13", "ISBN-13: 978-0-123456-78-9"),
            "cp_isbn_10": form_data.get("cp_isbn_10", "ISBN-10: 0-123456-78-X"),
            "cp_copyright_text": form_data.get("cp_copyright_text", "© 2026 The Hidden Shelf. All rights reserved."),
            "cp_contact_web": form_data.get("cp_contact_web", "thehiddenshelf.com"),
            "cp_contact_email": form_data.get("cp_contact_email", "books@thehiddenshelf.com"),

            "index_title": "Index",
            "index_subtitle": "Strategic Breakdown",

            "bio_name": form_data.get("bio_name", "Touhidul Islam"),
            "bio_title_tag": form_data.get("bio_title_tag", "FOUNDER, THE HIDDEN SHELF"),
            "bio_description": form_data.get("bio_description", "A strategic thinker and content strategist."),
            
            "cta_headline": form_data.get("cta_headline", "Join the Discussion"),
            "cta_text": form_data.get("cta_text", "Join our exclusive strategic community."),
            "group_link": form_data.get("group_link", "https://facebook.com/groups/hidden-shelf")
        }

        # Handle Author Image
        if 'author_image' in request.files:
            img_file = request.files['author_image']
            img_bytes = img_file.read()
            book_config['bio_img_url'] = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode()
        else:
            # Use a placeholder if no image is provided
            book_config['bio_img_url'] = "https://placehold.co/300x300/e94560/ffffff?text=Author"

        # Generate QR Code
        book_config['qr_code'] = generate_qr_base64(book_config['group_link'])

        # 2. Process Chapters
        chapter_count = int(form_data.get('chapter_count', 0))
        toc_data = []
        uploaded_pdfs = []
        # Assume Front Matter takes 3 pages initially
        current_page_counter = 4 

        for i in range(chapter_count):
            file_key = f'chapter_{i}'
            title_key = f'chapter_{i}_title'
            
            if file_key in request.files:
                pdf_file = request.files[file_key]
                title = form_data.get(title_key, f"Chapter {i+1}")
                
                pdf_bytes = io.BytesIO(pdf_file.read())
                reader = PdfReader(pdf_bytes)
                num_pages = len(reader.pages)
                
                toc_data.append({
                    "title": title,
                    "page": to_bangla_num(current_page_counter)
                })
                
                uploaded_pdfs.append({"reader": reader, "title": title})
                current_page_counter += num_pages

        book_config['toc_list'] = toc_data

        # 3. Render HTML Template to PDF (Front & Back Matter)
        rendered_html = Template(html_template_str).render(**book_config)
        template_pdf_bytes = io.BytesIO()
        # WeasyPrint generates the PDF from the rendered HTML
        HTML(string=rendered_html).write_pdf(template_pdf_bytes)
        template_reader = PdfReader(template_pdf_bytes)
        total_template_pages = len(template_reader.pages)

        # 4. Merge Everything
        merger = PdfWriter()
        
        # Inject Metadata
        metadata = {
            "/Title": f"{book_config['book_title_en']} - {book_config['book_title_bn']}",
            "/Author": book_config["author_name"],
            "/Creator": "Ebook Assembly Studio Engine"
        }
        merger.add_metadata(metadata)

        # A. Add Front Matter (Cover, Copyright, Index)
        # We assume these are the first 3 pages of the generated template.
        pages_to_add_front = min(3, total_template_pages)
        for i in range(pages_to_add_front):
            merger.add_page(template_reader.pages[i])

        # B. Add Chapters
        for item in uploaded_pdfs:
            reader = item["reader"]
            chapter_title = item["title"]
            # Add outline item linking to the start of this chapter
            merger.add_outline_item(title=chapter_title, page_number=len(merger.pages))
            for page in reader.pages:
                merger.add_page(page)

        # C. Add Back Cover
        # It should be the last page of the generated template if total pages >= 4.
        if total_template_pages >= 4:
            merger.add_page(template_reader.pages[total_template_pages - 1])
        elif total_template_pages > pages_to_add_front:
             # Fallback: if somehow it's less than 4 but more than front matter, take the last available page.
             merger.add_page(template_reader.pages[-1])


        # 5. Return Output
        output_stream = io.BytesIO()
        merger.write(output_stream)
        output_stream.seek(0)

        return send_file(
            output_stream,
            as_attachment=True,
            download_name="Full_Customized_Book.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error during generation: {e}")
        # Return a JSON error response for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # This block is for local testing only. 
    # On Render, Gunicorn will handle execution.
    app.run(debug=True, port=5000)
