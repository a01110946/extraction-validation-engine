// File: frontend/src/components/Viewer3D.jsx
/**
 * 3D viewer for reinforcement visualization using Three.js.
 */

import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { useExtractionStore } from '../store/useExtractionStore';
import './Viewer3D.css';

// Longitudinal bar component
function LongitudinalBar({ barData, section }) {
  // Transform coordinates: Engineering Z-up to Three.js Y-up
  // [x, y, z] backend -> [x, z, y] Three.js (Y is up, Z is depth)
  // Apply centering offset to align with ConcreteSection
  const offsetX = -section.width_mm / 2;
  const offsetZ = -section.depth_mm / 2;

  const start = [
    barData.start.x + offsetX,
    barData.start.z,
    barData.start.y + offsetZ
  ];
  const end = [
    barData.end.x + offsetX,
    barData.end.z,
    barData.end.y + offsetZ
  ];
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
      <mesh>
        <cylinderGeometry args={[radius, radius, length, 16]} />
        <meshStandardMaterial color="#cc3333" roughness={0.4} metalness={0.6} />
      </mesh>
    </group>
  );
}

// Stirrup component
function Stirrup({ stirrupData }) {
  // Transform coordinates: Engineering Z-up to Three.js Y-up
  const points = stirrupData.path.map((pt) => [pt.x, pt.z, pt.y]);
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

        // Calculate rotation to align cylinder with segment direction
        const direction = new THREE.Vector3(dx, dy, dz).normalize();
        const axis = new THREE.Vector3(0, 1, 0).cross(direction).normalize();
        const angle = Math.acos(new THREE.Vector3(0, 1, 0).dot(direction));

        return (
          <group key={idx} position={midpoint}>
            <mesh rotation={[axis.x * angle, axis.y * angle, axis.z * angle]}>
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
      {/* Bottom face (XZ plane at Y=0) */}
      <lineSegments rotation={[Math.PI / 2, 0, 0]}>
        <edgesGeometry
          args={[new THREE.BoxGeometry(width_mm, depth_mm, 1)]}
        />
        <lineBasicMaterial color="#666666" linewidth={2} />
      </lineSegments>

      {/* Top face (XZ plane at Y=height) */}
      <group position={[0, height_mm, 0]}>
        <lineSegments rotation={[Math.PI / 2, 0, 0]}>
          <edgesGeometry
            args={[new THREE.BoxGeometry(width_mm, depth_mm, 1)]}
          />
          <lineBasicMaterial color="#666666" linewidth={2} />
        </lineSegments>
      </group>

      {/* Vertical edges (along Y-axis) */}
      {[
        [-width_mm / 2, depth_mm / 2],
        [width_mm / 2, depth_mm / 2],
        [width_mm / 2, -depth_mm / 2],
        [-width_mm / 2, -depth_mm / 2],
      ].map(([x, z], idx) => (
        <mesh key={idx} position={[x, height_mm / 2, z]}>
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

      {/* All geometry in one group (no offset - section will handle its own centering) */}
      <group>
        {/* Concrete section outline */}
        <ConcreteSection section={section} />

        {/* Longitudinal bars */}
        {longitudinal_bars.map((bar, idx) => (
          <LongitudinalBar key={`bar-${idx}`} barData={bar} section={section} />
        ))}

        {/* Stirrups */}
        {stirrups.map((stirrup, idx) => (
          <Stirrup key={`stirrup-${idx}`} stirrupData={stirrup} section={section} />
        ))}
      </group>

      {/* Grid helper (on ground plane Y=0) */}
      <Grid
        args={[20000, 20000]}
        cellSize={500}
        cellThickness={1}
        cellColor="#444444"
        sectionSize={1000}
        sectionThickness={1.5}
        sectionColor="#666666"
        fadeDistance={25000}
        fadeStrength={0.5}
        infiniteGrid
        position={[0, -10, 0]}
        rotation={[0, 0, 0]}
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
          <PerspectiveCamera
            makeDefault
            position={[1500, 1500, 2000]}
            fov={60}
            near={10}
            far={50000}
          />
          <Suspense fallback={null}>
            <Scene />
          </Suspense>
          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            target={[0, 1500, 0]}
            minDistance={800}
            maxDistance={6000}
            zoomSpeed={0.5}
            panSpeed={0.5}
            rotateSpeed={0.4}
            dampingFactor={0.08}
            enableDamping={true}
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
