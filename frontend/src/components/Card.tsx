import React from 'react';
import styles from './Card.module.css';

export default function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={[styles.card, className].filter(Boolean).join(' ')}>{children}</div>;
}
