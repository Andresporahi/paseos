import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

class Database:
    def __init__(self, db_path: str = "paseos.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa las tablas de la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de paseos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paseos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de participantes en paseos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paseo_participantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paseo_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paseo_id) REFERENCES paseos(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                UNIQUE(paseo_id, usuario_id)
            )
        """)
        
        # Tabla de categorías de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paseo_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                icono TEXT DEFAULT '📦',
                color TEXT DEFAULT '#6366f1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paseo_id) REFERENCES paseos(id),
                UNIQUE(paseo_id, nombre)
            )
        """)
        
        # Tabla de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paseo_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                categoria_id INTEGER,
                concepto TEXT NOT NULL,
                valor REAL NOT NULL,
                fecha TIMESTAMP NOT NULL,
                tipo_archivo TEXT,
                archivo_path TEXT,
                transcripcion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paseo_id) REFERENCES paseos(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            )
        """)
        
        # Tabla de división de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gasto_divisiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gasto_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                porcentaje REAL NOT NULL,
                monto REAL NOT NULL,
                FOREIGN KEY (gasto_id) REFERENCES gastos(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                UNIQUE(gasto_id, usuario_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # Métodos de usuarios
    def crear_usuario(self, username: str, password: str, nombre: str, email: str = None) -> bool:
        """Crea un nuevo usuario"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre, email)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, nombre, email))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verificar_usuario(self, username: str, password: str) -> Optional[Dict]:
        """Verifica las credenciales del usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            SELECT id, username, nombre, email FROM usuarios
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    
    def get_usuario(self, usuario_id: int) -> Optional[Dict]:
        """Obtiene información de un usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, nombre, email FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    
    def buscar_usuario_por_username(self, username: str) -> Optional[Dict]:
        """Busca un usuario por su nombre de usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, nombre, email FROM usuarios WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    
    # Métodos de paseos
    def crear_paseo(self, nombre: str, descripcion: str, created_by: int) -> int:
        """Crea un nuevo paseo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO paseos (nombre, descripcion, created_by)
            VALUES (?, ?, ?)
        """, (nombre, descripcion, created_by))
        paseo_id = cursor.lastrowid
        # Agregar el creador como participante
        cursor.execute("""
            INSERT INTO paseo_participantes (paseo_id, usuario_id)
            VALUES (?, ?)
        """, (paseo_id, created_by))
        
        # Crear categorías predeterminadas
        categorias_default = [
            ("🍽️ Restaurante", "🍽️", "#ef4444"),
            ("☕ Cafetería", "☕", "#f59e0b"),
            ("🚗 Transporte", "🚗", "#3b82f6"),
            ("🏨 Hospedaje", "🏨", "#8b5cf6"),
            ("🎫 Entradas", "🎫", "#ec4899"),
            ("🛒 Supermercado", "🛒", "#10b981"),
            ("⛽ Gasolina", "⛽", "#6366f1"),
            ("🎉 Entretenimiento", "🎉", "#f97316"),
            ("💊 Farmacia", "💊", "#14b8a6"),
            ("📦 Otros", "📦", "#94a3b8"),
        ]
        for cat_nombre, icono, color in categorias_default:
            cursor.execute("""
                INSERT INTO categorias (paseo_id, nombre, icono, color)
                VALUES (?, ?, ?, ?)
            """, (paseo_id, cat_nombre, icono, color))
        
        conn.commit()
        conn.close()
        return paseo_id
    
    # Métodos de categorías
    def get_categorias_paseo(self, paseo_id: int) -> List[Dict]:
        """Obtiene todas las categorías de un paseo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM categorias WHERE paseo_id = ? ORDER BY nombre
        """, (paseo_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def crear_categoria(self, paseo_id: int, nombre: str, icono: str = "📦", color: str = "#6366f1") -> int:
        """Crea una nueva categoría"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categorias (paseo_id, nombre, icono, color)
                VALUES (?, ?, ?, ?)
            """, (paseo_id, nombre, icono, color))
            categoria_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return categoria_id
        except sqlite3.IntegrityError:
            return -1
    
    def eliminar_categoria(self, categoria_id: int) -> bool:
        """Elimina una categoría"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Primero quitar la categoría de los gastos
        cursor.execute("UPDATE gastos SET categoria_id = NULL WHERE categoria_id = ?", (categoria_id,))
        cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_paseos_usuario(self, usuario_id: int) -> List[Dict]:
        """Obtiene todos los paseos de un usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT p.*, u.nombre as creador_nombre
            FROM paseos p
            JOIN paseo_participantes pp ON p.id = pp.paseo_id
            JOIN usuarios u ON p.created_by = u.id
            WHERE pp.usuario_id = ?
            ORDER BY p.created_at DESC
        """, (usuario_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def agregar_participante(self, paseo_id: int, usuario_id: int) -> bool:
        """Agrega un participante a un paseo"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO paseo_participantes (paseo_id, usuario_id)
                VALUES (?, ?)
            """, (paseo_id, usuario_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_participantes_paseo(self, paseo_id: int) -> List[Dict]:
        """Obtiene todos los participantes de un paseo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.nombre, u.email
            FROM usuarios u
            JOIN paseo_participantes pp ON u.id = pp.usuario_id
            WHERE pp.paseo_id = ?
        """, (paseo_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # Métodos de gastos
    def crear_gasto(self, paseo_id: int, usuario_id: int, concepto: str, 
                   valor: float, fecha: datetime, tipo_archivo: str = None, 
                   archivo_path: str = None, transcripcion: str = None,
                   categoria_id: int = None) -> int:
        """Crea un nuevo gasto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO gastos (paseo_id, usuario_id, categoria_id, concepto, valor, fecha, 
                              tipo_archivo, archivo_path, transcripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (paseo_id, usuario_id, categoria_id, concepto, valor, fecha, tipo_archivo, archivo_path, transcripcion))
        gasto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return gasto_id
    
    def get_gastos_paseo(self, paseo_id: int, categoria_id: int = None) -> List[Dict]:
        """Obtiene todos los gastos de un paseo, opcionalmente filtrados por categoría"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if categoria_id:
            cursor.execute("""
                SELECT g.*, u.nombre as usuario_nombre,
                       c.nombre as categoria_nombre, c.icono as categoria_icono, c.color as categoria_color
                FROM gastos g
                JOIN usuarios u ON g.usuario_id = u.id
                LEFT JOIN categorias c ON g.categoria_id = c.id
                WHERE g.paseo_id = ? AND g.categoria_id = ?
                ORDER BY g.fecha DESC
            """, (paseo_id, categoria_id))
        else:
            cursor.execute("""
                SELECT g.*, u.nombre as usuario_nombre,
                       c.nombre as categoria_nombre, c.icono as categoria_icono, c.color as categoria_color
                FROM gastos g
                JOIN usuarios u ON g.usuario_id = u.id
                LEFT JOIN categorias c ON g.categoria_id = c.id
                WHERE g.paseo_id = ?
                ORDER BY g.fecha DESC
            """, (paseo_id,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_gastos_por_categoria(self, paseo_id: int) -> List[Dict]:
        """Obtiene el resumen de gastos agrupados por categoría"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.nombre, c.icono, c.color,
                   COUNT(g.id) as cantidad_gastos,
                   COALESCE(SUM(g.valor), 0) as total
            FROM categorias c
            LEFT JOIN gastos g ON c.id = g.categoria_id
            WHERE c.paseo_id = ?
            GROUP BY c.id, c.nombre, c.icono, c.color
            ORDER BY total DESC
        """, (paseo_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def actualizar_gasto(self, gasto_id: int, concepto: str = None, 
                        valor: float = None, fecha: datetime = None) -> bool:
        """Actualiza un gasto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = []
        params = []
        
        if concepto is not None:
            updates.append("concepto = ?")
            params.append(concepto)
        if valor is not None:
            updates.append("valor = ?")
            params.append(valor)
        if fecha is not None:
            updates.append("fecha = ?")
            params.append(fecha)
        
        if not updates:
            return False
        
        params.append(gasto_id)
        query = f"UPDATE gastos SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    
    def eliminar_gasto(self, gasto_id: int) -> bool:
        """Elimina un gasto y sus divisiones"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gasto_divisiones WHERE gasto_id = ?", (gasto_id,))
        cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        conn.commit()
        conn.close()
        return True
    
    # Métodos de división de gastos
    def crear_division_gasto(self, gasto_id: int, divisiones: List[Dict]) -> bool:
        """Crea las divisiones de un gasto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Eliminar divisiones existentes
        cursor.execute("DELETE FROM gasto_divisiones WHERE gasto_id = ?", (gasto_id,))
        # Crear nuevas divisiones
        for division in divisiones:
            cursor.execute("""
                INSERT INTO gasto_divisiones (gasto_id, usuario_id, porcentaje, monto)
                VALUES (?, ?, ?, ?)
            """, (gasto_id, division['usuario_id'], division['porcentaje'], division['monto']))
        conn.commit()
        conn.close()
        return True
    
    def get_divisiones_gasto(self, gasto_id: int) -> List[Dict]:
        """Obtiene las divisiones de un gasto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gd.*, u.nombre as usuario_nombre
            FROM gasto_divisiones gd
            JOIN usuarios u ON gd.usuario_id = u.id
            WHERE gd.gasto_id = ?
        """, (gasto_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def calcular_deudas_paseo(self, paseo_id: int) -> List[Dict]:
        """Calcula las deudas entre usuarios en un paseo (con neteo de deudas cruzadas)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Obtener todos los gastos y sus divisiones
        cursor.execute("""
            SELECT g.id as gasto_id, g.usuario_id as pagador_id, u1.nombre as pagador_nombre,
                   gd.usuario_id as deudor_id, u2.nombre as deudor_nombre,
                   gd.monto, g.concepto
            FROM gastos g
            JOIN usuarios u1 ON g.usuario_id = u1.id
            JOIN gasto_divisiones gd ON g.id = gd.gasto_id
            JOIN usuarios u2 ON gd.usuario_id = u2.id
            WHERE g.paseo_id = ? AND g.usuario_id != gd.usuario_id
        """, (paseo_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Agrupar deudas brutas (antes de netear)
        deudas_brutas = {}
        nombres = {}  # Guardar nombres para después
        
        for row in rows:
            pagador_id = row['pagador_id']
            deudor_id = row['deudor_id']
            
            # Guardar nombres
            nombres[pagador_id] = row['pagador_nombre']
            nombres[deudor_id] = row['deudor_nombre']
            
            key = (pagador_id, deudor_id)
            if key not in deudas_brutas:
                deudas_brutas[key] = {
                    'total': 0,
                    'conceptos': []
                }
            deudas_brutas[key]['total'] += row['monto']
            deudas_brutas[key]['conceptos'].append({
                'concepto': row['concepto'],
                'monto': row['monto']
            })
        
        # Netear deudas cruzadas: si A debe a B y B debe a A, calcular la diferencia
        deudas_netas = {}
        procesados = set()
        
        for (pagador_id, deudor_id), data in deudas_brutas.items():
            # Crear clave normalizada (siempre menor primero)
            key_normalizada = tuple(sorted([pagador_id, deudor_id]))
            
            if key_normalizada in procesados:
                continue
            procesados.add(key_normalizada)
            
            # Deuda de deudor a pagador
            deuda_a_b = data['total']
            conceptos_a_b = data['conceptos']
            
            # Buscar deuda inversa (pagador debe a deudor)
            key_inversa = (deudor_id, pagador_id)
            deuda_b_a = 0
            conceptos_b_a = []
            if key_inversa in deudas_brutas:
                deuda_b_a = deudas_brutas[key_inversa]['total']
                conceptos_b_a = deudas_brutas[key_inversa]['conceptos']
            
            # Calcular deuda neta
            neto = deuda_a_b - deuda_b_a
            
            if abs(neto) > 0.01:  # Solo si hay deuda significativa
                if neto > 0:
                    # deudor le debe a pagador
                    deudas_netas[(pagador_id, deudor_id)] = {
                        'pagador_id': pagador_id,
                        'pagador_nombre': nombres[pagador_id],
                        'deudor_id': deudor_id,
                        'deudor_nombre': nombres[deudor_id],
                        'total': neto,
                        'conceptos': conceptos_a_b + [{'concepto': f"(-) {c['concepto']}", 'monto': -c['monto']} for c in conceptos_b_a]
                    }
                else:
                    # pagador le debe a deudor (invertir)
                    deudas_netas[(deudor_id, pagador_id)] = {
                        'pagador_id': deudor_id,
                        'pagador_nombre': nombres[deudor_id],
                        'deudor_id': pagador_id,
                        'deudor_nombre': nombres[pagador_id],
                        'total': abs(neto),
                        'conceptos': conceptos_b_a + [{'concepto': f"(-) {c['concepto']}", 'monto': -c['monto']} for c in conceptos_a_b]
                    }
        
        return list(deudas_netas.values())
    
    def get_resumen_usuario_paseo(self, usuario_id: int, paseo_id: int) -> Dict:
        """Obtiene el resumen de gastos de un usuario en un paseo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Gastos pagados por el usuario
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_pagado
            FROM gastos
            WHERE paseo_id = ? AND usuario_id = ?
        """, (paseo_id, usuario_id))
        total_pagado = cursor.fetchone()['total_pagado']
        
        # Gastos que debe el usuario
        cursor.execute("""
            SELECT COALESCE(SUM(gd.monto), 0) as total_debe
            FROM gasto_divisiones gd
            JOIN gastos g ON gd.gasto_id = g.id
            WHERE g.paseo_id = ? AND gd.usuario_id = ?
        """, (paseo_id, usuario_id))
        total_debe = cursor.fetchone()['total_debe']
        
        conn.close()
        
        return {
            'total_pagado': total_pagado,
            'total_debe': total_debe,
            'balance': total_pagado - total_debe
        }

