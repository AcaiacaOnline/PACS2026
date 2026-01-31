import React, { useState } from 'react';
import { X, FileDown, Info, Building2, User, Phone, Mail, MapPin, Calendar, FileText } from 'lucide-react';
import ClassificacaoSelector from './ClassificacaoSelector';

// Lista de Secretarias de Acaiaca
const SECRETARIAS = [
  'Secretaria de Administração',
  'Secretaria de Educação',
  'Secretaria de Saúde',
  'Secretaria de Assistência Social',
  'Secretaria de Obras e Urbanismo',
  'Secretaria de Agricultura e Meio Ambiente',
  'Secretaria de Esportes e Lazer',
  'Secretaria de Cultura e Turismo',
  'Secretaria de Finanças',
  'Gabinete do Prefeito'
];

// Unidades de medida
const UNIDADES = [
  'Unidade', 'UN', 'Caixa', 'CX', 'Pacote', 'PCT', 'Resma', 'Rolo', 'Metro', 'M', 
  'Metro Quadrado', 'M2', 'Litro', 'L', 'Quilograma', 'KG', 'Galão', 'Frasco', 
  'Tubo', 'Par', 'Jogo', 'Kit', 'Serviço', 'Hora', 'Diária', 'Mês'
];

// Prioridades
const PRIORIDADES = ['Alta', 'Média', 'Baixa'];

// Tipos de Item
const TIPOS_ITEM = [
  'Material de Consumo',
  'Material Permanente',
  'Serviço de Terceiro (Pessoa Física)',
  'Serviço de Terceiro (Pessoa Jurídica)',
  'Obras e Instalações',
  'Equipamentos e Material Permanente'
];

const TemplateModal = ({ isOpen, onClose, onApply, type = 'pac' }) => {
  const [step, setStep] = useState(1);
  
  // Dados do Cabeçalho
  const [headerData, setHeaderData] = useState({
    secretaria: '',
    secretario: '',
    fiscal: '',
    telefone: '',
    email: '',
    endereco: '',
    ano: '2026'
  });

  // Itens do Template
  const [templateItems, setTemplateItems] = useState([]);
  const [currentItem, setCurrentItem] = useState({
    tipo: 'Material de Consumo',
    catmat: '',
    descricao: '',
    unidade: 'Unidade',
    quantidade: 1,
    valorUnitario: 0,
    prioridade: 'Alta',
    justificativa: '',
    codigo_classificacao: '',
    subitem_classificacao: ''
  });

  // Secretarias selecionadas (para PAC Geral)
  const [secretariasSelecionadas, setSecretariasSelecionadas] = useState([]);

  const handleHeaderChange = (field, value) => {
    setHeaderData(prev => ({ ...prev, [field]: value }));
  };

  const handleItemChange = (field, value) => {
    setCurrentItem(prev => ({ ...prev, [field]: value }));
  };

  const addItem = () => {
    if (!currentItem.descricao) {
      alert('Informe a descrição do item');
      return;
    }
    setTemplateItems(prev => [...prev, { ...currentItem, id: Date.now() }]);
    setCurrentItem({
      tipo: 'Material de Consumo',
      catmat: '',
      descricao: '',
      unidade: 'Unidade',
      quantidade: 1,
      valorUnitario: 0,
      prioridade: 'Alta',
      justificativa: '',
      codigo_classificacao: '',
      subitem_classificacao: ''
    });
  };

  const removeItem = (id) => {
    setTemplateItems(prev => prev.filter(item => item.id !== id));
  };

  const handleApply = () => {
    const data = {
      header: headerData,
      items: templateItems,
      secretariasSelecionadas: type === 'pac-geral' ? secretariasSelecionadas : undefined
    };
    onApply(data);
    onClose();
  };

  const toggleSecretaria = (sec) => {
    setSecretariasSelecionadas(prev => 
      prev.includes(sec) 
        ? prev.filter(s => s !== sec) 
        : [...prev, sec]
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-start justify-center z-50 p-4 pt-8 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#1F4E78] to-[#2E7D32] px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3 text-white">
            <FileText className="w-6 h-6" />
            <div>
              <h2 className="text-xl font-bold">
                Template {type === 'pac-geral' ? 'PAC Geral' : 'PAC Individual'}
              </h2>
              <p className="text-sm opacity-90">Passo {step} de 3</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white hover:bg-white/20 p-2 rounded-lg">
            <X size={24} />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="bg-gray-100 px-6 py-2">
          <div className="flex gap-2">
            {[1, 2, 3].map(s => (
              <div 
                key={s}
                className={`flex-1 h-2 rounded-full ${s <= step ? 'bg-[#1F4E78]' : 'bg-gray-300'}`}
              />
            ))}
          </div>
          <div className="flex justify-between text-xs mt-1 text-gray-600">
            <span className={step === 1 ? 'font-bold' : ''}>Dados da Secretaria</span>
            <span className={step === 2 ? 'font-bold' : ''}>Adicionar Itens</span>
            <span className={step === 3 ? 'font-bold' : ''}>Revisar e Aplicar</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Dados da Secretaria */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
                <Info className="text-blue-600 mt-0.5" size={20} />
                <div className="text-sm text-blue-800">
                  <strong>Preencha os dados da secretaria responsável.</strong>
                  <p className="mt-1">Essas informações aparecerão no cabeçalho do PAC e nos relatórios gerados.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Building2 size={16} className="inline mr-1" />
                    Secretaria *
                  </label>
                  <select
                    value={headerData.secretaria}
                    onChange={(e) => handleHeaderChange('secretaria', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">Selecione a Secretaria</option>
                    {SECRETARIAS.map(sec => (
                      <option key={sec} value={sec}>{sec}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <User size={16} className="inline mr-1" />
                    Secretário(a) Responsável *
                  </label>
                  <input
                    type="text"
                    value={headerData.secretario}
                    onChange={(e) => handleHeaderChange('secretario', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Nome completo"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <User size={16} className="inline mr-1" />
                    Fiscal do Contrato
                  </label>
                  <input
                    type="text"
                    value={headerData.fiscal}
                    onChange={(e) => handleHeaderChange('fiscal', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Nome do fiscal"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Phone size={16} className="inline mr-1" />
                    Telefone
                  </label>
                  <input
                    type="text"
                    value={headerData.telefone}
                    onChange={(e) => handleHeaderChange('telefone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="(31) 99999-9999"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Mail size={16} className="inline mr-1" />
                    E-mail
                  </label>
                  <input
                    type="email"
                    value={headerData.email}
                    onChange={(e) => handleHeaderChange('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="email@acaiaca.mg.gov.br"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Calendar size={16} className="inline mr-1" />
                    Ano do PAC
                  </label>
                  <select
                    value={headerData.ano}
                    onChange={(e) => handleHeaderChange('ano', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                    <option value="2027">2027</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <MapPin size={16} className="inline mr-1" />
                  Endereço Completo
                </label>
                <textarea
                  value={headerData.endereco}
                  onChange={(e) => handleHeaderChange('endereco', e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Rua, número, bairro, CEP..."
                />
              </div>

              {/* Secretarias participantes (só para PAC Geral) */}
              {type === 'pac-geral' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Secretarias Participantes
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {SECRETARIAS.map(sec => (
                      <label key={sec} className="flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={secretariasSelecionadas.includes(sec)}
                          onChange={() => toggleSecretaria(sec)}
                          className="rounded"
                        />
                        <span className="text-sm">{sec}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Adicionar Itens */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                <Info className="text-green-600 mt-0.5" size={20} />
                <div className="text-sm text-green-800">
                  <strong>Adicione os itens do PAC.</strong>
                  <p className="mt-1">Preencha todas as informações de cada item. Você pode adicionar quantos itens precisar.</p>
                </div>
              </div>

              {/* Formulário de Item */}
              <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                <h3 className="font-semibold text-gray-800">Novo Item</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Item</label>
                    <select
                      value={currentItem.tipo}
                      onChange={(e) => handleItemChange('tipo', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      {TIPOS_ITEM.map(tipo => (
                        <option key={tipo} value={tipo}>{tipo}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Código CATMAT/CATSER</label>
                    <input
                      type="text"
                      value={currentItem.catmat}
                      onChange={(e) => handleItemChange('catmat', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      placeholder="Ex: 234567"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Prioridade</label>
                    <select
                      value={currentItem.prioridade}
                      onChange={(e) => handleItemChange('prioridade', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      {PRIORIDADES.map(p => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Descrição do Objeto *</label>
                  <textarea
                    value={currentItem.descricao}
                    onChange={(e) => handleItemChange('descricao', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Descreva o item de forma completa..."
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Unidade</label>
                    <select
                      value={currentItem.unidade}
                      onChange={(e) => handleItemChange('unidade', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      {UNIDADES.map(u => (
                        <option key={u} value={u}>{u}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Quantidade *</label>
                    <input
                      type="number"
                      value={currentItem.quantidade}
                      onChange={(e) => handleItemChange('quantidade', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      min="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Valor Unitário (R$) *</label>
                    <input
                      type="number"
                      value={currentItem.valorUnitario}
                      onChange={(e) => handleItemChange('valorUnitario', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      min="0"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Valor Total</label>
                    <div className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg font-medium">
                      R$ {(currentItem.quantidade * currentItem.valorUnitario).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Justificativa da Contratação</label>
                  <textarea
                    value={currentItem.justificativa}
                    onChange={(e) => handleItemChange('justificativa', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Descreva a necessidade e justificativa..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Classificação Orçamentária</label>
                  <ClassificacaoSelector
                    codigoValue={currentItem.codigo_classificacao}
                    subitemValue={currentItem.subitem_classificacao}
                    onCodigoChange={(value) => handleItemChange('codigo_classificacao', value)}
                    onSubitemChange={(value) => handleItemChange('subitem_classificacao', value)}
                  />
                </div>

                <button
                  type="button"
                  onClick={addItem}
                  className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  + Adicionar Item à Lista
                </button>
              </div>

              {/* Lista de Itens Adicionados */}
              {templateItems.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Itens Adicionados ({templateItems.length})</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {templateItems.map((item, idx) => (
                      <div key={item.id} className="flex items-center justify-between bg-white p-3 rounded-lg border">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{idx + 1}. {item.descricao}</div>
                          <div className="text-xs text-gray-500">
                            {item.quantidade} {item.unidade} × R$ {item.valorUnitario.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} = 
                            <strong> R$ {(item.quantidade * item.valorUnitario).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</strong>
                          </div>
                        </div>
                        <button
                          onClick={() => removeItem(item.id)}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <X size={18} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Revisar e Aplicar */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
                <Info className="text-amber-600 mt-0.5" size={20} />
                <div className="text-sm text-amber-800">
                  <strong>Revise as informações antes de aplicar.</strong>
                  <p className="mt-1">Ao clicar em "Aplicar Template", os dados serão preenchidos automaticamente no formulário.</p>
                </div>
              </div>

              {/* Resumo do Cabeçalho */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <Building2 size={18} />
                  Dados da Secretaria
                </h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><strong>Secretaria:</strong> {headerData.secretaria || '-'}</div>
                  <div><strong>Secretário(a):</strong> {headerData.secretario || '-'}</div>
                  <div><strong>Fiscal:</strong> {headerData.fiscal || '-'}</div>
                  <div><strong>Telefone:</strong> {headerData.telefone || '-'}</div>
                  <div><strong>E-mail:</strong> {headerData.email || '-'}</div>
                  <div><strong>Ano:</strong> {headerData.ano}</div>
                  <div className="col-span-2"><strong>Endereço:</strong> {headerData.endereco || '-'}</div>
                </div>
                {type === 'pac-geral' && secretariasSelecionadas.length > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <strong>Secretarias Participantes:</strong>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {secretariasSelecionadas.map(sec => (
                        <span key={sec} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
                          {sec}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Resumo dos Itens */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <FileText size={18} />
                  Itens ({templateItems.length})
                </h3>
                {templateItems.length === 0 ? (
                  <p className="text-gray-500 text-sm">Nenhum item adicionado</p>
                ) : (
                  <>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {templateItems.map((item, idx) => (
                        <div key={item.id} className="bg-gray-50 p-2 rounded text-sm">
                          <div className="font-medium">{idx + 1}. {item.descricao}</div>
                          <div className="text-xs text-gray-600 mt-1">
                            {item.tipo} | {item.quantidade} {item.unidade} | R$ {(item.quantidade * item.valorUnitario).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                            {item.codigo_classificacao && ` | ${item.codigo_classificacao}`}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-3 pt-3 border-t flex justify-between font-bold">
                      <span>VALOR TOTAL ESTIMADO:</span>
                      <span className="text-green-600">
                        R$ {templateItems.reduce((sum, item) => sum + (item.quantidade * item.valorUnitario), 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-100 px-6 py-4 flex justify-between">
          <button
            onClick={() => step > 1 ? setStep(step - 1) : onClose()}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors"
          >
            {step === 1 ? 'Cancelar' : 'Voltar'}
          </button>

          {step < 3 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="px-6 py-2 bg-[#1F4E78] text-white rounded-lg hover:bg-[#1F4E78]/90 transition-colors font-medium"
            >
              Próximo
            </button>
          ) : (
            <button
              onClick={handleApply}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
            >
              <FileDown size={18} />
              Aplicar Template
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TemplateModal;
