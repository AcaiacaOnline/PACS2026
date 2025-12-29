import React, { useState, useEffect } from 'react';
import { 
  Database, Download, Upload, Shield, AlertTriangle, 
  CheckCircle, FileJson, Clock, RefreshCw, Info
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const Backup = () => {
  const [backupInfo, setBackupInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [showConfirmRestore, setShowConfirmRestore] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [restoreResult, setRestoreResult] = useState(null);

  useEffect(() => {
    fetchBackupInfo();
  }, []);

  const fetchBackupInfo = async () => {
    try {
      const response = await api.get('/backup/info');
      setBackupInfo(response.data);
    } catch (error) {
      toast.error('Erro ao carregar informações de backup');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await api.get('/backup/export', {
        responseType: 'blob'
      });
      
      // Criar link de download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Nome do arquivo com data/hora
      const now = new Date();
      const filename = `backup_pac_acaiaca_${now.toISOString().slice(0,10)}_${now.toTimeString().slice(0,8).replace(/:/g, '')}.json`;
      link.setAttribute('download', filename);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Backup exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar backup');
    } finally {
      setExporting(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
        toast.error('Por favor, selecione um arquivo JSON válido');
        return;
      }
      setSelectedFile(file);
      setShowConfirmRestore(true);
    }
  };

  const handleRestore = async () => {
    if (!selectedFile) return;
    
    setImporting(true);
    setShowConfirmRestore(false);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      const response = await api.post('/backup/restore', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setRestoreResult(response.data);
      toast.success('Backup restaurado com sucesso!');
      
      // Recarregar informações
      await fetchBackupInfo();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao restaurar backup');
    } finally {
      setImporting(false);
      setSelectedFile(null);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Cabeçalho */}
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-primary/10 p-3 rounded-xl">
            <Database className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-heading font-bold text-foreground">
              Backup e Restauração
            </h2>
            <p className="text-muted-foreground">
              Proteja seus dados contra perda durante forks e redeploys
            </p>
          </div>
        </div>

        {/* Aviso Importante */}
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-800 dark:text-amber-200">
                Importante: Sobre Fork e Redeploy
              </h3>
              <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                Ao fazer <strong>fork</strong> ou <strong>redeploy</strong> na plataforma, 
                o banco de dados pode ser resetado. <strong>Sempre faça um backup antes</strong> dessas operações 
                para garantir que seus dados possam ser restaurados.
              </p>
            </div>
          </div>
        </div>

        {/* Status Atual do Sistema */}
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="bg-gradient-to-r from-primary/10 to-secondary/10 px-6 py-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Info className="w-5 h-5 text-primary" />
                <h3 className="font-bold text-foreground">Status Atual do Sistema</h3>
              </div>
              <button 
                onClick={fetchBackupInfo}
                className="text-muted-foreground hover:text-foreground"
              >
                <RefreshCw size={18} />
              </button>
            </div>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-muted/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-foreground">
                  {backupInfo?.current_data?.users || 0}
                </div>
                <div className="text-sm text-muted-foreground">Usuários</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-foreground">
                  {backupInfo?.current_data?.pacs || 0}
                </div>
                <div className="text-sm text-muted-foreground">PACs Individuais</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-foreground">
                  {backupInfo?.current_data?.pac_items || 0}
                </div>
                <div className="text-sm text-muted-foreground">Itens PAC</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-foreground">
                  {backupInfo?.current_data?.pacs_geral || 0}
                </div>
                <div className="text-sm text-muted-foreground">PACs Gerais</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-foreground">
                  {backupInfo?.current_data?.pac_geral_items || 0}
                </div>
                <div className="text-sm text-muted-foreground">Itens PAC Geral</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-foreground">
                  {backupInfo?.current_data?.processos || 0}
                </div>
                <div className="text-sm text-muted-foreground">Processos</div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Total de registros:</span>
                <span className="font-bold text-foreground">
                  {backupInfo?.total_records || 0}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Ações de Backup */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Exportar Backup */}
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="bg-gradient-to-r from-green-500/10 to-green-600/10 px-6 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Download className="w-5 h-5 text-green-600" />
                <h3 className="font-bold text-foreground">Exportar Backup</h3>
              </div>
            </div>
            
            <div className="p-6">
              <p className="text-sm text-muted-foreground mb-4">
                Baixe um arquivo JSON contendo todos os dados do sistema. 
                Este arquivo pode ser usado para restaurar os dados após um fork ou redeploy.
              </p>
              
              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle size={16} className="text-green-500" />
                  <span>Todos os usuários e permissões</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle size={16} className="text-green-500" />
                  <span>PACs Individuais e seus itens</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle size={16} className="text-green-500" />
                  <span>PACs Gerais e seus itens</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle size={16} className="text-green-500" />
                  <span>Todos os processos da Gestão Processual</span>
                </div>
              </div>
              
              <button
                onClick={handleExport}
                disabled={exporting}
                className="w-full flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {exporting ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Gerando Backup...
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5" />
                    Baixar Backup Completo
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Restaurar Backup */}
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500/10 to-blue-600/10 px-6 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-foreground">Restaurar Backup</h3>
              </div>
            </div>
            
            <div className="p-6">
              <p className="text-sm text-muted-foreground mb-4">
                Selecione um arquivo de backup JSON para restaurar os dados. 
                Os dados existentes serão atualizados/substituídos.
              </p>
              
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3 mb-4">
                <div className="flex items-start gap-2">
                  <Shield size={16} className="text-red-600 mt-0.5" />
                  <p className="text-xs text-red-700 dark:text-red-300">
                    <strong>Atenção:</strong> Esta operação substituirá os dados existentes. 
                    Certifique-se de que o arquivo de backup é válido e recente.
                  </p>
                </div>
              </div>
              
              <label className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
                <FileJson className="w-5 h-5" />
                {importing ? 'Restaurando...' : 'Selecionar Arquivo de Backup'}
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={handleFileSelect}
                  disabled={importing}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Resultado da Restauração */}
        {restoreResult && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <div className="flex-1">
                <h3 className="font-semibold text-green-800 dark:text-green-200 mb-2">
                  Backup Restaurado com Sucesso!
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                  <div className="bg-white/50 dark:bg-black/20 rounded p-2">
                    <div className="font-bold text-green-700">{restoreResult.stats?.users || 0}</div>
                    <div className="text-green-600 text-xs">Usuários</div>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded p-2">
                    <div className="font-bold text-green-700">{restoreResult.stats?.pacs || 0}</div>
                    <div className="text-green-600 text-xs">PACs</div>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded p-2">
                    <div className="font-bold text-green-700">{restoreResult.stats?.pac_items || 0}</div>
                    <div className="text-green-600 text-xs">Itens PAC</div>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded p-2">
                    <div className="font-bold text-green-700">{restoreResult.stats?.pacs_geral || 0}</div>
                    <div className="text-green-600 text-xs">PACs Gerais</div>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded p-2">
                    <div className="font-bold text-green-700">{restoreResult.stats?.pac_geral_items || 0}</div>
                    <div className="text-green-600 text-xs">Itens PAC Geral</div>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded p-2">
                    <div className="font-bold text-green-700">{restoreResult.stats?.processos || 0}</div>
                    <div className="text-green-600 text-xs">Processos</div>
                  </div>
                </div>
                {restoreResult.backup_metadata && (
                  <div className="mt-3 text-xs text-green-600">
                    <Clock size={14} className="inline mr-1" />
                    Backup criado em: {new Date(restoreResult.backup_metadata.exported_at).toLocaleString('pt-BR')}
                    {restoreResult.backup_metadata.exported_by && ` por ${restoreResult.backup_metadata.exported_by}`}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Instruções */}
        <div className="bg-muted/30 border border-border rounded-xl p-6">
          <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
            <Info size={18} />
            Como usar o Backup
          </h3>
          <ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
            <li>
              <strong>Antes de fazer fork ou redeploy:</strong> Clique em "Baixar Backup Completo" e salve o arquivo JSON
            </li>
            <li>
              <strong>Após o fork/redeploy:</strong> Faça login com suas credenciais de administrador
            </li>
            <li>
              <strong>Restaure os dados:</strong> Clique em "Selecionar Arquivo de Backup" e escolha o arquivo JSON salvo
            </li>
            <li>
              <strong>Confirme:</strong> Os dados serão restaurados e você poderá continuar trabalhando normalmente
            </li>
          </ol>
          <p className="mt-4 text-xs text-muted-foreground">
            💡 <strong>Dica:</strong> Faça backups regulares para proteger seus dados. 
            O arquivo de backup é um JSON que pode ser aberto em qualquer editor de texto.
          </p>
        </div>
      </div>

      {/* Modal de Confirmação */}
      {showConfirmRestore && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-amber-100 dark:bg-amber-900/50 p-2 rounded-full">
                <AlertTriangle className="w-6 h-6 text-amber-600" />
              </div>
              <h3 className="text-lg font-bold text-foreground">Confirmar Restauração</h3>
            </div>
            
            <p className="text-muted-foreground mb-4">
              Você está prestes a restaurar os dados do arquivo:
            </p>
            
            <div className="bg-muted/50 rounded-lg p-3 mb-4">
              <div className="flex items-center gap-2">
                <FileJson size={20} className="text-primary" />
                <span className="font-mono text-sm truncate">{selectedFile?.name}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Tamanho: {(selectedFile?.size / 1024).toFixed(2)} KB
              </div>
            </div>
            
            <p className="text-sm text-amber-600 dark:text-amber-400 mb-4">
              ⚠️ Os dados existentes serão atualizados/substituídos pelos dados do backup.
            </p>
            
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowConfirmRestore(false);
                  setSelectedFile(null);
                }}
                className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleRestore}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Confirmar Restauração
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default Backup;
