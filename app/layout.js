import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "YTTMP3.com - YouTube to MP3 Converter | Fast & Free",
  description: "Convert YouTube videos to high-quality MP3 files instantly. Free, fast, and secure YouTube to MP3 converter. No registration required - Download MP3 from YouTube now!",
  keywords: "youtube to mp3, youtube converter, mp3 converter, youtube downloader, free mp3, audio converter",
  authors: [{ name: "YTTMP3.com" }],
  openGraph: {
    title: "YTTMP3.com - YouTube to MP3 Converter",
    description: "Convert YouTube videos to high-quality MP3 files instantly. Free, fast, and secure.",
    url: "https://yttmp3.com",
    siteName: "YTTMP3.com",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "YTTMP3.com - YouTube to MP3 Converter",
    description: "Convert YouTube videos to high-quality MP3 files instantly. Free, fast, and secure.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

// Next.js 15: move viewport and themeColor into the dedicated viewport export
export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#4f46e5",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="canonical" href="https://yttmp3.com" />
        <meta name="google-site-verification" content="your-google-verification-code" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
