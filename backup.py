#!/usr/bin/env python3
"""
Script de backup para Admin Skypass
Crea copias de seguridad de la base de datos
"""

import os
import shutil
import sqlite3
from datetime import datetime
import argparse

def crear_backup(db_path='isps.db', backup_dir='backups'):
    """Crear backup de la base de datos"""
    
    # Crear directorio de backups si no existe
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"📁 Directorio de backups creado: {backup_dir}")
    
    # Verificar que la base de datos existe
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos {db_path}")
        return False
    
    # Generar nombre del archivo de backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"isps_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Crear backup usando SQLite
        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        
        source_conn.backup(backup_conn)
        
        source_conn.close()
        backup_conn.close()
        
        # Obtener tamaño del archivo
        file_size = os.path.getsize(backup_path)
        size_mb = file_size / (1024 * 1024)
        
        print(f"✅ Backup creado exitosamente:")
        print(f"   - Archivo: {backup_path}")
        print(f"   - Tamaño: {size_mb:.2f} MB")
        print(f"   - Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear backup: {e}")
        return False

def listar_backups(backup_dir='backups'):
    """Listar todos los backups disponibles"""
    
    if not os.path.exists(backup_dir):
        print(f"📁 No existe el directorio de backups: {backup_dir}")
        return
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.startswith('isps_backup_') and filename.endswith('.db'):
            file_path = os.path.join(backup_dir, filename)
            stat = os.stat(file_path)
            backups.append({
                'filename': filename,
                'path': file_path,
                'size': stat.st_size,
                'date': datetime.fromtimestamp(stat.st_mtime)
            })
    
    if not backups:
        print("📁 No se encontraron backups")
        return
    
    # Ordenar por fecha (más reciente primero)
    backups.sort(key=lambda x: x['date'], reverse=True)
    
    print(f"📋 Backups disponibles ({len(backups)}):")
    print("-" * 80)
    print(f"{'Archivo':<30} {'Fecha':<20} {'Tamaño':<10}")
    print("-" * 80)
    
    for backup in backups:
        size_mb = backup['size'] / (1024 * 1024)
        print(f"{backup['filename']:<30} {backup['date'].strftime('%Y-%m-%d %H:%M:%S'):<20} {size_mb:.2f} MB")

def restaurar_backup(backup_path, db_path='isps.db'):
    """Restaurar backup de la base de datos"""
    
    if not os.path.exists(backup_path):
        print(f"❌ Error: No se encontró el archivo de backup {backup_path}")
        return False
    
    try:
        # Crear backup de la base de datos actual
        if os.path.exists(db_path):
            backup_actual = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_actual)
            print(f"💾 Backup de la base de datos actual creado: {backup_actual}")
        
        # Restaurar desde backup
        shutil.copy2(backup_path, db_path)
        
        print(f"✅ Base de datos restaurada desde: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error al restaurar backup: {e}")
        return False

def limpiar_backups_antiguos(backup_dir='backups', dias=30):
    """Eliminar backups más antiguos que X días"""
    
    if not os.path.exists(backup_dir):
        print(f"📁 No existe el directorio de backups: {backup_dir}")
        return
    
    from datetime import timedelta
    fecha_limite = datetime.now() - timedelta(days=dias)
    eliminados = 0
    
    for filename in os.listdir(backup_dir):
        if filename.startswith('isps_backup_') and filename.endswith('.db'):
            file_path = os.path.join(backup_dir, filename)
            stat = os.stat(file_path)
            fecha_archivo = datetime.fromtimestamp(stat.st_mtime)
            
            if fecha_archivo < fecha_limite:
                try:
                    os.remove(file_path)
                    print(f"🗑️  Eliminado: {filename}")
                    eliminados += 1
                except Exception as e:
                    print(f"❌ Error al eliminar {filename}: {e}")
    
    print(f"✅ Se eliminaron {eliminados} backups antiguos (más de {dias} días)")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Script de backup para Admin Skypass')
    parser.add_argument('--crear', action='store_true', help='Crear nuevo backup')
    parser.add_argument('--listar', action='store_true', help='Listar backups disponibles')
    parser.add_argument('--restaurar', type=str, help='Restaurar desde backup (ruta del archivo)')
    parser.add_argument('--limpiar', type=int, metavar='DIAS', help='Limpiar backups más antiguos que X días')
    parser.add_argument('--db', default='isps.db', help='Ruta de la base de datos (default: isps.db)')
    parser.add_argument('--backup-dir', default='backups', help='Directorio de backups (default: backups)')
    
    args = parser.parse_args()
    
    print("🌐 Admin Skypass - Script de Backup")
    print("=" * 40)
    
    if args.crear:
        crear_backup(args.db, args.backup_dir)
    elif args.listar:
        listar_backups(args.backup_dir)
    elif args.restaurar:
        restaurar_backup(args.restaurar, args.db)
    elif args.limpiar:
        limpiar_backups_antiguos(args.backup_dir, args.limpiar)
    else:
        # Por defecto, crear backup
        crear_backup(args.db, args.backup_dir)

if __name__ == '__main__':
    main()
