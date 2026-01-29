#!/usr/bin/env python3
"""
MatVerse ACOA - Deploy com Testes e Rastreamento
Versão: 1.0.0 | Data: 2026-01-30

Este módulo executa o deploy real de artefatos do repositório matverse-acoa/papers,
com validação rigorosa, testes automatizados, rastreamento criptográfico e integração
com Zenodo/ORCID.

Requisitos:
    - gitpython
    - requests
    - cryptography
    - pydantic
    - (opcional) python-dotenv para variáveis de ambiente

Configuração:
    Defina as variáveis de ambiente:
        ZENODO_TOKEN: token de acesso à API do Zenodo
        ZENODO_SANDBOX: true/false (usa sandbox.zenodo.org se true)
        GITHUB_TOKEN: token para push automático (se necessário)
        ORCID_TOKEN: token para registro ORCID (opcional)
        MATVERSE_CORE_URL: endpoint do core MatVerse para validação Ω-Gate
"""

import hashlib
import json
import logging
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import git
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import BaseModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("deploy_trace.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Constantes
REPO_PATH = Path(__file__).resolve().parents[2]
DEPLOY_BRANCH = "main"
ZENODO_API_SANDBOX = "https://sandbox.zenodo.org/api"
ZENODO_API_PRODUCTION = "https://zenodo.org/api"
MATVERSE_CORE_URL = os.getenv("MATVERSE_CORE_URL", "https://core.matverse.acoa.io")


# Modelos Pydantic para validação
class PaperMetadata(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    license: str = "CC-BY-4.0"
    upload_type: str = "publication"
    publication_type: str = "article"
    communities: List[Dict[str, str]] = [{"identifier": "matverse"}]


class DeployConfig(BaseModel):
    enable_zenodo: bool = True
    enable_github_push: bool = True
    enable_orcid_update: bool = False
    require_omega_gate: bool = True
    test_timeout: int = 300  # segundos


# Classes principais
class SecurityTracer:
    """Rastreamento criptográfico e assinatura."""

    def __init__(self, private_key_path: Optional[str] = None):
        if private_key_path and Path(private_key_path).exists():
            with open(private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                )
        else:
            self.private_key = ed25519.Ed25519PrivateKey.generate()

        self.public_key = self.private_key.public_key()
        self.trace_id = self._generate_trace_id()
        logger.info("Trace ID gerado: %s", self.trace_id)

    def _generate_trace_id(self) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        random = os.urandom(16).hex()
        return hashlib.sha3_512(f"{timestamp}{random}".encode()).hexdigest()[:32]

    def sign_data(self, data: bytes) -> str:
        signature = self.private_key.sign(data)
        return signature.hex()

    def hash_file(self, file_path: Path) -> str:
        sha3 = hashlib.sha3_512()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha3.update(chunk)
        return sha3.hexdigest()

    def create_manifest(self, files: List[Path]) -> Dict[str, Any]:
        manifest = {
            "trace_id": self.trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files": {},
        }

        for file in files:
            if file.exists():
                manifest["files"][str(file)] = {
                    "sha3_512": self.hash_file(file),
                    "size": file.stat().st_size,
                    "modified": file.stat().st_mtime,
                }

        manifest_json = json.dumps(manifest, sort_keys=True, indent=2)
        manifest["signature"] = self.sign_data(manifest_json.encode())

        return manifest


class TestRunner:
    """Execução de testes automatizados."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.test_results: Dict[str, Dict[str, Any]] = {}

    def run_latex_build_test(self) -> Tuple[bool, str]:
        """Testa compilação LaTeX de todos os .tex."""
        try:
            tex_files = list(self.repo_path.glob("**/*.tex"))
            if not tex_files:
                return True, "Nenhum arquivo .tex encontrado"

            success_count = 0
            error_logs = []

            for tex_file in tex_files:
                try:
                    cmd = [
                        "latexmk",
                        "-cd",
                        "-pdf",
                        "-interaction=nonstopmode",
                        str(tex_file),
                    ]
                    result = subprocess.run(
                        cmd,
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        check=False,
                    )

                    if result.returncode == 0:
                        success_count += 1
                    else:
                        error_logs.append(f"{tex_file}: {result.stderr[:500]}")

                except subprocess.TimeoutExpired:
                    error_logs.append(f"{tex_file}: timeout")
                except Exception as exc:
                    error_logs.append(f"{tex_file}: {exc}")

            success = success_count == len(tex_files)
            msg = f"Compilados {success_count}/{len(tex_files)} arquivos .tex"
            if error_logs:
                msg += f" | Erros: {error_logs[:3]}"

            return success, msg

        except Exception as exc:
            return False, f"Erro no teste LaTeX: {exc}"

    def run_python_tests(self) -> Tuple[bool, str]:
        """Testa scripts Python no repositório."""
        try:
            python_files = list(self.repo_path.glob("**/*.py"))
            if not python_files:
                return True, "Nenhum arquivo .py encontrado"

            for py_file in python_files:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    return False, (
                        f"Erro de sintaxe em {py_file}: {result.stderr[:200]}"
                    )

            test_dir = self.repo_path / "tests"
            if test_dir.exists():
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_dir), "-v"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if result.returncode != 0:
                    return False, f"Testes falharam: {result.stderr[:500]}"

            return True, "Todos os testes Python passaram"

        except Exception as exc:
            return False, f"Erro no teste Python: {exc}"

    def run_security_scan(self) -> Tuple[bool, str]:
        """Verificação básica de segurança."""
        try:
            sensitive_patterns = [
                r"password\s*=\s*['\"][^'\"]+['\"]",
                r"token\s*=\s*['\"][^'\"]+['\"]",
                r"secret\s*=\s*['\"][^'\"]+['\"]",
                r"api_key\s*=\s*['\"][^'\"]+['\"]",
            ]

            import re

            issues = []

            for file_path in self.repo_path.glob("**/*.py"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern in sensitive_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(f"Possível senha/token em {file_path}")

            if issues:
                return False, f"Problemas de segurança: {issues[:3]}"

            return True, "Scan de segurança básico passou"

        except Exception as exc:
            return False, f"Erro no scan de segurança: {exc}"

    def run_all_tests(self) -> Dict[str, Dict[str, Any]]:
        """Executa todos os testes."""
        tests = {
            "latex_build": self.run_latex_build_test,
            "python_tests": self.run_python_tests,
            "security_scan": self.run_security_scan,
        }

        for name, test_func in tests.items():
            logger.info("Executando teste: %s", name)
            success, message = test_func()
            self.test_results[name] = {
                "success": success,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            if not success:
                logger.error("Teste falhou: %s - %s", name, message)
            else:
                logger.info("Teste passou: %s", name)

        return self.test_results


class OmegaGateValidator:
    """Validação via Ω-Gate do core MatVerse."""

    def __init__(self, core_url: str):
        self.core_url = core_url.rstrip("/")

    def validate_deploy(
        self, manifest: Dict, test_results: Dict
    ) -> Tuple[bool, str, Dict]:
        """Envia para Ω-Gate e retorna decisão."""
        try:
            payload = {
                "action": "deploy_papers",
                "manifest": manifest,
                "test_results": test_results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            response = requests.post(
                f"{self.core_url}/omega-gate/validate",
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return (
                    result.get("decision") == "PASS",
                    result.get("message", ""),
                    result,
                )
            return False, f"Erro HTTP {response.status_code}", {}

        except requests.exceptions.RequestException as exc:
            return False, f"Erro de conexão com Ω-Gate: {exc}", {}
        except Exception as exc:
            return False, f"Erro na validação Ω-Gate: {exc}", {}


class ZenodoPublisher:
    """Publicação no Zenodo."""

    def __init__(self, token: str, sandbox: bool = True):
        self.token = token
        self.api_url = ZENODO_API_SANDBOX if sandbox else ZENODO_API_PRODUCTION
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def create_deposition(self, metadata: Dict) -> Optional[str]:
        """Cria um novo deposition no Zenodo."""
        try:
            response = requests.post(
                f"{self.api_url}/deposit/depositions",
                json=metadata,
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 201:
                deposition_id = response.json()["id"]
                logger.info("Deposition criado: %s", deposition_id)
                return str(deposition_id)
            logger.error("Erro ao criar deposition: %s", response.text)
            return None

        except Exception as exc:
            logger.error("Erro no create_deposition: %s", exc)
            return None

    def upload_file(self, deposition_id: str, file_path: Path) -> bool:
        """Faz upload de um arquivo para o deposition."""
        try:
            with open(file_path, "rb") as file_handle:
                files = {"file": file_handle}
                response = requests.put(
                    f"{self.api_url}/deposit/depositions/{deposition_id}/files",
                    files=files,
                    headers=self.headers,
                    timeout=60,
                )

            if response.status_code in [200, 201]:
                logger.info("Arquivo enviado: %s", file_path.name)
                return True
            logger.error("Erro no upload: %s", response.text)
            return False

        except Exception as exc:
            logger.error("Erro no upload_file: %s", exc)
            return False

    def publish(self, deposition_id: str) -> Optional[str]:
        """Publica o deposition (torna público)."""
        try:
            response = requests.post(
                f"{self.api_url}/deposit/depositions/{deposition_id}/actions/publish",
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 202:
                doi = response.json().get("doi", "")
                logger.info("Publicado com DOI: %s", doi)
                return doi
            logger.error("Erro ao publicar: %s", response.text)
            return None

        except Exception as exc:
            logger.error("Erro no publish: %s", exc)
            return None


class DeployExecutor:
    """Executor principal do deploy."""

    def __init__(self, config: DeployConfig):
        self.config = config
        self.repo_path = REPO_PATH
        self.tracer = SecurityTracer()
        self.test_runner = TestRunner(self.repo_path)
        self.omega_validator = OmegaGateValidator(MATVERSE_CORE_URL)

        zenodo_token = os.getenv("ZENODO_TOKEN")
        zenodo_sandbox = os.getenv("ZENODO_SANDBOX", "true").lower() == "true"

        if zenodo_token and config.enable_zenodo:
            self.zenodo_publisher = ZenodoPublisher(zenodo_token, zenodo_sandbox)
        else:
            self.zenodo_publisher = None

        self.deploy_results: Dict[str, Any] = {
            "trace_id": self.tracer.trace_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "steps": {},
        }

    def execute(self) -> Dict[str, Any]:
        """Executa o pipeline completo de deploy."""
        logger.info("Iniciando deploy com trace ID: %s", self.tracer.trace_id)

        try:
            files_to_deploy = self._collect_deploy_files()
            if not files_to_deploy:
                raise RuntimeError("Nenhum arquivo para deploy encontrado")

            manifest = self.tracer.create_manifest(files_to_deploy)
            self.deploy_results["steps"]["manifest"] = {
                "success": True,
                "files_count": len(files_to_deploy),
                "manifest_hash": hashlib.sha3_512(
                    json.dumps(manifest).encode()
                ).hexdigest()[:16],
            }

            logger.info("Executando testes...")
            test_results = self.test_runner.run_all_tests()
            self.deploy_results["steps"]["tests"] = test_results

            all_tests_passed = all(result["success"] for result in test_results.values())
            if not all_tests_passed:
                raise RuntimeError("Testes falharam")

            if self.config.require_omega_gate:
                logger.info("Validando com Ω-Gate...")
                omega_ok, omega_msg, omega_details = (
                    self.omega_validator.validate_deploy(manifest, test_results)
                )

                self.deploy_results["steps"]["omega_gate"] = {
                    "success": omega_ok,
                    "message": omega_msg,
                    "details": omega_details,
                }

                if not omega_ok:
                    raise RuntimeError(f"Ω-Gate rejeitou: {omega_msg}")

            if self.config.enable_zenodo and self.zenodo_publisher:
                logger.info("Publicando no Zenodo...")
                zenodo_result = self._publish_to_zenodo(files_to_deploy)
                self.deploy_results["steps"]["zenodo"] = zenodo_result

                if not zenodo_result["success"]:
                    raise RuntimeError(
                        f"Falha no Zenodo: {zenodo_result['message']}"
                    )

            if self.config.enable_github_push:
                logger.info("Fazendo push para GitHub...")
                github_result = self._push_to_github()
                self.deploy_results["steps"]["github"] = github_result

                if not github_result["success"]:
                    raise RuntimeError(
                        f"Falha no GitHub: {github_result['message']}"
                    )

            if self.config.enable_orcid_update:
                logger.info("Atualizando ORCID...")
                orcid_result = self._update_orcid()
                self.deploy_results["steps"]["orcid"] = orcid_result

            self.deploy_results["success"] = True
            self.deploy_results["end_time"] = datetime.now(timezone.utc).isoformat()
            self.deploy_results["duration_seconds"] = (
                datetime.now(timezone.utc)
                - datetime.fromisoformat(
                    self.deploy_results["start_time"].replace("Z", "+00:00")
                )
            ).total_seconds()

            logger.info("Deploy concluído com sucesso! Trace ID: %s", self.tracer.trace_id)

            self._save_report()

            return self.deploy_results

        except Exception as exc:
            logger.error("Erro no deploy: %s", exc)
            logger.error(traceback.format_exc())

            self.deploy_results["success"] = False
            self.deploy_results["error"] = str(exc)
            self.deploy_results["end_time"] = datetime.now(timezone.utc).isoformat()

            self._save_report()

            return self.deploy_results

    def _collect_deploy_files(self) -> List[Path]:
        """Coleta arquivos para deploy."""
        file_patterns = [
            "**/*.pdf",
            "**/*.tex",
            "**/README.md",
            "**/LICENSE*",
            "**/metadata.json",
            "**/checksums.txt",
            "tools/exocortex_executor/**/*.py",
        ]

        files: List[Path] = []
        for pattern in file_patterns:
            files.extend(self.repo_path.glob(pattern))

        unique_files = list(set(files))
        existing_files = [
            file for file in unique_files if file.exists() and file.is_file()
        ]

        logger.info("Encontrados %s arquivos para deploy", len(existing_files))
        return existing_files

    def _publish_to_zenodo(self, files: List[Path]) -> Dict[str, Any]:
        """Publica arquivos no Zenodo."""
        result = {"success": False, "message": "", "doi": "", "deposition_id": ""}

        try:
            metadata = {
                "metadata": {
                    "title": (
                        "MatVerse ACOA Papers - "
                        f"{datetime.now(timezone.utc).date()}"
                    ),
                    "description": "Conjunto de papers e artefatos do projeto MatVerse ACOA",
                    "creators": [{"name": "MatVerse Research Collective"}],
                    "keywords": [
                        "matverse",
                        "acoa",
                        "antifragile",
                        "quantum",
                        "governance",
                    ],
                    "license": "cc-by-4.0",
                    "upload_type": "publication",
                    "publication_type": "collection",
                    "communities": [{"identifier": "matverse"}],
                }
            }

            deposition_id = self.zenodo_publisher.create_deposition(metadata)
            if not deposition_id:
                result["message"] = "Falha ao criar deposition"
                return result

            result["deposition_id"] = deposition_id

            upload_success = True
            for file_path in files[:10]:
                if not self.zenodo_publisher.upload_file(deposition_id, file_path):
                    upload_success = False
                    logger.warning("Falha no upload de %s", file_path.name)

            if not upload_success:
                result["message"] = "Alguns uploads falharam"
                return result

            doi = self.zenodo_publisher.publish(deposition_id)
            if doi:
                result["success"] = True
                result["doi"] = doi
                result["message"] = f"Publicado com sucesso: {doi}"
            else:
                result["message"] = "Falha ao publicar"

        except Exception as exc:
            result["message"] = f"Erro no Zenodo: {exc}"

        return result

    def _push_to_github(self) -> Dict[str, Any]:
        """Faz push das alterações para GitHub."""
        result = {"success": False, "message": "", "commit_hash": ""}

        try:
            repo = git.Repo(self.repo_path)

            if not repo.is_dirty() and not repo.untracked_files:
                result["message"] = "Nenhuma alteração para commitar"
                result["success"] = True
                return result

            repo.git.add(A=True)

            commit_msg = (
                "Deploy automático "
                f"{datetime.now(timezone.utc).date()} - Trace ID: "
                f"{self.tracer.trace_id}"
            )
            commit = repo.index.commit(commit_msg)
            result["commit_hash"] = commit.hexsha

            if repo.remotes:
                origin = repo.remotes.origin
                origin.push()
                result["message"] = f"Push realizado: {commit.hexsha[:8]}"
            else:
                result["message"] = f"Commit local: {commit.hexsha[:8]} (sem remote)"

            result["success"] = True

        except Exception as exc:
            result["message"] = f"Erro no GitHub: {exc}"

        return result

    def _update_orcid(self) -> Dict[str, Any]:
        """Atualiza ORCID com o novo trabalho."""
        return {"success": False, "message": "Não implementado"}

    def _save_report(self) -> None:
        """Salva relatório do deploy."""
        report_path = (
            self.repo_path
            / f"deploy_reports/deploy_{self.tracer.trace_id}.json"
        )
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.deploy_results, f, indent=2, ensure_ascii=False, default=str)

        logger.info("Relatório salvo em: %s", report_path)


def main() -> None:
    """Função principal."""
    print("\n" + "=" * 80)
    print("MATVERSE ACOA - DEPLOY COM TESTES E RASTREAMENTO")
    print("=" * 80)

    if not REPO_PATH.exists():
        print(f"ERRO: Repositório não encontrado em {REPO_PATH}")
        print("Execute este script do diretório matverse-acoa/papers")
        sys.exit(1)

    config = DeployConfig(
        enable_zenodo=os.getenv("ENABLE_ZENODO", "true").lower() == "true",
        enable_github_push=os.getenv("ENABLE_GITHUB_PUSH", "true").lower() == "true",
        require_omega_gate=os.getenv("REQUIRE_OMEGA_GATE", "true").lower() == "true",
    )

    executor = DeployExecutor(config)
    results = executor.execute()

    print("\n" + "=" * 80)
    print("RESUMO DO DEPLOY")
    print("=" * 80)

    print(f"Trace ID:       {results.get('trace_id', 'N/A')}")
    print(f"Sucesso:        {'✅' if results.get('success') else '❌'}")
    print(f"Início:         {results.get('start_time', 'N/A')}")
    print(f"Término:        {results.get('end_time', 'N/A')}")

    if results.get("duration_seconds"):
        print(f"Duração:        {results.get('duration_seconds'):.1f} segundos")

    print("\nPASSOS:")
    for step_name, step_result in results.get("steps", {}).items():
        if isinstance(step_result, dict) and "success" in step_result:
            status = "✅" if step_result["success"] else "❌"
            print(f"  {status} {step_name}: {step_result.get('message', '')}")

    report_path = (
        REPO_PATH / f"deploy_reports/deploy_{results.get('trace_id', 'unknown')}.json"
    )
    if report_path.exists():
        print(f"\nRelatório completo: {report_path}")

    if results.get("success"):
        print("\n✅ DEPLOY CONCLUÍDO COM SUCESSO!")
        sys.exit(0)

    print(f"\n❌ DEPLOY FALHOU: {results.get('error', 'Erro desconhecido')}")
    sys.exit(1)


if __name__ == "__main__":
    main()
