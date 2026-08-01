import React, { useState, useRef } from 'react';
import { Sphere, Html, DragControls } from '@react-three/drei';

export default function WorkerDot({ worker, isSelected, onClick, onPositionChange }) {
  const [hovered, setHovered] = useState(false);
  const groupRef = useRef();
  
  const { x, y, z } = worker.position || { x: 0, y: 0, z: 0 };
  const isAccident = worker.status === 'accident';
  
  // 사고 발생은 항상 빨간색 유지, 그 외에는 선택 시 초록색, 기본 파란색
  const color = isAccident ? '#ef4444' : (isSelected ? '#10b981' : '#3b82f6');
  
  return (
    <DragControls
      autoTransform={true}
      onDragEnd={() => {
        if (groupRef.current && onPositionChange) {
          const pos = groupRef.current.position;
          // Subtract 0.5 because we added 0.5 to y for rendering
          onPositionChange(worker.id, pos.x, pos.y - 0.5, pos.z);
        }
      }}
    >
      <group ref={groupRef} position={[x, y + 0.5, z]}>
        <Sphere 
          args={[1.0, 32, 32]} 
          onClick={(e) => {
            // Keep propagation for DragControls, but only toggle selection
            onClick(worker.id);
          }}
          onPointerOver={(e) => {
            document.body.style.cursor = 'grab';
            setHovered(true);
          }}
          onPointerOut={(e) => {
            document.body.style.cursor = 'default';
            setHovered(false);
          }}
          onPointerDown={(e) => {
            document.body.style.cursor = 'grabbing';
          }}
          onPointerUp={(e) => {
            document.body.style.cursor = 'grab';
          }}
        >
          <meshStandardMaterial 
            color={color} 
            emissive={color} 
            emissiveIntensity={hovered ? 0.8 : 0.3} 
          />
        </Sphere>
        
        {/* 팝업 정보 (Hover 시 표시) */}
        {hovered && (
          <Html position={[0, 0.8, 0]} center zIndexRange={[100, 0]} style={{ pointerEvents: 'none' }}>
            <div className="worker-popup">
              <div className="worker-popup-name">{worker.name}</div>
              <div className={`worker-popup-status ${isAccident ? 'accident' : 'normal'}`}>
                {isAccident ? '🚨 사고 발생' : '✅ 정상'}
              </div>
            </div>
          </Html>
        )}
      </group>
    </DragControls>
  );
}
