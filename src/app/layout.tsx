import type {Metadata} from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EDELIA | VPN: Надежное соединение',
  description: 'Премиальный VPN-сервис с ультрабыстрыми серверами и шифрованием военного уровня.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Stardos+Stencil:wght@400;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="font-body antialiased bg-background text-foreground selection:bg-white/20">
        {children}
      </body>
    </html>
  );
}