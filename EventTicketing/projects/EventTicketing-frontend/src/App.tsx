import React, { useState, useEffect, useCallback } from 'react';
import * as algokit from '@algorandfoundation/algokit-utils';
import { EventTicketingClient } from '../contracts/clients/EventTicketingClient';
import algosdk from 'algosdk';
import { useWallet } from '@txnlab/use-wallet'; // Cüzdan bağlantısı için

function App() {
  // --- React State Değişkenleri ---
  const [eventName, setEventName] = useState<string>('');
  const [ticketPrice, setTicketPrice] = useState<bigint>(BigInt(0));
  const [totalTickets, setTotalTickets] = useState<bigint>(BigInt(0));
  const [ticketsSold, setTicketsSold] = useState<bigint>(BigInt(0));
  const [ticketAsaId, setTicketAsaId] = useState<bigint>(BigInt(0)); // NFT ID'sini de saklayalım
  const [contractClient, setContractClient] = useState<EventTicketingClient | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // --- use-wallet Kancaları ---
  // Cüzdan bağlantı durumunu ve bağlı hesabı almak için
  const { signer, activeAddress, providers, activeProvider } = useWallet();

  // --- Algorand Bağlantı Bilgileri ---
  const algodConfig = algokit.getAlgodConfigFromEnvironment();
  const algodClient = algokit.getAlgoClient(algodConfig);
  const APP_ID = parseInt(import.meta.env.VITE_EVENT_TICKETING_APP_ID || '0');

  // --- useEffect Kancası: Kontrat Bilgilerini Çek ---
  useEffect(() => {
    async function setupContractClient() {
      if (APP_ID === 0) {
        setError('App ID bulunamadı. Lütfen .env dosyasını kontrol edin veya kontratı deploy edin.');
        setLoading(false); return;
      }
      try {
        setLoading(true); setError(null);
        console.log(`Kontrat ID (${APP_ID}) ile bağlanılıyor...`);

        // Sadece okuma için rastgele bir gönderici yeterli
        const genericSender = { addr: algosdk.generateAccount().addr, signer: algosdk.makeBasicAccountTransactionSigner(algosdk.generateAccount()) };

        const client = new EventTicketingClient({ sender: genericSender, resolveBy: 'id', id: APP_ID }, algodClient);
        setContractClient(client);

        console.log('Kontrat global state okunuyor...');
        const state = await client.getGlobalState();

        const name = state.event_name?.asString();
        const price = state.ticket_price?.asBigInt();
        const total = state.total_tickets?.asBigInt();
        const sold = state.tickets_sold?.asBigInt();
        const asaId = state.ticket_asa_id?.asBigInt(); // NFT ID'sini de okuyoruz

        console.log('Okunan bilgiler:', { name, price, total, sold, asaId });

        if (name) setEventName(name);
        if (price !== undefined) setTicketPrice(price);
        if (total !== undefined) setTotalTickets(total);
        if (sold !== undefined) setTicketsSold(sold);
        if (asaId !== undefined) setTicketAsaId(asaId); // NFT ID'sini state'e kaydet

      } catch (e: any) {
        console.error('Kontrat bilgilerini alırken hata:', e);
        setError(`Kontrat bilgilerini alırken hata: ${e.message?.substring(0, 100)}...`); // Hata mesajını kısalt
      } finally {
        setLoading(false);
      }
    }
    setupContractClient();
  }, [APP_ID]); // APP_ID değişirse tekrar çalışır


  // --- Cüzdan Bağlantı Fonksiyonları ---
  const connectWallet = useCallback(async () => {
    // Kullanıcıya cüzdan seçtir (Pera, Defly vb.)
    if (!activeAddress && providers) {
      const provider = await providers[0].connect(); // Genellikle ilk sıradaki Pera olur
       if(!provider) {
         console.error("Cüzdan bağlantısı kurulamadı.");
         setError("Cüzdan bağlantısı kurulamadı.");
       }
    }
  }, [providers, activeAddress]);

  const disconnectWallet = useCallback(async () => {
    if (activeProvider) {
       await activeProvider.disconnect();
    }
  }, [activeProvider]);

  // --- Arayüzü (JSX) Oluşturma ---
  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', lineHeight: '1.6' }}>
      <h1>Algorand Bilet Satış dApp</h1>

      {/* Cüzdan Bağlantı Butonları */}
      <div>
        {!activeAddress ? (
          <button onClick={connectWallet} disabled={!providers}>
            Cüzdan Bağla
          </button>
        ) : (
          <div>
            <p>Bağlı Cüzdan: {algokit.truncateAddress(activeAddress)}</p>
            <button onClick={disconnectWallet}>
              Bağlantıyı Kes
            </button>
          </div>
        )}
      </div>
      <hr style={{ margin: '20px 0' }}/>

      {/* Kontrat Bilgileri */}
      <h2>Etkinlik Bilgileri</h2>
      {loading && <p>Yükleniyor...</p>}
      {error && <p style={{ color: 'red' }}>HATA: {error}</p>}

      {!loading && !error && contractClient && (
        <div>
          <p><strong>Kontrat App ID:</strong> {APP_ID}</p>
          <p><strong>Etkinlik Adı:</strong> {eventName || 'Alınamadı'}</p>
          <p><strong>Bilet Fiyatı:</strong> {ticketPrice !== undefined ? `${algosdk.microalgosToAlgos(Number(ticketPrice))} Algo` : 'Alınamadı'}</p>
          <p><strong>Toplam Bilet:</strong> {totalTickets !== undefined ? totalTickets.toString() : 'Alınamadı'}</p>
          <p><strong>Satılan Bilet:</strong> {ticketsSold !== undefined ? ticketsSold.toString() : 'Alınamadı'}</p>
          <p><strong>Kalan Bilet:</strong> {(totalTickets !== undefined && ticketsSold !== undefined) ? (totalTickets - ticketsSold).toString() : 'Hesaplanamadı'}</p>
          <p><strong>Bilet NFT ID (ASA ID):</strong> {ticketAsaId !== undefined && ticketAsaId !== BigInt(0) ? ticketAsaId.toString() : 'Henüz Basılmadı/Alınamadı'}</p>

          {/* Buraya Opt-in ve Satın Alma Butonları Eklenecek */}

        </div>
      )}
    </div>
  );
}

// App bileşenini use-wallet sağlayıcısı ile sarmallamamız gerekiyor
// Bu genellikle main.tsx veya index.tsx dosyasında yapılır.
// Eğer zaten sarılı değilse, aşağıdaki kodu oraya eklemelisiniz:
/*
import { WalletProvider, useInitializeProviders } from '@txnlab/use-wallet'

const Providers = ({ children }) => {
  const providers = useInitializeProviders()
  return <WalletProvider value={providers}>{children}</WalletProvider>
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Providers> // <--- Bu sarmalayıcı eklendi
      <App />
    </Providers> // <--- Bu sarmalayıcı eklendi
  </React.StrictMode>,
)
*/

export default App;
