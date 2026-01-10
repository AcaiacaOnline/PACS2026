import React, { useState, useEffect } from 'react';
import { Users as UsersIcon, Plus, Edit, Trash2, UserCheck, UserX, Shield, User as UserIcon, X, Save, Eye, FileText, Settings, Lock, PenTool, MapPin, Search } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import { TelefoneInput, EmailInput, CEPInput, CPFInput } from '../utils/masks';
import Pagination, { usePagination, paginateData } from '../components/Pagination';

const PERMISSIONS_CONFIG = [
  { key: 'can_view', label: 'Visualizar PACs', icon: Eye, description: 'Pode visualizar todos os PACs e PACs Gerais' },
  { key: 'can_edit', label: 'Editar PACs', icon: Edit, description: 'Pode editar PACs e PACs Gerais existentes' },
  { key: 'can_delete', label: 'Excluir PACs', icon: Trash2, description: 'Pode excluir PACs e itens' },
  { key: 'can_export', label: 'Gerar Relatórios', icon: FileText, description: 'Pode exportar PDF e XLSX' },
  { key: 'can_manage_users', label: 'Cadastrar Usuários', icon: UsersIcon, description: 'Pode criar e gerenciar usuários' },
  { key: 'is_full_admin', label: 'Administrador Completo', icon: Shield, description: 'Todos os privilégios do sistema' }
];

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Paginação
  const { currentPage, setCurrentPage, pageSize, setPageSize, resetPage } = usePagination(20);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    is_admin: false,
    is_active: true,
    permissions: {
      can_view: true,
      can_edit: false,
      can_delete: false,
      can_export: false,
      can_manage_users: false,
      is_full_admin: false
    },
    signature_data: {
      cpf: '',
      cargo: '',
      endereco: '',
      cep: '',
      telefone: ''
    }
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Acesso negado. Apenas administradores podem acessar esta página.');
      } else {
        toast.error('Erro ao carregar usuários');
      }
    } finally {
      setLoading(false);
    }
  };

  const openModal = (user = null) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        name: user.name,
        email: user.email,
        password: '',
        is_admin: user.is_admin,
        is_active: user.is_active ?? true,
        permissions: user.permissions || {
          can_view: true,
          can_edit: user.is_admin,
          can_delete: user.is_admin,
          can_export: user.is_admin,
          can_manage_users: user.is_admin,
          is_full_admin: user.is_admin
        },
        signature_data: user.signature_data || {
          cpf: '',
          cargo: '',
          endereco: '',
          cep: '',
          telefone: ''
        }
      });
    } else {
      setEditingUser(null);
      setFormData({
        name: '',
        email: '',
        password: '',
        is_admin: false,
        is_active: true,
        permissions: {
          can_view: true,
          can_edit: false,
          can_delete: false,
          can_export: false,
          can_manage_users: false,
          is_full_admin: false
        },
        signature_data: {
          cpf: '',
          cargo: '',
          endereco: '',
          cep: '',
          telefone: ''
        }
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingUser(null);
  };

  const handlePermissionChange = (key) => {
    setFormData(prev => {
      const newPermissions = { ...prev.permissions };
      
      // Se marcou is_full_admin, marca todas as outras permissões
      if (key === 'is_full_admin' && !newPermissions.is_full_admin) {
        return {
          ...prev,
          is_admin: true,
          permissions: {
            can_view: true,
            can_edit: true,
            can_delete: true,
            can_export: true,
            can_manage_users: true,
            is_full_admin: true
          }
        };
      }
      
      // Se desmarcou is_full_admin
      if (key === 'is_full_admin' && newPermissions.is_full_admin) {
        return {
          ...prev,
          is_admin: false,
          permissions: {
            ...newPermissions,
            is_full_admin: false
          }
        };
      }
      
      // Verifica se está desmarcando uma permissão quando is_full_admin está ativo
      if (newPermissions.is_full_admin && newPermissions[key]) {
        return {
          ...prev,
          is_admin: false,
          permissions: {
            ...newPermissions,
            [key]: false,
            is_full_admin: false
          }
        };
      }
      
      newPermissions[key] = !newPermissions[key];
      
      return {
        ...prev,
        permissions: newPermissions
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name || !formData.email) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    if (!editingUser && !formData.password) {
      toast.error('Senha é obrigatória para novos usuários');
      return;
    }

    try {
      const submitData = {
        name: formData.name,
        email: formData.email,
        is_admin: formData.permissions.is_full_admin || formData.is_admin,
        is_active: formData.is_active,
        permissions: formData.permissions,
        signature_data: formData.signature_data
      };

      if (formData.password) {
        submitData.password = formData.password;
      }

      if (editingUser) {
        await api.put(`/users/${editingUser.user_id}`, submitData);
        toast.success('Usuário atualizado com sucesso!');
      } else {
        await api.post('/users', submitData);
        toast.success('Usuário criado com sucesso!');
      }
      closeModal();
      fetchUsers();
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao salvar usuário';
      toast.error(message);
    }
  };

  const handleDelete = async (userId, userName) => {
    if (!window.confirm(`Tem certeza que deseja excluir o usuário "${userName}"? Esta ação não pode ser desfeita.`)) {
      return;
    }

    try {
      await api.delete(`/users/${userId}`);
      toast.success('Usuário excluído com sucesso!');
      fetchUsers();
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao excluir usuário';
      toast.error(message);
    }
  };

  const toggleStatus = async (user) => {
    try {
      await api.put(`/users/${user.user_id}`, {
        is_active: !user.is_active
      });
      toast.success(`Usuário ${user.is_active ? 'desativado' : 'ativado'} com sucesso!`);
      fetchUsers();
    } catch (error) {
      toast.error('Erro ao alterar status do usuário');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getPermissionsBadges = (user) => {
    if (!user.permissions) {
      return user.is_admin ? 'Admin' : 'Visualizar';
    }
    
    if (user.permissions.is_full_admin) {
      return 'Admin Completo';
    }

    const activePerms = [];
    if (user.permissions.can_view) activePerms.push('Ver');
    if (user.permissions.can_edit) activePerms.push('Editar');
    if (user.permissions.can_delete) activePerms.push('Excluir');
    if (user.permissions.can_export) activePerms.push('Exportar');
    if (user.permissions.can_manage_users) activePerms.push('Usuários');
    
    return activePerms.join(', ') || 'Sem permissões';
  };

  // Filtrar usuários
  const filteredUsers = users.filter(user => {
    const matchSearch = 
      user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchSearch;
  });

  // Dados paginados
  const paginatedUsers = paginateData(filteredUsers, currentPage, pageSize);

  // Reset página quando filtro muda
  useEffect(() => {
    resetPage();
  }, [searchTerm]);

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
      <div className="space-y-6" data-testid="users-page">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground flex items-center gap-2">
              <UsersIcon size={32} />
              Gerenciamento de Usuários
            </h2>
            <p className="text-muted-foreground mt-1">{filteredUsers.length} usuário(s) encontrado(s)</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Campo de Busca */}
            <div className="relative">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Buscar por nome ou email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none w-64"
                data-testid="search-users-input"
              />
            </div>
            <button
              onClick={() => openModal()}
              data-testid="create-user-btn"
              className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-lg hover:bg-secondary/90 transition-colors shadow-sm"
            >
              <Plus size={18} />
              Novo Usuário
            </button>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted text-foreground">
                <tr>
                  <th className="px-4 py-3 text-left">Nome</th>
                  <th className="px-4 py-3 text-left">E-mail</th>
                  <th className="px-4 py-3 text-center">Perfil</th>
                  <th className="px-4 py-3 text-left">Permissões</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-center">Cadastro</th>
                  <th className="px-4 py-3 text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {paginatedUsers.map((user) => (
                  <tr key={user.user_id} className="border-b border-border hover:bg-muted/50 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      <div className="flex items-center gap-2">
                        {user.is_admin ? (
                          <Shield className="w-4 h-4 text-amber-600" title="Administrador" />
                        ) : (
                          <UserIcon className="w-4 h-4 text-muted-foreground" title="Usuário Padrão" />
                        )}
                        {user.name}
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{user.email}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        user.is_admin 
                          ? 'bg-amber-100 text-amber-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {user.is_admin ? 'Administrador' : 'Usuário Padrão'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {user.permissions?.is_full_admin ? (
                          <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-xs flex items-center gap-1">
                            <Shield className="w-3 h-3" /> Admin Completo
                          </span>
                        ) : (
                          <>
                            {user.permissions?.can_view && (
                              <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">Ver</span>
                            )}
                            {user.permissions?.can_edit && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs">Editar</span>
                            )}
                            {user.permissions?.can_delete && (
                              <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded text-xs">Excluir</span>
                            )}
                            {user.permissions?.can_export && (
                              <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-xs">Exportar</span>
                            )}
                            {user.permissions?.can_manage_users && (
                              <span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded text-xs">Usuários</span>
                            )}
                            {!user.permissions && (
                              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                                {user.is_admin ? 'Admin (legado)' : 'Ver apenas'}
                              </span>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => toggleStatus(user)}
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold transition-colors ${
                          user.is_active !== false
                            ? 'bg-green-100 text-green-800 hover:bg-green-200'
                            : 'bg-red-100 text-red-800 hover:bg-red-200'
                        }`}
                      >
                        {user.is_active !== false ? (
                          <>
                            <UserCheck className="w-3 h-3" />
                            Ativo
                          </>
                        ) : (
                          <>
                            <UserX className="w-3 h-3" />
                            Inativo
                          </>
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-muted-foreground">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => openModal(user)}
                          className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(user.user_id, user.name)}
                          className="p-2 text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                          title="Excluir"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginação */}
          <div className="p-4 border-t border-border">
            <Pagination
              currentPage={currentPage}
              totalItems={filteredUsers.length}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
              onPageSizeChange={setPageSize}
            />
          </div>

          {filteredUsers.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              {searchTerm ? 'Nenhum usuário encontrado com os filtros aplicados' : 'Nenhum usuário cadastrado'}
            </div>
          )}
        </div>

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex justify-between items-center">
                <h3 className="text-xl font-heading font-bold text-foreground">
                  {editingUser ? 'Editar Usuário' : 'Novo Usuário'}
                </h3>
                <button
                  onClick={closeModal}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                {/* Dados Básicos */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Nome Completo *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="Digite o nome"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      E-mail *
                    </label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="email@exemplo.com"
                      required
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-foreground mb-1">
                      {editingUser ? 'Nova Senha (deixe em branco para manter)' : 'Senha *'}
                    </label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder={editingUser ? '••••••••' : 'Digite a senha'}
                      required={!editingUser}
                    />
                  </div>
                </div>

                {/* Permissões */}
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <Lock className="w-5 h-5 text-primary" />
                    <h4 className="text-lg font-semibold text-foreground">Permissões do Usuário</h4>
                  </div>
                  
                  <div className="bg-muted/30 rounded-lg p-4 space-y-3">
                    {PERMISSIONS_CONFIG.map(({ key, label, icon: Icon, description }) => (
                      <label
                        key={key}
                        className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                          formData.permissions[key]
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={formData.permissions[key]}
                          onChange={() => handlePermissionChange(key)}
                          className="mt-1 h-4 w-4 text-primary border-border rounded focus:ring-primary"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Icon className={`w-4 h-4 ${formData.permissions[key] ? 'text-primary' : 'text-muted-foreground'}`} />
                            <span className={`font-medium ${formData.permissions[key] ? 'text-foreground' : 'text-muted-foreground'}`}>
                              {label}
                            </span>
                            {key === 'is_full_admin' && (
                              <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-xs">
                                Master
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">{description}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Dados para Assinatura Digital */}
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <PenTool className="w-5 h-5 text-primary" />
                    <h4 className="text-lg font-semibold text-foreground">Dados para Assinatura Digital</h4>
                    <span className="text-xs text-amber-600 font-medium">(CPF e Cargo são obrigatórios para assinar documentos)</span>
                  </div>
                  
                  <div className="bg-muted/30 rounded-lg p-4 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          CPF <span className="text-red-500">*</span>
                        </label>
                        <CPFInput
                          value={formData.signature_data?.cpf || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            signature_data: { ...formData.signature_data, cpf: e.target.value }
                          })}
                          className={`w-full px-3 py-2 border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent ${
                            !formData.signature_data?.cpf?.trim() ? 'border-amber-400' : 'border-border'
                          }`}
                          data-testid="user-cpf-input"
                        />
                        <p className="text-xs text-muted-foreground mt-1">Obrigatório para assinar documentos</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          Cargo Ocupado <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.signature_data?.cargo || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            signature_data: { ...formData.signature_data, cargo: e.target.value }
                          })}
                          className={`w-full px-3 py-2 border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent ${
                            !formData.signature_data?.cargo?.trim() ? 'border-amber-400' : 'border-border'
                          }`}
                          placeholder="Ex: Assessor de Planejamento"
                          data-testid="user-cargo-input"
                        />
                        <p className="text-xs text-muted-foreground mt-1">Obrigatório para assinar documentos</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          Telefone
                        </label>
                        <TelefoneInput
                          value={formData.signature_data?.telefone || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            signature_data: { ...formData.signature_data, telefone: e.target.value }
                          })}
                          className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                          data-testid="user-telefone-input"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          CEP
                        </label>
                        <CEPInput
                          value={formData.signature_data?.cep || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            signature_data: { ...formData.signature_data, cep: e.target.value }
                          })}
                          className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                          data-testid="user-cep-input"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-foreground mb-1">
                          <MapPin size={14} className="inline mr-1" />
                          Endereço Completo
                        </label>
                        <input
                          type="text"
                          value={formData.signature_data?.endereco || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            signature_data: { ...formData.signature_data, endereco: e.target.value }
                          })}
                          className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
                          placeholder="Rua, Número, Bairro, Cidade - UF"
                          data-testid="user-endereco-input"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Status */}
                <div className="flex items-center gap-3 p-4 bg-muted/30 rounded-lg">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="h-4 w-4 text-primary border-border rounded focus:ring-primary"
                    />
                    <span className="font-medium text-foreground">Usuário Ativo</span>
                  </label>
                  <span className="text-xs text-muted-foreground">
                    (Usuários inativos não podem fazer login)
                  </span>
                </div>

                {/* Botões */}
                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                  >
                    <Save size={18} />
                    {editingUser ? 'Salvar Alterações' : 'Criar Usuário'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Users;
