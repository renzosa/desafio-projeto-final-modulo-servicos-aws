import React, { useState, useEffect } from 'react';
import axios from 'axios';

function DashboardPage({ onLogout }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_API_GATEWAY_URL}/files`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setFiles(response.data);
      setLoading(false);
    } catch (err) {
      setError('Erro ao carregar arquivos');
      setLoading(false);
    }
  };

  const generateFile = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${process.env.REACT_APP_API_GATEWAY_URL}/files/generate`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      fetchFiles();
    } catch (err) {
      setError('Erro ao gerar arquivo');
    }
  };

  const deleteFile = async (fileName) => {
    const confirmDelete = window.confirm(`Deseja realmente excluir o arquivo ${fileName}?`);

    if (confirmDelete) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(
          `${process.env.REACT_APP_API_GATEWAY_URL}/files/${fileName}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        fetchFiles();
      } catch (err) {
        setError('Erro ao excluir arquivo');
      }
    }
  };

  if (loading) {
    return (
      <div className="container mt-5">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <nav className="navbar navbar-expand-lg navbar-light bg-light mb-4">
        <div className="container-fluid">
          <span className="navbar-brand">Gerenciador de Arquivos</span>
          <button
            className="btn btn-outline-danger ms-auto"
            onClick={onLogout}
          >
            Logout
          </button>
        </div>
      </nav>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Lista de Arquivos</h5>
          <button
            className="btn btn-primary"
            onClick={generateFile}
          >
            Gerar Novo Arquivo
          </button>
        </div>
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Nome do Arquivo</th>
                  <th>Número de Linhas</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.name}>
                    <td>{file.name}</td>
                    <td>{file.lines}</td>
                    <td>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => deleteFile(file.name)}
                      >
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))}
                {files.length === 0 && (
                  <tr>
                    <td colSpan="3" className="text-center">
                      Nenhum arquivo encontrado
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;