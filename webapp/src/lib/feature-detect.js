export const isMobile = /Mobile|Android|iPad|iPhone|iPod/i.test(navigator.userAgent) ||
(navigator.platform === 'MacIntel' && navigator.standalone)

export const supportsNotifications = 'Notification' in window

export const supportsDesktopNotifications = supportsNotifications && !isMobile
export const supportsWebPushNotifications = supportsNotifications && 'serviceWorker' in navigator && 'PushManager' in window
