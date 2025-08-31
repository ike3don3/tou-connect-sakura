// TOU Connect Service Worker
const CACHE_NAME = 'tou-connect-v1.0.0';
const urlsToCache = [
  '/',
  '/static/css/modern.css',
  '/static/js/app.js',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// インストール時のキャッシュ
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('キャッシュを開きました');
        return cache.addAll(urlsToCache);
      })
  );
});

// フェッチ時のキャッシュ戦略
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // キャッシュにあればそれを返す
        if (response) {
          return response;
        }

        return fetch(event.request).then((response) => {
          // 有効なレスポンスかチェック
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // レスポンスのクローンを作成
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      }).catch(() => {
        // ネットワークエラー時のフォールバック
        if (event.request.destination === 'document') {
          return caches.match('/');
        }
      })
  );
});

// アップデート時の古いキャッシュ削除
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('古いキャッシュを削除:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// バックグラウンド同期
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // オフライン時に蓄積されたデータの同期処理
  return new Promise((resolve) => {
    // 実際の同期処理をここに実装
    console.log('バックグラウンド同期を実行');
    resolve();
  });
}

// プッシュ通知
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : '新しい学友候補が見つかりました！',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '確認する',
        icon: '/static/icons/check.png'
      },
      {
        action: 'close',
        title: '閉じる',
        icon: '/static/icons/cross.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('TOU Connect', options)
  );
});

// 通知クリック処理
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});
