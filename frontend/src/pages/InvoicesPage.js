import React, { useState, useEffect } from "react";
import axios from "../utils/axios";
import "../styles/InvoicesPage.css";

function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const res = await axios.get("/invoices");
      setInvoices(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load invoices:", err);
      setError("Failed to load your invoices. Please try again later.");
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading your invoices...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="invoices-container">
      <h1>Your Invoices</h1>
      
      {invoices.length === 0 ? (
        <div className="no-invoices">
          <p>You don't have any invoices yet.</p>
        </div>
      ) : (
        <div className="invoices-table-container">
          <table className="invoices-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Date</th>
                <th>Description</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(invoice => (
                <tr key={invoice.id}>
                  <td>{invoice.invoice_number}</td>
                  <td>{new Date(invoice.created_at).toLocaleDateString()}</td>
                  <td>{invoice.description}</td>
                  <td>${invoice.amount.toFixed(2)}</td>
                  <td>
                    <span className={`status-badge ${invoice.status.toLowerCase()}`}>
                      {invoice.status}
                    </span>
                  </td>
                  <td>
                    {invoice.pdf_url && (
                      <a 
                        href={invoice.pdf_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="download-link"
                      >
                        Download PDF
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default InvoicesPage;
