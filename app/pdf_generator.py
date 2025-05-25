# backend/app/pdf_generator.py

import io
from fpdf import FPDF
from datetime import datetime

class ReportPDF(FPDF):
    def __init__(self, title="Relatório de Análise de Dados"):
        super().__init__()
        self.title = title
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.add_header()
        
    def add_header(self):
        # Configurar fonte e tamanho
        self.set_font("helvetica", "B", 16)
        # Título centralizado
        self.cell(0, 10, self.title, align="C", ln=True)
        # Data do relatório
        self.set_font("helvetica", "", 10)
        self.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", align="C", ln=True)
        # Linha separadora
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(5)
        
    def add_footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")
        
    def add_interaction(self, question, answer, code=None):
        # Pergunta
        self.set_font("helvetica", "B", 12)
        self.multi_cell(0, 7, "Pergunta:", ln=True)
        self.set_font("helvetica", "", 11)
        self.multi_cell(0, 7, question, ln=True)
        self.ln(3)
        
        # Resposta
        self.set_font("helvetica", "B", 12)
        self.multi_cell(0, 7, "Resposta:", ln=True)
        self.set_font("helvetica", "", 11)
        self.multi_cell(0, 7, answer, ln=True)
        self.ln(3)
        
        # Código (se existir)
        if code:
            self.set_font("helvetica", "B", 12)
            self.multi_cell(0, 7, "Código Gerado:", ln=True)
            self.set_font("courier", "", 9)
            # Fundo cinza claro para o código
            self.set_fill_color(240, 240, 240)
            self.multi_cell(0, 7, code, ln=True, fill=True)
            self.ln(3)
        
        # Separador entre interações
        self.ln(5)
        self.line(20, self.get_y(), self.w - 20, self.get_y())
        self.ln(8)

def generate_report_pdf(interactions, source_name="Dados"):
    """
    Gera um relatório PDF com as interações selecionadas.
    
    Args:
        interactions: Lista de dicionários com as interações (question, answer, code)
        source_name: Nome da fonte de dados (arquivo ou banco de dados)
        
    Returns:
        bytes: Conteúdo do PDF em bytes
    """
    # Criar PDF
    pdf = ReportPDF(f"Relatório de Análise - {source_name}")
    
    # Adicionar informações iniciais
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, f"Fonte de dados: {source_name}", ln=True)
    pdf.cell(0, 10, f"Total de interações: {len(interactions)}", ln=True)
    pdf.ln(5)
    
    # Adicionar cada interação
    for item in interactions:
        pdf.add_interaction(
            question=item["question"],
            answer=item["answer"],
            code=item.get("code")
        )
        
        # Verificar se precisa adicionar nova página para a próxima interação
        if pdf.get_y() > pdf.h - 40:
            pdf.add_page()
    
    # Obter o PDF como bytes
    pdf_bytes = io.BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)
    
    return pdf_bytes.getvalue()
