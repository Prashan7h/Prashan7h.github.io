import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Population Graphs - Global Data Visualization',
  description: 'Interactive graphs showing global population and life expectancy data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}
