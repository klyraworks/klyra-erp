import "@/src/landing/landing.css";
import {
  Hero,
  Features,
  Benefits,
  Pricing,
  Testimonials,
  CTA,
  Footer,
} from "@/src/landing";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <Hero />
      <Features />
      <Benefits />
      <Pricing />
      <Testimonials />
      <CTA />
      <Footer />
    </main>
  );
}
