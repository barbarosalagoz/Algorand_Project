# smart_contracts/event_ticketing/deploy_config.py
# Bu dosya, __main__.py tarafından çağrılır.

import logging
from algokit_utils import AlgorandClient, SendParams, CommonAppCallCreateParams
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from smart_contracts.artifacts.event_ticketing.event_ticketing_client import (
    EventTicketingClient,
)

# --- Kontrat Ayarları ---
EVENT_NAME = "Harika Algorand Konseri"
TICKET_PRICE = 1_000_000      # 1 ALGO (microAlgo)
TOTAL_TICKETS = 100
# 0.1 (Min Bakiye) + 0.1 (ASA Oluşturma Ücreti)
APP_FUNDING_ALGOS = 0.2

logger = logging.getLogger(__name__)

# deploy fonksiyonu __main__.py tarafından bu imzayla çağrılır:
def deploy(
    app_client: EventTicketingClient, # __main__ tarafından oluşturulur
    app_id: int,                      # __main__ tarafından verilir (yeni için 0)
    creator: AccountTransactionSigner # __main__ tarafından verilir (artık doğru tipte)
) -> None:
    """
    Akıllı kontratı dağıtır, fonlar ve biletleri basar.
    """

    # algo client'ı app_client'tan alabiliriz
    algo = app_client.algorand

    # --- 1. Adım: Kontratı Oluşturma (Create) ---
    # __main__.py zaten 'build' adımını çalıştırdı.
    # __main__.py'nin 'deploy_contract' fonksiyonu bizim için 'create' işlemini
    # (veya update/delete) zaten yapmalı.
    
    # ChatGPT'nin __main__.py'si 'app_client'ı app_id=0 ile oluşturur.
    # Bizim create_application'ı burada çağırmamız gerekiyor.
    
    if app_id == 0:
        logger.info("Kontrat oluşturuluyor (create_application çağrılıyor)...")
        # app_client zaten 'creator'ı signer olarak biliyor
        create_result = app_client.create_application(
            args=(EVENT_NAME, TICKET_PRICE, TOTAL_TICKETS),
            # 'params'a gerek yok, __main__ zaten 'signer=creator' ile kurdu
        )
        app_id = create_result.app_id
        app_addr = create_result.app_address
        logger.info(f"Kontrat başarıyla oluşturuldu. App ID: {app_id}, App Address: {app_addr}")
    else:
        app_addr = app_client.app_address
        logger.info(f"Mevcut kontrat {app_id} güncelleniyor (eğer gerekiyorsa)...")
        # (Güncelleme mantığı buraya eklenebilir, şimdilik atlıyoruz)
        logger.info("Kontrat güncellendi.")


    # --- 2. Adım: Kontratı Fonlama (Funding) ---
    logger.info(f"Kontrat {app_id} fonlanıyor ({APP_FUNDING_ALGOS} ALGO gönderiliyor)...")
    
    # 'algo' istemcisi __main__.py'den gelir ve varsayılan imzalayıcıyı
    # (creator) bilmesi gerekir.
    try:
        algo.send.payment(
            app_addr,
            int(APP_FUNDING_ALGOS * 1_000_000)
        )
        logger.info("Fonlama başarılı.")
    except Exception as e:
        logger.error(f"Fonlama BAŞARISIZ: {e}")
        # 'AttributeError: str object has no attribute signer' alırsak,
        # __main__.py'nin 'algo' nesnesini doğru ayarlamadığı anlamına gelir.
        raise

    # --- 3. Adım: Biletleri Basma (Minting) ---
    logger.info(f"Biletler basılıyor ('mint_tickets' çağrılıyor)...")
    try:
        # 'app_client' zaten 'creator'ı signer olarak biliyor.
        mint_result = app_client.mint_tickets(
            send_params=SendParams(extra_fee=2_000) # Sadece ekstra ücreti ver
        )
        logger.info("Bilet basma (Mint) OK.")
        logger.info(f"Oluşturulan ASA ID: {mint_result.return_value}")
    except LogicError as e:
        logger.error(f"Bilet basma (Mint) BAŞARISIZ: {str(e)}")
        return
    except Exception as e:
        logger.error(f"Bilet basma sırasında beklenmeyen hata: {e}")
        raise

    # --- 4. Adım: Global State'i Doğrula ---
    logger.info("Global State okunuyor...")
    gs = app_client.get_global_state()
    logger.info("Global State:")
    for k, v in gs.items():
        # Değerleri daha okunaklı hale getir
        key_str = k.decode('utf-8') if isinstance(k, bytes) else k
        logger.info(f"  {key_str}: {v}")

    logger.info("Deploy betiği başarıyla tamamlandı.")
