CREATE TABLE IF NOT EXISTS citas_prueba (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, fecha_hora TEXT NOT NULL, lugar TEXT NOT NULL DEFAULT '');

CREATE TABLE IF NOT EXISTS envios (id INTEGER PRIMARY KEY AUTOINCREMENT, enviado_en TEXT NOT NULL);

INSERT OR REPLACE INTO citas_prueba (id, titulo, fecha_hora, lugar) VALUES (1, 'Cita de prueba con la doctora Ejemplo', '2026-11-20 10:00', 'Hospital Inventado'), (2, 'Revisión de mentira', '2026-11-25 17:30', 'Centro de Salud Ficticio');
