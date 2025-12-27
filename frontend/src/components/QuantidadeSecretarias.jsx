import React from 'react';

const QuantidadeSecretarias = ({ valores, onChange, disabled = false }) => {
  const secretarias = [
    { sigla: 'AD', nome: 'Administração', color: 'bg-blue-50 border-blue-200' },
    { sigla: 'FA', nome: 'Fazenda', color: 'bg-green-50 border-green-200' },
    { sigla: 'SA', nome: 'Saúde', color: 'bg-red-50 border-red-200' },
    { sigla: 'SE', nome: 'Educação', color: 'bg-purple-50 border-purple-200' },
    { sigla: 'AS', nome: 'Assistência Social', color: 'bg-pink-50 border-pink-200' },
    { sigla: 'AG', nome: 'Agricultura', color: 'bg-lime-50 border-lime-200' },
    { sigla: 'OB', nome: 'Obras', color: 'bg-orange-50 border-orange-200' },
    { sigla: 'TR', nome: 'Transporte', color: 'bg-cyan-50 border-cyan-200' },
    { sigla: 'CUL', nome: 'Cultura', color: 'bg-indigo-50 border-indigo-200' }
  ];

  const handleChange = (sigla, value) => {
    const numValue = parseFloat(value) || 0;
    onChange(sigla.toLowerCase(), numValue);
  };

  const calcularTotal = () => {
    return secretarias.reduce((sum, sec) => {
      const key = `qtd_${sec.sigla.toLowerCase()}`;
      return sum + (valores[key] || 0);
    }, 0);
  };

  return (
    <div className="space-y-4">
      <div className="border border-border rounded-lg p-4 bg-muted/30">
        <h3 className="text-sm font-bold text-foreground mb-3 flex items-center">
          <span className="bg-primary text-primary-foreground px-2 py-1 rounded text-xs mr-2">QTDE</span>
          Quantidade por Secretaria
        </h3>
        
        <div className="grid grid-cols-3 gap-3">
          {secretarias.map((sec) => {
            const key = `qtd_${sec.sigla.toLowerCase()}`;
            return (
              <div key={sec.sigla} className={`border rounded-lg p-3 ${sec.color}`}>
                <label className="block text-xs font-bold text-foreground mb-1">
                  {sec.sigla}
                </label>
                <div className="text-xs text-muted-foreground mb-2">{sec.nome}</div>
                <input
                  type="number"
                  value={valores[key] || 0}
                  onChange={(e) => handleChange(sec.sigla, e.target.value)}
                  disabled={disabled}
                  min="0"
                  step="0.01"
                  className="w-full px-2 py-1.5 text-sm border border-input bg-background rounded focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50"
                  data-testid={`qtd-${sec.sigla.toLowerCase()}-input`}
                />
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-primary/10 border-2 border-primary rounded-lg p-4">
        <div className="flex justify-between items-center">
          <span className="text-sm font-bold text-foreground">Quantidade Total:</span>
          <span className="text-2xl font-bold text-primary" data-testid="quantidade-total">
            {calcularTotal().toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default QuantidadeSecretarias;