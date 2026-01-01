import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Dashboard from './pages/Dashboard'
import PipelineCreate from './pages/PipelineCreate'
import PipelineList from './pages/PipelineList'
import PipelineExecute from './pages/PipelineExecute'
import ExecutionDetails from './pages/ExecutionDetails'
import ExecutionsList from './pages/ExecutionsList'
import ESGStandards from './pages/ESGStandards'
import BlockchainAnchor from './pages/BlockchainAnchor'
import Login from './pages/Login'
import Register from './pages/Register'
import AdminPortal from './pages/AdminPortal'
import ProtectedRoute from './components/ProtectedRoute'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/admin"
              element={
                <ProtectedRoute requireAdmin>
                  <AdminPortal />
                </ProtectedRoute>
              }
            />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pipelines"
              element={
                <ProtectedRoute>
                  <PipelineList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pipelines/create"
              element={
                <ProtectedRoute>
                  <PipelineCreate />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pipelines/:id/execute"
              element={
                <ProtectedRoute>
                  <PipelineExecute />
                </ProtectedRoute>
              }
            />
            <Route
              path="/executions"
              element={
                <ProtectedRoute>
                  <ExecutionsList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/executions/:id"
              element={
                <ProtectedRoute>
                  <ExecutionDetails />
                </ProtectedRoute>
              }
            />
            <Route
              path="/executions/:id/blockchain"
              element={
                <ProtectedRoute>
                  <BlockchainAnchor />
                </ProtectedRoute>
              }
            />
            <Route
              path="/esg-standards"
              element={
                <ProtectedRoute>
                  <ESGStandards />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  )
}

export default App

