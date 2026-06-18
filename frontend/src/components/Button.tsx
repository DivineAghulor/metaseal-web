import React from 'react';
import styles from './Button.module.css';

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'solid' | 'outline';
};

export default function Button({ variant = 'solid', className, disabled, children, ...rest }: Props) {
  const cls = [styles.root, variant === 'solid' ? styles.solid : styles.outline, disabled ? styles.disabled : '', className]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={cls} disabled={disabled} {...rest}>
      {children}
    </button>
  );
}
