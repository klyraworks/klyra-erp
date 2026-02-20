"use client";

import { useEffect, useState, useRef } from "react";
import {
  Package,
  DollarSign,
  ShoppingCart,
  Truck,
  Users,
  BarChart3,
} from "lucide-react";

const features = [
  {
    icon: Package,
    title: "Inventario",
    description:
      "Control total de stock, productos, categorias, bodegas y movimientos en tiempo real.",
  },
  {
    icon: DollarSign,
    title: "Finanzas",
    description:
      "Gestion de cuentas por cobrar, pagar, flujo de caja y reportes financieros.",
  },
  {
    icon: ShoppingCart,
    title: "Ventas",
    description:
      "Cotizaciones, ordenes de venta, facturacion y seguimiento de clientes.",
  },
  {
    icon: Truck,
    title: "Compras",
    description:
      "Ordenes de compra, gestion de proveedores y control de costos.",
  },
  {
    icon: Users,
    title: "RRHH",
    description:
      "Administracion de empleados, nominas, asistencia y evaluaciones.",
  },
  {
    icon: BarChart3,
    title: "Reportes",
    description:
      "Dashboards personalizables con metricas clave para tomar decisiones.",
  },
];

export function Features() {
  const [isVisible, setIsVisible] = useState(false);
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
      id="features"
      className="py-24 lg:py-32 bg-muted/30"
    >
      <div className="container mx-auto px-4">
        {/* Section header */}
        <div className="max-w-2xl mx-auto text-center mb-16">
          <span
            className={`inline-block text-accent font-medium text-sm tracking-wider uppercase mb-4 transition-all duration-700 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
          >
            Caracteristicas
          </span>
          <h2
            className={`text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance transition-all duration-700 delay-100 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
          >
            Todo lo que necesitas, nada que no
          </h2>
          <p
            className={`text-muted-foreground text-lg transition-all duration-700 delay-200 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
          >
            Modulos integrados que trabajan en armonia para simplificar la
            gestion de tu empresa.
          </p>
        </div>

        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className={`transition-all duration-700 ${
                isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
              }`}
              style={{ transitionDelay: `${(index + 3) * 100}ms` }}
            >
              <div className="group h-full p-6 lg:p-8 rounded-xl bg-card border border-border hover:border-accent/50 transition-all duration-300 hover:shadow-lg hover:shadow-accent/5">
                <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-5 group-hover:bg-accent/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
