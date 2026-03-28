# 19 — Event Emitter Bus (TypeScript)

**Categories:** Memory Leaks, Type Safety, Error Handling, Iteration Safety

## Bug 1: No Maximum Listener Limit (Memory Leak)

The `on()` method allows unlimited listeners to be registered for any event. If a component repeatedly calls `on()` without a corresponding `off()` (e.g., re-registering on every render cycle or reconnection), listeners accumulate indefinitely and are never garbage collected. Unlike Node.js's `EventEmitter`, which warns at 10 listeners by default, this implementation has no limit or warning.

**Fix:** Add a configurable `maxListeners` option and warn or throw when exceeded:

```typescript
on<K extends keyof Events>(event: K, handler: EventHandler<Events[K]>): void {
  const handlers = this.listeners.get(event) ?? [];
  if (handlers.length >= this.options.maxListeners) {
    console.warn(`[EventBus] Max listeners (${this.options.maxListeners}) exceeded for "${String(event)}"`);
  }
  // ...
}
```

## Bug 2: Error in One Listener Kills All Subsequent Listeners

The `emit()` method iterates through handlers and calls each one directly with no error handling. If any listener throws an exception, the `for...of` loop terminates immediately and all remaining listeners for that event are silently skipped. This means a single buggy listener can break the entire event pipeline.

**Fix:** Wrap each handler call in a try/catch:

```typescript
for (const handler of handlers) {
  try {
    handler(payload);
  } catch (error) {
    console.error(`[EventBus] Error in listener for "${String(event)}":`, error);
  }
}
```

## Bug 3: `once()` Cannot Be Removed — Arrow Function Reference Mismatch

The `once()` method wraps the original handler in a new `wrappedHandler` arrow function and registers **that** with `on()`. However, it then calls `this.off(event, handler)` (the original handler reference) inside the wrapper. Since `off()` searches for the original `handler` reference in the listeners array, but the array actually contains `wrappedHandler`, the `indexOf` check always returns -1 and the listener is never removed. The "once" listener fires on every emit.

**Fix:** Remove the `wrappedHandler` reference instead, or store a mapping:

```typescript
once<K extends keyof Events>(event: K, handler: EventHandler<Events[K]>): void {
  const wrappedHandler = (payload: Events[K]) => {
    handler(payload);
    this.off(event, wrappedHandler); // remove wrappedHandler, not handler
  };
  this.on(event, wrappedHandler);
}
```

## Bug 4: Listeners Array Mutated During Iteration

When `emit()` iterates over the handlers array with `for...of`, and a handler triggers a removal (e.g., via `once()` or an explicit `off()` call inside a listener), the `splice()` in `off()` mutates the same array that is currently being iterated. This can cause listeners to be skipped or the iteration to behave unpredictably, depending on the index of the removed element.

**Fix:** Iterate over a shallow copy of the handlers array:

```typescript
emit<K extends keyof Events>(event: K, payload: Events[K]): void {
  const handlers = this.listeners.get(event);
  if (!handlers) return;

  const snapshot = [...handlers];
  for (const handler of snapshot) {
    handler(payload);
  }
}
```

## Bug 5: Global Singleton Loses Type Safety

The `getGlobalBus()` function creates a single `TypedEventBus<any>` instance. Once created with any type parameter, all subsequent calls return the same instance regardless of the generic type passed. This means `getGlobalBus<AppEvents>()` and `getGlobalBus<OtherEvents>()` return the same object, but TypeScript shows different types. The `any` in `globalBus: TypedEventBus<any>` erases all type safety, allowing any event name and payload to be emitted without compile-time errors.

**Fix:** Avoid a globally typed singleton. Instead, export a pre-typed instance or use a factory:

```typescript
// Export a typed instance directly
export const appBus = new TypedEventBus<AppEvents>();

// Or use a factory pattern without caching
function createBus<Events extends EventMap>(options?: EventBusOptions): TypedEventBus<Events> {
  return new TypedEventBus<Events>(options);
}
```
