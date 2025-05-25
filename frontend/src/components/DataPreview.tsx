import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface DataPreviewProps {
  dataType: 'dataframe' | 'database' | null;
  columns: string[];
  preview: any[];
  dbTables?: string[];
  dbPreviews?: Record<string, any>;
  currentTable?: string;
  onTableChange?: (table: string) => void;
}

const DataPreview: React.FC<DataPreviewProps> = ({
  dataType,
  columns,
  preview,
  dbTables = [],
  dbPreviews = {},
  currentTable = '',
  onTableChange = () => {},
}) => {
  if (!columns.length || !preview.length) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          Pré-visualização dos Dados
          {dataType === 'database' && currentTable && (
            <span className="ml-2 text-gray-500">
              (Tabela: {currentTable})
            </span>
          )}
        </CardTitle>
        
        {dataType === 'database' && dbTables.length > 0 && (
          <select
            value={currentTable}
            onChange={(e) => onTableChange(e.target.value)}
            className="text-xs rounded border border-gray-300 px-2 py-1"
          >
            {dbTables.map((table) => (
              <option key={table} value={table}>
                {table}
              </option>
            ))}
          </select>
        )}
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-700">
            <thead className="text-xs text-gray-700 uppercase bg-gray-100">
              <tr>
                {columns.map((column) => (
                  <th key={column} className="px-4 py-2">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-b hover:bg-gray-50">
                  {columns.map((column) => (
                    <td key={`${rowIndex}-${column}`} className="px-4 py-2">
                      {row[column] !== undefined ? String(row[column]) : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Mostrando {preview.length} de {preview.length} linhas
        </p>
      </CardContent>
    </Card>
  );
};

export default DataPreview;
