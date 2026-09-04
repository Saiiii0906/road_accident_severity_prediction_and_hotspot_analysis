import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  Bell,
  CheckCheck,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  BrainCircuit,
  Gauge,
  MapPinned,
  Navigation,
  ShieldAlert,
  Info,
  Trash2,
  BellOff,
} from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  useNotifications,
  type NotificationType,
  type VantageNotification,
} from "@/lib/notifications";
import { cn } from "@/lib/utils";

function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case "journey_success":
      return <Navigation className="h-4 w-4 text-success" aria-hidden="true" />;
    case "journey_failure":
      return <AlertCircle className="h-4 w-4 text-destructive" aria-hidden="true" />;
    case "gemini_fallback":
      return <BrainCircuit className="h-4 w-4 text-warning" aria-hidden="true" />;
    case "severe_risk":
      return <ShieldAlert className="h-4 w-4 text-destructive" aria-hidden="true" />;
    case "severity_prediction":
      return <Gauge className="h-4 w-4 text-primary" aria-hidden="true" />;
    case "hotspot_analysis":
      return <MapPinned className="h-4 w-4 text-primary" aria-hidden="true" />;
    case "system":
    default:
      return <Info className="h-4 w-4 text-muted-foreground" aria-hidden="true" />;
  }
}

function formatRelativeTime(isoString: string): string {
  try {
    const diffMs = Date.now() - new Date(isoString).getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return "Just now";
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDays = Math.floor(diffHr / 24);
    return `${diffDays}d ago`;
  } catch {
    return "Recently";
  }
}

export function NotificationPopover() {
  const [open, setOpen] = useState(false);
  const { notifications, unreadCount, markAsRead, markAllAsRead, clearAll } = useNotifications();

  const handleNotificationClick = (item: VantageNotification) => {
    if (!item.read) {
      markAsRead(item.id);
    }
    if (item.link) {
      setOpen(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative text-muted-foreground hover:text-foreground"
          aria-label={`Notifications (${unreadCount} unread)`}
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 ? (
            <span className="absolute top-1.5 right-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-bold text-accent-foreground shadow-sm">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          ) : null}
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-80 sm:w-96 p-0 shadow-lg border-border bg-card"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-bold text-foreground">Notifications</h4>
            {unreadCount > 0 ? (
              <Badge variant="secondary" className="text-[11px] px-1.5 py-0 font-medium">
                {unreadCount} unread
              </Badge>
            ) : null}
          </div>

          <div className="flex items-center gap-1">
            {unreadCount > 0 ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                onClick={markAllAsRead}
                title="Mark all as read"
              >
                <CheckCheck className="h-3.5 w-3.5 mr-1" />
                Mark all read
              </Button>
            ) : null}

            {notifications.length > 0 ? (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                onClick={clearAll}
                title="Clear all notifications"
                aria-label="Clear all notifications"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            ) : null}
          </div>
        </div>

        {/* List of items */}
        <div className="max-h-[380px] overflow-y-auto divide-y divide-border/50">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
              <div className="grid h-10 w-10 place-items-center rounded-full bg-muted/60 text-muted-foreground mb-3">
                <BellOff className="h-5 w-5" />
              </div>
              <p className="text-sm font-medium text-foreground">No notifications</p>
              <p className="mt-1 text-xs text-muted-foreground max-w-[220px]">
                Safety analysis updates, risk alerts, and system notices will appear here.
              </p>
            </div>
          ) : (
            notifications.map((item) => {
              const inner = (
                <div
                  onClick={() => handleNotificationClick(item)}
                  className={cn(
                    "flex items-start gap-3 p-3.5 text-left transition-colors cursor-pointer hover:bg-muted/40",
                    !item.read && "bg-accent/5 font-medium",
                  )}
                >
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg border border-border/80 bg-background mt-0.5">
                    {getNotificationIcon(item.type)}
                  </span>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <p
                        className={cn(
                          "text-xs leading-snug truncate",
                          item.read ? "text-foreground font-medium" : "text-foreground font-bold",
                        )}
                      >
                        {item.title}
                      </p>
                      <span className="shrink-0 text-[10px] text-muted-foreground">
                        {formatRelativeTime(item.timestamp)}
                      </span>
                    </div>

                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground line-clamp-2">
                      {item.message}
                    </p>
                  </div>

                  {!item.read && (
                    <span
                      className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary"
                      aria-label="Unread"
                    />
                  )}
                </div>
              );

              return item.link ? (
                <Link key={item.id} to={item.link} className="block">
                  {inner}
                </Link>
              ) : (
                <div key={item.id}>{inner}</div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        {notifications.length > 0 && (
          <div className="px-4 py-2 border-t border-border bg-muted/20 text-center">
            <span className="text-[11px] text-muted-foreground">
              Notifications stored locally in workspace
            </span>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
