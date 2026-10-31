import React from 'react';
import styles from './SignalLine.module.css';

// The brand device as an interface state: one cyan line across the navy ground, with nodes
// where structure is found. Drawn once on load; still for people who ask for reduced motion.
const POINTS = [
  [0, 210], [70, 180], [120, 196], [170, 150], [230, 168], [290, 118], [340, 132], [400, 92],
  [450, 120], [510, 70], [560, 88], [620, 52], [680, 76], [740, 40], [800, 58],
];
const NODES = [3, 7, 11, 13];

export default function SignalLine(): JSX.Element {
  const d = POINTS.map(([x, y], i) => `${i ? 'L' : 'M'} ${x} ${y}`).join(' ');
  return (
    <svg className={styles.svg} viewBox="0 0 800 240" preserveAspectRatio="none" aria-hidden="true">
      {[60, 120, 180].map((y) => (
        <line key={y} x1="0" x2="800" y1={y} y2={y} className={styles.grid} />
      ))}
      <path d={d} className={styles.line} pathLength={1} />
      {NODES.map((i) => (
        <circle key={i} cx={POINTS[i][0]} cy={POINTS[i][1]} r="5" className={styles.node}
                style={{animationDelay: `${0.4 + i * 0.08}s`}} />
      ))}
    </svg>
  );
}
