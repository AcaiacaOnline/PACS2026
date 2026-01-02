import React, { useState, useEffect, useCallback } from 'react';

// ============ FUNÇÕES DE MÁSCARA ============

/**
 * Aplica máscara de telefone brasileiro
 * Formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
 */
export const maskTelefone = (value) => {
  if (!value) return '';
  const numbers = value.replace(/\D/g, '');
  
  if (numbers.length <= 2) {
    return `(${numbers}`;
  }
  if (numbers.length <= 6) {
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
  }
  if (numbers.length <= 10) {
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 6)}-${numbers.slice(6)}`;
  }
  // Celular com 9 dígitos
  return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7, 11)}`;
};

/**
 * Aplica máscara de CEP
 * Formato: XXXXX-XXX
 */
export const maskCEP = (value) => {
  if (!value) return '';
  const numbers = value.replace(/\D/g, '');
  
  if (numbers.length <= 5) {
    return numbers;
  }
  return `${numbers.slice(0, 5)}-${numbers.slice(5, 8)}`;
};

/**
 * Aplica máscara de CPF
 * Formato: XXX.XXX.XXX-XX
 */
export const maskCPF = (value) => {
  if (!value) return '';
  const numbers = value.replace(/\D/g, '');
  
  if (numbers.length <= 3) {
    return numbers;
  }
  if (numbers.length <= 6) {
    return `${numbers.slice(0, 3)}.${numbers.slice(3)}`;
  }
  if (numbers.length <= 9) {
    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`;
  }
  return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9, 11)}`;
};

/**
 * Aplica máscara de CNPJ
 * Formato: XX.XXX.XXX/XXXX-XX
 */
export const maskCNPJ = (value) => {
  if (!value) return '';
  const numbers = value.replace(/\D/g, '');
  
  if (numbers.length <= 2) {
    return numbers;
  }
  if (numbers.length <= 5) {
    return `${numbers.slice(0, 2)}.${numbers.slice(2)}`;
  }
  if (numbers.length <= 8) {
    return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5)}`;
  }
  if (numbers.length <= 12) {
    return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5, 8)}/${numbers.slice(8)}`;
  }
  return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5, 8)}/${numbers.slice(8, 12)}-${numbers.slice(12, 14)}`;
};

/**
 * Aplica máscara de moeda brasileira (Real)
 * Formato: R$ X.XXX,XX
 */
export const maskCurrency = (value) => {
  if (value === null || value === undefined || value === '') return '';
  
  // Se for número, converter para centavos
  let numbers;
  if (typeof value === 'number') {
    numbers = Math.round(value * 100).toString();
  } else {
    numbers = value.toString().replace(/\D/g, '');
  }
  
  if (!numbers || numbers === '0') return 'R$ 0,00';
  
  // Converter para número e formatar
  const numValue = parseInt(numbers, 10) / 100;
  return numValue.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
};

/**
 * Remove máscara de moeda e retorna número
 */
export const unmaskCurrency = (value) => {
  if (!value) return 0;
  if (typeof value === 'number') return value;
  
  // Remove R$, pontos e substitui vírgula por ponto
  const cleaned = value
    .replace(/R\$\s?/g, '')
    .replace(/\./g, '')
    .replace(',', '.');
  
  return parseFloat(cleaned) || 0;
};

/**
 * Aplica máscara de número inteiro com separador de milhar
 * Formato: X.XXX.XXX
 */
export const maskNumber = (value) => {
  if (!value) return '';
  const numbers = value.toString().replace(/\D/g, '');
  return parseInt(numbers || '0', 10).toLocaleString('pt-BR');
};

/**
 * Remove máscara de número
 */
export const unmaskNumber = (value) => {
  if (!value) return 0;
  if (typeof value === 'number') return value;
  return parseInt(value.replace(/\D/g, '') || '0', 10);
};

/**
 * Aplica máscara de número de processo
 * Formato: XXX - XXXX/XXXX
 */
export const maskProcesso = (value) => {
  if (!value) return '';
  const upper = value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  
  if (upper.length <= 3) {
    return upper;
  }
  if (upper.length <= 7) {
    return `${upper.slice(0, 3)} - ${upper.slice(3)}`;
  }
  return `${upper.slice(0, 3)} - ${upper.slice(3, 7)}/${upper.slice(7, 11)}`;
};

// ============ COMPONENTES DE INPUT MASCARADO ============

/**
 * Input com máscara de telefone
 */
export const TelefoneInput = ({ value, onChange, className, ...props }) => {
  const handleChange = (e) => {
    const masked = maskTelefone(e.target.value);
    onChange({ target: { value: masked, name: e.target.name } });
  };

  return (
    <input
      type="tel"
      value={maskTelefone(value)}
      onChange={handleChange}
      placeholder="(00) 00000-0000"
      maxLength={15}
      className={className}
      {...props}
    />
  );
};

/**
 * Input com máscara de CEP
 */
export const CEPInput = ({ value, onChange, className, onBlur, ...props }) => {
  const handleChange = (e) => {
    const masked = maskCEP(e.target.value);
    onChange({ target: { value: masked, name: e.target.name } });
  };

  const handleBlur = async (e) => {
    const cep = e.target.value.replace(/\D/g, '');
    if (cep.length === 8 && onBlur) {
      onBlur(e, cep);
    }
  };

  return (
    <input
      type="text"
      value={maskCEP(value)}
      onChange={handleChange}
      onBlur={handleBlur}
      placeholder="00000-000"
      maxLength={9}
      className={className}
      {...props}
    />
  );
};

/**
 * Input com máscara de CPF
 */
export const CPFInput = ({ value, onChange, className, ...props }) => {
  const handleChange = (e) => {
    const masked = maskCPF(e.target.value);
    onChange({ target: { value: masked, name: e.target.name } });
  };

  return (
    <input
      type="text"
      value={maskCPF(value)}
      onChange={handleChange}
      placeholder="000.000.000-00"
      maxLength={14}
      className={className}
      {...props}
    />
  );
};

/**
 * Input com máscara de CNPJ
 */
export const CNPJInput = ({ value, onChange, className, ...props }) => {
  const handleChange = (e) => {
    const masked = maskCNPJ(e.target.value);
    onChange({ target: { value: masked, name: e.target.name } });
  };

  return (
    <input
      type="text"
      value={maskCNPJ(value)}
      onChange={handleChange}
      placeholder="00.000.000/0000-00"
      maxLength={18}
      className={className}
      {...props}
    />
  );
};

/**
 * Input com máscara de moeda (R$)
 */
export const CurrencyInput = ({ value, onChange, className, ...props }) => {
  const [displayValue, setDisplayValue] = useState('');

  useEffect(() => {
    if (value !== undefined && value !== null) {
      setDisplayValue(maskCurrency(value));
    }
  }, [value]);

  const handleChange = (e) => {
    const inputValue = e.target.value;
    const numbers = inputValue.replace(/\D/g, '');
    
    if (numbers === '') {
      setDisplayValue('');
      onChange({ target: { value: 0, name: e.target.name } });
      return;
    }
    
    const numericValue = parseInt(numbers, 10) / 100;
    const formatted = maskCurrency(numericValue);
    
    setDisplayValue(formatted);
    onChange({ target: { value: numericValue, name: e.target.name } });
  };

  const handleFocus = (e) => {
    // Selecionar todo o texto ao focar
    e.target.select();
  };

  return (
    <input
      type="text"
      value={displayValue}
      onChange={handleChange}
      onFocus={handleFocus}
      placeholder="R$ 0,00"
      className={className}
      {...props}
    />
  );
};

/**
 * Input com máscara de número inteiro
 */
export const NumberInput = ({ value, onChange, className, ...props }) => {
  const handleChange = (e) => {
    const numbers = e.target.value.replace(/\D/g, '');
    const numValue = parseInt(numbers || '0', 10);
    onChange({ target: { value: numValue, name: e.target.name } });
  };

  return (
    <input
      type="text"
      value={value ? maskNumber(value) : ''}
      onChange={handleChange}
      placeholder="0"
      className={className}
      {...props}
    />
  );
};

/**
 * Input com validação de email em tempo real
 */
export const EmailInput = ({ value, onChange, className, onValidate, ...props }) => {
  const [isValid, setIsValid] = useState(true);
  
  const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const handleChange = (e) => {
    const email = e.target.value;
    const valid = !email || validateEmail(email);
    setIsValid(valid);
    if (onValidate) onValidate(valid);
    onChange(e);
  };

  const handleBlur = (e) => {
    if (e.target.value) {
      setIsValid(validateEmail(e.target.value));
    }
  };

  return (
    <div className="relative">
      <input
        type="email"
        value={value}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="email@exemplo.com"
        className={`${className} ${!isValid ? 'border-red-500 focus:ring-red-500' : ''}`}
        {...props}
      />
      {!isValid && value && (
        <p className="text-red-500 text-xs mt-1">Email inválido</p>
      )}
    </div>
  );
};

// Export default object with all masks and components
export default {
  // Funções de máscara
  maskTelefone,
  maskCEP,
  maskCPF,
  maskCNPJ,
  maskCurrency,
  unmaskCurrency,
  maskNumber,
  unmaskNumber,
  maskProcesso,
  // Componentes
  TelefoneInput,
  CEPInput,
  CPFInput,
  CNPJInput,
  CurrencyInput,
  NumberInput,
  EmailInput
};
