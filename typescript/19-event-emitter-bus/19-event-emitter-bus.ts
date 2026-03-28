// AI-generated PR — review this code
// Description: "Added typed event emitter bus for decoupled inter-module communication"

type EventHandler<T = any> = (payload: T) => void;

interface EventMap {
  [event: string]: any;
}

interface EventBusOptions {
  debugMode?: boolean;
}

class TypedEventBus<Events extends EventMap> {
  private listeners: Map<keyof Events, EventHandler[]> = new Map();
  private options: EventBusOptions;

  constructor(options: EventBusOptions = {}) {
    this.options = options;
  }

  /**
   * Register an event listener for a given event type.
   */
  on<K extends keyof Events>(event: K, handler: EventHandler<Events[K]>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }

    const handlers = this.listeners.get(event)!;
    handlers.push(handler);

    if (this.options.debugMode) {
      console.log(`[EventBus] Registered listener for "${String(event)}" (${handlers.length} total)`);
    }
  }

  /**
   * Register a one-time event listener that automatically removes itself.
   */
  once<K extends keyof Events>(event: K, handler: EventHandler<Events[K]>): void {
    const wrappedHandler = (payload: Events[K]) => {
      handler(payload);
      this.off(event, handler);
    };
    this.on(event, wrappedHandler);
  }

  /**
   * Remove a specific listener for an event.
   */
  off<K extends keyof Events>(event: K, handler: EventHandler<Events[K]>): void {
    const handlers = this.listeners.get(event);
    if (!handlers) return;

    const index = handlers.indexOf(handler);
    if (index !== -1) {
      handlers.splice(index, 1);
    }

    if (this.options.debugMode) {
      console.log(`[EventBus] Removed listener for "${String(event)}" (${handlers.length} remaining)`);
    }
  }

  /**
   * Emit an event, calling all registered listeners with the payload.
   */
  emit<K extends keyof Events>(event: K, payload: Events[K]): void {
    const handlers = this.listeners.get(event);
    if (!handlers) return;

    if (this.options.debugMode) {
      console.log(`[EventBus] Emitting "${String(event)}" to ${handlers.length} listeners`);
    }

    for (const handler of handlers) {
      handler(payload);
    }
  }

  /**
   * Remove all listeners for a specific event, or all events if no event specified.
   */
  removeAllListeners<K extends keyof Events>(event?: K): void {
    if (event) {
      this.listeners.delete(event);
    } else {
      this.listeners.clear();
    }
  }

  /**
   * Get the number of listeners for an event.
   */
  listenerCount<K extends keyof Events>(event: K): number {
    return this.listeners.get(event)?.length ?? 0;
  }

  /**
   * Pipe events from this bus to another bus.
   */
  pipe<K extends keyof Events>(event: K, target: TypedEventBus<Events>): void {
    this.on(event, (payload) => {
      target.emit(event, payload);
    });
  }
}

// Convenience: create a global singleton bus
let globalBus: TypedEventBus<any> | null = null;

function getGlobalBus<Events extends EventMap>(): TypedEventBus<Events> {
  if (!globalBus) {
    globalBus = new TypedEventBus<Events>();
  }
  return globalBus as TypedEventBus<Events>;
}

// --- Example usage ---

interface AppEvents {
  "user:login": { userId: string; timestamp: number };
  "user:logout": { userId: string };
  "notification:new": { message: string; level: "info" | "warn" | "error" };
  "data:sync": { records: number; duration: number };
}

const bus = new TypedEventBus<AppEvents>({ debugMode: true });

// Register listeners
bus.on("user:login", (payload) => {
  console.log(`User ${payload.userId} logged in at ${payload.timestamp}`);
});

bus.on("user:login", (payload) => {
  // Analytics tracking
  fetch("/api/analytics/track", {
    method: "POST",
    body: JSON.stringify({ event: "login", userId: payload.userId }),
  });
});

bus.on("notification:new", (payload) => {
  if (payload.level === "error") {
    console.error(`[ALERT] ${payload.message}`);
  }
});

// One-time listener
bus.once("data:sync", (payload) => {
  console.log(`Initial sync complete: ${payload.records} records in ${payload.duration}ms`);
});

// Emit events
bus.emit("user:login", { userId: "user_123", timestamp: Date.now() });
bus.emit("notification:new", { message: "Welcome back!", level: "info" });
bus.emit("data:sync", { records: 150, duration: 320 });
bus.emit("data:sync", { records: 10, duration: 50 }); // once listener should not fire

export { TypedEventBus, getGlobalBus };
export type { EventHandler, EventMap, EventBusOptions, AppEvents };
