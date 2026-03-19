import os
import base64
from weasyprint import HTML, CSS

class PDFService:
    CATEGORY_LABELS = {
        "weather": "Weather",
        "calendar": "Calendar",
        "finance": "Finance",
        "news": "News",
        "trends": "Trends",
        "tech": "Technology",
    }

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

        section_count = len(results)

        # 1. Premium CSS Template
        css_string = f"""
            {font_css}

            :root {{
                --ink: #1f2937;
                --muted: #6b7280;
                --line: #dbe3ea;
                --soft: #f4f7fb;
                --panel: #ffffff;
                --brand: #c96b2c;
                --brand-deep: #8d4320;
                --brand-soft: #fff2e8;
                --accent: #0f766e;
                --warn-bg: #fff4db;
                --warn-line: #f2b94b;
                --alert-bg: #edf9f6;
                --alert-line: #57b39c;
            }}

            @page {{
                size: A4 portrait;
                margin: 16mm 16mm 18mm 18mm;

                @top-right {{
                    content: "Daily Briefing";
                    font-size: 8.5pt;
                    color: #94a3b8;
                    font-family: 'Roboto';
                    letter-spacing: 0.8px;
                }}

                @bottom-right {{
                    content: "Page " counter(page);
                    font-size: 8.5pt;
                    color: #94a3b8;
                    font-family: 'Roboto';
                }}
            }}

            @page cover {{
                margin: 0;
                @top-right {{ content: none; }}
                @bottom-right {{ content: none; }}
            }}

            * {{
                box-sizing: border-box;
            }}

            html {{
                color-adjust: exact;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            body {{
                font-family: 'Roboto', sans-serif; 
                font-size: 10pt;
                line-height: 1.58;
                color: var(--ink);
                background: #fff;
                margin: 0;
            }}

            p, ul, ol {{
                margin-top: 0;
            }}

            ul, ol {{
                padding-left: 18px;
            }}

            .report-shell {{
                padding: 0;
            }}

            .cover-page {{
                page: cover;
                width: 210mm;
                height: calc(297mm - 1px);
                position: relative;
                background:
                    radial-gradient(circle at top right, rgba(255,255,255,0.09), transparent 28%),
                    radial-gradient(circle at 15% 20%, rgba(255,214,179,0.18), transparent 22%),
                    linear-gradient(145deg, #15202b 0%, #1f2937 48%, #3b2c25 100%);
                color: white;
                padding: 22mm 20mm 18mm 20mm;
                overflow: hidden;
                break-after: page;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}

            .cover-page::before {{
                content: "";
                position: absolute;
                inset: auto -28mm -28mm auto;
                width: 120mm;
                height: 120mm;
                border-radius: 50%;
                background: rgba(201, 107, 44, 0.18);
            }}

            .cover-page::after {{
                content: "";
                position: absolute;
                inset: 18mm auto auto -20mm;
                width: 90mm;
                height: 6mm;
                background: linear-gradient(90deg, var(--brand), transparent);
                transform: rotate(-12deg);
                opacity: 0.8;
            }}

            .cover-grid {{
                position: relative;
                z-index: 1;
                display: flex;
                flex-direction: column;
                gap: 18mm;
                height: 100%;
            }}

            .cover-kicker {{
                display: inline-block;
                padding: 5px 10px;
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 999px;
                background: rgba(255,255,255,0.06);
                color: #f6d3bc;
                font-size: 9pt;
                letter-spacing: 1.3px;
                text-transform: uppercase;
            }}

            .cover-title {{
                margin: 0;
                max-width: 120mm;
                font-size: 34pt;
                line-height: 1.04;
                font-weight: 800;
                letter-spacing: -0.6px;
            }}

            .cover-title strong {{
                color: #ffbe8f;
            }}

            .cover-subtitle {{
                max-width: 118mm;
                margin: 8mm 0 0;
                color: #d6dee7;
                font-size: 12pt;
                line-height: 1.65;
            }}

            .cover-metrics {{
                display: flex;
                gap: 10mm;
                margin-top: 10mm;
            }}

            .cover-metric {{
                min-width: 36mm;
                padding: 9px 10px;
                border-radius: 12px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.08);
            }}

            .cover-metric-label {{
                display: block;
                font-size: 8pt;
                color: #d6dee7;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 4px;
            }}

            .cover-metric-value {{
                font-size: 12.5pt;
                font-weight: 700;
                color: #fff;
            }}

            .cover-footer {{
                position: relative;
                z-index: 1;
                display: flex;
                justify-content: space-between;
                align-items: end;
                gap: 12mm;
            }}

            .cover-stamp {{
                text-align: right;
            }}

            .cover-date {{
                font-size: 27pt;
                font-weight: 800;
                line-height: 1;
            }}

            .cover-updated {{
                margin-top: 4mm;
                font-size: 10pt;
                color: #d6dee7;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}

            .cover-credit {{
                max-width: 70mm;
                padding-top: 5mm;
                border-top: 1px solid rgba(255,255,255,0.24);
                color: #d6dee7;
                font-size: 10pt;
                line-height: 1.5;
            }}

            .content-section {{
                margin: 0 0 11mm;
                break-inside: auto;
                page-break-inside: auto;
            }}

            .section-frame {{
                border: 1px solid var(--line);
                border-radius: 18px;
                background:
                    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(249,251,253,0.98));
                overflow: visible;
                break-inside: auto;
                page-break-inside: auto;
            }}

            .section-topbar {{
                padding: 12px 14px 10px;
                border-bottom: 1px solid var(--line);
                background: linear-gradient(90deg, #fff7f1 0%, #ffffff 68%);
                break-after: avoid;
                page-break-after: avoid;
            }}

            h1.section-header {{ 
                color: var(--ink);
                font-size: 18pt;
                margin: 0;
                letter-spacing: 0.3px;
                font-weight: 800;
                text-transform: none;
            }}

            .section-kicker {{
                display: inline-block;
                margin-bottom: 6px;
                color: var(--brand);
                font-size: 8.5pt;
                text-transform: uppercase;
                letter-spacing: 1.4px;
                font-weight: 700;
            }}

            .section-content {{
                padding: 14px;
            }}

            h2 {{
                color: var(--brand-deep);
                font-size: 14pt;
                margin: 16px 0 8px;
                font-weight: 700;
            }}

            h3 {{
                color: var(--ink);
                font-size: 11.5pt;
                margin: 12px 0 6px;
                font-weight: 700;
            }}

            .card {{ 
                background: var(--panel);
                border: 1px solid var(--line);
                border-left: 5px solid var(--brand);
                border-radius: 14px;
                padding: 14px 16px;
                margin-bottom: 14px;
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
                break-inside: auto;
                page-break-inside: auto;
            }}

            .item-title {{ 
                font-size: 13pt;
                font-weight: 800;
                color: var(--ink);
                margin-bottom: 12px;
                border-bottom: 1px solid #edf2f7;
                padding-bottom: 9px;
                display: flex;
                align-items: center;
                gap: 7px;
            }}

            .item-meta {{
                background: var(--soft);
                padding: 8px 11px;
                border-radius: 10px;
                border: 1px solid #e9eef5;
                color: #4b5563;
                font-size: 8.7pt;
                margin-bottom: 12px;
            }}

            .item-content {{
                margin-bottom: 11px;
            }}

            .sub-label {{
                font-size: 7.9pt;
                font-weight: 700;
                color: var(--muted);
                text-transform: uppercase;
                margin-bottom: 4px;
                letter-spacing: 0.8px;
                margin-top: 8px;
                display: block;
            }}

            table {{ 
                width: 100% !important;
                border-collapse: collapse;
                margin: 10px 0 6px;
                font-size: 9pt;
                table-layout: auto;
                border: 1px solid #e8edf3;
                border-radius: 10px;
                overflow: visible;
            }}
            th {{ 
                background-color: #253444;
                color: #fff;
                padding: 9px 10px;
                text-align: left;
                font-weight: 600;
            }}
            td {{ 
                padding: 8px 10px;
                border-bottom: 1px solid #ecf0f1;
                vertical-align: top;
            }}
            tr:nth-child(even) {{ background-color: #fbfcfd; }}

            .alert {{ 
                background-color: var(--alert-bg);
                color: #0f6f61;
                padding: 10px 12px;
                border: 1px solid #d5efe8;
                border-left: 4px solid var(--alert-line);
                border-radius: 10px;
                margin-top: 12px;
                font-size: 9pt;
            }}

            .action-highlight {{
                background-color: var(--warn-bg);
                color: #8a4a09;
                border-left: 5px solid var(--warn-line);
                padding: 12px;
                margin-top: 12px;
                font-size: 9.5pt;
                border-radius: 10px;
            }}

            .chart-grid {{
                display: block;
                margin-top: 8px;
                break-inside: auto;
                page-break-inside: auto;
            }}

            .chart-item {{
                width: 100%;
                background: #fff;
                border: 1px solid var(--line);
                padding: 10px;
                border-radius: 14px;
                text-align: center;
                max-width: 100%;
                margin-bottom: 10px;
                break-inside: avoid;
                page-break-inside: avoid;
            }}

            .chart-img {{
                max-width: 100%;
                height: auto;
                display: block;
                border-radius: 8px;
            }}

            .chart-title {{
                margin: 0 0 8px;
                font-size: 9pt;
                font-weight: 700;
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 0.8px;
                text-align: left;
            }}

            .motto {{
                margin-top: 18px;
                padding: 10px 12px;
                border-radius: 10px;
                background: linear-gradient(90deg, #f8fafc, #fff7f1);
                border: 1px solid var(--line);
                color: #435266;
                font-size: 9pt;
            }}

            a {{
                color: #1769aa;
                text-decoration: none;
                font-weight: 500;
            }}

            hr {{
                border: none;
                border-top: 1px solid #e8edf3;
                margin: 10px 0;
            }}

            code {{
                font-size: 8.7pt;
                background: #f8fafc;
                padding: 1px 5px;
                border-radius: 5px;
                border: 1px solid #edf2f7;
            }}
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
            <div class="cover-page">
                <div class="cover-grid">
                    <div>
                        <span class="cover-kicker">Morning intelligence</span>
                        <h1 class="cover-title">Daily <strong>Briefing</strong></h1>
                        <p class="cover-subtitle">
                            Ban tin tong hop cho ngay moi, gom cac tin hieu ve tai chinh, thoi tiet,
                            xu huong, tin tuc va cong nghe duoc trinh bay theo huong de doc, de quyet dinh.
                        </p>

                        <div class="cover-metrics">
                            <div class="cover-metric">
                                <span class="cover-metric-label">Sections</span>
                                <span class="cover-metric-value">{section_count}</span>
                            </div>
                            <div class="cover-metric">
                                <span class="cover-metric-label">Timezone</span>
                                <span class="cover-metric-value">Asia/Ho_Chi_Minh</span>
                            </div>
                        </div>
                    </div>

                    <div class="cover-footer">
                        <div class="cover-credit">
                            Prepared by <b>Daily-Bot AI</b><br/>
                            Structured report for Telegram and PDF delivery.
                        </div>
                        <div class="cover-stamp">
                            <div class="cover-date">{date_str}</div>
                            <div class="cover-updated">Updated {time_str}</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="report-shell">
        """

        # Category Pages
        for res in results:
            raw_cat = res.get("category", "unknown")
            cat = raw_cat.upper()
            content = res.get("content", "")
            pretty_label = PDFService.CATEGORY_LABELS.get(raw_cat, raw_cat.title())
            
            html_body += f"""
            <div class="content-section">
                <div class="section-frame">
                    <div class="section-topbar">
                        <div class="section-kicker">Section</div>
                        <h1 class="section-header">{cat}</h1>
                    </div>
                    <div class="section-content">
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
                                    <div class="chart-title">{pretty_label} chart</div>
                                    <img class="chart-img" src="data:image/png;base64,{b64_img}" />
                                </div>
                            """
                html_body += '</div>'
            
            html_body += """
                    </div>
                </div>
            </div>
            """

        html_body += """
            </div>
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
            print("⏳ Rendering PDF with WeasyPrint (Standard Layout)...")
            HTML(string=html_body, base_url=".").write_pdf(
                pdf_path, 
                stylesheets=[CSS(string=css_string)]
            )
            return pdf_path
        except Exception as e:
             print(f"❌ PDF Write Error: {e}")
             return None
