import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface FileUploadProps {
  onFileUploaded: (sessionId: string, filename: string, columns: string[], preview: any[]) => void;
  apiUrl: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded, apiUrl }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao fazer upload do arquivo');
      }

      const data = await response.json();
      onFileUploaded(
        data.session_id,
        data.filename,
        data.columns,
        data.preview
      );
      
      setFile(null);
    } catch (err) {
      setError(`Erro: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>1. Carregar Arquivo (CSV/Excel)</CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p>Erro: {error}</p>
          </div>
        )}

        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center ${
            dragActive ? 'border-primary bg-primary/5' : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="p-3 rounded-full bg-primary/10">
              <svg
                className="h-8 w-8 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                ></path>
              </svg>
            </div>
            <div className="space-y-1 text-center">
              <p className="text-sm text-gray-500">
                Solte o arquivo aqui
              </p>
              <p className="text-xs text-gray-500">- ou -</p>
              <p className="text-sm text-gray-500">
                Clique para fazer upload
              </p>
            </div>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              accept=".csv,.xlsx,.xls,.json,.parquet"
              onChange={handleFileChange}
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90"
            >
              Escolher arquivo
            </label>
          </div>
        </div>

        {file && (
          <div className="mt-4">
            <p className="text-sm font-medium">Arquivo selecionado:</p>
            <p className="text-sm text-gray-500">{file.name}</p>
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="mt-2 w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
            >
              {isUploading ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FileUpload;
