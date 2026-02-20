// frontend/src/middleware/middleware.ts

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const host = request.headers.get('host') || '';
  const url = request.nextUrl.clone();

  // Dominio principal → mostrar landing (NO redirigir)
  if (host === 'localhost:3000' || host === '127.0.0.1:3000' ||
      host === 'klyra.com' || host === 'www.klyra.com') {

    // Si intenta acceder a rutas protegidas, redirigir a landing
    if (url.pathname.startsWith('/inventario') ||
        url.pathname.startsWith('/ventas') ||
        url.pathname.startsWith('/compras') ||
        url.pathname.startsWith('/finanzas') ||
        url.pathname.startsWith('/rrhh') ||
        url.pathname.startsWith('/dashboard') ||
        url.pathname.startsWith('/login')) {
      return NextResponse.redirect(new URL('/', request.url));
    }

    // Permitir acceso a landing
    return NextResponse.next();
  }

  // Subdominios (.local o .klyra.com) → permitir app
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};