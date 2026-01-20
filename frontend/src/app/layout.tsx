/**
 * Root Layout Component
 * Next.js App Router layout.
 */

import type { Metadata } from 'next';
import '../styles/globals.css';
import { ErrorBoundary } from '../components/ErrorBoundary';

export const metadata: Metadata = {
  title: 'Voice-First Travel Assistant',
  description: 'Plan your trip with voice commands',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}
