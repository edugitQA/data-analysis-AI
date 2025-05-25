import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ChatInterfaceProps {
  sessionId: string;
  onSendQuestion: (question: string) => void;
  isLoading: boolean;
  currentQuestion: string;
  currentAnswer: string | null;
  currentCode: string | null;
  history: Array<{
    id: string;
    question: string;
    answer: string;
    code: string | null;
  }>;
  onClearCurrent: () => void;
  onAddToReport: (id: string) => void;
  selectedForReport: string[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  onSendQuestion,
  isLoading,
  currentQuestion,
  currentAnswer,
  currentCode,
  history,
  onClearCurrent,
  onAddToReport,
  selectedForReport,
}) => {
  const [question, setQuestion] = React.useState('');
  const chatContainerRef = React.useRef<HTMLDivElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSendQuestion(question);
      setQuestion('');
    }
  };

  // Rolar para o final quando novas mensagens chegarem
  React.useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [currentAnswer, history]);

  return (
    <div className="flex flex-col h-full">
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto mb-4 space-y-4"
      >
        {history.length > 0 && (
          <div className="space-y-4 mb-6">
            {history.map((item) => (
              <div key={item.id} className="space-y-2">
                <div className="bg-gray-100 p-3 rounded-lg">
                  <p className="font-medium">Pergunta:</p>
                  <p>{item.question}</p>
                </div>
                <div className="bg-primary/10 p-3 rounded-lg">
                  <p className="font-medium">Resposta:</p>
                  <p>{item.answer}</p>
                </div>
                {item.code && (
                  <div className="bg-gray-800 text-gray-100 p-3 rounded-lg font-mono text-sm overflow-x-auto">
                    <pre>{item.code}</pre>
                  </div>
                )}
                <div className="flex justify-end">
                  <button
                    onClick={() => onAddToReport(item.id)}
                    className={`text-xs px-2 py-1 rounded ${
                      selectedForReport.includes(item.id)
                        ? 'bg-primary text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {selectedForReport.includes(item.id)
                      ? 'Adicionado ao PDF'
                      : 'Adicionar ao PDF'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {currentQuestion && (
          <div className="space-y-2">
            <div className="bg-gray-100 p-3 rounded-lg">
              <p className="font-medium">Pergunta:</p>
              <p>{currentQuestion}</p>
            </div>
            {isLoading ? (
              <div className="bg-primary/10 p-3 rounded-lg animate-pulse">
                <p>Processando...</p>
              </div>
            ) : (
              currentAnswer && (
                <>
                  <div className="bg-primary/10 p-3 rounded-lg">
                    <p className="font-medium">Resposta:</p>
                    <p>{currentAnswer}</p>
                  </div>
                  {currentCode && (
                    <div className="bg-gray-800 text-gray-100 p-3 rounded-lg font-mono text-sm overflow-x-auto">
                      <pre>{currentCode}</pre>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <button
                      onClick={onClearCurrent}
                      className="text-xs px-2 py-1 rounded bg-gray-200 text-gray-700 hover:bg-gray-300"
                    >
                      Limpar pergunta e resultado
                    </button>
                    <button
                      onClick={() => onAddToReport('current')}
                      className={`text-xs px-2 py-1 rounded ${
                        selectedForReport.includes('current')
                          ? 'bg-primary text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {selectedForReport.includes('current')
                        ? 'Adicionado ao PDF'
                        : 'Adicionar ao PDF'}
                    </button>
                  </div>
                </>
              )
            )}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-auto">
        <div className="flex space-x-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Digite sua pergunta sobre os dados..."
            className="flex-1 min-w-0 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
