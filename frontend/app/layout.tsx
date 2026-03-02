import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FIN-QA RedSun Dashboard",
  description: "Financial document analysis dashboard with mocked retrieval pipeline."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
