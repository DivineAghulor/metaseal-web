import { useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '../supabaseClient';
import Card from '../components/Card';
import FileUploader from '../components/FileUploader';
import Input from '../components/Input';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import useFakeProgress from '../hooks/useFakeProgress';

export default function Dashboard({ session }: { session: Session }) {
  const [file, setFile] = useState<File | null>(null);
  const [caption, setCaption] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const { progress, visible } = useFakeProgress(loading, 15000);

  const handleWatermark = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('image', file);
    formData.append('caption', caption);

    try {
      const response = await fetch(`${import.meta.env.VITE_MODAL_BACKEND_URL}/watermark`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}` // Send the JWT for backend validation
        },
        body: formData,
      });

      if (!response.ok) throw new Error("Watermark failed");
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '760px', margin: '40px auto', fontFamily: 'Inter, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <h2>Researcher Dashboard</h2>
        <div style={{ color: 'var(--muted)' }}>Logged in as: {session.user.email}</div>
      </div>

      <Card className="center" style={{ marginTop: 16 }}>
        <form onSubmit={handleWatermark} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <FileUploader label="Select Image to Protect" accept="image/png, image/jpeg" currentName={file?.name || null} onFileChange={(f) => setFile(f)} />
          <Input label="Image Caption (Optional)" type="text" placeholder="Caption or notes" value={caption} onChange={(e) => setCaption(e.target.value)} />

          <Button type="submit" disabled={!file || loading}>{loading ? 'Embedding Watermark...' : 'Protect & Watermark Image'}</Button>
          {visible && <ProgressBar value={progress} />}
        </form>
      </Card>

      {result && (
        <Card style={{ marginTop: 20 }}>
          <h3 style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>✓</span>
            Watermark Successful
          </h3>
          <p style={{ color: 'var(--muted)' }}><strong>Image ID:</strong> {result.image_id}</p>
          <p><a href={result.watermarked_url} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)' }}>Download Watermarked Image</a></p>
          <details>
            <summary style={{ color: 'var(--muted)' }}>View Public Key</summary>
            <pre style={{ fontSize: 12, overflowX: 'auto', marginTop: 8 }}>{result.public_key}</pre>
          </details>
        </Card>
      )}
    </div>
  );
}