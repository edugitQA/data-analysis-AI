// Ajuste no App.tsx para corrigir a URL da API para o domínio público
import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Database, FileUp, MessageSquare } from 'lucide-react';
import FileUpload from './components/FileUpload';
import DBConnection from './components/DBConnection';
import ChatInterface from './components/ChatInterface';
import DataPreview from './components/DataPreview';
import PDFGenerator from './components/PDFGenerator';

// URL base da API - Ajustada para usar o proxy do Vite
const API_URL = '/api';

function App() {
  // Estado da sessão
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [dataType, setDataType] = useState<'dataframe' | 'database' | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [dbPath, setDbPath] = useState<string | null>(null);
  
  // Estado dos dados
  const [columns, setColumns] = useState<string[]>([]);
  const [preview, setPreview] = useState<any[]>([]);
  const [dbTables, setDbTables] = useState<string[]>([]);
  const [dbPreviews, setDbPreviews] = useState<Record<string, any>>({});
  const [activeTable, setActiveTable] = useState<string>('');
  
  // Estado do chat
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [currentAnswer, setCurrentAnswer] = useState<string | null>(null);
  const [currentCode, setCurrentCode] = useState<string | null>(null);
  const [history, setHistory] = useState<Array<{
    id: string;
    question: string;
    answer: string;
    code: string | null;
  }>>([]);
  
  // Estado do PDF
  const [selectedForReport, setSelectedForReport] = useState<string[]>([]);
  
  // Estado da interface
  const [activeTab, setActiveTab] = useState('upload');

  // Manipuladores de eventos para upload de arquivo
  const handleFileUploaded = (
    newSessionId: string,
    newFilename: string,
    newColumns: string[],
    newPreview: any[]
  ) => {
    setSessionId(newSessionId);
    setFilename(newFilename);
    setColumns(newColumns);
    setPreview(newPreview);
    setDataType('dataframe');
    setDbPath(null);
    setDbTables([]);
    setDbPreviews({});
    setHistory([]);
    setCurrentQuestion('');
    setCurrentAnswer(null);
    setCurrentCode(null);
    setSelectedForReport([]);
    setActiveTab('chat');
    console.log('activeTab after file upload:', 'chat'); // Adicionado log
  };

  // Manipuladores de eventos para conexão com banco de dados
  const handleDBConnected = (
    newSessionId: string,
    newDbPath: string,
    newTables: string[],
    newPreviews: any
  ) => {
    setSessionId(newSessionId);
    setDbPath(newDbPath);
    setDbTables(newTables);
    setDbPreviews(newPreviews);
    setActiveTable(newTables.length > 0 ? newTables[0] : '');
    setDataType('database');
    setFilename(null);
    setColumns([]);
    setPreview([]);
    setHistory([]);
    setCurrentQuestion('');
    setCurrentAnswer(null);
    setCurrentCode(null);
    setSelectedForReport([]);
    setActiveTab('chat');
  };

  // Manipuladores de eventos para o chat
  const handleSendQuestion = async (question: string) => {
    if (!sessionId) return;
    
    setIsLoading(true);
    setCurrentQuestion(question);
    setCurrentAnswer(null);
    setCurrentCode(null);
    
    try {
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: question,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao processar a consulta');
      }
      
      const data = await response.json();
      setCurrentAnswer(data.answer);
      setCurrentCode(data.generated_code);
      
    } catch (err) {
      setCurrentAnswer(`Erro: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearCurrent = () => {
    if (currentQuestion && currentAnswer) {
      // Adicionar ao histórico antes de limpar
      setHistory([
        ...history,
        {
          id: Date.now().toString(), // Simplificado, idealmente seria um UUID
          question: currentQuestion,
          answer: currentAnswer,
          code: currentCode,
        },
      ]);
    }
    
    setCurrentQuestion('');
    setCurrentAnswer(null);
    setCurrentCode(null);
  };

  // Manipuladores de eventos para o PDF
  const handleToggleInteraction = (id: string) => {
    setSelectedForReport((prev) =>
      prev.includes(id)
        ? prev.filter((item) => item !== id)
        : [...prev, id]
    );
  };

  // Efeito para atualizar colunas e preview quando a tabela ativa muda (para banco de dados)
  useEffect(() => {
    if (dataType === 'database' && activeTable && dbPreviews[activeTable]) {
      const tablePreview = dbPreviews[activeTable];
      setColumns(tablePreview.columns || []);
      setPreview(tablePreview.data || []);
    }
  }, [dataType, activeTable, dbPreviews]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col p-4">
      <header className="bg-white border-b py-4 px-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-primary">Analisando os dados 🔍 🎲</h1>
          <p className="text-gray-600 mt-1">
            Carregue um arquivo ou conecte-se a um banco de dados e faça perguntas em linguagem natural.
          </p>
        </div>
      </header>
      
      <main className="flex-1 py-6 px-6">
        <div className="max-w-7xl mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid grid-cols-3 w-full max-w-md mx-auto mb-6">
              <TabsTrigger value="upload" className="flex items-center">
                <FileUp className="h-4 w-4 mr-2" />
                Upload
              </TabsTrigger>
              <TabsTrigger value="database" className="flex items-center">
                <Database className="h-4 w-4 mr-2" />
                Banco de Dados
              </TabsTrigger>
              <TabsTrigger value="chat" className="flex items-center">
                <MessageSquare className="h-4 w-4 mr-2" />
                Perguntas
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="upload" className="space-y-6">
              <FileUpload 
                onFileUploaded={handleFileUploaded}
                apiUrl={API_URL}
              />
            </TabsContent>
            
            <TabsContent value="database" className="space-y-6">
              <DBConnection 
                onDBConnected={handleDBConnected}
                apiUrl={API_URL}
              />
            </TabsContent>
            
            <TabsContent value="chat" className="space-y-6">
              {sessionId ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="md:col-span-2 space-y-6">
                    {/* Pré-visualização dos dados */}
                    <DataPreview
                      dataType={dataType}
                      columns={columns}
                      preview={preview}
                      dbTables={dbTables}
                      dbPreviews={dbPreviews}
                      currentTable={activeTable}
                      onTableChange={setActiveTable}
                    />
                    
                    {/* Interface de chat */}
                    <Card className="h-[600px]">
                      <CardHeader>
                        <CardTitle>Faça perguntas sobre os dados</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ChatInterface
                          sessionId={sessionId}
                          onSendQuestion={handleSendQuestion}
                          isLoading={isLoading}
                          currentQuestion={currentQuestion}
                          currentAnswer={currentAnswer}
                          currentCode={currentCode}
                          history={history}
                          onClearCurrent={handleClearCurrent}
                          onAddToReport={handleToggleInteraction}
                          selectedForReport={selectedForReport}
                        />
                      </CardContent>
                    </Card>
                  </div>
                  
                  <div>
                    {/* Gerador de PDF */}
                    <PDFGenerator
                      sessionId={sessionId}
                      selectedInteractions={selectedForReport}
                      history={[
                        ...history,
                        ...(currentQuestion && currentAnswer
                          ? [{
                              id: 'current',
                              question: currentQuestion,
                              answer: currentAnswer,
                              code: currentCode,
                            }]
                          : []),
                      ]}
                      apiUrl={API_URL}
                      onToggleInteraction={handleToggleInteraction}
                    />
                    
                    {/* Informações da sessão */}
                    <Card className="mt-6">
                      <CardHeader>
                        <CardTitle>Informações da Sessão</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          <p>
                            <span className="font-medium">Tipo de dados:</span>{' '}
                            {dataType === 'dataframe' ? 'Arquivo' : 'Banco de Dados'}
                          </p>
                          {dataType === 'dataframe' && filename && (
                            <p>
                              <span className="font-medium">Arquivo:</span> {filename}
                            </p>
                          )}
                          {dataType === 'database' && dbPath && (
                            <>
                              <p>
                                <span className="font-medium">Banco de dados:</span> {dbPath}
                              </p>
                              <p>
                                <span className="font-medium">Tabelas:</span> {dbTables.join(', ')}
                              </p>
                            </>
                          )}
                          <p>
                            <span className="font-medium">Perguntas realizadas:</span>{' '}
                            {history.length + (currentQuestion && currentAnswer ? 1 : 0)}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              ) : (
                <Card>
                  <CardContent className="p-6 text-center">
                    <p className="text-gray-500">
                      Carregue um arquivo ou conecte-se a um banco de dados primeiro para começar a fazer perguntas.
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
      
      <footer className="bg-white border-t py-4 px-6">
        <div className="max-w-7xl mx-auto text-center text-gray-500 text-sm">
          Análise de Dados com IA Generativa • Powered by LlamaIndex e OpenAI
        </div>
      </footer>
    </div>
  );
}

export default App;
