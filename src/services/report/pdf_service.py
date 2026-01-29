import os
import base64
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

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
        Generates a PDF report using WeasyPrint.
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
                size: A4;
                margin: 2cm;
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 9pt;
                    color: #999;
                    font-family: 'Roboto';
                }}
                @bottom-left {{
                    content: "Daily Strategy Report";
                    font-size: 9pt;
                    color: #999;
                    font-family: 'Roboto';
                }}
            }}
            
            /* --- RESET & GLOBAL --- */
            * {{
                box-sizing: border-box;
            }}

            body {{ 
                font-family: 'Roboto', sans-serif; 
                font-size: 11pt; 
                line-height: 1.6; 
                color: #333;
                width: 100%;
            }}
            
            /* --- TYPOGRAPHY --- */
            h1 {{ 
                color: #1a252f; 
                font-size: 24pt; 
                text-transform: uppercase; 
                letter-spacing: 2px;
                border-bottom: 3px solid #3498db; 
                padding-bottom: 15px; 
                margin-top: 0;
            }}
            
            h2 {{ 
                color: #2980b9; 
                font-size: 16pt; 
                margin-top: 30px; 
                margin-bottom: 15px;
                font-weight: 700;
            }}
            
            /* --- COMPONENTS --- */
            .category-section {{ 
                break-after: always; 
                width: 100%;
            }}

            /* Modern Card Style */
            .card {{ 
                background-color: #fff; 
                border: 1px solid #e0e0e0;
                border-left: 5px solid #3498db; /* Blue Accent */
                border-radius: 4px;
                padding: 20px; 
                margin-bottom: 25px; 
                break-inside: avoid;
                box-decoration-break: clone;
                width: 100%;
            }}
            
            .item-title {{ 
                font-size: 13pt; 
                font-weight: bold; 
                color: #2c3e50; 
                margin-bottom: 15px;
                display: block;
                border-bottom: 1px solid #eee;
                padding-bottom: 8px;
            }}
            
            /* Professional Table */
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 15px; 
                font-size: 10pt;
                table-layout: fixed; /* Fix width to page */
            }}
            
            th {{ 
                background-color: #34495e; 
                color: #fff; 
                padding: 10px 12px; 
                text-align: left; 
                font-weight: 600;
                border: 1px solid #34495e;
                word-wrap: break-word; /* Prevent overflow */
            }}
            
            td {{ 
                padding: 10px 12px; 
                border: 1px solid #e0e0e0; 
                vertical-align: top;
                word-wrap: break-word; /* Prevent overflow */
                overflow-wrap: break-word;
            }}
            
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            /* Alert Box */
            .alert {{ 
                background-color: #fff8e1; 
                color: #856404; 
                padding: 12px; 
                border: 1px solid #ffeeba; 
                border-radius: 4px; 
                margin-top: 10px; 
                font-size: 10pt;
            }}
            
            /* Motto Footer */
            .motto {{ 
                text-align: center; 
                font-style: italic; 
                color: #7f8c8d; 
                margin-top: 50px; 
                padding-top: 20px; 
                border-top: 1px solid #eee; 
            }}
            
            .chart-container {{ 
                text-align: center; 
                margin: 30px 0; 
                break-inside: avoid; 
                padding: 10px;
                background: #fff;
                border: 1px solid #ddd;
            }}
            .chart-img {{ 
                max-width: 100%; 
                height: auto; 
            }}
            
            ul {{ margin: 0; padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
            
            /* Links */
            a {{ color: #2980b9; text-decoration: none; }}
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
            <!-- TITLE PAGE -->
            <div style="
                height: 90vh; 
                display: flex; 
                flex-direction: column; 
                justify-content: center; 
                align-items: center; 
                text-align: center; 
                border: 2px solid #34495e;
                padding: 40px;
                margin-top: 20px;
                break-after: always;
            ">
                <div style="font-size: 60px; margin-bottom: 20px;">📊</div>
                <h1 style="font-size: 28pt; border: none; margin-bottom: 10px; color: #2c3e50;">BÁO CÁO HÀNG NGÀY</h1>
                <h2 style="font-size: 16pt; border: none; color: #7f8c8d; font-weight: 300; margin-top: 0;">DAILY INTELLIGENCE BRIEFING</h2>
                
                <div style="margin-top: 60px; border-top: 2px solid #3498db; display: inline-block; padding-top: 20px; width: 50%;">
                    <h3 style="font-size: 24pt; margin: 0; color: #2c3e50;">{date_str}</h3>
                    <p style="color: #95a5a6; margin-top: 5px;">Cập nhật lúc: {time_str}</p>
                </div>

                <div style="margin-top: auto; color: #bdc3c7; font-size: 10pt;">
                    PREPARED BY <b>DAILY-BOT AI</b><br>
                    INTERNAL USE ONLY
                </div>
            </div>
        """

        # Category Pages
        for res in results:
            cat = res.get("category", "unknown").upper()
            content = res.get("content", "")
            
            # Start New Section
            html_body += f"""
            <div class="category-section">
                <h1>{cat} REPORT</h1>
                {content}
            """
            
            # Embed Chart
            c_path = chart_map.get(res.get("category"))
            if c_path and os.path.exists(c_path):
                b64_img = PDFService._read_file_as_base64(c_path)
                if b64_img:
                    html_body += f"""
                    <div class="chart-container">
                        <h3>Biểu đồ {cat}</h3>
                        <img class="chart-img" src="data:image/png;base64,{b64_img}" />
                    </div>
                    """
            
            html_body += "</div>" # Close category-section

        html_body += """
        </body>
        </html>
        """

        # 3. Generate PDF
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Filename with Date: Daily_Report_YYYY-MM-DD.pdf
        file_date = now_dt.strftime('%Y-%m-%d')
        pdf_path = os.path.join(output_dir, f"Daily_Report_{file_date}.pdf")
        
        try:
            print("⏳ Rendering PDF with WeasyPrint...")
            HTML(string=html_body, base_url=".").write_pdf(
                pdf_path, 
                stylesheets=[CSS(string=css_string)]
            )
            return pdf_path
        except Exception as e:
             print(f"❌ PDF Write Error: {e}")
             return None

