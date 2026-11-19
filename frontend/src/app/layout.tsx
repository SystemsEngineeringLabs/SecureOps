import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "SecureOps — Security Operations & GRC Platform",
  description:
    "Unified platform for security operations, compliance management, risk assessment, and audit readiness.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="secureops">
      <body className="min-h-screen bg-base-100">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
