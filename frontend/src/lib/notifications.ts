import { useState, useEffect, useCallback } from "react";

export type NotificationType =
  | "journey_success"
  | "journey_failure"
  | "gemini_fallback"
  | "severe_risk"
  | "severity_prediction"
  | "hotspot_analysis"
  | "system";

export interface VantageNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string; // ISO string
  read: boolean;
  link?: string;
}

export const NOTIFICATIONS_STORAGE_KEY = "vantage_notifications";
const NOTIFICATIONS_EVENT_KEY = "vantage:notifications-changed";

export function loadNotifications(): VantageNotification[] {
  if (typeof window === "undefined") {
    return [];
  }
  try {
    const raw = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    console.error("Failed to load notifications from localStorage", e);
    return [];
  }
}

export function saveNotifications(notifications: VantageNotification[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifications));
    window.dispatchEvent(new CustomEvent(NOTIFICATIONS_EVENT_KEY));
  } catch (e) {
    console.error("Failed to save notifications to localStorage", e);
  }
}

export function addNotification(params: {
  type: NotificationType;
  title: string;
  message: string;
  link?: string;
}): VantageNotification {
  const newNotif: VantageNotification = {
    id: `notif_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    type: params.type,
    title: params.title,
    message: params.message,
    timestamp: new Date().toISOString(),
    read: false,
    link: params.link,
  };

  const current = loadNotifications();
  // Keep up to 50 latest notifications
  const updated = [newNotif, ...current.slice(0, 49)];
  saveNotifications(updated);
  return newNotif;
}

export function markNotificationRead(id: string): void {
  const current = loadNotifications();
  let changed = false;
  const updated = current.map((n) => {
    if (n.id === id && !n.read) {
      changed = true;
      return { ...n, read: true };
    }
    return n;
  });
  if (changed) {
    saveNotifications(updated);
  }
}

export function markAllNotificationsRead(): void {
  const current = loadNotifications();
  const updated = current.map((n) => ({ ...n, read: true }));
  saveNotifications(updated);
}

export function clearAllNotifications(): void {
  saveNotifications([]);
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<VantageNotification[]>([]);

  useEffect(() => {
    setNotifications(loadNotifications());

    const handleUpdate = () => {
      setNotifications(loadNotifications());
    };

    window.addEventListener(NOTIFICATIONS_EVENT_KEY, handleUpdate);
    window.addEventListener("storage", handleUpdate);

    return () => {
      window.removeEventListener(NOTIFICATIONS_EVENT_KEY, handleUpdate);
      window.removeEventListener("storage", handleUpdate);
    };
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAsRead = useCallback((id: string) => {
    markNotificationRead(id);
  }, []);

  const markAllAsRead = useCallback(() => {
    markAllNotificationsRead();
  }, []);

  const clearAll = useCallback(() => {
    clearAllNotifications();
  }, []);

  const notify = useCallback(
    (params: { type: NotificationType; title: string; message: string; link?: string }) => {
      return addNotification(params);
    },
    [],
  );

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearAll,
    notify,
  };
}
