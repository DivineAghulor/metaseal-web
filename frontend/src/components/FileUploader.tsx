import React from 'react';
import styles from './FileUploader.module.css';

export default function FileUploader({
  accept,
  onFileChange,
  label,
  currentName,
}: {
  accept?: string;
  label?: string;
  currentName?: string | null;
  onFileChange: (file: File | null) => void;
}) {
  return (
    <label className={styles.uploader}>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, color: 'var(--text)' }}>{label || 'Upload file'}</div>
        <div className={styles.placeholder}>{currentName || 'PNG or JPEG, up to 10MB'}</div>
      </div>
      <input
        className={styles.input}
        type="file"
        accept={accept}
        onChange={(e) => onFileChange(e.target.files?.[0] || null)}
      />
      <span className={styles.button}>Choose</span>
    </label>
  );
}
