# projects/smart_contracts/__main__.py
# --- BAŞLANGIÇ: __main__.py dosyasının tamamı ---
from __future__ import annotations

import dataclasses
import importlib
import logging
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from shutil import rmtree

from dotenv import load_dotenv

# --- Gerekli Import'ları Ekleyelim ---
try:
    from algokit_utils import AlgorandClient, get_localnet_default_account, get_account_from_environment
    from algosdk.atomic_transaction_composer import AccountTransactionSigner
except ImportError:
    print("HATA: algokit_utils veya algosdk bulunamadı. Lütfen 'poetry install' komutunu çalıştırdığınızdan emin olun.")
    sys.exit(1)
# ------------------------------------


# --------------------------------------------------------------------
# Logging & env
# --------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s: %(message)s")
logger = logging.getLogger("smart_contracts")
logger.info("Loading .env")
load_dotenv()

# Root = this package folder (projects/smart_contracts)
root_path = Path(__file__).parent.resolve()

# --- KAYIP OLAN SATIR BURADA ---
# Build ve Deploy fonksiyonlarının 'artifacts' klasörünü bulması için gerekli
artifact_root = root_path / "artifacts"
# --------------------------------

# Kontrat klasörünün adı (tek bir uygulamayı hedefliyoruz)
DEFAULT_CONTRACT_NAME = "event_ticketing"

# --------------------------------------------------------------------
# Data modeli
# --------------------------------------------------------------------
@dataclasses.dataclass
class SmartContract:
    path: Path                  # contract.py dosyasının yolu
    name: str                   # klasör adı (event_ticketing)
    # deploy_config.py'den gelen fonksiyonun imzası (düzeltildi)
    deploy: Callable[[object, int, AccountTransactionSigner], None] | None = None


# --------------------------------------------------------------------
# Kontrat bulma yardımcıları
# --------------------------------------------------------------------
def _require_file(p: Path) -> Path:
    if not p.exists():
        raise FileNotFoundError(str(p))
    return p

def import_contract(folder: Path) -> Path:
    return _require_file(folder / "contract.py")

def import_deploy_if_exists(folder: Path) -> Callable[[object, int, AccountTransactionSigner], None] | None:
    """
    smart_contracts.<folder>.deploy_config içindeki deploy fonksiyonunu import eder.
    (DÜZELTİLDİ: doğru import yoluyla)
    """
    module_name = f"smart_contracts.{folder.name}.deploy_config"
    try:
        logger.debug(f"Importing deploy function from {module_name} ...")
        mod = importlib.import_module(module_name)
        fn = getattr(mod, "deploy", None)
        if callable(fn):
            logger.info(f"Found deploy() in {module_name}")
            return fn  # type: ignore[return-value]
        logger.warning(f"{module_name} bulundu ama içinde deploy fonksiyonu yok.")
        return None
    except ModuleNotFoundError:
        logger.warning(f"{folder.name} için deploy_config bulunamadı (bu opsiyoneldir).")
        return None
    except Exception as e:
        logger.error(f"Deploy fonksiyonu import edilirken hata: {e}")
        return None


def discover_contracts(target_name: str | None = None) -> list[SmartContract]:
    # Bizim basit yapımız için sadece varsayılan klasörü arayalım
    names = [target_name] if target_name else [DEFAULT_CONTRACT_NAME]
    results: list[SmartContract] = []
    for name in names:
        folder = root_path / name
        if folder.is_dir() and (folder / "contract.py").exists():
            logger.info(f"Kontrat bulundu: {name}")
            results.append(
                SmartContract(
                    path=import_contract(folder),
                    name=name,
                    deploy=import_deploy_if_exists(folder),
                )
            )
        else:
            logger.warning(f"Kontrat {folder}/contract.py adresinde bulunamadı")
    return results


# --------------------------------------------------------------------
# Build (Compile + Typed Client)
# --------------------------------------------------------------------
def _ensure_pkg_init(pyfile: Path) -> None:
    """__init__.py dosyalarının varlığını kontrol eder (Python paketi olması için)"""
    parent = pyfile.parent
    while parent and parent != parent.parent:
        init_file = parent / "__init__.py"
        if not init_file.exists():
            logger.debug(f"Creating missing __init__.py at {init_file}")
            init_file.write_text("# auto-generated to make this a package\n", encoding="utf-8")
        if parent == root_path:
            break
        parent = parent.parent

def _client_output_path(output_dir: Path, contract_name: str, ext: str = "py") -> Path:
    return output_dir / f"{contract_name}_client.{ext}"

def build(output_dir: Path, contract_path: Path, contract_name: str) -> Path | None:
    """
    Kontratı derler (compile) ve typed client oluşturur (generate).
    .arc56.json dosyasının yolunu döndürür.
    """
    output_dir = output_dir.resolve()
    if output_dir.exists():
        rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Derleniyor: {contract_path} -> {output_dir}")

    compile_cmd = [
        "algokit", "compile", "py",
        str(contract_path.resolve()),
        f"--out-dir={str(output_dir)}",
        "--output-source-map", "--output-arc56", "--output-teal",
    ]
    logger.debug(f"Running command: {' '.join(compile_cmd)}")
    res = subprocess.run(compile_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.stdout:
        print(res.stdout, end="")
    if res.returncode != 0:
        raise RuntimeError("Derleme (compile) BAŞARISIZ OLDU")

    spec_files = list(output_dir.glob("*.arc56.json"))
    if not spec_files:
        logger.warning("No .arc56.json produced; typed client generation will be skipped.")
        return None

    spec_path = spec_files[0]

    # Import edilebilmesi için __init__.py dosyalarını oluştur
    _ensure_pkg_init(artifact_root / "__init__.py")
    _ensure_pkg_init(output_dir / "__init__.py")

    client_out = _client_output_path(output_dir, contract_name, "py")
    gen_cmd = [
        "algokit", "generate", "client",
        str(spec_path),
        "--output", str(client_out),
    ]
    logger.debug(f"Running command: {' '.join(gen_cmd)}")
    gen = subprocess.run(gen_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if gen.stdout:
        print(gen.stdout, end="")
    if gen.returncode != 0:
        if "No such command" in (gen.stdout or ""):
            raise RuntimeError("Typed client oluşturma hatası (algokit >= 2.0.0 gerekli)")
        raise RuntimeError("Typed client oluşturma BAŞARISIZ OLDU")

    logger.info(f"Typed client oluşturuldu: {client_out}")
    return spec_path


# --------------------------------------------------------------------
# Deploy (LocalNet)
# --------------------------------------------------------------------
def _get_algorand_context() -> tuple[AlgorandClient, AccountTransactionSigner]:
    """
    LocalNet için (algo_client, creator_signer) döndürür.
    (DÜZELTİLDİ: Account yerine AccountTransactionSigner döndürür)
    """
    try:
        algo = AlgorandClient.default_localnet()
        creator_account = get_localnet_default_account(algo)
        creator_signer = AccountTransactionSigner(creator_account.private_key) # Bu bizim anahtar düzeltmemizdi
        logger.info(f"LocalNet varsayılan imzalayıcısı bulundu: {creator_account.address}")
        return algo, creator_signer
    except Exception as e:
        logger.warning(f"LocalNet varsayılan hesabı alınamadı: {e}. .env (CREATOR_MNEMONIC) deneniyor...")
        algo = AlgorandClient.default_localnet()
        creator_account = get_account_from_environment(algo, "CREATOR")
        creator_signer = AccountTransactionSigner(creator_account.private_key)
        logger.info(f".env dosyasından imzalayıcı yüklendi: {creator_account.address}")
        return algo, creator_signer


def _load_typed_client(contract_name: str):
    """Oluşturulan typed client'ı import eder"""
    module_name = f"smart_contracts.artifacts.{contract_name}_client"
    if str(root_path.parent) not in sys.path:
        sys.path.insert(0, str(root_path.parent))
    return importlib.import_module(module_name)


def deploy_contract(contract: SmartContract) -> None:
    """
    Typed client oluşturur ve deploy_config.py içindeki deploy fonksiyonunu çağırır.
    (DÜZELTİLDİ: 'artifact_root' hatası giderildi ve doğru signer kullanılır)
    """
    # 'artifact_root' artık globalde tanımlı (en üstte)
    out_dir = artifact_root / contract.name
    if not out_dir.exists():
        raise FileNotFoundError(f"Artifacts klasörü {out_dir} adresinde bulunamadı; önce 'build' çalıştırın.")

    algo, creator_signer = _get_algorand_context()
    app_id = 0  # Yeni oluşturma

    client_mod = _load_typed_client(contract.name)
    EventTicketingClient = getattr(client_mod, "EventTicketingClient")

    # Client'ı doğru imzalayıcı (signer) ile oluştur
    app_client = EventTicketingClient(
        algod_client=algo.client.algod,
        app_id=app_id,
        signer=creator_signer,
    )

    if not contract.deploy:
        logger.warning(f"{contract.name} için deploy() fonksiyonu bulunamadı; dağıtım atlanıyor.")
        return

    logger.info(f"Dağıtılıyor (deploying) {contract.name} ...")
    # deploy_config.py'deki fonksiyona doğru argümanları (signer dahil) iletiyoruz
    contract.deploy(app_client, app_id, creator_signer)
    logger.info(f"Dağıtım (deploy) {contract.name} için tamamlandı.")


# --------------------------------------------------------------------
# CLI (build / deploy / all)
# --------------------------------------------------------------------
def main(action: str, target_contract_name: str | None = None) -> None:
    contracts = discover_contracts(target_contract_name)
    if not contracts:
        logger.error("Dağıtılacak geçerli bir kontrat bulunamadı. (smart_contracts/event_ticketing/contract.py var mı?)")
        sys.exit(1)

    match action:
        case "build":
            for c in contracts:
                logger.info(f"--- {c.name}: build ---")
                build(artifact_root / c.name, c.path, c.name)

        case "deploy":
            for c in contracts:
                logger.info(f"--- {c.name}: deploy ---")
                deploy_contract(c)

        case "all":
            for c in contracts:
                logger.info(f"--- {c.name}: build ---")
                build(artifact_root / c.name, c.path, c.name)
                logger.info(f"--- {c.name}: deploy ---")
                deploy_contract(c)
                logger.info(f"--- {c.name}: done ---")

        case _:
            logger.error(f"Bilinmeyen eylem: {action}")
            sys.exit(2)


if __name__ == "__main__":
    action = "all"
    target = None

    if len(sys.argv) > 2:
        action = sys.argv[1]
        target = sys.argv[2]
    elif len(sys.argv) > 1:
        a = sys.argv[1]
        if a in {"build", "deploy", "all"}:
            action = a
        else:
            target = a
            action = "all"

    logger.info(f"Eylem: {action}" + (f" | Kontrat: {target}" if target else ""))
    main(action, target)

# --- SON: __main__.py dosyasının tamamı ---
