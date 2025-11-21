// File: frontend/src/components/Viewer3D.jsx
/**
 * 3D viewer for reinforcement visualization using Three.js.
 */

import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, PerspectiveCamera } from '@react-three/drei';
import { useExtractionStore } from '../store/useExtractionStore';
import './Viewer3D.css';

// Longitudinal bar component
function LongitudinalBar({ barData }) {
  const start = [barData.start.x, barData.start.y, barData.start.z];
  const end = [barData.end.x, barData.end.y, barData.end.z];
  const radius = barData.diameter_mm / 2;

  // Calculate bar direction and length
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const dz = end[2] - start[2];
  const length = Math.sqrt(dx * dx + dy * dy + dz * dz);

  // Calculate rotation to align cylinder with bar direction
  const midpoint = [
    (start[0] + end[0]) / 2,
    (start[1] + end[1]) / 2,
    (start[2] + end[2]) / 2,
  ];

  return (
    <group position={midpoint}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[radius, radius, length, 16]} />
        <meshStandardMaterial color="#cc3333" roughness={0.4} metalness={0.6} />
      </mesh>
    </group>
  );
}

// Stirrup component
function Stirrup({ stirrupData }) {
  const points = stirrupData.path.map((pt) => [pt.x, pt.y, pt.z]);
  const radius = stirrupData.diameter_mm / 2;

  return (
    <group>
      {points.slice(0, -1).map((start, idx) => {
        const end = points[idx + 1];
        const dx = end[0] - start[0];
        const dy = end[1] - start[1];
        const dz = end[2] - start[2];
        const length = Math.sqrt(dx * dx + dy * dy + dz * dz);

        const midpoint = [
          (start[0] + end[0]) / 2,
          (start[1] + end[1]) / 2,
          (start[2] + end[2]) / 2,
        ];

        // Calculate rotation angle
        const angle = Math.atan2(dy, dx);

        return (
          <group key={idx} position={midpoint}>
            <mesh rotation={[0, 0, angle]}>
              <cylinderGeometry args={[radius, radius, length, 8]} />
              <meshStandardMaterial
                color="#3399ff"
                roughness={0.5}
                metalness={0.5}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

// Concrete section outline
function ConcreteSection({ section }) {
  const { width_mm, depth_mm, height_mm } = section;

  return (
    <group>
      {/* Bottom face */}
      <lineSegments>
        <edgesGeometry
          args={[new THREE.BoxGeometry(width_mm, depth_mm, 1)]}
        />
        <lineBasicMaterial color="#666666" linewidth={2} />
      </lineSegments>

      {/* Top face */}
      <group position={[0, 0, height_mm]}>
        <lineSegments>
          <edgesGeometry
            args={[new THREE.BoxGeometry(width_mm, depth_mm, 1)]}
          />
          <lineBasicMaterial color="#666666" linewidth={2} />
        </lineSegments>
      </group>

      {/* Vertical edges */}
      {[
        [-width_mm / 2, -depth_mm / 2],
        [width_mm / 2, -depth_mm / 2],
        [width_mm / 2, depth_mm / 2],
        [-width_mm / 2, depth_mm / 2],
      ].map(([x, y], idx) => (
        <mesh key={idx} position={[x, y, height_mm / 2]}>
          <cylinderGeometry args={[0.5, 0.5, height_mm, 8]} />
          <meshBasicMaterial color="#666666" />
        </mesh>
      ))}
    </group>
  );
}

// Main scene component
function Scene() {
  const { geometry } = useExtractionStore();

  if (!geometry) {
    return (
      <group>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
      </group>
    );
  }

  const { longitudinal_bars, stirrups, section } = geometry;

  return (
    <group>
      {/* Lighting */}
      <ambientLight intensity={0.6} />
      <pointLight position={[1000, 1000, 1000]} intensity={0.8} />
      <pointLight position={[-1000, -1000, 500]} intensity={0.4} />

      {/* Center geometry at origin */}
      <group position={[-section.width_mm / 2, -section.depth_mm / 2, 0]}>
        {/* Concrete section outline */}
        <ConcreteSection section={section} />

        {/* Longitudinal bars */}
        {longitudinal_bars.map((bar, idx) => (
          <LongitudinalBar key={`bar-${idx}`} barData={bar} />
        ))}

        {/* Stirrups */}
        {stirrups.map((stirrup, idx) => (
          <Stirrup key={`stirrup-${idx}`} stirrupData={stirrup} />
        ))}
      </group>

      {/* Grid helper */}
      <Grid
        args={[10000, 10000]}
        cellSize={500}
        cellThickness={1}
        cellColor="#444444"
        sectionSize={1000}
        sectionThickness={1.5}
        sectionColor="#666666"
        fadeDistance={15000}
        fadeStrength={1}
        infiniteGrid
        position={[0, 0, -10]}
      />
    </group>
  );
}

export default function Viewer3D() {
  const { geometry, loading } = useExtractionStore();

  return (
    <div className="viewer-container">
      {loading ? (
        <div className="viewer-loading">
          <div className="spinner"></div>
          <p>Processing extraction...</p>
        </div>
      ) : geometry ? (
        <Canvas shadows>
          <PerspectiveCamera makeDefault position={[2000, 2000, 1500]} fov={50} />
          <Suspense fallback={null}>
            <Scene />
          </Suspense>
          <OrbitControls
            enablePan
            enableZoom
            enableRotate
            minDistance={500}
            maxDistance={10000}
          />
        </Canvas>
      ) : (
        <div className="viewer-empty">
          <p>Upload an image to view 3D reinforcement</p>
        </div>
      )}
    </div>
  );
}
