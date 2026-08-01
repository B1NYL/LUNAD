import React from 'react';
import { Box, Plane } from '@react-three/drei';

export default function Building3D() {
  const floorHeight = 4;

  return (
    <group>
      {/* Ground / Floor 1 */}
      <Plane args={[20, 20]} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]}>
        <meshStandardMaterial color="#1e293b" transparent opacity={0.8} />
      </Plane>
      {/* Floor 2 */}
      <Plane args={[20, 20]} rotation={[-Math.PI / 2, 0, 0]} position={[0, floorHeight - 0.1, 0]}>
        <meshStandardMaterial color="#334155" transparent opacity={0.4} />
      </Plane>
      {/* Floor 3 */}
      <Plane args={[20, 20]} rotation={[-Math.PI / 2, 0, 0]} position={[0, floorHeight * 2 - 0.1, 0]}>
        <meshStandardMaterial color="#475569" transparent opacity={0.4} />
      </Plane>

      {/* Pillars */}
      {[
        [-9, -9], [-9, 9], [9, -9], [9, 9]
      ].map(([x, z], i) => (
        <Box key={i} args={[0.5, floorHeight * 2, 0.5]} position={[x, floorHeight, z]}>
          <meshStandardMaterial color="#64748b" />
        </Box>
      ))}
    </group>
  );
}
