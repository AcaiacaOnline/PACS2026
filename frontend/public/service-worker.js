/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'pac-acaiaca-v1';
const STATIC_CACHE = 'pac-static-v1';
const DYNAMIC_CACHE = 'pac-dynamic-v1';

// Recursos estáticos para cache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/brasao-acaiaca.png',
  '/bg-acaiaca.png'
];

// URLs que devem ser sempre buscadas da rede (API)
const NETWORK_ONLY = [
  '/api/'
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Instalando Service Worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Cache de recursos estáticos');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Service Worker instalado com sucesso');
        return self.skipWaiting();
      })
      .catch((err) => {
        console.error('[SW] Erro na instalação:', err);
      })
  );
});

// Ativação do Service Worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Ativando Service Worker...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
            .map((name) => {
              console.log('[SW] Removendo cache antigo:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker ativado');
        return self.clients.claim();
      })
  );
});

// Interceptação de requisições
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar requisições não-GET
  if (request.method !== 'GET') {
    return;
  }

  // Ignorar requisições de extensões do Chrome
  if (url.protocol === 'chrome-extension:') {
    return;
  }

  // API: Network first, cache fallback
  if (NETWORK_ONLY.some(path => url.pathname.startsWith(path))) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cachear resposta de API bem sucedida
          if (response.ok) {
            const clonedResponse = response.clone();
            caches.open(DYNAMIC_CACHE)
              .then((cache) => cache.put(request, clonedResponse));
          }
          return response;
        })
        .catch(() => {
          // Fallback para cache se offline
          return caches.match(request);
        })
    );
    return;
  }

  // Recursos estáticos: Cache first, network fallback
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          // Retornar do cache e atualizar em background
          fetch(request)
            .then((response) => {
              if (response.ok) {
                caches.open(STATIC_CACHE)
                  .then((cache) => cache.put(request, response));
              }
            })
            .catch(() => {});
          return cachedResponse;
        }

        // Não encontrado no cache, buscar da rede
        return fetch(request)
          .then((response) => {
            if (!response.ok) {
              return response;
            }
            const clonedResponse = response.clone();
            caches.open(DYNAMIC_CACHE)
              .then((cache) => cache.put(request, clonedResponse));
            return response;
          })
          .catch(() => {
            // Página offline
            if (request.destination === 'document') {
              return caches.match('/index.html');
            }
            return new Response('Offline', { status: 503 });
          });
      })
  );
});

// Sincronização em background (para quando voltar online)
self.addEventListener('sync', (event) => {
  console.log('[SW] Sincronização em background:', event.tag);
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push recebido');
  
  let data = {
    title: 'Planejamento Acaiaca',
    body: 'Nova notificação',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png'
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: data.badge,
      vibrate: [100, 50, 100],
      data: data.data || {},
      actions: data.actions || []
    })
  );
});

// Click em notificação
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notificação clicada');
  event.notification.close();

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Se já tem uma janela aberta, focar nela
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            return client.focus();
          }
        }
        // Senão, abrir nova janela
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
  );
});

// Função auxiliar para sincronização
async function syncData() {
  console.log('[SW] Sincronizando dados...');
  // Implementar lógica de sincronização se necessário
}
