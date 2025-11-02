import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "대학교 데이터 시각화 대시보드",
  description: "대학교 데이터 시각화 대시보드 - Django REST + Next.js",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased">{children}</body>
    </html>
  );
}
