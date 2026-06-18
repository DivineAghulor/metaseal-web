import { useEffect, useRef, useState } from 'react';

export default function useFakeProgress(isLoading: boolean, estimatedDurationMs: number) {
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);
  const intervalRef = useRef<number | null>(null);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (isLoading) {
      setVisible(true);
      setProgress(0);

      const start = Date.now();
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }

      intervalRef.current = window.setInterval(() => {
        const elapsed = Date.now() - start;
        const nextProgress = Math.min(90, (elapsed / estimatedDurationMs) * 90);
        setProgress((current) => Math.max(current, nextProgress));

        if (elapsed >= estimatedDurationMs) {
          if (intervalRef.current) window.clearInterval(intervalRef.current);
        }
      }, 50);
    } else if (visible) {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }

      setProgress(100);
      timeoutRef.current = window.setTimeout(() => {
        setVisible(false);
        setProgress(0);
      }, 500);
    }

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, [isLoading, estimatedDurationMs, visible]);

  return { progress, visible };
}
