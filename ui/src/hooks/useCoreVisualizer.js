import { useEffect, useRef } from 'react';

/**
 * useCoreVisualizer - Renders a rotating 3D-like geometric wireframe.
 * Reacts to phase and potentially audio.
 */
export function useCoreVisualizer(canvasRef, phase, awakened) {
    const rafRef = useRef(null);
    const angleRef = useRef(0);
    const scaleRef = useRef(1);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();
        window.addEventListener('resize', resize);

        // Simple 3D projection points for an Icosahedron-like shape
        const points = [];
        const phi = (1 + Math.sqrt(5)) / 2;
        const vertices = [
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
        ];

        const edges = [];
        for (let i = 0; i < vertices.length; i++) {
            for (let j = i + 1; j < vertices.length; j++) {
                const d = Math.sqrt(
                    Math.pow(vertices[i][0] - vertices[j][0], 2) +
                    Math.pow(vertices[i][1] - vertices[j][1], 2) +
                    Math.pow(vertices[i][2] - vertices[j][2], 2)
                );
                // Edges connect vertices that are a certain distance apart
                if (Math.abs(d - 2) < 0.1) edges.push([i, j]);
            }
        }

        const project = (x, y, z, angle, scale, cx, cy) => {
            // Rotation
            const x1 = x * Math.cos(angle) - z * Math.sin(angle);
            const z1 = x * Math.sin(angle) + z * Math.cos(angle);
            const y1 = y * Math.cos(angle * 0.7) - z1 * Math.sin(angle * 0.7);
            const z2 = y * Math.sin(angle * 0.7) + z1 * Math.cos(angle * 0.7);

            // Projection
            const factor = 400 / (400 + z2);
            return {
                x: x1 * factor * scale + cx,
                y: y1 * factor * scale + cy
            };
        };

        const loop = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            const cx = canvas.width / 2;
            const cy = canvas.height / 2;
            
            // Animation logic
            angleRef.current += 0.01;
            
            // Pulsing logic based on phase
            let targetScale = awakened ? 150 : 100;
            if (phase === 'listen') targetScale = 220 + Math.sin(Date.now() / 100) * 20;
            if (phase === 'think') targetScale = 180 + Math.sin(Date.now() / 50) * 40;
            if (phase === 'speak') targetScale = 200 + Math.sin(Date.now() / 150) * 10;
            
            scaleRef.current += (targetScale - scaleRef.current) * 0.1;

            const color = phase === 'listen' ? '#ff3d5a' : 
                          phase === 'think' ? '#ffb300' : 
                          phase === 'speak' ? '#00e5ff' : 
                          awakened ? '#00e5ff' : '#1a237e';

            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.shadowBlur = 15;
            ctx.shadowColor = color;

            const projected = vertices.map(v => project(v[0], v[1], v[2], angleRef.current, scaleRef.current, cx, cy));

            ctx.beginPath();
            edges.forEach(([i, j]) => {
                ctx.moveTo(projected[i].x, projected[i].y);
                ctx.lineTo(projected[j].x, projected[j].y);
            });
            ctx.stroke();

            // Draw small nodes at vertices
            projected.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
            });

            rafRef.current = requestAnimationFrame(loop);
        };

        loop();

        return () => {
            cancelAnimationFrame(rafRef.current);
            window.removeEventListener('resize', resize);
        };
    }, [phase, awakened, canvasRef]);
}
