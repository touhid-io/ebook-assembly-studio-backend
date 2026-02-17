import os
import io
import base64
import qrcode
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from jinja2 import Template
from weasyprint import HTML
from pypdf import PdfWriter, PdfReader

app = Flask(__name__)
CORS(app)

# --- HTML Template (Table Layout for Stability) ---
html_template_str = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <title>Ebook Template</title>
    <style>
        /* Global Reset */
        @page { size: A4; margin: 0; padding: 0; }
        html, body { margin: 0; padding: 0; width: 210mm; height: 297mm; background-color: #2d3142; }
        
        :root {
            --primary-color: #1a1a2e; --accent-color: #e94560; --premium-gold: #d4af37;
            --paper-white: #fffef9; --cream: #faf8f3; --text-primary: #1a1a1a; --text-secondary: #4a4a4a;
            
            /* Linux Server Fonts (Render Compatible) */
            --font-display: 'Liberation Serif', serif;
            --font-bengali: 'Noto Sans Bengali', 'Lohit Bengali', 'Mukti Narrow', 'Siyam Rupali', sans-serif;
            --font-sans: 'Liberation Sans', sans-serif;
        }

        body { font-family: var(--font-bengali); }
        
        /* Page Container */
        .page { 
            width: 210mm; height: 297mm; background: var(--paper-white); 
            position: relative; overflow: hidden; page-break-after: always; 
        }

        /* --- FRONT COVER --- */
        .front-cover { 
            background: linear-gradient(165deg, var(--paper-white) 0%, var(--cream) 100%); 
            display: flex; flex-direction: column; justify-content: space-between; 
            border: 3mm solid var(--primary-color); 
            outline: 2px solid var(--premium-gold); outline-offset: -10px; 
            height: 297mm; 
        }
        .cover-header { text-align: center; padding-top: 40px; }
        .cover-footer { text-align: center; padding-bottom: 40px; }
        .cover-main { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
        
        .publisher-badge { background: var(--primary-color); color: #fff; padding: 6px 12px; font-size: 9px; font-weight: 700; letter-spacing: 3px; border-radius: 2px; }
        .book-title-en { font-family: var(--font-display); font-size: 64px; font-weight: 700; line-height: 1; color: var(--primary-color); margin: 0; text-transform: uppercase; }
        .book-title-bn { font-family: var(--font-bengali); font-size: 32px; font-weight: 700; color: var(--accent-color); margin-top: 20px; }
        
        /* --- COPYRIGHT PAGE (TABLE LAYOUT FIX) --- */
        .copyright-page { padding: 15mm; display: flex; flex-direction: column; height: 297mm; }
        
        .copyright-header { text-align: center; margin-bottom: 30px; border-bottom: 1px solid #ddd; padding-bottom: 20px; }
        .copyright-title { font-size: 24px; font-weight: 700; color: var(--primary-color); }
        
        /* Table Styles - The Nuclear Solution for Layout */
        .cp-table { width: 100%; border-collapse: collapse; margin-top: 10px; table-layout: fixed; }
        .cp-table td { vertical-align: top; padding: 10px; width: 50%; }
        
        .cp-section h3 { 
            font-family: var(--font-sans); font-size: 11px; font-weight: 700; 
            color: var(--primary-color); text-transform: uppercase; margin-bottom: 8px; 
            border-left: 3px solid var(--accent-color); padding-left: 8px; 
        }
        .cp-section p { font-size: 12px; line-height: 1.6; color: var(--text-secondary); margin-bottom: 4px; }
        
        .isbn-box { 
            background: var(--cream); padding: 15px; border-radius: 4px; 
            margin-top: 20px; text-align: center; border: 1px solid #eee;
        }
        
        .cp-footer { margin-top: auto; text-align: center; font-size: 10px; border-top: 1px solid #ddd; padding-top: 20px; }

        /* --- INDEX PAGE --- */
        .index-page { padding: 15mm; height: 297mm; }
        .index-header { text-align: center; margin-bottom: 40px; }
        .index-title { font-size: 48px; font-weight: 700; color: var(--primary-color); }
        .toc-table { width: 100%; border-collapse: collapse; }
        .toc-row td { padding: 12px 0; border-bottom: 1px dashed #ccc; font-size: 14px; font-weight: 600; }
        .toc-page { text-align: right; color: var(--accent-color); font-weight: 700; }

        /* --- BACK COVER --- */
        .back-cover { background: linear-gradient(165deg, var(--cream) 0%, var(--paper-white) 100%); height: 297mm; display: flex; flex-direction: column; }
        .bio-section { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 40px; }
        .author-photo { width: 140px; height: 140px; border-radius: 50%; border: 4px solid var(--premium-gold); margin-bottom: 20px; object-fit: cover; }
        .cta-section { background: var(--primary-color); padding: 40px; display: flex; align-items: center; justify-content: space-between; color: white; }
        .qr-container { background: white; padding: 10px; border-radius: 8px; }
        .qr-container img { width: 80px; height: 80px; }
    </style>
</head>
<body>

    <div class="page front-cover">
        <div class="cover-header">
            <div class="publisher-badge">{{ publisher_badge }}</div>
            <span style="display:block; margin-top:10px; font-size:11px; color:var(--accent-color); font-weight:600;">{{ genre_tag }}</span>
        </div>
        <div class="cover-main">
            <h1 class="book-title-en">{{ book_title_en }}</h1>
            <div class="book-title-bn">{{ book_title_bn }}</div>
            <p style="font-style:italic; margin-top:10px; color:var(--text-secondary);">{{ subtitle }}</p>
            <div style="margin-top:40px;">
                <span style="font-size:10px; text-transform:uppercase; letter-spacing:1px;">{{ author_label }}</span>
                <div style="font-size:24px; font-weight:600; color:var(--text-primary); margin-top:10px;">{{ author_name }}</div>
            </div>
        </div>
        <div class="cover-footer">
            <span style="font-size:10px; text-transform:uppercase; letter-spacing:1px; color:var(--accent-color);">{{ translator_label }}</span>
            <div style="font-size:16px; font-weight:700; color:var(--primary-color);">{{ translator_name }}</div>
        </div>
    </div>

    <div class="page copyright-page">
        <div class="copyright-header">
            <div class="copyright-title">{{ cp_title }}</div>
            <div style="color:var(--text-secondary);">{{ cp_subtitle }}</div>
        </div>
        
        <table class="cp-table">
            <tr>
                <td>
                    <div class="cp-section">
                        <h3>Original Work</h3>
                        <p><strong>Author:</strong> {{ cp_original_author }}</p>
                        <p><strong>Published:</strong> {{ cp_pub_year }}</p>
                        <p><strong>Language:</strong> {{ cp_lang }}</p>
                    </div>
                </td>
                <td>
                    <div class="cp-section">
                        <h3>This Edition</h3>
                        <p><strong>Translator:</strong> {{ cp_translator }}</p>
                        <p><strong>Publisher:</strong> {{ cp_publisher }}</p>
                        <p><strong>Edition:</strong> {{ cp_edition }}</p>
                    </div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="cp-section" style="margin-top:20px;">
                        <h3>Contact</h3>
                        <p><strong>Web:</strong> {{ cp_contact_web }}</p>
                        <p><strong>Email:</strong> {{ cp_contact_email }}</p>
                    </div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="isbn-box">
                        <p><strong>{{ cp_isbn_13 }}</strong></p>
                        <p>{{ cp_isbn_10 }}</p>
                    </div>
                </td>
            </tr>
            <tr>
                <td colspan="2" style="text-align:center; padding-top:30px;">
                     <div class="cp-section" style="border:none; padding:0;">
                        <h3>Copyright Notice</h3>
                        <p>{{ cp_copyright_text }}</p>
                     </div>
                </td>
            </tr>
        </table>

        <div class="cp-footer">
            Designed & Published in Bangladesh
        </div>
    </div>

    <div class="page index-page">
        <div class="index-header">
            <div class="index-title">{{ index_title }}</div>
            <div style="font-size:12px; letter-spacing:2px; text-transform:uppercase; color:var(--accent-color);">{{ index_subtitle }}</div>
        </div>
        <table class="toc-table">
            {% for item in toc_list %}
            <tr class="toc-row">
                <td>{{ item.title }}</td>
                <td class="toc-page">{{ item.page }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="page back-cover">
        <div class="bio-section">
            <img src="{{ bio_img_url }}" class="author-photo" alt="Author">
            <h3 style="font-size:24px; font-weight:700; margin-bottom:5px; color:var(--primary-color);">{{ bio_name }}</h3>
            <span style="font-size:11px; letter-spacing:2px; text-transform:uppercase; color:var(--accent-color); display:block; margin-bottom:15px;">{{ bio_title_tag }}</span>
            <p style="max-width:400px; line-height:1.6; font-size:14px; color:var(--text-secondary);">{{ bio_description }}</p>
        </div>
        <div class="cta-section">
            <div style="flex:1; padding-right:20px;">
                <h3 style="font-size:20px; font-weight:700; margin-bottom:10px;">{{ cta_headline }}</h3>
                <p style="font-size:13px; opacity:0.9;">{{ cta_text }}</p>
            </div>
            <div class="qr-container">
                <img src="{{ qr_code }}" alt="QR">
            </div>
        </div>
    </div>

</body>
</html>
"""

def generate_qr_base64(data):
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

def to_bangla_num(n):
    return str(n).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))

@app.route('/api/generate', methods=['POST'])
def generate_book():
    try:
        form_data = request.form
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

        if 'author_image' in request.files:
            img_file = request.files['author_image']
            img_bytes = img_file.read()
            book_config['bio_img_url'] = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode()
        else:
            book_config['bio_img_url'] = "https://placehold.co/300x300/e94560/ffffff?text=Author"

        book_config['qr_code'] = generate_qr_base64(book_config['group_link'])

        chapter_count = int(form_data.get('chapter_count', 0))
        toc_data = []
        uploaded_pdfs = []
        current_page_counter = 4 

        for i in range(chapter_count):
            file_key = f'chapter_{i}'
            title_key = f'chapter_{i}_title'
            if file_key in request.files:
                pdf_file = request.files[file_key]
                title = form_data.get(title_key, f"Chapter {i+1}")
                pdf_bytes = io.BytesIO(pdf_file.read())
                reader = PdfReader(pdf_bytes)
                uploaded_pdfs.append({"reader": reader, "title": title})
                toc_data.append({"title": title, "page": to_bangla_num(current_page_counter)})
                current_page_counter += len(reader.pages)

        book_config['toc_list'] = toc_data

        rendered_html = Template(html_template_str).render(**book_config)
        template_pdf_bytes = io.BytesIO()
        HTML(string=rendered_html).write_pdf(template_pdf_bytes)
        template_reader = PdfReader(template_pdf_bytes)
        total_template_pages = len(template_reader.pages)

        merger = PdfWriter()
        metadata = {
            "/Title": f"{book_config['book_title_en']} - {book_config['book_title_bn']}",
            "/Author": book_config["author_name"],
            "/Creator": "Ebook Assembly Studio Engine"
        }
        merger.add_metadata(metadata)

        pages_to_add_front = min(3, total_template_pages)
        for i in range(pages_to_add_front):
            merger.add_page(template_reader.pages[i])

        for item in uploaded_pdfs:
            reader = item["reader"]
            chapter_title = item["title"]
            merger.add_outline_item(title=chapter_title, page_number=len(merger.pages))
            for page in reader.pages:
                merger.add_page(page)

        if total_template_pages >= 4:
            merger.add_page(template_reader.pages[total_template_pages - 1])
        elif total_template_pages > pages_to_add_front:
             merger.add_page(template_reader.pages[-1])

        output_stream = io.BytesIO()
        merger.write(output_stream)
        output_stream.seek(0)

        return send_file(output_stream, as_attachment=True, download_name="Full_Customized_Book.pdf", mimetype='application/pdf')

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
