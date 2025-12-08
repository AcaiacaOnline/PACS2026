import React, { useState, useEffect } from 'react';
import { Users as UsersIcon, Plus, Edit, Trash2, UserCheck, UserX, Shield, User as UserIcon, X, Save } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    is_admin: false,
    is_active: true
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
        is_active: user.is_active ?? true
      });
    } else {
      setEditingUser(null);
      setFormData({
        name: '',
        email: '',
        password: '',
        is_admin: false,
        is_active: true
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingUser(null);
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
      if (editingUser) {
        const updateData = { ...formData };
        if (!updateData.password) {
          delete updateData.password;
        }
        await api.put(`/users/${editingUser.user_id}`, updateData);
        toast.success('Usuário atualizado com sucesso!');
      } else {
        await api.post('/users', formData);
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
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground flex items-center gap-2">
              <UsersIcon size={32} />
              Gerenciamento de Usuários
            </h2>
            <p className="text-muted-foreground mt-1">{users.length} usuário(s) cadastrado(s)</p>
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

        {/* Users Table */}
        <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted text-foreground">
                <tr>
                  <th className="px-4 py-3 text-left">Nome</th>
                  <th className="px-4 py-3 text-left">E-mail</th>
                  <th className="px-4 py-3 text-center">Perfil</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-center">Cadastro</th>
                  <th className="px-4 py-3 text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
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
                    <td className="px-4 py-3 text-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        user.is_active !== false
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {user.is_active !== false ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-muted-foreground">{formatDate(user.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => openModal(user)}
                          data-testid={`edit-user-${user.user_id}`}
                          className="text-accent hover:text-accent/80 transition-colors p-1"
                          title="Editar"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => toggleStatus(user)}
                          data-testid={`toggle-status-${user.user_id}`}
                          className={`transition-colors p-1 ${
                            user.is_active !== false
                              ? 'text-orange-600 hover:text-orange-700' 
                              : 'text-green-600 hover:text-green-700'
                          }`}
                          title={user.is_active !== false ? 'Desativar' : 'Ativar'}
                        >
                          {user.is_active !== false ? <UserX size={16} /> : <UserCheck size={16} />}
                        </button>
                        <button
                          onClick={() => handleDelete(user.user_id, user.name)}
                          data-testid={`delete-user-${user.user_id}`}
                          className="text-destructive hover:text-destructive/80 transition-colors p-1"
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
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-md border border-border">
            <div className="flex justify-between items-center p-6 border-b border-border">
              <h3 className="text-xl font-heading font-bold text-foreground">
                {editingUser ? 'Editar Usuário' : 'Novo Usuário'}
              </h3>
              <button onClick={closeModal} className="text-muted-foreground hover:text-foreground transition-colors">
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">
                  Nome Completo <span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="user-name-input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">
                  E-mail <span className="text-destructive">*</span>
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="user-email-input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">
                  Senha {!editingUser && <span className="text-destructive">*</span>}
                  {editingUser && <span className="text-muted-foreground text-xs ml-2">(deixe em branco para manter)</span>}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="user-password-input"
                  required={!editingUser}
                />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_admin}
                    onChange={(e) => setFormData({ ...formData, is_admin: e.target.checked })}
                    className="w-4 h-4 rounded border-input focus:ring-2 focus:ring-ring"
                    data-testid="user-admin-checkbox"
                  />
                  <span className="text-sm font-semibold text-foreground flex items-center gap-1">
                    <Shield size={16} className="text-amber-600" />
                    Administrador
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 rounded border-input focus:ring-2 focus:ring-ring"
                    data-testid="user-active-checkbox"
                  />
                  <span className="text-sm font-semibold text-foreground flex items-center gap-1">
                    <UserCheck size={16} className="text-green-600" />
                    Ativo
                  </span>
                </label>
              </div>
              {!formData.is_admin && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm text-blue-800">
                  <strong>Permissões de Usuário Padrão:</strong>
                  <ul className="mt-1 ml-4 list-disc">
                    <li>Criar seus próprios PACs</li>
                    <li>Editar e excluir apenas seus PACs</li>
                    <li>Visualizar PACs de outros usuários</li>
                  </ul>
                </div>
              )}
            </form>
            <div className="p-6 border-t border-border bg-muted/50 rounded-b-xl flex justify-end gap-3">
              <button
                type="button"
                onClick={closeModal}
                className="px-4 py-2 border border-border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmit}
                data-testid="save-user-btn"
                className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Save size={16} />
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default Users;
