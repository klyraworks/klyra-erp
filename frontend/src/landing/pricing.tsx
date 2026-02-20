"use client";

import { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Check, ArrowRight, Sparkles } from "lucide-react";

const plans = [
  {
    name: "Starter",
    description: "Para pequenas empresas que inician su transformacion digital",
    price: "11.99",
    period: "/mes",
    features: [
      "Hasta 3 usuarios",
      "Inventario basico",
      "Ventas y facturacion",
      "Reportes esenciales",
      "Soporte por email",
    ],
    cta: "Comenzar gratis",
    popular: false,
  },
  {
    name: "Business",
    description: "Para empresas en crecimiento que necesitan mas poder",
    price: "144",
    period: "/año",
    features: [
      "Hasta 15 usuarios",
      "Todos los modulos",
      "Multi-bodega",
      "APIs de integracion",
      "Soporte prioritario",
      "Capacitacion incluida",
    ],
    cta: "Comenzar ahora",
    popular: true,
  },
  {
    name: "Enterprise",
    description: "Para grandes organizaciones con necesidades especificas",
    price: "Personalizado",
    period: "",
    features: [
      "Usuarios ilimitados",
      "Multi-empresa",
      "Personalizacion avanzada",
      "SLA garantizado",
      "Gerente de cuenta dedicado",
      "Implementacion asistida",
    ],
    cta: "Contactar ventas",
    popular: false,
  },
];

export function Pricing() {
  const [isVisible, setIsVisible] = useState(false);
  const [hoveredPlan, setHoveredPlan] = useState<string | null>(null);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="pricing"
      className="relative py-32 lg:py-40 bg-muted/30 overflow-hidden"
    >
      {/* Background decoration */}
      <div className="absolute inset-0">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
      </div>

      <div className="container relative mx-auto px-4">
        {/* Section header */}
        <div className="max-w-3xl mx-auto text-center mb-20">
          <span
            className={`inline-block text-accent font-semibold text-sm tracking-[0.2em] uppercase mb-6
              transition-all duration-1000 ease-elegant ${
                isVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-8"
              }`}
          >
            Precios
          </span>
          <h2
            className={`text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-6 text-balance
              transition-all duration-1000 delay-100 ease-elegant ${
                isVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-8"
              }`}
          >
            Planes que{" "}
            <span className="gradient-text">crecen contigo</span>
          </h2>
          <p
            className={`text-xl text-muted-foreground leading-relaxed
              transition-all duration-1000 delay-200 ease-elegant ${
                isVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-8"
              }`}
          >
            Sin contratos a largo plazo. Cancela cuando quieras.
            <br className="hidden sm:block" />
            Todos los planes incluyen 14 dias de prueba gratis.
          </p>
        </div>

        {/* Pricing cards */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={plan.name}
              className={`transition-all duration-700 ease-elegant ${
                isVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-12"
              }`}
              style={{ transitionDelay: `${(index + 3) * 100}ms` }}
              onMouseEnter={() => setHoveredPlan(plan.name)}
              onMouseLeave={() => setHoveredPlan(null)}
            >
              <div
                className={`relative h-full flex flex-col rounded-2xl border overflow-hidden
                  transition-all duration-500 ease-elegant ${
                    plan.popular
                      ? "bg-primary border-primary shadow-2xl shadow-primary/20 scale-105 z-10"
                      : `bg-card border-border/50 ${
                          hoveredPlan === plan.name
                            ? "border-accent/50 shadow-xl shadow-accent/10 -translate-y-2"
                            : ""
                        }`
                  }`}
              >
                {/* Popular badge with animation */}
                {plan.popular && (
                  <div className="absolute -top-px left-1/2 -translate-x-1/2">
                    <div className="relative">
                      <div className="absolute inset-0 bg-accent blur-sm opacity-50" />
                      <span className="relative flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold bg-accent text-accent-foreground rounded-b-lg">
                        <Sparkles className="w-3 h-3" />
                        Mas popular
                      </span>
                    </div>
                  </div>
                )}

                <div className="p-8 lg:p-10 flex flex-col h-full">
                  {/* Plan header */}
                  <div className="mb-8">
                    <h3
                      className={`text-2xl font-semibold mb-2 ${
                        plan.popular ? "text-primary-foreground" : "text-foreground"
                      }`}
                    >
                      {plan.name}
                    </h3>
                    <p
                      className={`text-sm leading-relaxed ${
                        plan.popular
                          ? "text-primary-foreground/70"
                          : "text-muted-foreground"
                      }`}
                    >
                      {plan.description}
                    </p>
                  </div>

                  {/* Price */}
                  <div className="mb-8">
                    <div className="flex items-baseline gap-1">
                      <span
                        className={`font-bold ${
                          plan.popular ? "text-primary-foreground" : "text-foreground"} ${
                          plan.price === "Personalizado" ? "text-4xl" : "text-5xl"
                        }`}
                      >
                        {plan.price !== "Personalizado" && "$"}
                        {plan.price}
                      </span>
                      <span
                        className={`text-lg ${
                          plan.popular
                            ? "text-primary-foreground/70"
                            : "text-muted-foreground"
                        }`}
                      >
                        {plan.period}
                      </span>
                    </div>
                  </div>

                  {/* Features */}
                  <ul className="space-y-4 mb-10 flex-grow">
                    {plan.features.map((feature, featureIndex) => (
                      <li
                        key={feature}
                        className={`flex items-start gap-3 transition-all duration-500 ${
                          isVisible
                            ? "opacity-100 translate-x-0"
                            : "opacity-0 -translate-x-4"
                        }`}
                        style={{
                          transitionDelay: `${(index * 100) + (featureIndex * 50) + 500}ms`,
                        }}
                      >
                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                            plan.popular ? "bg-accent/30" : "bg-accent/10"
                          }`}
                        >
                          <Check className="w-3 h-3 text-accent" />
                        </div>
                        <span
                          className={
                            plan.popular
                              ? "text-primary-foreground/90"
                              : "text-foreground"
                          }
                        >
                          {feature}
                        </span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA Button */}
                  <Button
                    className={`group w-full py-6 text-base font-medium transition-all duration-300 ${
                      plan.popular
                        ? "bg-accent text-accent-foreground hover:bg-accent/90"
                        : "bg-primary text-primary-foreground hover:bg-primary/90"
                    }`}
                    size="lg"
                  >
                    {plan.cta}
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </Button>
                </div>

                {/* Decorative corner gradient */}
                {!plan.popular && (
                  <div
                    className={`absolute -bottom-20 -right-20 w-40 h-40 rounded-full transition-all duration-700 ${
                      hoveredPlan === plan.name
                        ? "bg-accent/10 scale-150"
                        : "bg-accent/5 scale-100"
                    }`}
                  />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Trust indicators */}
        <div
          className={`mt-16 text-center transition-all duration-1000 delay-700 ease-elegant ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <p className="text-muted-foreground">
            Mas de{" "}
            <span className="font-semibold text-foreground">500 empresas</span>{" "}
            confian en Klyra para gestionar sus operaciones
          </p>
        </div>
      </div>
    </section>
  );
}
