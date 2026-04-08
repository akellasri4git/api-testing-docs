"""
Convert Markdown documentation to professional PDF format
Uses ReportLab for high-quality PDF generation
"""

import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import blue, teal, green, gray
import markdown
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("MarkdownToPdf")


class MarkdownToPdfConverter:
    """Convert Markdown to professional PDF"""

    def __init__(self, markdown_path: str):
        self.markdown_path = Path(markdown_path)
        self.project_name = "SoapUI Project"

    def convert(self, output_path: str):
        """Convert markdown to PDF with professional formatting"""
        logger.info("Reading Markdown file...")

        with open(self.markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract project name from markdown
        project_match = re.search(r'\*\*Project Name:\*\* (.+)', content)
        if project_match:
            self.project_name = project_match.group(1).strip()

        logger.info("Converting Markdown to PDF...")

        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Get styles
        styles = getSampleStyleSheet()
        self._customize_styles(styles)

        # Build story (content elements)
        story = []

        # Add cover page
        story.extend(self._create_cover_page(styles))

        # Convert markdown content
        story.extend(self._convert_markdown_to_pdf(content, styles))

        # Build PDF
        doc.build(story)
        logger.info(f"✓ PDF saved to: {output_path}")

    def _customize_styles(self, styles):
        """Customize the styles for professional appearance"""
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=blue
        ))

        # Project title style
        styles.add(ParagraphStyle(
            name='ProjectTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=teal
        ))

        # Cover meta style
        styles.add(ParagraphStyle(
            name='CoverMeta',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=gray,
            spaceAfter=15
        ))

        # Section headers
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=blue
        ))

        # Subsection headers
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=teal
        ))

        # Code style
        styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=9,
            backColor=gray,
            borderColor=gray,
            borderWidth=1,
            borderPadding=8,
            leftIndent=10,
            spaceBefore=6,
            spaceAfter=6
        ))

        # Normal text with better formatting
        styles['Normal'].fontSize = 11
        styles['Normal'].leading = 14
        styles['Normal'].spaceAfter = 6

    def _create_cover_page(self, styles):
        """Create the cover page elements"""
        story = []

        # Add some vertical space
        story.append(Spacer(1, 2*inch))

        # Main title
        story.append(Paragraph("Understanding Document", styles['CustomTitle']))

        # Project name
        story.append(Paragraph(self.project_name, styles['ProjectTitle']))

        # Meta information
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Generated on " + datetime.now().strftime('%B %d, %Y'), styles['CoverMeta']))
        story.append(Paragraph("AI-Powered API Testing Documentation", styles['CoverMeta']))

        # Page break
        story.append(PageBreak())

        return story

    def _convert_markdown_to_pdf(self, content, styles):
        """Convert markdown content to PDF elements"""
        story = []

        # Split content into lines
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('# '):
                # H1
                title = line[2:].strip()
                story.append(Paragraph(title, styles['SectionHeader']))
                story.append(Spacer(1, 6))
                i += 1

            elif line.startswith('## '):
                # H2
                title = line[3:].strip()
                story.append(Paragraph(title, styles['SubsectionHeader']))
                story.append(Spacer(1, 6))
                i += 1

            elif line.startswith('### '):
                # H3
                title = line[4:].strip()
                story.append(Paragraph(title, styles['Heading4']))
                story.append(Spacer(1, 6))
                i += 1

            elif line.startswith('#### '):
                # H4 - handle code in headers
                title = line[5:].strip()
                # Remove backticks from headers
                title = title.replace('`', '')
                story.append(Paragraph(title, styles['Heading4']))
                story.append(Spacer(1, 6))
                i += 1

            elif line.startswith('*') and not line.startswith('**'):
                # Italic text
                italic_text = line[1:-1] if line.endswith('*') else line[1:]
                story.append(Paragraph(f"<i>{italic_text}</i>", styles['Normal']))
                story.append(Spacer(1, 6))
                i += 1

            elif line.startswith('- ') or line.startswith('• '):
                # List items - collect all consecutive list items
                list_items = []
                while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('• ')):
                    item_text = lines[i].strip()[2:].strip()
                    # Handle bold text in list items
                    item_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', item_text)
                    list_items.append(f"• {item_text}")
                    i += 1

                for item in list_items:
                    story.append(Paragraph(item, styles['Normal']))
                    story.append(Spacer(1, 2))

            elif line.startswith('```'):
                # Code block
                i += 1  # Skip opening ```
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # Skip closing ```

                code_text = '<br/>'.join(code_lines)
                story.append(Paragraph(code_text, styles['CodeBlock']))
                story.append(Spacer(1, 6))

            elif line.startswith('`') and line.endswith('`') and len(line) > 2:
                # Inline code
                code_text = line[1:-1]
                story.append(Paragraph(f"<code>{code_text}</code>", styles['Normal']))
                story.append(Spacer(1, 6))
                i += 1

            elif line.startswith('|') and i + 1 < len(lines) and lines[i + 1].strip().startswith('|'):
                # Table
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i])
                    i += 1

                # Skip separator line
                if i < len(lines) and re.match(r'^\s*\|[\s\-\|:]+\|\s*$', lines[i]):
                    i += 1

                for table_line in table_lines:
                    cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                    table_text = ' | '.join(cells)
                    story.append(Paragraph(table_text, styles['Normal']))
                    story.append(Spacer(1, 2))

            elif line and not line.startswith('---'):
                # Regular paragraph - handle bold text
                para_lines = [line]
                i += 1

                # Accumulate paragraph lines
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('#') and not lines[i].strip().startswith('-') and not lines[i].strip().startswith('•') and not lines[i].strip().startswith('*') and not lines[i].strip().startswith('```') and not lines[i].strip().startswith('|') and not lines[i].strip().startswith('`'):
                    para_lines.append(lines[i].strip())
                    i += 1

                paragraph_text = ' '.join(para_lines)

                # Handle markdown formatting
                paragraph_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', paragraph_text)  # Bold
                paragraph_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', paragraph_text)  # Italic
                paragraph_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', paragraph_text)  # Inline code

                if paragraph_text.strip():
                    story.append(Paragraph(paragraph_text, styles['Normal']))
                    story.append(Spacer(1, 6))

            else:
                i += 1

        return story


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python md_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    converter = MarkdownToPdfConverter(input_file)
    converter.convert(output_file)