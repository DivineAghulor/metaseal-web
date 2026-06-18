import React from 'react';
import Header from './Header';
import styles from './Layout.module.css';

export default function Layout({ children, session }: { children: React.ReactNode; session: any }) {
  return (
    <div>
      <Header session={session} />
      <main className={styles.container}>{children}</main>
    </div>
  );
}
