import React from 'react';
import styles from './ProgressBar.module.css';

export default function ProgressBar({ value }: { value: number }) {
  return (
    <div className={styles.container}>
      <div className={styles.bar} style={{ width: `${value}%` }} />
    </div>
  );
}
