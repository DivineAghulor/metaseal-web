import React from 'react';
import styles from './Header.module.css';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';

export default function Header({ session }: { session: any }) {
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/login');
  };

  return (
    <header className={styles.header}>
      <div className={styles.logo}>Image Authenticate Pro</div>
      <div className={styles.nav}>
        {session?.user?.email ? (
          <>
            <div className={styles.user}>{session.user.email}</div>
            <button className={styles.signout} onClick={handleSignOut}>Sign Out</button>
          </>
        ) : (
          <div />
        )}
      </div>
    </header>
  );
}
