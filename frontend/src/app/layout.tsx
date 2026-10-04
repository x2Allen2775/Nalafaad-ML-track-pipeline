import type { Metadata, Viewport } from "next";
import "./globals.css";
/*color kardunga iskoo*/

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};
/*color kardunga iskoo*/

export const metadata: Metadata = {
  title: "SplitSnap | Proportional Bill Splitter",
  description:
    "OCR-free restaurant receipt parsing and mathematically fair proportional bill splitting.",
};
/*color kardunga iskoo*/

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-100 min-h-screen selection:bg-zinc-800 selection:text-white antialiased">
        {children}
      </body>
    </html>
  );
}
/*color kardunga iskoo*/
