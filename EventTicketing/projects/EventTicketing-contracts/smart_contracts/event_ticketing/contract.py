# smart_contracts/event_ticketing/contract.py

import algopy
from algopy import (
    ARC4Contract,
    arc4,
    Global,
    Txn,
    UInt64,
    String,
    Asset,
    gtxn,
    GlobalState,
)

class EventTicketing(ARC4Contract):
    """
    Event Ticketing Akıllı Kontratı
    Biletleri ASA/NFT olarak basar ve satar.
    """

    # Storage tanımları (proxy'ler)
    ticket_asa_id: GlobalState[UInt64]
    ticket_price: GlobalState[UInt64]
    total_tickets: GlobalState[UInt64]
    tickets_sold: GlobalState[UInt64]
    event_name: GlobalState[String]

    def __init__(self) -> None:
        self.ticket_asa_id = GlobalState(UInt64, key=b"asa_id", description="Mint edilen bilet ASA ID")
        self.ticket_price   = GlobalState(UInt64, key=b"price",  description="Bilet fiyatı (µAlgo)")
        self.total_tickets  = GlobalState(UInt64, key=b"total",  description="Toplam bilet")
        self.tickets_sold   = GlobalState(UInt64, key=b"sold",   description="Satılan bilet")
        self.event_name     = GlobalState(String, key=b"name",   description="Etkinlik adı")

    # --- 1) Create / Init ---
    @arc4.abimethod(create="require")
    def create_application(
        self: "EventTicketing",
        event_name: String,
        ticket_price: UInt64,
        total_tickets: UInt64,
    ) -> None:
        self.event_name.value = event_name
        self.ticket_price.value = ticket_price
        self.total_tickets.value = total_tickets
        self.tickets_sold.value = UInt64(0)
        self.ticket_asa_id.value = UInt64(0)

    # --- 2) Mint tickets (ASA) ---
    @arc4.abimethod
    def mint_tickets(self: "EventTicketing") -> Asset:
        # Sadece kurucu
        assert Txn.sender == Global.creator_address, "Sadece kontrat kurucusu bilet basabilir"
        # Daha önce basılmadı mı?
        assert self.ticket_asa_id.value == UInt64(0), "Biletler zaten basılmış"

        created_asset_id = algopy.itxn.AssetConfig(
            asset_name=self.event_name.value,
            unit_name="TICKET",
            total=self.total_tickets.value,
            decimals=0,
            default_frozen=False,
            manager=Global.current_application_address,
            reserve=Global.current_application_address,
            freeze=Global.current_application_address,
            clawback=Global.current_application_address,
        ).submit().created_asset.id

        self.ticket_asa_id.value = created_asset_id
        return Asset(created_asset_id)

    # --- 3) Buy ticket (atomic with payment) ---
    @arc4.abimethod
    def buy_ticket(self: "EventTicketing", payment: gtxn.PaymentTransaction) -> None:
        assert self.tickets_sold.value < self.total_tickets.value, "Biletler tükendi"
        assert self.ticket_asa_id.value != UInt64(0), "Bilet satışı henüz başlamadı"

        assert payment.amount == self.ticket_price.value, "Ödeme miktarı bilet fiyatıyla eşleşmiyor"
        assert payment.receiver == Global.current_application_address, "Ödeme bu kontrata yapılmalı"

        # NFT transferi (inner tx)
        algopy.itxn.AssetTransfer(
            xfer_asset=self.ticket_asa_id.value,
            asset_receiver=Txn.sender,
            asset_amount=1,
        ).submit()

        self.tickets_sold.value = self.tickets_sold.value + UInt64(1)
