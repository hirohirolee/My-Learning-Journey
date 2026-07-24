import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "十大機器學習演算法：全方位動態學習報告",
  description: "NCHU AI Training 互動網頁教材 - 結合 Face API 表情感知與互動式數學沙盒。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-Hant" className="scroll-smooth">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
