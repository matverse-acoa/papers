#!/usr/bin/env python3
"""
Update evidence/index.json with SHA256 hashes
"""
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime

def calculate_sha256(filepath):
    """Calculate SHA256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def update_index(tarball_path):
    """Add or update entry in evidence/index.json"""
    index_file = "evidence/index.json"
    
    if not os.path.exists(tarball_path):
        print(f"❌ Erro: arquivo '{tarball_path}' não encontrado")
        exit(1)
    
    # Calcular SHA256
    sha256_hash = calculate_sha256(tarball_path)
    
    # Metadados
    entry = {
        "package": Path(tarball_path).stem,
        "tarball": tarball_path,
        "sha256": sha256_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "size_bytes": os.path.getsize(tarball_path)
    }
    
    # Carregar ou criar index
    if os.path.exists(index_file):
        with open(index_file, 'r') as f:
            index = json.load(f)
    else:
        index = {"entries": [], "updated_at": None}
    
    # Adicionar ou atualizar entrada
    index["entries"] = [e for e in index.get("entries", []) if e["package"] != entry["package"]]
    index["entries"].append(entry)
    index["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Salvar
    os.makedirs("evidence", exist_ok=True)
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"✅ Index atualizado:")
    print(f"   Pacote: {entry['package']}")
    print(f"   SHA256: {sha256_hash}")
    print(f"   Tamanho: {entry['size_bytes']} bytes")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: ./sha256_update.py <caminho-do-tarball>")
        exit(1)
    update_index(sys.argv[1])
