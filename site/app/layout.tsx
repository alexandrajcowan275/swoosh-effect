import type { Metadata, Viewport } from 'next';
import localFont from 'next/font/local';
import './globals.css';
import story from '@/data/story.json';

const display = localFont({ src: '../node_modules/@fontsource/barlow-condensed/files/barlow-condensed-latin-800-normal.woff2', weight: '800', display: 'swap', variable: '--font-display' });
const body = localFont({ src: [
  { path: '../node_modules/@fontsource/inter/files/inter-latin-400-normal.woff2', weight: '400' },
  { path: '../node_modules/@fontsource/inter/files/inter-latin-600-normal.woff2', weight: '600' },
], display: 'swap', variable: '--font-body' });

const deploymentHost = process.env.VERCEL_PROJECT_PRODUCTION_URL || process.env.VERCEL_URL;
export const metadata: Metadata = {
  metadataBase: new URL(deploymentHost ? `https://${deploymentHost}` : 'http://localhost:3000'),
  title: 'The Swoosh Effect | Alexandra Cowan',
  description: story.copy.subhead,
  authors: [{ name: 'Alexandra Cowan', url: story.links.linkedin }],
  openGraph: { type: 'website', title: story.copy.hero, description: story.copy.subhead, siteName: 'The Swoosh Effect', images: [{ url: '/share.png', width: 1200, height: 630, alt: story.copy.hero }] },
  twitter: { card: 'summary_large_image', title: story.copy.hero, description: story.copy.subhead, images: ['/share.png'] },
  icons: { icon: '/icon.svg' },
};
export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#000000' };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${display.variable} ${body.variable}`}>{children}</body></html>;
}
