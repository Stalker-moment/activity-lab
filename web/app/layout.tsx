import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Activity Lab — Live Model Testing",
  description:
    "Uji pengenalan aktivitas menggunakan ANN dan X-CLIP zero-shot pada kamera lokal.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
