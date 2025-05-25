import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface DBConnectionProps {
  onDBConnected: (sessionId: string, dbPath: string, tables: string[], previews: any) => void;
  apiUrl: string;
}

const DBConnection: React.FC<DBConnectionProps> = ({ onDBConnected, apiUrl }) => {
  const [dbPath, setDbPath] = React.useState('');
  const [isConnecting, setIsConnecting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleConnect = async () => {
    if (!dbPath.trim()) {
      setError('Por favor, informe o caminho do banco de dados.');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/connect_db`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          db_path: dbPath,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao conectar ao banco de dados');
      }

      const data = await response.json();
      onDBConnected(
        data.session_id,
        data.db_path,
        data.tables,
        data.previews
      );
      
      setDbPath('');
    } catch (err) {
      setError(`Erro: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>2. Conectar ao Banco de Dados</CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p>Erro: {error}</p>
          </div>
        )}

        <div className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="db-path" className="block text-sm font-medium text-gray-700">
              Caminho do Banco de Dados SQLite
            </label>
            <input
              id="db-path"
              type="text"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
              placeholder="/caminho/para/seu/banco.db"
              value={dbPath}
              onChange={(e) => setDbPath(e.target.value)}
            />
            <p className="text-xs text-gray-500">
              Exemplo: /home/usuario/dados/meu_banco.db
            </p>
          </div>

          <button
            onClick={handleConnect}
            disabled={isConnecting || !dbPath.trim()}
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
          >
            {isConnecting ? 'Conectando...' : 'Conectar'}
          </button>
        </div>
      </CardContent>
    </Card>
  );
};

export default DBConnection;
