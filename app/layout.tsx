import type {Metadata} from "next";import "./globals.css";
export const metadata:Metadata={title:"Visual Wiring Definition Tool",description:"Design, validate, and export pin-to-pin electrical connections."};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
