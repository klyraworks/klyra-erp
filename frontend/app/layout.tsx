// app/layout.tsx

import type React from "react"
import type {Metadata} from "next"
import {Inter, Geist_Mono} from "next/font/google"
import {Analytics} from "@vercel/analytics/next"
import "./globals.css"
import "@/public/fontawesome/css/all.css"
import {StoreProvider} from "@/src/core/store"
import {ThemeProvider} from "@/src/core/theme/provider"
import {Toaster} from 'react-hot-toast'

const inter = Inter({subsets: ["latin"]})
const _geistMono = Geist_Mono({subsets: ["latin"]})

export const metadata: Metadata = {
    title: "Klyra ERP - Sistema de Gestión Empresarial",
    description: "Sistema ERP para gestión de ventas, inventario, finanzas y recursos humanos",
    generator: "v0.app",
    icons: {
        icon: [
            {
                url: "/icon-light-32x32.png",
                media: "(prefers-color-scheme: light)",
            },
            {
                url: "/icon-dark-32x32.png",
                media: "(prefers-color-scheme: dark)",
            },
            {
                url: "/icon.svg",
                type: "image/svg+xml",
            },
        ],
        apple: "/apple-icon.png",
    },
}

export default function RootLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="es" suppressHydrationWarning>
        <head/>
        <body className="font-sans antialiased" suppressHydrationWarning>
        <script
            dangerouslySetInnerHTML={{
                __html: `
              (function() {
                try {
                  const theme = localStorage.getItem('klyra_theme');
                  if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                    document.documentElement.classList.add('dark');
                  }
                } catch (e) {}
              })();
            `,
            }}
        />
        <Toaster position="top-right" reverseOrder={false}/>
        <ThemeProvider>
            <StoreProvider>
                {children}
            </StoreProvider>
        </ThemeProvider>
        <Analytics/>
        </body>
        </html>
    )
}