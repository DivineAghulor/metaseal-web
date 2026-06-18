import { useState } from 'react';
import Card from '../components/Card';
import FileUploader from '../components/FileUploader';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import useFakeProgress from '../hooks/useFakeProgress';

export default function Verify() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const { progress, visible } = useFakeProgress(loading, 15000);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch(`${import.meta.env.VITE_MODAL_BACKEND_URL}/verify`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error("Verification request failed");
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '760px', margin: '40px auto', fontFamily: 'Inter, sans-serif' }}>
      <h2>Public Image Verification</h2>
      <p style={{ color: 'var(--muted)', marginTop: 6 }}>Upload an image to verify its cryptographic authenticity.</p>

      <Card className="center" style={{ marginTop: 16 }}>
        <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <FileUploader label="Image to Verify" accept="image/png, image/jpeg" currentName={file?.name || null} onFileChange={(f) => setFile(f)} />
          <Button type="submit" disabled={!file || loading}>{loading ? 'Verifying on Cloud GPU...' : 'Verify Image'}</Button>
          {visible && <ProgressBar value={progress} />}
        </form>
      </Card>

      {error && <p style={{ color: 'var(--error)', marginTop: '20px' }}>{error}</p>}

      {result && (
        <Card style={{ marginTop: 20 }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: result.outcome === 'authentic' ? 'var(--primary)' : 'var(--error)' }}>{result.outcome === 'authentic' ? '✓' : '⚠'}</span>
            Result: <span style={{ marginLeft: 6, color: result.outcome === 'authentic' ? 'var(--primary)' : 'var(--error)' }}>{result.outcome.toUpperCase()}</span>
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 8, marginTop: 12 }}>
            <div><strong>VSR:</strong> <span style={{ color: result.vsr ? 'var(--primary)' : 'var(--error)' }}>{result.vsr ? 'Passed' : 'Failed'}</span></div>
            <div><strong>QR Recovery:</strong> <span style={{ color: result.qr_recovery ? 'var(--primary)' : 'var(--error)' }}>{result.qr_recovery ? 'Success' : 'Failed'}</span></div>
            <div><strong>Extracted ID:</strong> <span style={{ color: 'var(--muted)' }}>{result.extracted_id || 'None'}</span></div>
          </div>
        </Card>
      )}
    </div>
  );
}