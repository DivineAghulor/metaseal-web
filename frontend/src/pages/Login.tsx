import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import Card from '../components/Card';
import Input from '../components/Input';
import Button from '../components/Button';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleAuth = async (isSignUp: boolean) => {
    setLoading(true);
    setError(null);
    setMessage(null);

    if (!email || !password) {
      setError('Email and password are required.');
      setLoading(false);
      return;
    }

    const { data, error } = isSignUp
      ? await supabase.auth.signUp({ email, password })
      : await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError(error.message);
    } else if (isSignUp) {
      if (data?.session) {
        navigate('/dashboard');
      } else {
        setMessage('Account created. Please check your email to confirm your address before signing in.');
      }
    } else {
      if (data?.session) {
        navigate('/dashboard');
      } else {
        setError('Unable to sign in. Please check your credentials.');
      }
    }

    setLoading(false);
  };

  return (
    <div style={{ maxWidth: '480px', margin: '80px auto', fontFamily: 'Inter, sans-serif' }}>
      <Card className="center">
        <h2 style={{ marginBottom: 8 }}>Image Authenticate Pro</h2>
        {error && <p style={{ color: 'var(--error)' }}>{error}</p>}
        {message && <p style={{ color: 'var(--primary)' }}>{message}</p>}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAuth(false);
          }}
          style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: 8 }}
        >
          <Input label="Email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input label="Password" type="password" placeholder="Enter password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />

          <Button type="submit" disabled={loading || !email || !password}>
            {loading ? 'Processing...' : 'Sign In'}
          </Button>

          <Button type="button" variant="outline" onClick={() => handleAuth(true)} disabled={loading || !email || !password}>
            Create Account
          </Button>

          <div style={{ marginTop: 6, textAlign: 'right' }}>
            <a href="#" style={{ color: 'var(--muted)', fontSize: 13 }}>Forgot password?</a>
          </div>
        </form>
      </Card>
    </div>
  );
}