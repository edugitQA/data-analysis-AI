import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface PDFGeneratorProps {
  sessionId: string;
  selectedInteractions: string[];
  history: Array<{
    id: string;
    question: string;
    answer: string;
    code: string | null;
  }>;
  apiUrl: string;
  onToggleInteraction: (id: string) => void;
}

const PDFGenerator: React.FC<PDFGeneratorProps> = ({
  sessionId,
  selectedInteractions,
  history,
  apiUrl,
  onToggleInteraction,
}) => {
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleGeneratePDF = async () => {
    if (selectedInteractions.length === 0) {
      setError('Selecione pelo menos uma interação para gerar o PDF.');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      // Converter 'current' para o ID real da interação atual
      const interactionIds = selectedInteractions.map(id => 
        id === 'current' ? history.find(item => item.id === 'current')?.id || id : id
      );

      // Fazer a requisição para gerar o PDF
      const response = await fetch(`${apiUrl}/generate_pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          interaction_ids: interactionIds,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao gerar o PDF');
      }

      // Obter o blob do PDF
      const blob = await response.blob();
      
      // Criar URL para download
      const url = window.URL.createObjectURL(blob);
      
      // Criar link e simular clique para download
      const a = document.createElement('a');
      a.href = url;
      a.download = `relatorio_analise_dados.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Limpar
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(`Erro: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Gerar Relatório PDF</CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p>{error}</p>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Interações selecionadas:</p>
            <p className="text-2xl font-bold">{selectedInteractions.length}</p>
            <p className="text-xs text-gray-500">
              Clique em "Adicionar ao PDF" nas interações que deseja incluir no relatório.
            </p>
          </div>

          <button
            onClick={handleGeneratePDF}
            disabled={isGenerating || selectedInteractions.length === 0}
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
          >
            {isGenerating ? 'Gerando PDF...' : 'Gerar PDF'}
          </button>
        </div>
      </CardContent>
    </Card>
  );
};

export default PDFGenerator;
