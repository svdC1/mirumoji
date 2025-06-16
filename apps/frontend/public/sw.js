// public/sw.js
self.addEventListener("install", (e) => {
    // immediately take control
    self.skipWaiting();
  });
  self.addEventListener("activate", (e) => {
    self.clients.claim();
  });
  