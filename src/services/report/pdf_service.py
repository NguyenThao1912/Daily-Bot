import os
import base64
from weasyprint import HTML, CSS

class PDFService:
    @staticmethod
    def _read_file_as_base64(path):
        """Helper to convert image to base64 for embedding in HTML"""
        try:
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"⚠️ Image read error ({path}): {e}")
            return None

    @staticmethod
    def _ensure_font():
        """Downloads Roboto font if missing to support Vietnamese."""
        font_dir = "assets/fonts"
        font_path = os.path.join(font_dir, "Roboto-Regular.ttf")
        
        if not os.path.exists(font_dir):
            os.makedirs(font_dir)
            
        if not os.path.exists(font_path):
            print("⬇️ Downloading Roboto font for Vietnamese support...")
            url = "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Regular.ttf"
            try:
                import requests
                response = requests.get(url)
                with open(font_path, "wb") as f:
                    f.write(response.content)
                print("✅ Font downloaded.")
            except Exception as e:
                print(f"⚠️ Font download failed: {e}. PDF might have font issues.")
                return None
        return os.path.abspath(font_path)

    @staticmethod
    def generate_report(results, chart_map=None):
        """
        Generates a PDF report using WeasyPrint with Premium Magazine Style.
        """
        if not chart_map:
            chart_map = {}

        # Ensure Font
        font_path = PDFService._ensure_font()
        font_css = ""
        if font_path:
            font_css = f"""
            @font-face {{
                font-family: 'Roboto';
                src: url('file://{font_path}');
            }}
            """

        # 1. Premium CSS Template
        css_string = f"""
            {font_css}
            @page {{
                size: A4 portrait;
                margin: 0;
            }}
            
            /* --- RESET & GLOBAL --- */
            * {{ box-sizing: border-box; }}

            body {{ 
                font-family: 'Roboto', sans-serif; 
                font-size: 10pt; 
                line-height: 1.5; 
                color: #2c3e50;
                background-color: #fff;
                margin: 0; 
                padding: 0;
                width: 210mm; /* Strict A4 Width */
            }}
            
            /* --- LAYOUT CONTAINERS --- */
            .cover-page {{
                width: 210mm;
                height: 297mm;
                position: relative;
                background-color: #2c3e50;
                color: white;
                padding: 20mm 20mm 40mm 20mm; /* Increased bottom padding to lift footer */
                overflow: hidden;
                page-break-after: always;
                display: flex; 
                flex-direction: column; 
                justify-content: space-between;
            }}

            .page-container {{
                width: 210mm;
                min-height: 297mm;
                padding: 20mm;
                position: relative;
                page-break-after: always;
                background-color: white;
            }}
            
            /* Prevent blank page at the end */
            .page-container:last-child {{
                page-break-after: avoid;
            }}

            .footer-counter {{
                position: absolute;
                bottom: 15mm;
                right: 20mm;
                font-size: 9pt;
                color: #bdc3c7;
            }}
            
            /* --- HEADINGS --- */
            h1.section-header {{ 
                color: #2c3e50; 
                font-size: 24pt; 
                text-transform: uppercase; 
                letter-spacing: 2px;
                border-bottom: 4px solid #e67e22; /* Amber Accent */
                padding-bottom: 10px; 
                margin-top: 0;
                margin-bottom: 30px;
                text-align: right;
            }}

            h2 {{ color: #e67e22; font-size: 14pt; margin-top: 20px; font-weight: 700; }}
            h3 {{ color: #34495e; font-size: 12pt; margin-bottom: 5px; font-weight: 600; }}
            
            /* --- CARD COMPONENT --- */
            .card {{ 
                background-color: #fdfdfd; 
                border: 1px solid #eee;
                border-left: 6px solid #e67e22; /* Amber Accent */
                border-radius: 6px;
                padding: 15px 20px; 
                margin-bottom: 25px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                break-inside: avoid;
            }}
            
            .item-title {{ 
                font-size: 13pt; 
                font-weight: 800; 
                color: #2c3e50; 
                margin-bottom: 15px;
                border-bottom: 1px solid #eee;
                padding-bottom: 8px;
                display: flex; align-items: center;
            }}
            
            /* --- METADATA & LABELS --- */
            .item-meta {{
                background: #f4f6f7;
                padding: 8px 12px;
                border-radius: 4px;
                border: 1px solid #ecf0f1;
                color: #555;
                font-size: 9pt;
                margin-bottom: 12px;
            }}
            
            .sub-label {{
                font-size: 8pt;
                font-weight: 700;
                color: #7f8c8d;
                text-transform: uppercase;
                margin-bottom: 4px;
                letter-spacing: 0.5px;
                margin-top: 10px;
                display: block;
            }}

            /* --- TABLES --- */
            table {{ 
                width: 100% !important; 
                border-collapse: collapse; 
                margin: 10px 0; 
                font-size: 9pt;
                table-layout: auto; 
            }}
            th {{ 
                background-color: #34495e; 
                color: #fff; 
                padding: 10px; 
                text-align: left; 
                font-weight: 600;
            }}
            td {{ 
                padding: 8px 10px; 
                border-bottom: 1px solid #ecf0f1; 
                vertical-align: top;
            }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            
            /* --- ALERTS --- */
            .alert {{ 
                background-color: #e8f8f5; /* Mint Green */
                color: #16a085; 
                padding: 10px; 
                border: 1px solid #d1f2eb; 
                border-radius: 4px; 
                margin-top: 15px; 
                font-size: 9pt;
                font-style: italic;
            }}

            /* --- CHARTS GRID --- */
            .chart-grid {{
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                gap: 15px;
                margin-top: 20px;
            }}
            .chart-item {{
                flex: 1 1 48%; /* 2 per row */
                background: #fff;
                border: 1px solid #e0e0e0;
                padding: 5px;
                border-radius: 4px;
                text-align: center;
                min-width: 300px;
            }}
            .chart-img {{
                max-width: 100%; height: auto; display: block;
            }}
            
            /* --- LINKS --- */
            a {{ color: #2980b9; text-decoration: none; font-weight: 500; }}
        """

        # 2. Build HTML Content
        from datetime import datetime
        import pytz
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_dt = datetime.now(vn_tz)
        date_str = now_dt.strftime('%d/%m/%Y')
        time_str = now_dt.strftime('%H:%M')

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Daily Report</title>
        </head>
        <body>
            <!-- COVER PAGE -->
            <div class="cover-page">
                <div>
                     <!-- Decorative Background Elements could go here -->
                     
                     <div style="position: relative; z-index: 1; border-left: 8px solid #e67e22; padding-left: 25px; margin-top: 80px;">
                        <h1 style="font-size: 42pt; margin: 0; line-height: 1.1; color: white; border: none;">DAILY</h1>
                        <h1 style="font-size: 42pt; margin: 0; line-height: 1.1; color: #e67e22; border: none;">BRIEFING</h1>
                        <p style="font-size: 14pt; margin-top: 15px; color: #bdc3c7; letter-spacing: 2px; text-transform: uppercase;">Intelligence Report</p>
                     </div>
                </div>

                <div style="text-align: right; z-index: 1;">
                    <div style="font-size: 28pt; font-weight: bold;">{date_str}</div>
                    <div style="font-size: 12pt; color: #bdc3c7;">UPDATED: {time_str}</div>
                    <div style="margin-top: 30px; border-top: 1px solid #7f8c8d; padding-top: 15px; font-size: 10pt;">
                        PREPARED BY <b>DAILY-BOT AI</b>
                    </div>
                </div>
            </div>
        """

        # Category Pages
        for index, res in enumerate(results):
            cat = res.get("category", "unknown").upper()
            content = res.get("content", "")
            
            # Start New Section
            html_body += f"""
            <div class="page-container">
                <h1 class="section-header">{cat}</h1>
                {content}
            """
            
            # Embed Chart(s)
            c_val = chart_map.get(res.get("category"))
            
            # Normalize to list
            c_paths = []
            if isinstance(c_val, list):
                c_paths = c_val
            elif isinstance(c_val, str):
                c_paths = [c_val]
                
            if c_paths:
                html_body += '<div class="chart-grid">'
                for c_path in c_paths:
                    if c_path and os.path.exists(c_path):
                        b64_img = PDFService._read_file_as_base64(c_path)
                        if b64_img:
                             html_body += f"""
                                <div class="chart-item">
                                    <img class="chart-img" src="data:image/png;base64,{b64_img}" />
                                </div>
                            """
                html_body += '</div>'
            
            # Page Number (excluding cover, so +1)
            html_body += f'<div class="footer-counter">Page {index + 1}</div>'
            html_body += "</div>" # Close page-container

        html_body += """
        </body>
        </html>
        """

        # 3. Generate PDF
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        file_date = now_dt.strftime('%Y-%m-%d')
        pdf_path = os.path.join(output_dir, f"Daily_Report_{file_date}.pdf")
        
        try:
            print("⏳ Rendering PDF with WeasyPrint (Premium Layout)...")
            HTML(string=html_body, base_url=".").write_pdf(
                pdf_path, 
                stylesheets=[CSS(string=css_string)]
            )
            return pdf_path
        except Exception as e:
             print(f"❌ PDF Write Error: {e}")
             return None
