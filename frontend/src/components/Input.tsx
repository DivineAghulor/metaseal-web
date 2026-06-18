import React from 'react';
import styles from './Input.module.css';

type Props = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
};

export default function Input({ label, className, ...rest }: Props) {
  return (
    <div className={[styles.wrapper, className].filter(Boolean).join(' ')}>
      {label && <label className={styles.label}>{label}</label>}
      <input className={styles.input} {...rest} />
    </div>
  );
}
