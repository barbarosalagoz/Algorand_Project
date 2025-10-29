// src/main.tsx (DÜZELTİLMİŞ)

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/main.css';
import ErrorBoundary from './components/ErrorBoundary';

// --- YENİ EKLENEN IMPORTLAR ---
import { WalletProvider, useInitializeProviders } from '@txnlab/use-wallet';
import algosdk from 'algosdk'; // Genellikle Pera için gerekli olabilir
import { PeraWalletConnect } from '@perawallet/connect'; // Pera Wallet için
// Defly Wallet için (isteğe bağlı)
// import { DeflyWalletConnect } from '@blockshake/defly-connect';
// --- IMPORTLAR SONU ---


// --- YENİ EKLENEN PROVIDERS BİLEŞENİ ---
// Bu bileşen, cüzdan sağlayıcılarını başlatır ve WalletProvider'ı ayarlar.
const Providers = ({ children }: { children: React.ReactNode }) => {
  const providers = useInitializeProviders({
    providers: [
      // Eklemek istediğiniz cüzdanları buraya listeyin
      { id: 'pera', clientStatic: PeraWalletConnect },
      // { id: 'defly', clientStatic: DeflyWalletConnect },
    ],
    // İsteğe Bağlı: nodeConfig ile doğrudan LocalNet/TestNet/MainNet'e bağlanabilirsiniz
    // Ancak App.tsx içinde algokit'ten aldığımız için burada gerek yok.
    // nodeConfig: {
    //   network: import.meta.env.VITE_ALGOD_NETWORK || 'localnet',
    //   nodeServer: import.meta.env.VITE_ALGOD_SERVER || 'http://localhost',
    //   nodePort: import.meta.env.VITE_ALGOD_PORT || '4001',
    //   nodeToken: import.meta.env.VITE_ALGOD_TOKEN || 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    // }
  });

  // WalletProvider'ı başlatılan sağlayıcılarla döndür
  return <WalletProvider value={providers}>{children}</WalletProvider>;
};
// --- PROVIDERS BİLEŞENİ SONU ---


ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      {/* --- DEĞİŞİKLİK BURADA --- */}
      <Providers> {/* App'i Providers ile sarmaladık */}
        <App />
      </Providers>
      {/* --- DEĞİŞİKLİK SONU --- */}
    </ErrorBoundary>
  </React.StrictMode>,
);
